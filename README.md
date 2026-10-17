# ClaudeCode-Skill

Skills for Claude Code coming from different projects. Each folder groups the skills of one domain; every skill is a
folder with a `SKILL.md`, and ready-to-upload `.skill` files are in the domain's `dist/` folder.

| Folder | Skills | Domain |
|---|---|---|
| [`fibaro-hc3/`](fibaro-hc3/README.md) | `hc3-quickapp`, `hc3-lua-scenes`, `hc3-packaging`, `hc3-icons` | Fibaro Home Center 3 / Yubii Home: QuickApps (Lua), Lua scenes, `.fqa` packaging, device icons |
| [`neeo-meta/`](neeo-meta/README.md) | `neeo-meta-driver` | NEEO remote with the meta engine (jac459): JSON drivers, listeners, discovery, directories, Node-RED / MQTT companion services, log diagnosis |

## Install a skill
- **Claude Code, one project**: copy the skill folder into `<project>/.claude/skills/`.
- **Claude Code, all projects**: copy it into `~/.claude/skills/`.
- **Claude.ai / desktop app**: Settings → Capabilities → Skills → upload the `.skill` file.

The skills contain only general know-how: no data from anyone's installation (no IP, id, password or name).

## License

[MIT](LICENSE): free to use, modify and share, with no warranty.
