---
name: neeo-meta-driver
description: Create, modify, review and debug drivers for the NEEO remote through the meta engine (jac459/meta) - JSON device files with buttons, labels, sliders, switches, images, directories, listeners, discovery and registration - plus their companion services (Node-RED flows over MQTT, small local REST bridges). Use whenever the user mentions NEEO, the NEEO Brain, meta / metaCore / metadriver, a NEEO driver or device file, or wants to control a device (TV, AV receiver, media player, lights...) from a NEEO remote, or shares meta, Mosquitto or Brain logs or a Brain JSON dump to diagnose.
---

# NEEO drivers with meta

meta (`jac459/meta`) is a Node.js engine that reads JSON *device files* from its `active/` folder and turns each one into a NEEO SDK driver registered with the local NEEO Brain. You describe the device in JSON; you do not write JavaScript (except small `DYNAMIK` expressions).

**Language**: write to the user in their language. JSON keys, engine keywords, button names and log strings stay exactly as documented here (English).

**Scope**: only the pre-acquisition NEEO SDK, the local Brain and meta matter. Ignore Control4 material and the NEEO cloud (shut down).

## Ground rules (never skip)

1. **Never invent a JSON key or command type.** If a feature is not in the references, say so and offer an alternative: a companion service (Node-RED + MQTT, or a small local REST bridge, see `references/companion-services.md`), a `cli` command, or a hidden-button chain.
2. **Pure JSON**: no comments, no trailing commas, double quotes. Validate with `python3 -m json.tool file.json` and `python3 scripts/check_driver.py file.json`.
3. **Command types are case-sensitive**: `http-get`, `http-rest`, `http-post`, `http-get-soap`, `static`, `cli`, `repl`, `webSocket`, `socketIO`, `jsontcp`, `mqtt`, `wol`, `mDNS`, `android`.
4. **Bump `version`** whenever a visible component is added. The Brain only *adds* components; renaming or removing one requires deleting and re-adding the device in the NEEO app (recipes and shortcuts must be redone). Even a bump is sometimes not enough on an installed device: check the Brain (`references/debugging.md`).
5. **Names (keys) of labels, switches, sliders, images and sensors: letters and digits only.** A space or symbol breaks the sensor link (`"sensor": null` in the Brain) and the remote crashes at sync as soon as the component is used as a shortcut. The displayed `label` text is free. Button names may contain spaces, but avoid `+` and accents (`DISNEY PLUS`, label `Disney+`).
6. **Never write `""` into a variable bound to a label**: on meta v1.2.0, a label going from a text back to `""` stops meta. Write `" "` (or a readable fallback). Initialise label variables with `" "` too, as a habit.
7. **Sanitize every external text before it reaches a label**: `"` -> `'`, `\` -> `/`, control characters -> space, `$` -> `＄` (full-width). Do it in the driver *and* at the source.
8. **Listeners start once per session, through the `ListenerOn` guard** + hidden `__LISTEN` button wired into every visible control. Never rely on `POWER ON` alone, and never call `__CLEANUP` on an `mqtt` listener (`references/listeners-and-state.md`).
9. **Events over polling** (`webSocket`, `socketIO`, `mqtt`). If polling, `pooltime` >= `3000`.
10. **`$Result` is always a string**, `"undefined"` on failure: guard every `JSON.parse`. A button gets a scalar (`ok`); a directory action feeder gets `["ok"]`.
11. **Variable names**: never use a name that is a prefix of another; `$Var` glued to letters is read as a different variable.
12. **Security**: `DYNAMIK` and `cli` execute code on the meta host. No secrets hard-coded in a driver meant to be shared; meta must not run as root/admin.
13. **Irreversible changes need consent**: adding visible components (e.g. `DIGIT 0`-`9`) cannot be undone without reinstalling the device. Ask first.
14. **Separate deliverables**: a meta driver is a JSON object (starts with `{`, never `-flow` in its name, goes in `active/`); a Node-RED flow is a JSON list (starts with `[`, always named `*-flow.json`, imported into Node-RED).
15. In `template`, `dynamicname` and `dynamicid` are mandatory; `dynamicid` must be **stable** (MAC address or hardware id rather than a DHCP IP).

## Workflow

1. **Collect what you need** (ask at most 3 targeted questions at a time): exact device model; its control protocol or API (HTTP/REST, WebSocket, raw TCP, MQTT, IR only, Android TV...); fixed IP or not and a stable id (MAC); what must be controlled and what state must be shown; meta version and where meta runs (Pi with pm2, Docker...); whether an MQTT broker and Node-RED are available. Look for the device's official API documentation when it exists.
2. **Choose the NEEO type** (`references/driver-anatomy.md`, section types and recognized buttons) and the **discovery pattern** (`references/discovery.md`): static single device, user-entered IP, mDNS, or hub.
3. **Start from a skeleton** in `assets/`: `skeleton-static.json` (one device, fixed address) or `skeleton-register-ip.json` (the user types the IP). Reuse proven patterns from `references/patterns.md`.
4. **Decide where the logic lives.** Simple HTTP or WebSocket device: everything in the driver. Binary or stateful protocol (raw TCP, persistent sessions, pairing, bursty state): put a companion service in between, with fast HTTP commands and state pushed as a retained MQTT message (`references/companion-services.md`).
5. **Check before delivering**:
   - `python3 -m json.tool driver.json` then `python3 scripts/check_driver.py driver.json` (names, empty label values, types, version, guard, polling...);
   - `node scripts/simulate_guard.js driver.json` when the driver has listeners (counts `__INITIALISE` / `__CLEANUP` over sessions);
   - evaluate tricky `DYNAMIK` expressions in Node with the real substitution rules (`references/logic-and-commands.md`);
   - re-read `references/pitfalls.md`.
6. **Deliver** in this order: summary (device, protocol, NEEO type, discovery pattern, covered / not covered); the complete validated JSON file with an explicit filename; deployment steps (copy to `active/`, restart meta, add the device in the NEEO app, recipe visibility and shortcuts to create); test plan (buttons to try, expected result, log lines to look for); assumptions not verified on the real device; next iteration. For multi-file projects (driver + flow + service): order of operations, a version marker in each deliverable and how to check which version is installed. Always say what was not tested on the real device.

## Reference map (read only what the task needs)

| File | Read when |
|---|---|
| `references/meta-engine.md` | Architecture, install, folders, restart, log levels, MQTT topics exposed by meta, Docker/NAS hosting, known meta v1.2.0 bugs |
| `references/driver-anatomy.md` | Top-level keys, NEEO device types and recognized button names, variables, `$` substitution, `DYNAMIK`, UI components |
| `references/logic-and-commands.md` | `evalwrite`, `evaldo`, `evalnext`, special buttons, every command type, `queryresult` / JSONPath |
| `references/listeners-and-state.md` | Listeners, the `ListenerOn` guard, MQTT listener behaviour, bursty state sources, instance rebuilds |
| `references/discovery.md` | `discover`, `register`, `template`, `initcommandset`, mDNS, IP entry, hubs, pairing |
| `references/directories.md` | Lists, feeders, `item*` fields, actions, multi-level navigation |
| `references/patterns.md` | Proven recipes: volume, power, status bar, persistence, chains, loops, fallback path, app launcher, artwork image |
| `references/pitfalls.md` | Mandatory re-read before delivering |
| `references/debugging.md` | Reading meta, Mosquitto and Brain data, log signatures, isolating a link, sandbox testing |
| `references/companion-services.md` | Node-RED and MQTT bridges, local REST bridges, Apple TV / pyatv lessons |
| `references/community-drivers.md` | Reference drivers to imitate, SDK <-> meta mapping, sources |

## Evidence tags used in the references

`[code v1.2.0]` read in meta's source (branch `Release`); `[observed]` seen in real drivers or real installations; `[to verify]` deduction not yet tested. When a behaviour matters and is not tagged, check meta's code (`git clone --depth 1 --branch Release https://github.com/jac459/meta`) rather than guessing, and say which you did.
