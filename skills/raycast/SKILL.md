---
name: raycast
description: "Best practices and workflows for developing and modifying Raycast Extensions (React/Node) AND Raycast Script Commands (shell scripts with @raycast metadata). Use this skill whenever the user wants to create, update, or troubleshoot anything that runs inside Raycast — extensions, script commands, menu-bar commands, AI extension tools, deeplinks, quicklinks. Triggers include: 'make a Raycast command', 'Raycast script command', 'fix my Raycast script', '@raycast.title', registering a Script Directory, useCachedPromise, useFetch, useForm, popToRoot, MenuBarExtra, raycast:// deeplinks, a red warning triangle beside 'Command' in root search, extensions missing after a Raycast 2 upgrade or v1 migration, calling AppleScript/shell/SSH from Raycast, or any task involving Raycast script command files. Use even when the user asks for a 'quick automation' or 'Raycast hotkey' without explicitly naming the type — Claude should pick script command vs extension based on the task."
---

# Raycast Development

This skill defines the preferred workflow and best practices for building, modifying, and troubleshooting Raycast **Extensions** (React/Node) and **Script Commands** (shell scripts with `@raycast.*` metadata).

## 0. Reference files — read the one that matches the task

The sections below are the rules. The exact signatures and doc facts live in `references/`, distilled from developers.raycast.com and manual.raycast.com (API 2.5.0, @raycast/utils 2.3.0), re-checked against Raycast 2.6.2 and refreshed to npm API 2.7.0 (live stamp: `references/FRESHNESS.json`; npm: utils 2.3.2; the docs changelog has no API change after 2.5.0, so the v2 differences are app-side and live in section 3 *Raycast 2* and `references/script-commands-and-app.md` *Raycast 2 app*):

| 📄 File | Open it when you are… |
|---|---|
| `references/platform.md` | editing `package.json` (commands, modes, `interval`, arguments, preferences, `platforms`), using LaunchProps / background refresh / deeplinks, running `ray` CLI commands, debugging, building AI tools / `ai.yaml` / evals |
| `references/api-reference.md` | writing UI or calling `@raycast/api`: List, Grid, Form, Detail, Actions, MenuBarExtra, Toast/HUD/Alert, Clipboard, Cache, LocalStorage, Keyboard shortcuts, launchCommand, OAuth, AI.ask, WindowManagement, BrowserExtension |
| `references/utils-hooks.md` | picking or configuring a `@raycast/utils` hook (usePromise, useCachedPromise, useFetch, useExec, useSQL, useForm, useFrecencySorting…), pagination, optimistic `mutate`, runAppleScript, OAuthService, and changelog / migration / ESM questions |
| `references/script-commands-and-app.md` | writing a Script Command (every `@raycast.*` key, arguments, output per mode, exit codes), or using app features: aliases, hotkeys, Hyper Key, quicklinks, Dynamic Placeholders, `raycast://` URLs, MCP, Raycast AI skills, logs |

*Trigger:* you are about to write a Raycast prop, option, manifest key, or metadata key you have not checked in this session. *Discrimination:* the rules below are enough for workflow decisions; they are not enough for exact names and defaults (`filtering`, `keepPreviousData`, `refreshTime`…), which drift between API versions. *Action:* grep the matching reference file first. If it is missing or looks stale, ask the live docs: `curl -s 'https://developers.raycast.com/readme.md?ask=<question>'` (the answer comes back with excerpts), or grep `https://developers.raycast.com/llms-full.txt` (two parts, the second at `/llms-full.txt/1`) and `https://manual.raycast.com/llms-full.txt`. Then add what you learned to the reference file.

**Refresh step: run this first, every time the skill loads.**
*Trigger:* this skill was just loaded, for any Raycast task. *Discrimination:* the references are a snapshot; Raycast ships API versions every few days (2.5.0 → 2.7.0 in two weeks), the docs on developers.raycast.com come from `docs/` in github.com/raycast/extensions (store guidelines included), and manual.raycast.com changes pages almost daily. The per-prop live check above only catches what you happen to look up; this catches everything new. Nothing runs between sessions: never turn this into a scheduled job without asking. *Action:*
1. `python3 ~/.claude/skills/raycast/scripts/refresh-check.py` (one network check per day, reused after that; offline prints ⚠️ and exits 0, so carry on). It compares npm `@raycast/api` / `@raycast/utils`, new `docs/` commits, and every manual page (hashed, from `manual.raycast.com/llms-full.txt`) with `references/FRESHNESS.json`.
2. ✅ = current: say nothing about it, start the task.
3. 🔄 = something is newer. Before the task, read only what it lists:
   - a version jump: the printed `npm diff` command, filtered to `types/index.d.ts` and the `dist/commands/` file list (the bundle is minified). A jump also runs **🧪 tsc + ray lint** on a throwaway copy of every extension in the user's extensions folder with the new versions installed, so `ray lint` is the NEW CLI with its new store and manifest rules (copies in `~/Library/Caches/raycast-skill-refresh/typecheck/`, the user's checkouts and `node_modules` untouched). Lint is compared with a baseline (`~/Library/Application Support/raycast-skill-refresh/lint-baseline.json`); only NEW findings show, and an "Invalid author" error can be dropped for personal extensions with no Store account. A tsc ❌ is a defect in the extension: fix it in that repo the same turn (then reinstall it in dev mode), or say plainly ❌ Not fixed and why. A new lint ⚠️ is a new rule: one line in the reply naming it and the extension, fixed only if it changes how the extension works in Raycast (store-only style rules stay as they are unless the user asks). `--stamp` then accepts that run's findings into the baseline. `--checks` runs both on demand; `--checks --baseline` re-records the baseline after the user fixes or changes something.
   - docs files: `gh api repos/raycast/extensions/contents/docs/<file> --jq .content | base64 -d`, or the listed commit's diff.
   - manual pages: `refresh-check.py --diff-manual <page>` diffs a page against the snapshot taken at the last stamp (`~/Library/Application Support/raycast-skill-refresh/manual/`). Read only pages about things this skill covers (extensions, script commands, aliases, hotkeys, Hyper Key, quicklinks, placeholders, deeplinks, AI commands / tools / MCP / skills, import-export, troubleshooting, settings); billing, enterprise and the like need nothing.

   Add each change that matters to the matching reference file as a tagged line (`[API 2.7.0]`, `[utils v2.3.2]`, `[MAN 10-07-26]`), update the version note at the top of section 0, then `refresh-check.py --stamp` (it also saves the new manual snapshot). A change that touches one of the user's extensions gets one line in the reply; everything else stays out of it.

## 1. Decide: Script Command or Extension?

Pick the simplest tool that fits. Choosing wrong adds complexity (Extensions) or hits walls (Script Commands).

**Use a Script Command when:**
- The action is a single shell invocation (run a command, fire a magic packet, restart a service, SSH somewhere and run something).
- No UI is needed beyond a brief HUD-style success/failure toast, or one line of live text in root search (`inline` mode + `refreshTime`).
- No persistent state, no dropdowns populated from APIs, no multi-step forms. (A fixed dropdown argument is fine: `"type": "dropdown"` with `data`.)
- A single `.sh` (or `.py`, `.swift`, etc.) file is enough — no `npm install`, no build step.

**Use an Extension when:**
- The user needs a form, a list, a dropdown populated from an API, or any other interactive UI.
- The command has multiple steps that the user navigates between.
- It integrates with an external API and needs to manage tokens via Raycast preferences.
- It needs caching, debouncing, background refresh on a schedule, a menu-bar item, or tools Raycast AI can call.

**Before either, check the built-ins.** A URL with a slot is a **Quicklink** (`{argument name="query"}`, up to 3 arguments, any app deeplink works). Fixed text is a **Snippet**. One prompt run on selected text is an **AI Command**. None of these needs code.

When in doubt, lean Script Command first. Migrating up to an Extension later is easy; downgrading a half-built Extension to a Script Command feels like wasted work.

## 2. Script Commands

### Anatomy

A Script Command is a single executable file with `@raycast.*` metadata comments near the top. Minimal template:

```bash
#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title My Command
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🔧
# @raycast.packageName Personal
# @raycast.description Does the thing.
# @raycast.argument1 { "type": "text", "placeholder": "Optional input", "optional": true }
# @raycast.needsConfirmation false
```

**Modes — what each shows:**

| Mode | Shows | Use for |
|---|---|---|
| `compact` | LAST line of stdout in a toast | Best default for personal automations |
| `silent` | LAST line (if any) as a HUD after the window closes | Fire-and-forget |
| `inline` | FIRST line inside the root-search row, re-run every `refreshTime` | Live status (favorite it for a dashboard) |
| `fullOutput` | All stdout in a terminal-like view | Long output or long-running jobs |

Other languages work too — use `#!/usr/bin/env python3`, `#!/usr/bin/env node`, `.applescript`, etc. The metadata format is the same (`//` comments work too).

**Metadata keys the template leaves out** (full list: `references/script-commands-and-app.md`):
- `@raycast.needsConfirmation true` — a confirm alert before running. Use it on anything destructive.
- `@raycast.refreshTime 1m` — `inline` only, minimum `10s`. `inline` WITHOUT it silently behaves like `compact`. Only the first 10 inline commands refresh on their own.
- `@raycast.currentDirectoryPath ~/somewhere` — default is the script's own folder.
- `@raycast.iconDark` — dark-theme icon. `packageName` defaults to the script folder's name.
- Arguments: max 3; `type` is `text` / `password` / `dropdown` (dropdown needs `data: [{"title","value"}]`); `percentEncoded: true` for URL use; arguments are REQUIRED unless `"optional": true`; values arrive as `$1 $2 $3`, an omitted optional one as `""`.

### Registration

1. Place the script in a stable directory (e.g. `~/raycast-scripts/`).
2. `chmod +x` the file.
3. In Raycast 2: **Settings → Script Commands → Add Script Directory** → point at the directory (v1 had it under Settings → Extensions → `+`). Or run **Create Script Command** to scaffold one into a directory already added.
4. Raycast auto-picks up metadata edits — no restart needed.

**A script that never shows up** fails one of: all 3 required keys present (`schemaVersion`, `title`, `mode`), not executable, or its filename contains `.template.` (Raycast ignores those on purpose).

### Critical gotchas

These bite every time and aren't obvious from Raycast's documentation:

- **Minimal PATH.** Raycast runs script commands in a NON-login shell and only appends `/usr/local/bin` — `/opt/homebrew/bin` (Apple Silicon Homebrew) is missing. Tools like `wakeonlan`, `jq`, `ffmpeg`, `gh`, `kubectl` will fail with "command not found" even though they work in Terminal. Locate them explicitly (or `export PATH="/opt/homebrew/bin:$PATH"` at the top, or a `#!/bin/bash -l` shebang):
  ```bash
  TOOL=""
  if command -v wakeonlan &> /dev/null; then
    TOOL="$(command -v wakeonlan)"
  else
    for p in /opt/homebrew/bin /usr/local/bin; do
      [ -x "$p/wakeonlan" ] && TOOL="$p/wakeonlan" && break
    done
  fi
  ```

- **SSH calls need `BatchMode` and `ConnectTimeout`.** Without `-o BatchMode=yes`, a failed key auth falls back to a password prompt that hangs Raycast indefinitely. Without `-o ConnectTimeout=N`, an unreachable host blocks until the system-level timeout (~75 seconds). Pattern:
  ```bash
  ssh -o BatchMode=yes -o ConnectTimeout=5 user@host "command"
  ```

- **Errors: print the reason LAST, then exit non-zero.** A non-zero exit shows a failure toast, and in `compact`/`inline` the last output line becomes the error text: `echo "Mac Mini is asleep"; exit 1`. Chatty tools (`zip` without `-q`, progress bars) break `compact`/`silent`/`inline` — quiet them or use `fullOutput`.

- **macOS `/bin/bash` 3.2 misparses a quoted heredoc inside `$( )`.** *Trigger:* `syntax error near unexpected token` on a line of Python or another language inside `X="$(python3 - <<'PY' … PY)"`, often after adding a line with `'` or `(`. *Discrimination:* the heredoc is quoted and correct; bash 3.2 still scans its body for quotes and parentheses while matching the `$( )`, so an odd number of apostrophes in comments (`Raycast 2's`) or a `r'…'` string breaks it, and `bash -n` fails while bash 5 passes. *Action:* read the heredoc into a variable outside the substitution, `read -r -d '' SRC <<'PY' || true` … `PY`, then `X="$(python3 -c "$SRC")"`; check with `/bin/bash -n`.
- **Test from Terminal first.** In `compact` mode Raycast suppresses stderr by default. If a script silently fails when run via Raycast but works in Terminal, suspect a PATH or environment difference and add explicit absolute paths. Reproduce with a stripped env: `env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/local/bin ./script.sh`.

- **Permissions belong to Raycast.** Accessibility, Automation, and Full Disk Access prompts name Raycast, not Terminal. A script that works in Terminal can still need its own grant for Raycast.

- **Arguments are optional UI surface.** Hardcoding values in a CONFIG block at the top of the script is often cleaner for personal automations than exposing arguments. Use `@raycast.argument1` only when variability actually helps.

- **Hotkey- and refresh-triggered scripts must be idempotent** — "ensure X is on" beats a toggle that drifts out of sync.

- **Clone-and-deprecate before editing an existing Script Command.** *Trigger:* the user points at an existing script file and asks to modify, fix, rewrite or "make a new version of" it. *Discrimination:* a brand-new script needs no clone. Every subfolder of a Script Directory is scanned, so a clone left as `.sh` shows up in root search as a second command; Raycast only loads known extensions, so the `.disabled` suffix is what "disabled" means here. *Action:* (1) BEFORE touching it: `mkdir -p "<Script Directory>/Deprecated"` and `cp -p` the file to `Deprecated/<Original Name> [Deprecated MM-DD-YY].sh.disabled` (date from `date +%m-%d-%y`; a second clone the same day adds ` h:MM AM/PM`), then `cmp` the two; (2) edit the ORIGINAL file in place, so its alias and hotkey (stored by path) keep working; (3) a comment in the new script names the clone; (4) rollback = rename the clone back to `.sh` over the original (one `mv`). Keep the clone until the user has tried the new version and kept it.

- **"Show X in the Raycast prompt / title" usually means the ROOT-SEARCH ROW, and a title can never change.** *Trigger:* the user asks for live data (the playing track, a count, a status) "in the Raycast prompt", "in the title", or circles the command's name in a root-search screenshot. *Discrimination:* the same words can be read as a search box prefilled with the data, which is a different build. What can change in the row: a title NEVER (`@raycast.title` and `package.json` titles are static); an extension command's gray SUBTITLE can (`updateCommandMetadata({ subtitle })`); a script command only via `@raycast.mode inline` + `refreshTime` (min 10 s), which is polling. Keeping a subtitle current needs an event source (e.g. Spotify's distributed notification `com.spotify.client.PlaybackStateChanged`), i.e. a background helper: ask before building it. *Action:* when the words could mean the row or a box, ask in the user's own terms ("the row in root search, or a box after it opens?") BEFORE building; state plainly that the title itself cannot change and offer the subtitle.

### When NOT to use a Script Command

If the script ends up needing any of these, migrate to an Extension instead:
- Dropdown populated dynamically from an API.
- Form with multiple fields the user fills in.
- Cached/debounced state across runs.
- Branching UI based on results (a list of items the user picks from).

## 3. Extension Scaffolding & Setup

- **Preferred Method (Duplication)**: The fastest way to start a new extension is often duplicating the folder of an *existing* extension. If you do this, you must carefully update the `package.json`:
  - `"name"`
  - `"title"`
  - `"description"`
  - `"author"`
  - `"commands"` array (update `name`, `title`, and `description`).
- **Standard Method**: If not duplicating, use `npx @raycast/api@latest create`, or Raycast's **Create Extension** command, whose templates include Show List, Show Grid, Submit Form, Menu Bar Extra, Run Script (no-view + HUD), Show Typeahead Results, and AI.
- **Adding a command to an existing extension**: Raycast's **Manage Extensions** → your extension → **Add New Command** (or **Add New Tool**, ⌥⌘T) updates `package.json` and scaffolds `src/<name>.tsx` in one step.
- **Local Dev**: After creating/duplicating, run `npm install` then `npm run dev` (`ray develop`). This builds the extension, imports it into the user's Raycast app, and starts a watcher. The build is finished once you see `ready - built extension successfully`. The import **persists after you stop the watcher**, so for a one-off install you can stop `ray develop` after the first successful build. `npm run build` (`ray build -e dist`) with no `-o` does NOT compile to `dist/`: it overwrites the installed copy in `~/.config/raycast/extensions/<name>/` from the checkout it runs in (no `dist/` folder appears, and the installed source map points at that checkout). For a compile-and-type check that leaves Raycast alone, use `npx ray build -e dist -o <scratch dir>` or `npx tsc --noEmit -p .`; to change what Raycast loads, use `ray develop`.
- **One-shot import from a session (no watcher left running).** *Trigger:* you changed an extension and need Raycast to load it, but nobody will watch a dev terminal. *Discrimination:* `npm run build` overwrites the installed copy without a proper import (section 3); a `ray develop` left running keeps a watcher alive in the background. *Action:* start `npm run dev > <scratch>/dev.log 2>&1` in the background, wait with `until grep -qE 'built extension successfully|rror' <log>; do sleep 1; done`, then `pgrep -lf -- '<ext>/node_modules/.bin/ray develop'` and `kill <that PID>` (never a pattern kill). Confirm the install by reading `~/.config/raycast/extensions/<name>/package.json` or `cmp`-ing an asset.
- **Red ⚠️ triangle beside "Command" on every command of a dev extension = its import folder is gone.** *Trigger:* root search shows a red triangle on each command of one of your dev extensions; or an installed `~/.config/raycast/extensions/<name>/*.js.map` whose `sources` point into a `.claude/worktrees/<name>/` folder that no longer exists. *Discrimination:* Raycast keeps loading a dev import from the folder `ray develop` (or `ray build`) last ran in; a session in a worktree imports from the worktree, and when the worktree is deleted after merging, every command gets the triangle. A single command with a warning after a background run is a runtime error instead (section 9) — check the map paths first. Store installs map to `../src/…` inside their own folder and never do this. *Action:* re-import from the MAIN checkout. **Removing a dev extension:** delete its folder from the repo, then `~/.config/raycast/extensions/<name>/`; if a row still shows, ⌘K → Uninstall in Raycast. **Renaming the folder that holds your extensions:** every dev import breaks at once, because Raycast loads each by path. After the move, run `git worktree repair` on each worktree, re-import EVERY extension with `ray develop` (one may fail once on a transient build; re-run it), and search your scripts and configs for hardcoded copies of the old path.
- **Dev extensions vanish after the Raycast 2 upgrade or migration.** *Trigger:* after a Raycast update or a **Migrate from Raycast v1** run, your own dev commands are missing from root search (no triangle, just gone), or `grep -n 'Skipping unavailable local node extension' ~/Library/Logs/com.raycast.macos/raycast-x-*.log` names your `<author>/<name>` ids. *Discrimination:* Raycast 2.6.2's migration stored each dev import's folder as a `file://` URL with spaces left encoded (`My%20Extensions`), `stat`ed that literal path, failed with ENOENT and dropped every dev extension stored that way; Store extensions came across fine, and the built copies in `~/.config/raycast/extensions/<name>/` were still on disk, so the folder looking intact proves nothing. A `.rayconfig` export carries only Store extensions, never dev ones. A red triangle instead is the deleted-worktree case (previous bullet). A deeplink to such a command logs `Command not found: <cmd> in <ext>`. *Action:* re-import each with `ray develop` (the manual's own advice for custom extensions that didn't import). Then tell the user to check the aliases and hotkeys on those commands (the migration could not attach them while the extension was missing; v2 sets both from the Action Panel in root search), and that a re-run of **Migrate from Raycast v1** is additive and skips duplicates.
- **`ray develop` reaches Raycast 2 only while it is running.** *Trigger:* an import that "succeeds" but nothing shows in Raycast, or a session importing while Raycast is quit. *Discrimination:* the manual: `npm run dev` opens the extension in Raycast v2 if it is running and falls back to v1 otherwise, and v1 is gone after the upgrade. *Action:* check `pgrep -qx Raycast` first and `open -g -a Raycast` if it isn't running. Keep `@raycast/api` on the current major (`^2.x`, `@raycast/utils` `^2.x`) so the CLI carries v2's dev-command behavior; 1.x to 2.x had no breaking changes. After an upgrade merges, re-import each extension from main (`npm install` when `package.json` is newer than `node_modules`, then `ray develop`): until then Raycast keeps the build made with the old API. The CLI needs Node >= 22.22.2.
- **`EACCES … node_modules/esbuild/bin/esbuild` on `npm install` / `ray develop`.** *Trigger:* that error, or `[ -x node_modules/.bin/ray ]` false while the file exists. *Discrimination:* the deps are present but lost their executable bits (a `node_modules` copied or moved between folders); `npm install` on top does not repair it. *Action:* `rm -rf node_modules && npm ci` in that extension.
- **First view command in a no-view extension fails with TS17004 "Cannot use JSX unless the '--jsx' flag is provided".** *Trigger:* adding a `.tsx` command to an extension whose commands were all `.ts`. *Discrimination:* the tsconfig was written for no-view commands and has no `jsx` setting; the code is fine. *Action:* add `"jsx": "react-jsx"` to `compilerOptions`.
- **A failed rebuild keeps the OLD code running.** *Trigger:* the user says a change "didn't apply" while `ray develop` is running. *Discrimination:* the watcher only swaps in a build that compiled; a TypeScript error leaves the last good build loaded, and the only sign is the command icon (bottom-left) in a failed state. *Action:* read the `ray develop` terminal output (or `npx ray build -e dist`) for the error before touching anything else.
- **A subtitle set with `updateCommandMetadata` outlives every re-import.** *Trigger:* you change a command's `subtitle` in `package.json`, re-import, and root search still shows the old text. *Discrimination:* the runtime value is stored per command and wins over the manifest until that command calls `updateCommandMetadata` again; `ray develop` does not clear it, and renaming the command's `name` would (along with the user's alias and hotkey, so never do that for this). *Action:* have the command write the new subtitle itself on its next run, and tell the user the old text stays until they run it once.
- **`ray lint` errors that `ray build` ignores.** *Trigger:* `npx ray lint` fails on a personal extension. *Discrimination:* lint applies Store rules: `Invalid author "<handle>"` (the handle is not a Store user) and `must NOT have fewer than 2 characters` (a one-emoji subtitle like `🔊`) both fail lint while `ray build` / `ray develop` build fine. *Action:* for personal extensions, a clean `npx ray build -e dist -o <scratch>` is the check; fix lint-only findings only when publishing.
- **Other CLI commands** (`npx ray …`): `lint`, `migrate` (codemods to the latest API — review the diff), `bundle -o <path>` (a `.rayext` file, a way to archive or share a personal extension without the Store). Details in `references/platform.md`.
- **`package.json` hygiene**: set `"platforms": ["macOS"]` whenever the extension uses AppleScript or other macOS-only APIs. Never add a `"version"` field (Raycast has none). Keep `raycast-env.d.ts` gitignored and let the build regenerate it.
- **Renaming an existing extension**: changing the `name` field (and/or the source folder) makes Raycast treat it as a *new* development extension. The old entry lingers under Settings → Extensions pointing at the old path and must be removed manually, and preferences (`notionToken`, etc.) do **not** carry over to the new identity — they must be re-entered. Keep the command `name` in `package.json` in sync with its entry-point filename (`src/<command-name>.tsx`); `raycast-env.d.ts` is auto-generated from `package.json`, so let the build regenerate it rather than editing it by hand.
- **`Cannot find namespace 'Arguments'` (or `'Preferences'`) on build.** *Trigger:* `ray build` fails with TS2503 on `Arguments.X` / `Preferences.X`. *Discrimination:* the types exist — `raycast-env.d.ts` is generated at the extension root — but a `tsconfig.json` copied from an older extension only includes `src/**/*`. *Action:* set `"include": ["src/**/*", "raycast-env.d.ts"]`; check this whenever you duplicate a tsconfig.
- **ESM-only npm packages** need the whole extension converted to ESM (`"type": "module"`, `node16` module resolution, `.js` extensions on relative imports) — prefer a CommonJS alternative for a personal extension. Global `fetch` exists (API 1.94+); don't add `node-fetch`.

## 4. Extension UI & UX Requirements

When modifying or creating forms and commands, adhere to these standards:

- **Clean Inputs**: Do not set `defaultValue` with placeholder characters (e.g., `- ` for bullet points) unless explicitly requested. When a field needs explaining, the `info` prop (a tooltip) is an alternative to `placeholder` ghost text. Raycast's Store guidelines and ESLint rule (`@raycast/prefer-placeholders`) ask for placeholders; a personal extension that skips them can turn that rule off in `eslint.config.js`. Either way: command `arguments` REQUIRE a `placeholder` in `package.json` — it is the field's only label, so make it one short noun ("minutes"), never a sentence (the box cuts text off at about 17 characters).
- **Timing and progress feedback for fire-and-forget commands**: end with a confirmation that says what will happen and when (`⏱️ 5 min Timer Set` · `Ends at 4:58 PM`), not just "Started".
- **For confirmations the user waits on, consider a macOS notification with the extension's own icon instead of Raycast's HUD.** *Trigger:* a command confirms something the user will wait on (a timer set, a job started) or reports an error after its window closed, and you are about to call `showHUD` or a toast. *Discrimination:* `osascript display notification` is not a substitute: macOS labels it Script Editor and uses Script Editor's icon, not the extension's. Quick in-window feedback while a view stays open (an Animated toast during a save) is not this rule. *Action:* `await closeMainWindow({ clearRootSearch: true })` first, then post the notification from the extension's helper app, built so its icon is `assets/extension-icon.png` (recipe: section 7, *Native notifications with the extension's icon*).
- **Auto-Close on Success**: After successfully completing an action (like adding a Notion page, running a system script, etc.), the extension should disappear and return the user to the root Raycast search, rather than retaining the form on-screen.
  - Import: `import { popToRoot } from "@raycast/api";`
  - Execute: `await popToRoot({ clearSearchBar: true });`
  - In a `no-view` command, `showHUD(...)` closes the window itself. Call `await closeMainWindow()` BEFORE slow work (AppleScript, network) so the command feels instant.
- **Remembered values**: `storeValue` on a Form item restores the last submitted value next time — use it for fields the user repeats (a default database, a project). `<Form enableDrafts>` keeps an unsent form, but `popToRoot()` skips draft saving.
- **Validation**: use `useForm` + `FormValidation.Required` from `@raycast/utils` (spread `itemProps.x`) rather than hand-rolled `error` state. `onSubmit` never fires while any field shows an error.
- **Titles**: Title Case for command and action titles (`Copy to Clipboard`, `Open in Browser`); commands are `<Verb> <Noun>` (`Search Contacts`, `Create Task`). Don't set `navigationTitle` on a root command.
- **No flicker**: pass `isLoading` to the top-level view and don't render an empty list before data arrives; use `List.EmptyView` only for a real empty state.
- **Toasts for long work**: `const t = await showToast({ style: Toast.Style.Animated, title: "Saving…" })`, then set `t.style` / `t.title` to Success or Failure in place. A toast shown while the window is closed turns into a HUD.
- **Icon Changes**: If an extension's icon is modified (e.g., `extension-icon.png`), **Raycast must be fully restarted (⌘Q → reopen)** to reflect the change — the watcher rebuild alone is not enough. Always explicitly alert the user to "Restart Raycast" when you modify an icon. The icon file must be a **real PNG with alpha channel** (not a renamed JPEG) — use `sips -s format png source.jpg --out assets/extension-icon.png` to convert if needed. A dark-mode variant is just `icon@dark.png` next to `icon.png`. Changed list/asset icons (not the extension icon) refresh without a restart through the dev action that clears the local assets cache.
- **Icon transparency & the Antigravity JPEG trap.** When the user attaches an image in Antigravity chat, the platform silently converts it to JPEG, which **strips the alpha channel** — transparent areas become black. `sips -s format png` re-encodes the pixels but cannot restore lost transparency. To fix icons with baked-in black corners, use a Python flood-fill from the four corners (Pillow: `Image.convert("RGBA")`, then flood-fill near-black pixels reachable from `(0,0)`, `(w-1,0)`, `(0,h-1)`, `(w-1,h-1)` with `(0,0,0,0)`). Better yet: **ask the user for a filesystem path** to the original PNG instead of a chat attachment — e.g., "drop it in `~/Downloads/` and give me the path."

## 5. Extension Data Fetching & State

- **Pick the hook by data source** (all from `@raycast/utils`; options in `references/utils-hooks.md`):

  | Data comes from | Use |
  |---|---|
  | An async function (SDK call, Notion, files) | `useCachedPromise` — shows the last result instantly, then refreshes |
  | An HTTP endpoint | `useFetch` (headers/body in options, `mapResult` to reshape) |
  | A CLI / binary | `useExec(file, args, { parseOutput })` |
  | A local SQLite DB (Notes, Messages) | `useSQL` — return its `permissionView` first |
  | Result can't be JSON-serialized, or must never be stale | `usePromise` |
  | A no-view command or AI tool (no hooks allowed) | `withCache(fn, { maxAge })` / `executeSQL` / plain `await` |

- **`useCachedPromise` results must be JSON-serializable.** A `Date` comes back as a string on the next launch. Store ISO strings and convert when rendering.
- **Hooks already show a failure toast.** The default `onError` shows "Failed to fetch latest data" with a Retry action; pass `failureToastOptions: { title }` to reword it. Passing `onError` replaces the toast, so show your own inside it.
- **Search-as-you-type:** setting `onSearchTextChange` on a `List` turns OFF native filtering. Pass `searchText` into the hook's args, add `throttle`, and set `keepPreviousData: true` so the list doesn't flash empty between keystrokes. If you only want to watch the text, pass `filtering={true}` explicitly.
- **Pagination:** make the hook's function return `async ({ page, cursor }) => ({ data, hasMore, cursor })` and pass the returned `pagination` to `<List pagination={pagination}>`. Only page 1 is cached.
- **Mutations:** prefer `await mutate(apiCall(), { optimisticUpdate: (d) => … })` over calling `revalidate()` by hand — it updates the UI at once, rolls back on error, and revalidates after. Wrap it in try/catch: it rethrows.
- **Where to keep state:**

  | Store | For | Notes |
  |---|---|---|
  | `LocalStorage` / `useLocalStorage` | small durable user data | async, encrypted, `string \| number \| boolean` values |
  | `Cache` / `useCachedState` | disposable fetched data, instant first paint | sync, strings only, 10 MB LRU |
  | files in `environment.supportPath` | anything large | plain `fs` |

  The dev action "Clear Local Storage & Cache" wipes both of the first two.
- **Recently used first:** `useFrecencySorting(items, { key })`, calling `visitItem(item)` in the primary action.
- **Dynamic Forms**: For fields like Notion's `select`, `multi_select`, or integrations with existing playlists, dynamic `Form.TagPicker` or `Form.Dropdown` components should be populated via `useCachedPromise` rather than hardcoding.

## 6. Extension Automation & Local Execution

When an extension requires triggering local MacOS functionality (where external APIs fall short or aren't applicable):

- **AppleScript**: prefer `runAppleScript` from `@raycast/utils`, passing values as an `args` array instead of splicing them into the script text (no quoting bugs). The script reads them with `on run argv` / `item 1 of argv`. For structured results use `language: "JavaScript"` and return JSON; `humanReadableOutput` defaults to true and flattens lists. Default timeout is 10 s. Raw `execFileSync("/usr/bin/osascript", ["-e", script])` is still fine; never `execSync("osascript -e '...'")`.
  - *Example*: `await runAppleScript('on run argv\n tell application "Finder" to reveal (POSIX file (item 1 of argv))\nend run', [filePath])`
- **Handy system calls** (`@raycast/api`): `getSelectedText()`, `getSelectedFinderItems()`, `getFrontmostApplication()`, `open(target, app)`, `showInFinder`, `trash` (moves to Trash, never deletes). The first two REJECT when nothing is selected or Finder isn't frontmost — wrap in try/catch and show a failure toast.
- **Opening a URL in ONE exact app: `open -b <bundle id>`, never `open(url, "<bundle id>")`.** *Trigger:* a command must open a page in a specific browser (Chrome vs Chrome Beta, Edge vs Edge Beta). *Discrimination:* Raycast's `open(url, "com.google.Chrome")` launched **Chrome Beta**: it does not match the bundle id exactly. An app PATH (`/Applications/Google Chrome.app`) is exact too; no app at all means the default browser and is fine. *Action:* `execFile("/usr/bin/open", ["-b", bundleId, url])`; verify the id with `osascript -e 'POSIX path of (path to application id "<id>")'`.
- **Clipboard Operations**: Always use the native `Clipboard` utilities from `@raycast/api` (e.g., `Clipboard.copy(text)`) rather than custom bash scripts. `{ concealed: true }` keeps secrets out of clipboard history; `Clipboard.copy({ file: path })` copies a file; `Clipboard.readText({ offset: 1 })` reads back into history.
- **Native Mac sounds** (for alarms and alerts; confirm the choice with the user before building): classic short alerts in `/System/Library/Sounds/*.aiff` (Glass, Hero, Ping, Submarine…), longer modern tones in `/System/Library/PrivateFrameworks/ToneLibrary.framework/Versions/A/Resources/AlertTones/Modern/*.m4r` (Circles, Chord, Pulse…). Preview with `afplay <file>` or System Settings → Sound → Alert sound. To loop an alarm until it is closed, set `NSSound.loops = true` in a Swift helper.
- **Commands calling commands**: `launchCommand({ name, type: LaunchType.Background, context })` — e.g. a form refreshing its menu-bar item after saving. The target reads `props.launchContext`.
- **Reconsider scope**: If the extension's *entire* purpose is to fire a single shell command, a Script Command is simpler. Extensions earn their weight when there's actual UI or state involved.

## 7. Native Binaries & Asset Bundling

When an extension shells out to a compiled binary (Swift, Go, Rust, etc.):

- **Put binaries in `assets/`.** Raycast copies `assets/` to the installed extension directory (`~/.config/raycast/extensions/<name>/assets/`). Files outside `assets/` (e.g., `swift/`, `bin/`) are **not copied** and will fail with "No such file or directory" at runtime.
- **Reference via `environment.assetsPath`.** Use `path.join(environment.assetsPath, "binary-name")` — never construct paths relative to the source tree with `..`.
- **Use `execFileSync`, not `execSync`.** The user's workspace path often contains spaces (e.g., `Raycast Scripts/…`, a Google Drive path). `execSync(cmd)` runs through a shell and breaks on unquoted spaces. `execFileSync(path, args)` bypasses the shell entirely and handles spaces safely. (In a view command, `useExec(path, args)` does the same with caching.)
  ```typescript
  // ✅ Correct — handles spaces, no shell quoting needed
  const stdout = execFileSync(BRIDGE_PATH, ["--search", query], { encoding: "utf8" });

  // ❌ Breaks on paths with spaces
  const stdout = execSync(`${BRIDGE_PATH} --search "${query}"`, { encoding: "utf8" });
  ```
- **Ensure execute permission.** After compiling or copying the binary, run `chmod +x` on the asset.
- **Work that must outlive the command (timers, alarms, watchers).** *Trigger:* a command has to act minutes later ("remind me in 5 min", "alert when done"). *Discrimination:* a `no-view` command is unloaded as soon as its promise resolves, and background `interval` is approximate and at least 1m — neither can hold a precise countdown. *Action:* launch a helper from `assets/` that runs on its own: an app bundle via `execFile("/usr/bin/open", ["-n", "-g", "-a", app, "--args", ...args])` (runs under launchd; `-n` = one instance per job, `-g` = no focus steal), or a bare binary via `spawn(bin, args, { detached: true, stdio: "ignore" }).unref()` when it posts no notifications. Then confirm with a notification (section 4) and return. The helper owns the wait (use a wall-clock deadline, e.g. `DispatchQueue.main.asyncAfter(wallDeadline:)`, so Mac sleep doesn't delay it) and any UI. Verify it survives: its PPID is 1 after the parent exits.
- **Listing and cancelling what detached helpers are doing.** *Trigger:* the user wants to see or stop jobs a command started ("show my running timers", "cancel that timer"). *Discrimination:* the extension cannot remember them itself — the command that started the helper is already unloaded, `LocalStorage` would go stale when a helper ends or crashes, and killing processes by a name pattern is unsafe. *Action:* the HELPER keeps one record per live job, `~/Library/Application Support/com.<your-handle>.raycast.<name>/running/<pid>.json` (label, `endsAt` epoch ms, flags, a `ringing`-style state it rewrites when the state changes), written atomically at start and removed on close; it handles SIGTERM with `signal(SIGTERM, SIG_IGN)` + `DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)` whose handler runs the normal close path (stop sound, remove record, terminate). A `view` command lists the records, checks each PID with one `ps -p <pids> -o pid=,comm=` call (keep only rows whose comm is the helper binary; delete records whose PID is gone), ticks a `setInterval` every second for a live countdown, and cancels by `process.kill(pid, "SIGTERM")` ONLY after re-confirming that PID is still the helper. Give it `keywords` matching the start command so it shows up under the same alias letters. Test headlessly: start a job with `open -n -g -a`, list, cancel, list again (empty), and `pgrep -lf -- "<App>.app/Contents/MacOS/<binary>"` shows nothing. **Cancel ONLY the PIDs your test started** (`pgrep -x <binary>` before and after launching, act on the difference): the user may have a real job running, and a test that cancels "everything listed" will kill it.
- **Native notifications with the extension's icon.** *Trigger:* an extension must post a macOS notification (section 4 says confirmations are notifications). *Discrimination:* Raycast's API has no native-notification call; a bare binary cannot use `UNUserNotificationCenter` (it needs a bundle id); `osascript display notification` works but shows as Script Editor. *Action:* ship the helper as `assets/<Name>.app`, built by a script in the repo (`swift/build.sh`) that (1) compiles into `Contents/MacOS/` with `-framework AppKit -framework UserNotifications`, (2) makes `Contents/Resources/AppIcon.icns` from `assets/extension-icon.png` (`sips -z` into an `.iconset` at 16–512 plus @2x, then `iconutil -c icns`), (3) writes an `Info.plist` with a `com.<your-handle>.raycast.<name>` id, `CFBundleIconFile` = `AppIcon`, `LSUIElement` true, and (4) ad-hoc signs it (`codesign --force --sign -`). Launch it with `open -n -g -a` (above), never by exec'ing the inner binary. In Swift: set a `UNUserNotificationCenterDelegate` whose `willPresent` returns `[.banner, .list]`, `requestAuthorization(options: [.alert])`, `add` the request, and only `exit` from the `add` completion (a `--notify-only` flag for error notices with no job). The first post shows macOS's one-time Allow prompt for the app — expected, say so. Verify: `codesign --verify --deep` on the INSTALLED copy (`~/.config/raycast/extensions/<name>/assets/`), and the helper exits after posting (`pgrep -lx <binary>`).
- **Surface errors visibly.** Don't `catch` and return empty results — `throw` or show a `showToast(Toast.Style.Failure, ...)` (or `showFailureToast(error)` from `@raycast/utils`) so the user sees what went wrong instead of a blank list.

## 8. List Navigation Patterns

- **Detail panel (`isShowingDetail`)**: Shows contact/item metadata alongside the list. Good for "see everything at a glance" without leaving the list. Fields rendered as `List.Item.Detail.Metadata.Link` are clickable with the mouse but **not keyboard-focusable** — they're read-only display. Don't combine `accessories` with `isShowingDetail`; use `Metadata.TagList` for colored tags inside the panel.
- **Drill-in navigation**: Use `Action.Push` as the primary action to push a second `List` where each field is its own `List.Item` with actions. This gives full keyboard navigation (↑↓ between fields, Enter to act, Esc to go back). Combine both patterns: detail panel for visual scanning + Enter to drill in for keyboard interaction. Use `onPop` on `Action.Push` to `revalidate()` the parent when the child changed something.
- **Filter dropdown**: `searchBarAccessory={<List.Dropdown tooltip="…" storeValue onChange={…}>}` gives a ⌘P filter in the search bar that remembers its choice.
- **Keyboard shortcuts**: Add `shortcut` props to frequently-used actions. Prefer `Keyboard.Shortcut.Common.*` (`Copy`, `Open`, `Refresh`, `Remove`, `Pin`, `Edit`…) over hand-picked combos — they match the rest of Raycast. Shortcuts show automatically in the action panel (⌘K). Add shortcut hints as `Metadata.Label` items at the bottom of a detail panel for persistent visibility. Raycast ignores ⌘K, ⌘W, and ⌘Esc. A custom shortcut on the first two actions works but is not displayed (they are ↵ and ⌘↵, or ⌘↵ and ⌘⇧↵ in a Form).
- **Action ordering**: The **first** action in the `ActionPanel` becomes the primary action shown in the bottom bar and triggered by Enter. Order actions by frequency of use. Group with `ActionPanel.Section`; a submenu title ends with `…` (`Set Priority…`).
- **Destructive actions (delete, etc.)**: Use `confirmAlert` with `Alert.ActionStyle.Destructive` for irreversible operations. Style the action itself with `style={Action.Style.Destructive}` so it renders in red. After the mutation, call `revalidate()` (from `useCachedPromise`) to refresh the list. Pattern:
  ```tsx
  <Action
    title="Delete Contact"
    icon={{ source: Icon.Trash, tintColor: Color.Red }}
    style={Action.Style.Destructive}
    shortcut={Keyboard.Shortcut.Common.Remove}
    onAction={async () => {
      const confirmed = await confirmAlert({
        title: "Delete Contact",
        message: `Permanently delete "${name}"?`,
        primaryAction: { title: "Delete", style: Alert.ActionStyle.Destructive },
      });
      if (confirmed) {
        deleteContact(id);
        await showToast(Toast.Style.Success, `Deleted "${name}"`);
        revalidate();
      }
    }}
  />
  ```
- **Revalidating after mutations.** Destructure `revalidate` from `useCachedPromise` and call it after any write operation (delete, update, create) to refresh the list without a full remount — or use `mutate` (section 5).

## 9. Background, Menu Bar, and Launch Entry Points

- **Nothing polls — event-driven first, a schedule last.** *Trigger:* you are about to add anything that runs repeatedly or waits: a manifest `"interval"`, a `setInterval`/`setTimeout` loop outside an open view, a launchd `StartInterval`, a watcher, a helper that checks state. *Discrimination:* "it's only a few milliseconds" is NOT the test — a cheap once-a-minute check is still waste when, most of the time, there is nothing to check. Work that runs only while the user is looking (a 1 s countdown inside an open List) is fine; work that runs while nothing is happening is the defect. *Action:* before writing it, list the EVENTS that change the state and trigger the update from them: the command that causes the change (`launchCommand({ name, type: LaunchType.Background })` after it acts), the helper process at its own milestones (`open -g "raycast://extensions/<author>/<ext>/<cmd>?launchType=background"`; Raycast prompts once, **Always Allow** stores `alwaysAllowsExternalLaunches` per command, not visible in Settings), a launchd `WatchPaths` on the one folder that changes, never a `StartInterval`. Use a schedule only when no event exists, say so to the user with the measured cost, and pick the longest interval that works. In the reply, state what runs when idle (ideally: nothing).
- **Live info in root search**: `updateCommandMetadata({ subtitle: "3 unread" })` inside a `no-view` command sets the text next to that command (it can only update ITSELF; `null` clears it). Refresh it on events (rule above): background-launch it from whatever changed the state. Branch on `environment.launchType === LaunchType.Background` to skip UI work. A manifest `"interval"` (min 1m, approximate, with a per-command toggle) is the last resort, never the default. Root search cannot list items, so a live list becomes a subtitle plus a view command Enter opens (`launchCommand` with `LaunchType.UserInitiated`).
- **Test a background command** without waiting: the dev actions **Run in Background** on the command in root search; the built-in **Extension Diagnostics** command lists last runs. Errors show as a warning icon on the command (a triangle on EVERY command of a dev extension is a missing import folder instead — section 3).
- **Menu-bar commands (`"mode": "menu-bar"`)** — *Trigger:* writing or fixing a `MenuBarExtra`. *Discrimination:* they are not long-lived apps; Raycast loads, renders, and unloads them, and after a Raycast restart it restores the last render WITHOUT running your code. *Action:* set `isLoading` true while fetching and ALWAYS flip it to false (in `finally`), or the command never unloads; read the last value from `Cache` synchronously for an instant first paint; return `null` to hide the item; never put two identical `MenuBarExtra.Item`s at one level (their handlers misfire). An item with no `onAction` renders disabled, so it works as a section label. `alternate` gives an ⌥-held variant. On macOS Tahoe a missing menu-bar item can be the OS hiding it: **System Settings → Menu Bar → Allow in the Menu Bar** must include Raycast, even when the command is enabled in Raycast.
- **Arguments** (up to 3 per command, `text` / `password` / `dropdown`) show as inline fields in root search; read them from `props.arguments`, typed as `LaunchProps<{ arguments: Arguments.MyCommand }>`. All values are strings.
- **Aliases are invisible to extensions, and argument placeholders are static.** *Trigger:* the user wants help text that names an alias, or any text in the argument box that changes at runtime. *Discrimination:* there is no API that reads aliases (they live in Raycast's encrypted DB), `placeholder` is fixed in `package.json`, and the argument box cuts text off at about 17 characters. Only the command `subtitle` can change at runtime, via `updateCommandMetadata`, which updates the CALLING command only and takes effect after it runs. *Action:* keep the placeholder short ("minutes"); put any reminder in the command's title or subtitle, naming the command rather than an alias (section 12).
- **Fallback commands**: read `props.fallbackText` to prefill from whatever the user typed in root search.
- **Deeplinks**: `raycast://extensions/<author>/<extension-name>/<command-name>?arguments=<url-encoded JSON>&context=<url-encoded JSON>&launchType=background`. Get the exact URL from the command's **Copy Deeplink** action (⇧⌘C) rather than building it by hand; inside code use `createDeeplink({ command, arguments })` from `@raycast/utils`. Any automation tool, script or helper app can `open -g` this URL.
- **Deeplinks from outside Raycast: one prompt, then silent — and the choice is invisible.** *Trigger:* a helper app or script launches a command via `raycast://…?launchType=background` and "nothing happens", or the user can't find an "Always Allow External Launches" setting. *Discrimination:* the first launch shows a Raycast confirmation and the command does NOT run until answered; clicking **Always Allow** stores `alwaysAllowsExternalLaunches` for that one command, which Raycast Settings never shows (not in the extension's command row, not in its detail pane). A command that never runs even after allowing is a wrong URL (author = `package.json` `author`, then extension `name`, then command `name`). *Action:* tell the user a prompt will appear once and to click Always Allow; verify WITHOUT screenshots through a side effect the command leaves (for example, drop a record with a dead PID into the helper's `running/` folder and `open -g` the link: the record is gone within seconds if it ran).

## 10. Production Mode & Publishing

- **The "Development" label** is inherent to all extensions loaded via `ray develop`. There is **no local production install** — the only way to remove it is `ray publish`, which submits the extension to the Raycast Store (requires `ray login`, public listing, and review).
- **`package.json` metadata semantics**: The `title` field in the top-level `package.json` is what Raycast shows as the extension subtitle next to the command name (e.g., "Search Contacts  **Search the Contacts app**"). The `commands[].title` is the command name itself. Change `title` when the user asks to rename what appears next to the command. A command-level `subtitle` overrides it per command and is also searchable; command-level `keywords` add root-search synonyms.

## 11. Debugging

- **`console.log` output goes to the terminal running `npm run dev`**, not to Raycast. If nothing appears there, turn on the dev option "Use file logging instead of OSLog".
- **Importing without leaving a watcher running.** *Trigger:* you changed an extension and Raycast must load it, but a live `npm run dev` would block the turn. *Discrimination:* `npm run build` overwrites the installed files but is not the import (section 3), and macOS has no `timeout` command. *Action:* `npx ray develop > "$TMPDIR/raydev.log" 2>&1 & P=$!`, poll the log for `ready` (1 s steps, ~30 tries), then `kill $P` — that one PID, never a pattern kill. The import persists after the watcher stops. A bundled `.app` in `assets/` arrives intact (check `codesign --verify --deep` on the installed copy).
- **"Command not found: <name> in <extension>" while the installed manifest HAS the command.** *Trigger:* a newly added command is missing from root search, and its deeplink logs that error, yet `~/.config/raycast/extensions/<ext>/package.json` lists it and `<name>.js` sits beside it. *Discrimination:* re-importing does not fix it: Raycast keeps a stale registration for that command NAME (a "Disable Command" on it is the likely cause, and Raycast's settings DB is encrypted, so it can't be read). A red ⚠️ triangle is the deleted-worktree case instead. *Action:* rename the command's `name` (and its `src/<name>.ts` and icon file), re-import, then confirm with `open -g "raycast://extensions/<author>/<ext>/<new name>"` + `grep commandExited` in the log. The title can stay; only the internal name changes.
- **Dev-only behavior:** gate it on `environment.isDevelopment`, not `NODE_ENV`.
- **Breakpoints / live props:** `npm i -D react-devtools@6.1.1`, re-run `npm run dev`, open the command, press ⌘⌥D.
- **"Command Out of Memory"**: choose "Reload with Memory Reporting"; `captureMemorySnapshot(label)` marks points to compare. Usually an unpaginated list or a huge cached blob.
- **Raycast's own logs**: the "Reveal Raycast Logs" / "Copy Raycast Logs" commands, or `~/Library/Logs/com.raycast.macos/raycast-x-<date> <time>.log` (Raycast 2, one file per launch). They are the only readable trail of extension state: Raycast 2's own databases (`~/Library/Application Support/com.raycast.macos/*.db`, `node_extensions.db` included) are encrypted, so `sqlite3` says "file is not a database". Useful greps: `Skipping unavailable local node extension` (a dev import Raycast dropped), `Command not found` (a deeplink to a command that isn't loaded), `No installed local extension for node command` (an alias or hotkey left without its command).
- **Runtime facts:** every extension runs in Raycast's own bundled Node (not Homebrew's), with the same stripped PATH as script commands. Extensions are not sandboxed for files, network, or child processes, and macOS privacy grants belong to Raycast.

## 12. Extension Preferences & Authentication

When building an extension that requires an external API (like Notion or Spotify):
- Add the required secrets/tokens to the `preferences` array in `package.json` (`"type": "password"`, `"required": true` — Raycast then blocks the command with a setup form until it is filled). Read them with `getPreferenceValues<Preferences.MyCommand>()`.
- **Put the setup steps in `help.md`** next to `package.json`: Raycast renders it beside the required-preferences form, so the instructions are there when the user needs them. On an auth error, offer an `Action` that calls `openExtensionPreferences()`.
- **User Instructions**: You must still proactively remind the user to configure the token when they first load the extension. For example, provide a short snippet:

  > ⚠️ **Integration Required**
  > You need to provide this extension with an API Token.
  > 1. Go to [Link to API dashboard]
  > 2. Create a new token.
  > 3. Open Raycast, run this new command, and paste the Token in the preferences when prompted.

- **Never ask for, store or show a command's alias.** *Trigger:* you are about to add a preference like "Silent Timer Alias", or a subtitle / hint that names an alias ("Use ts for NO sound"). *Discrimination:* extensions cannot read aliases: there is no API, and Raycast keeps them only in its SQLCipher-encrypted databases (`~/Library/Application Support/com.raycast.macos/settings*.db`, `main.db`; `sqlite3` says "file is not a database"), not in the plist or the logs. A typed-in copy goes stale the moment the user swaps aliases. *Action:* name the COMMAND instead (`Start Loud Timer` with subtitle `🔊`, `Start Silent Timer` with `🔇 No sound`), put the difference in the title, and add no alias preference. Never try the keychain key to decrypt the database (a permission prompt, and fragile).
- **OAuth instead of a pasted token**: `OAuthService.github|linear|slack|asana({ scope })` work out of the box with Raycast's hosted apps; `google|jira|zoom` need your own client ID. Wrap the command with `withAccessToken(service)(Command)` and read `getAccessToken().token`. Pass `personalAccessToken: prefs.token` to let a pasted token skip OAuth. Don't save source files mid-login while `ray develop` runs — the hot reload breaks the flow.

## 13. Notion-backed extensions

A common pattern is a set of small extensions that each wrap a Notion database behind a Raycast form (one isolated subfolder + `package.json` per extension). The token lives in a `notionToken` password preference; the form reads it via `getPreferenceValues` and builds `new Client({ auth })`.

- **Per-extension config when duplicating**: update `name`, `title`, `description`, `author` (your Raycast Store handle), and the `commands` array. Then set the `databaseId` const in the `.tsx` — extract the 32-char hex id from the database URL (`notion.so/.../<id>?v=...`).
- **Fetch options dynamically, in one call.** Pull every dynamic field (tags, status, …) from a single `databases.retrieve` inside one `useCachedPromise` — don't issue one retrieve per field. Find properties by `type` (and name) rather than a hardcoded key, so a renamed column still resolves; locate the title property with `Object.values(db.properties).find(p => p.type === "title")`.
- **multi_select with create-new.** `Form.TagPicker` only selects from items you provide — it has **no** freeform entry. To let the user *create* new options, pair the picker (existing options, with `value`/`title` set to the option **name**) with a companion `Form.TextField` for comma-separated new names. On submit, merge + dedupe both lists and send `multi_select: names.map(name => ({ name }))`. Notion matches existing options by name and auto-creates any that don't exist — sending by **name** (not id) is what makes create-on-write work.
- **single select / status.** Use `Form.Dropdown` with a leading `<Form.Dropdown.Item value="" title="None" />` so the field defaults to unset; skip writing the property when the value is empty. Handle both the `select` and `status` property types: `{ select: { name } }` vs `{ status: { name } }`.

### Auth & the "Could not find database" error

`APIResponseError: Could not find database with ID … make sure the relevant pages and databases are shared with your integration` almost always means **the integration is not connected to the database**, not that the ID is wrong — Notion returns the same `object_not_found` message for "doesn't exist" and "not shared."

- Confirm the DB exists and the ID is right by fetching it through the user's own account (Notion MCP `notion-fetch`, or the Notion app) — that bypasses the integration's permissions.
- The fix is manual (an integration cannot grant itself access): in Notion open the database → **⋯ → Connections → Add connections** → select the integration whose token is in Raycast.
- Verify a token before the user pastes it into Raycast:
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Notion-Version: 2022-06-28" \
    "https://api.notion.com/v1/databases/<id>"
  ```
  `200` = valid + shared; `404` = not shared / wrong id; `401` = bad token.
- The token is stored only in Raycast's encrypted preferences — you can't set it from the shell, and never hardcode it in source. (Note the rename caveat in section 3: a renamed extension needs the token re-entered.)

## 14. AI Extensions (tools Raycast AI can call)

*Trigger:* the user wants to ask Raycast AI to do something with one of their extensions ("@contacts find…"), or mentions tools, `ai.yaml`, or evals. *Discrimination:* a tool is NOT a command — it never shows in root search; only the AI calls it. A prompt run on selected text is an AI Command (no code). *Action:*
- Add a `tools` entry in `package.json` (`name`, `title`, `description`) → `src/tools/<name>.ts` default-exports an async function taking ONE input object. JSDoc on the function and each input field is what the AI reads — say formats (ISO 8601 dates) and where IDs come from.
- Guard writes: `export const confirmation: Tool.Confirmation<Input> = async (input) => ({ message: … })`. Return `undefined` to skip it for safe inputs.
- Domain rules go in `ai.yaml` (`instructions: |`) next to `package.json`. Don't write "You are an assistant" — several extensions share one chat.
- Evals: capture a working run with the **Copy Eval** action in AI Chat, paste into `ai.yaml` `evals:`, run `npx ray evals`.
- Needs Raycast Pro. Share code between a command and a tool with `environment.entryPointType` (`"command"` / `"tool"`).
- Raycast AI also reads Agent Skills from `~/.claude/skills` (top level). It silently skips a skill whose `description` is over 1024 characters or whose folder name differs from its `name`.

## 15. Opening Claude Desktop (Claude Code) in a folder

*Trigger:* the user wants a Raycast command that opens Claude Code in a folder/repo ("Raycast hotkey to open this project in Claude"). *Discrimination:* it is a script command, not an extension — one `open` of the desktop app's deep link `claude://code/new?folder=<percent-encoded absolute path>` (verified with Claude.app 2.110.1). Don't shell out to the `claude` CLI (that is the terminal app) and don't `open -a Claude <folder>` (lands in Cowork). *Action:*

```bash
#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title Open in Claude Desktop
# @raycast.mode silent
# @raycast.packageName Claude
# @raycast.argument1 { "type": "text", "placeholder": "absolute folder path" }
V="$1"; [ -d "$V" ] || { echo "not a folder: $V"; exit 1; }
open "claude://code/new?folder=$(V="$V" osascript -l JavaScript -e 'ObjC.import("stdlib"); function run(){return encodeURIComponent($.getenv("V"))}')"
```

Absolute paths only (`~` is not expanded). A "current Finder selection" variant needs `tell application "Finder"` — that triggers a one-time Automation permission prompt, so prefer the argument form or a fixed list of favorites unless the user asks. Prefill the first message with `&q=<encoded text>`.

## 16. What Raycast's app exposes, and what it never will

*Trigger:* a task needs Raycast's own state or UI (the user's Quicklinks, Snippets, aliases, hotkeys, enabled commands, whether the
bar is open) or asks for a Raycast feature that may already be built in. *Discrimination:* there is no API for any of it, and
guessing wastes a build; the facts below were read from Raycast 2.6.3's bundle and logs. *Action:* use the matching row.

- **User data:** the databases are encrypted (section 11). Readable exports the user makes themselves: Search Quicklinks / Search
  Snippets ▸ ⌘K ▸ Export → `~/Downloads/Quicklinks <date>.json` / `Snippets <date>.json` (plain JSON: `name`, `link` or
  `text`, `keyword`). The full Settings export `.rayconfig` starts `RAYCFG3\n` + a 4-byte length + a gzip JSON header
  (`exportedAt`, `encryption: {iv, salt}`), then a password-encrypted body. Never ask for that password.
- **Built-in action shortcuts can't be rebound.** Disable Command is `⌃⇧⌘D`, hard-coded in the app's shortcut table
  (`disableCommand:{mac: ctrl.shift.cmd.d}`); there is no setting. A remap needs an external key-remapping or automation tool. A command switched off by accident is re-enabled in Settings ▸ Extensions.
- **The search bar is not the active app.** Opening it leaves another app frontmost (the log says `App Active: false`), so an
  automation tool's trigger scoped to "only when Raycast is active" never fires. Detect the bar instead: an ON-SCREEN window owned by `Raycast` at
  window layer 8 (CGWindowList; main bar 900×570, compact 530×446). Raycast's AI/Notes windows are layer 0.
- **Raycast Focus is built in** (Start / Toggle / Pause / Complete Focus Session). Deeplinks:
  `raycast://focus/start?goal=<title>&categories=<a,b>&duration=<SECONDS>&mode=block|allow`, `raycast://focus/toggle`,
  `raycast://focus/complete`. Built-in category ids: `social` (x.com, twitter.com, linkedin.com…, plus the Twitter app),
  `messaging`, `gaming`, `shopping`, `streaming`, `news`, `travel`; no email category ships, so mail needs a custom category.
  A start deeplink is ignored while a session runs.
- **No Large Type.** Raycast has nothing that shows text huge over the screen; that needs a separate small app.
- **100 commands per extension** (`ray lint`: "must NOT have more than 100 items"); `ray build` still passes above it, so
  count before adding.
