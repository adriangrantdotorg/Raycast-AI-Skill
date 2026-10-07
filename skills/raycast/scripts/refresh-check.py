#!/usr/bin/env python3
"""Is the raycast skill current with the live Raycast docs, manual and packages?

Compares references/FRESHNESS.json (what the skill was last checked against) with:
  - npm: latest @raycast/api and @raycast/utils
  - github.com/raycast/extensions: commits touching docs/ (the source of developers.raycast.com,
    store guidelines included) since the stamped commit
  - manual.raycast.com/llms-full.txt: every page's text, hashed per page

Prints one ✅ line when nothing changed, or a 🔄 list of what to read. When an API or utils version
jumped, it also runs `tsc --noEmit` and `ray lint` (the new version's CLI) on every extension in your
Raycast repo (RAYCAST_REPO), in throwaway copies (your checkouts and node_modules are never touched). Lint findings are
compared with a baseline, so only NEW ones (a new store or manifest rule) are reported. Exit 0 = current or offline,
10 = refresh needed. One network check per day per stamp; later runs that day reuse the result.

  refresh-check.py                     check (cached for the day)
  refresh-check.py --force             check now, ignore the day cache
  refresh-check.py --diff-manual <p>   unified diff of one manual page (url or slug) since the stamp
  refresh-check.py --checks            tsc + ray lint on every extension against the latest npm versions now
  refresh-check.py --checks --baseline  same, then accept today's lint findings as the baseline
  refresh-check.py --stamp             after updating the references: write today's live state (and accept
                                       the lint findings of the last version-jump run as the new baseline)
"""
import datetime, difflib, hashlib, json, os, re, shutil, subprocess, sys, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = os.path.join(SKILL, "references", "FRESHNESS.json")
CACHE = os.path.expanduser("~/Library/Caches/raycast-skill-refresh/day.json")
TYPECHECK_DIR = os.path.expanduser("~/Library/Caches/raycast-skill-refresh/typecheck")
SNAPSHOT_DIR = os.path.expanduser("~/Library/Application Support/raycast-skill-refresh/manual")
LINT_BASELINE = os.path.expanduser("~/Library/Application Support/raycast-skill-refresh/lint-baseline.json")
LINT_PENDING = os.path.expanduser("~/Library/Caches/raycast-skill-refresh/lint-pending.json")
RAYCAST_REPO = os.environ.get("RAYCAST_REPO", os.path.expanduser("~/Raycast"))
REPO = "raycast/extensions"
MANUAL = "https://manual.raycast.com/llms-full.txt"
TODAY = datetime.date.today().isoformat()


def fetch(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode("utf-8")


def npm_latest(pkg):
    return json.loads(fetch(f"https://registry.npmjs.org/{pkg}/latest", 8))["version"]


def gh(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=20)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "gh api failed")
    return json.loads(out.stdout)


def mmddyy(iso):
    y, m, d = iso[:10].split("-")
    return f"{m}-{d}-{y[2:]}"


def slug(url):
    return url.removeprefix("https://manual.raycast.com/").strip("/").replace("/", "__") or "index"


def manual_pages():
    """{page url: page text} from the manual's single LLM dump; a page starts at its `Source:` line."""
    text = fetch(MANUAL)
    pages = {}
    for block in text.split("\nSource: ")[1:]:
        url, _, body = block.partition("\n")
        # The next page's heading sits at the end of this block; drop it so a new neighbour isn't a change.
        body = re.sub(r"\n#{2,3} [^\n]*\s*$", "\n", body)
        pages[url.strip()] = body.strip()
    if len(pages) < 20:
        raise RuntimeError(f"manual dump looks wrong ({len(pages)} pages)")
    return pages


def page_hash(text):
    # "Last updated" alone moves on cosmetic edits; hash the content without it.
    return hashlib.sha256(re.sub(r"^Last updated: .*$", "", text, flags=re.M).encode()).hexdigest()[:16]


def live_state(pages):
    head = gh(f"repos/{REPO}/commits?path=docs&per_page=1")[0]
    return {
        "api": npm_latest("@raycast/api"),
        "utils": npm_latest("@raycast/utils"),
        "docs_commit": head["sha"],
        "docs_commit_date": head["commit"]["committer"]["date"][:10],
        "manual": {u: page_hash(t) for u, t in sorted(pages.items())},
    }


def docs_changes(since_sha):
    """Commits on docs/ after the stamped one, with the files each touched."""
    cmp = gh(f"repos/{REPO}/compare/{since_sha}...HEAD")
    lines, files = [], set()
    for c in cmp.get("commits", []):
        detail = gh(f"repos/{REPO}/commits/{c['sha']}")
        docs = [f["filename"] for f in detail.get("files", []) if f["filename"].startswith("docs/")
                and not f["filename"].startswith("docs/.gitbook/")]
        if not docs:
            continue
        files.update(docs)
        lines.append(f"  {mmddyy(c['commit']['committer']['date'])} {c['commit']['message'].splitlines()[0]}")
    return lines, sorted(files)


def manual_changes(old, new):
    changed = sorted(u for u in new if u in old and old[u] != new[u])
    added = sorted(u for u in new if u not in old)
    removed = sorted(u for u in old if u not in new)
    out = []
    for label, urls in (("changed", changed), ("new", added), ("removed", removed)):
        if urls:
            out.append(f"  manual pages {label}: " + ", ".join(u.removeprefix("https://manual.raycast.com/") or "/" for u in urls))
    if changed:
        out.append("  read one: refresh-check.py --diff-manual <page>")
    return out


def save_snapshot(pages):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    for f in os.listdir(SNAPSHOT_DIR):
        os.remove(os.path.join(SNAPSHOT_DIR, f))
    for url, text in pages.items():
        with open(os.path.join(SNAPSHOT_DIR, slug(url) + ".md"), "w") as f:
            f.write(text + "\n")


def diff_manual(page):
    url = page if page.startswith("http") else "https://manual.raycast.com/" + page.strip("/")
    new = manual_pages().get(url)
    if new is None:
        print(f"❌ No manual page {url}")
        return 1
    path = os.path.join(SNAPSHOT_DIR, slug(url) + ".md")
    old = open(path).read() if os.path.exists(path) else ""
    if not old:
        print(f"(no snapshot of {url}; showing the whole page)\n")
    sys.stdout.writelines(difflib.unified_diff(old.splitlines(True), (new + "\n").splitlines(True),
                                               "stamped", "live"))
    return 0


def extensions():
    """Extension folders in the MAIN checkout of your Raycast repo (RAYCAST_REPO) (folders with a package.json naming @raycast/api)."""
    out = []
    for root, dirs, files in os.walk(RAYCAST_REPO):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".git", ".claude", "assets", "swift")]
        if "package.json" in files and root != RAYCAST_REPO:
            pkg = json.load(open(os.path.join(root, "package.json")))
            if "@raycast/api" in {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}:
                out.append(root)
                dirs[:] = []
    return sorted(out)


def run(cmd, cwd, timeout=300):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def prepare_copy(ext):
    """A throwaway copy of one extension, node_modules kept between runs; returns its folder."""
    name = os.path.relpath(ext, RAYCAST_REPO)
    work = os.path.join(TYPECHECK_DIR, name.replace("/", "__"))
    os.makedirs(work, exist_ok=True)
    for item in os.listdir(work):
        if item != "node_modules":
            p = os.path.join(work, item)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    for item in os.listdir(ext):
        if item in ("node_modules", "dist", "swift", "design", ".git") or item.endswith(".app"):
            continue
        src = os.path.join(ext, item)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(work, item), symlinks=True)
        else:
            shutil.copy2(src, work)
    return name, work


def lint_findings(output, work):
    """`ray lint` output → normalized findings: no paths, line numbers, versions or request ids, and never the
    "Invalid author" error (personal extensions often use an author name that is not a Store account)."""
    found = set()
    for line in output.splitlines():
        line = line.replace(work + "/", "").replace(work, "")
        m = re.match(r"^\s*(?:\d+:\d+\s+)?(error|warning)\s+(.*)$", line)
        if not m or "Invalid author" in line or "linting issues found" in line:
            continue
        msg = re.sub(r"\d+\.\d+\.\d+", "X", m.group(2))
        msg = re.sub(r"\s+RequestID.*", "", msg).strip()
        found.add(f"{m.group(1)}: {msg}")
    return sorted(found)


def checks(api, utils, baseline_now=False):
    """tsc --noEmit + ray lint for every extension, on a copy with the new @raycast/api / utils installed."""
    exts = extensions()
    if not exts:
        return [f"  🧪 checks: no extensions found in {RAYCAST_REPO}"]
    try:
        baseline = json.load(open(LINT_BASELINE))
    except Exception:
        baseline = {}
    lines, results = [f"  🧪 tsc + ray lint against API {api}, utils {utils}:"], {}
    for ext in exts:
        name, work = prepare_copy(ext)
        pkg = json.load(open(os.path.join(work, "package.json")))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        wanted = [f"@raycast/api@{api}"] + ([f"@raycast/utils@{utils}"] if "@raycast/utils" in deps else [])
        quiet = ["--no-audit", "--no-fund", "--ignore-scripts", "--loglevel=error"]
        inst = run(["npm", "install", *quiet], work)
        if inst.returncode == 0:
            inst = run(["npm", "install", *quiet, "--no-save", *wanted], work)
        if inst.returncode != 0:
            lines.append(f"    ⚠️ {name}: npm install failed: {(inst.stderr.strip().splitlines() or ['?'])[-1]}")
            continue
        problems = []
        tsc = run(["npx", "--no-install", "tsc", "--noEmit", "-p", "."], work)
        if tsc.returncode != 0:
            errors = [l for l in tsc.stdout.splitlines() if ": error TS" in l]
            problems.append(f"❌ tsc: {len(errors) or '?'} error(s)")
            problems += [f"   {l}" for l in (errors or tsc.stdout.splitlines() or tsc.stderr.splitlines())[:8]]
        lint = run(["npx", "--no-install", "ray", "lint"], work)
        found = lint_findings(lint.stdout + "\n" + lint.stderr, work)
        results[name] = found
        new = [f for f in found if f not in baseline.get(name, [])]
        if new and not baseline_now:
            problems.append(f"⚠️ ray lint: {len(new)} new finding(s) (fix: ray lint --fix, or by hand)")
            problems += [f"   {f}" for f in new[:12]]
        if problems:
            lines.append(f"    {name}:")
            lines += [f"      {p}" for p in problems]
        else:
            lines.append(f"    ✅ {name}")
    os.makedirs(os.path.dirname(LINT_PENDING), exist_ok=True)
    target = LINT_BASELINE if baseline_now else LINT_PENDING
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w") as f:
        json.dump(results, f, indent=2)
    if baseline_now:
        lines.append(f"  📌 lint baseline saved: {sum(len(v) for v in results.values())} known finding(s)")
    return lines


def main():
    args = sys.argv[1:]
    if args[:1] == ["--diff-manual"] and len(args) == 2:
        return diff_manual(args[1])
    stamp = json.load(open(STAMP))
    try:
        pages = manual_pages()
        live = live_state(pages)
    except Exception as e:  # offline or gh not signed in: never block work
        print(f"⚠️ Raycast skill refresh check skipped: {e}")
        return 0

    if "--checks" in args or "--typecheck" in args:
        print("\n".join(checks(live["api"], live["utils"], baseline_now="--baseline" in args)))
        return 0

    if "--stamp" in args:
        live["checked"] = TODAY
        with open(STAMP, "w") as f:
            json.dump(live, f, indent=2)
            f.write("\n")
        save_snapshot(pages)
        if os.path.exists(LINT_PENDING):  # the session reviewed the jump's new findings: they are known now
            os.makedirs(os.path.dirname(LINT_BASELINE), exist_ok=True)
            shutil.move(LINT_PENDING, LINT_BASELINE)
        print(f"✅ Stamped: API {live['api']}, utils {live['utils']}, docs through "
              f"{mmddyy(live['docs_commit_date'])}, manual {len(pages)} pages")
        return 0

    key = json.dumps([stamp, live], sort_keys=True)
    if "--force" not in args:
        try:
            cache = json.load(open(CACHE))
            if cache.get("day") == TODAY and cache.get("key") == key:
                print(cache["text"])
                return cache["code"]
        except Exception:
            pass

    out = []
    jumped = False
    for pkg in ("api", "utils"):
        if live[pkg] != stamp.get(pkg):
            jumped = True
            out.append(f"  @raycast/{pkg}: {stamp.get(pkg)} → {live[pkg]} "
                       f"(npm diff: npm diff --diff=@raycast/{pkg}@{stamp.get(pkg)} --diff=@raycast/{pkg}@{live[pkg]})")
    if live["docs_commit"] != stamp.get("docs_commit"):
        commits, files = docs_changes(stamp["docs_commit"])
        if commits:
            out.append("  docs commits:")
            out += ["  " + c for c in commits]
            out.append("  docs files: " + ", ".join(f.removeprefix("docs/") for f in files))
    out += manual_changes(stamp.get("manual", {}), live["manual"])
    if jumped:
        out += checks(live["api"], live["utils"])

    if out:
        text = f"🔄 Raycast skill needs a refresh (last checked {mmddyy(stamp['checked'])}):\n" + "\n".join(out)
        code = 10
    else:
        text = (f"✅ Raycast skill is current: API {live['api']}, utils {live['utils']}, "
                f"docs through {mmddyy(live['docs_commit_date'])}, manual {len(pages)} pages")
        code = 0
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w") as f:
        json.dump({"day": TODAY, "key": key, "text": text, "code": code}, f)
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
