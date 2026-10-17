# Claude Code skills — Fibaro HC3 QuickApps

Four shareable skills that teach Claude Code how to build QuickApps for the Fibaro Home Center 3 / Yubii Home.
They contain only general know-how (API, patterns, pitfalls, tools): **no data from any particular installation**
(no IP, device id, name, password or brand logo). Written in English; Claude answers in the user's language.

| Skill | What it does | Bundled tools |
|---|---|---|
| [`hc3-quickapp`](hc3-quickapp/SKILL.md) | Design, write, test and document QuickApps (types, structure, timers, network, UI, children, notifications, REST API, troubleshooting) | `hc3sim.lua` offline simulator with virtual clock · template QA + test scenario · browser-console exports (inventory, swagger, device history) · `swagger_index.py` |
| [`hc3-lua-scenes`](hc3-lua-scenes/SKILL.md) | Lua scenes: declarations, `sourceTrigger`, scene variables, restart option, traps | worked examples |
| [`hc3-packaging`](hc3-packaging/SKILL.md) | `.fqa` file + update script (keeps id and variables) + icon upload script | `build_fqa.py` |
| [`hc3-icons`](hc3-icons/SKILL.md) | Realistic device icons with a state badge, one per state, light / dark safe; HC3 upload rules | `icon_kit.py` |

## Install
- **Claude Code, one project**: copy the `hc3-*` folders into `<project>/.claude/skills/`.
- **Claude Code, all projects**: copy them into `~/.claude/skills/`.
- **Claude.ai / desktop app**: Settings → Capabilities → Skills → upload the `.skill` files from [`dist/`](dist/).

## Rebuild the .skill files
With Anthropic's `skill-creator` skill: `python -m scripts.package_skill fibaro-hc3/<name> fibaro-hc3/dist`
(a `.skill` file is a zip of the folder).

Requirements of the bundled tools: Lua 5.3/5.4 (simulator), Python 3 (+ `cairosvg pillow` for icons, `pyyaml`
optional for swagger YAML files), bash + curl on macOS / Linux / WSL (generated install scripts).
