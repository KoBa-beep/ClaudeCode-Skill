# Claude Code skills — NEEO remote with meta

A shareable skill that teaches Claude Code how to build drivers for the NEEO remote running on the
[meta](https://github.com/jac459/meta) engine (jac459), and their companion services (Node-RED flows over MQTT, small
local REST bridges). It contains only general know-how (engine behaviour, patterns, pitfalls, tools): **no data from any
particular installation** (no IP, device id, name or password). Written in English; Claude answers in the user's language.

| Skill | What it does | Bundled tools |
|---|---|---|
| [`neeo-meta-driver`](neeo-meta-driver/SKILL.md) | Design, write, review and debug meta JSON drivers (types, buttons, labels, sliders, switches, images, directories, listeners, discovery, registration), companion services, and read meta / Mosquitto / Brain data | `check_driver.py` static checks · `simulate_guard.js` listener-guard simulation · two driver skeletons |

```
neeo-meta-driver/
  SKILL.md                     ground rules, workflow, delivery format, reference map
  references/                  loaded on demand
    meta-engine.md             architecture, operation, MQTT topics, Docker/NAS hosting, known meta v1.2.0 bugs
    driver-anatomy.md          top-level keys, device types, button names, variables, DYNAMIK, components
    logic-and-commands.md      evalwrite / evaldo / evalnext, special buttons, command types, queryresult
    listeners-and-state.md     listeners, ListenerOn guard, MQTT listeners, bursty sources, rebuilds
    discovery.md               discover / register / template, mDNS, IP entry, hubs, pairing
    directories.md             lists, feeders, rows, actions, navigation
    patterns.md                proven recipes
    pitfalls.md                checklist before delivering
    debugging.md               log signatures, Brain checks, isolating a link, sandbox testing
    companion-services.md      Node-RED and Python bridges, pyatv / Apple TV notes, artwork search
    community-drivers.md       reference drivers, SDK mapping, sources
  assets/
    skeleton-static.json       one device at a fixed address, volume, status label, polling listener with guard
    skeleton-register-ip.json  the user types the device IP, validated by a call
  scripts/
    check_driver.py            static checks (names, empty labels, types, guard, references, version bump)
    simulate_guard.js          simulates meta's logic and counts listener starts over sessions
```

## Install
- **Claude Code, one project**: copy the `neeo-meta-driver` folder into `<project>/.claude/skills/`.
- **Claude Code, all projects**: copy it into `~/.claude/skills/`.
- **Claude.ai / desktop app**: Settings → Capabilities → Skills → upload [`dist/neeo-meta-driver.skill`](dist/).

Claude Code loads it automatically when a request is about NEEO or meta; it can also be called with `/neeo-meta-driver`.

## Tools on their own

```bash
python3 neeo-meta-driver/scripts/check_driver.py MyDriver.json                      # exit code 1 on errors
python3 neeo-meta-driver/scripts/check_driver.py MyDriver.json --previous Old.json  # also: version bump, removed components
node neeo-meta-driver/scripts/simulate_guard.js MyDriver.json                       # listener guard simulation
```

Requirements: Python 3 and Node.js, no extra package.

## Rebuild the .skill file
With Anthropic's `skill-creator` skill: `python -m scripts.package_skill neeo-meta/neeo-meta-driver neeo-meta/dist`
(a `.skill` file is a zip of the folder).

## Limits
Behaviours marked `[code v1.2.0]` were read in meta v1.2.0 (branch `Release`); later versions may differ. The skeletons
and patterns come from real drivers but must be tested on the real device. meta and the NEEO SDK belong to their
authors (meta is MIT-licensed).
