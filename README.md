# 🔍✨ Raycast AI Skill

![Raycast AI Skill Banner](banner.png)

> A free skill that teaches your AI coding assistant to build Raycast commands and extensions the right way, the first time.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE.txt) [![Raycast API](https://img.shields.io/badge/Raycast%20API-2.8.2-FF6363.svg)](https://developers.raycast.com/) [![Version](https://img.shields.io/github/v/release/adriangrantdotorg/Raycast-AI-Skill?color=orange&label=Version)](https://github.com/adriangrantdotorg/Raycast-AI-Skill/releases) [![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Standard-8A2BE2.svg)](https://github.com/anthropics/skills) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/adriangrantdotorg/Raycast-AI-Skill/pulls)

---

## ⬇️ Why Install?

- ⏱️ **Less time per command** — it gets things right on the first try
- 💸 **$0 added cost** — it rides on the AI you already pay for
- 📅 **Current with Raycast API 2.8.2** — not the AI's year-old memory

| | 😩 Without this Skill | 😌 With this Skill |
| --- | :---: | :---: |
| 🔁 Tries until it works | 🧪 3–5 | **1** |
| 📄 Code for a simple hotkey | 🧪 ~200 lines | **~10 lines** |
| 🛠️ Build steps | `npm install` + build | **none** |
| 🪙 AI usage burned on retries | 🧪 ~4× | **1×** |

<sub>🧪 estimate</sub>

---

## ✨ Features

Before writing code, the AI picks the lightest option that works: a built-in Quicklink or Snippet, a one-file Script Command, or a full Extension.

![The same request with and without the skill: without it, the AI guesses 212 lines, builds, and fails three times before it works on try 4; with it, the AI checks the rules, selects a 9-line Script Command, and it works on try 1, leaving the rest as time you get back](docs/media/with-vs-without-skill.svg)

- 📜 **Script Commands that don't hang** — every `@raycast.*` setting right, including traps like a hidden SSH password prompt
- 🎨 **Extensions that feel native** — keyboard-driven lists, self-closing forms, menu bar items, background refresh
- ⚡ **Instant, flicker-free data** — the right `@raycast/utils` hook for each job
- 🔐 **Secure tokens and sign-in** — encrypted preferences and built-in OAuth for GitHub, Linear and Slack
- 🤖 **Raycast AI tools** — tools Raycast AI can call for you, with evals
- 🩺 **Debugging that finds the real error** — reads Raycast's own logs, like dev extensions dropped after the v2 upgrade
- 🔄 **Stays current on its own** — checks Raycast's npm releases, docs and manual when it loads

---

## 🚀 Installation

Needs **[Raycast](https://www.raycast.com/)** and an AI assistant that supports [Agent Skills](https://github.com/anthropics/skills). Full Extensions also need **[Node.js](https://nodejs.org/)** 22.22.2+; the freshness check uses Python 3.

```bash
git clone https://github.com/adriangrantdotorg/Raycast-AI-Skill.git /tmp/Raycast-AI-Skill
cp -R /tmp/Raycast-AI-Skill/skills/raycast ~/.claude/skills/raycast   # Claude Code
cp -R /tmp/Raycast-AI-Skill/skills/raycast ~/.cursor/skills/raycast   # Cursor
cp -R /tmp/Raycast-AI-Skill/skills/raycast ~/.agents/skills/raycast   # ChatGPT & Codex
```

| **Platform** | **Skills folder** |
| --- | --- |
| **[Claude Code](https://code.claude.com/docs/en/skills)** | `~/.claude/skills/` |
| **[Cursor](https://cursor.com/docs/skills)** | `~/.cursor/skills/` |
| **[ChatGPT & Codex](https://learn.chatgpt.com/docs/build-skills)** | `~/.agents/skills/` |

Keep the folder named `raycast`; tools skip a skill whose folder name doesn't match its `name`.

---

## 💡 Usage

Describe what you want; the skill kicks in on its own.

| You say | The skill makes |
| --- | --- |
| "Make a Raycast command that wakes my Mac Mini over the network." | A **Script Command** in silent mode that shows a clear error toast if it fails |
| "Build a Raycast extension that adds a task to my Notion database, with a tag picker." | An **Extension** with the token stored securely, cached tags, and a form that closes when saved |
| "My extensions disappeared after updating to Raycast 2." | A **fix** that finds the dropped ones in Raycast's logs and re-imports each |

---

<div align="center">
  <sub>Built with ❤️ for the Raycast community & everyone who'd rather press a hotkey than click ✌🏾</sub>
</div>
