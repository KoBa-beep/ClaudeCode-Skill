---
name: hc3-quickapp
description: Design, write, test and document QuickApps (Lua) for the Fibaro Home Center 3 / Yubii Home (HC3, HC3L, firmware 5.x). Use this skill whenever the user mentions a QuickApp, QA, HC3, Home Center 3, Yubii, Fibaro Lua, a virtual device, child devices, a Z-Wave module to drive from Lua, HC3 notifications, or wants to integrate a device or cloud API (HTTP, TCP, UDP, MQTT, WebSocket) into Fibaro, even if they do not say "QuickApp" explicitly. Also use it to debug, review or upgrade an existing QuickApp, and to port HC2 Virtual Devices / LUA scenes to HC3.
---

# HC3 QuickApp development

QuickApps (QA) are long-running Lua programs that appear as devices on the Fibaro Home Center 3. This skill
captures what works on real boxes (firmware 5.2xx), the traps that waste hours, and a delivery format a beginner can
install without help.

**Language**: write code identifiers in English; write user-facing text (answers, code comments, labels,
notifications, README) in the user's language. Many HC3 users are beginners: explain each step.

Related skills (load them when the task touches their area): `hc3-lua-scenes` (Lua scenes), `hc3-packaging`
(.fqa files, one-click install / update scripts), `hc3-icons` (device icons).

## 1. Before writing code

HC3 ≠ HC2. Never use HC2 APIs (`fibaro:call`, `fibaro:getValue`, `fibaro:sleep` with colon, Virtual Devices,
`--[[ %% properties ]]` headers). In QuickApps it is `fibaro.call(...)` (dot) and methods on `self`.

Collect, from the conversation or the user's files, before coding (ask only for what is missing, in one grouped
message):

1. Goal and the real device / service (model, protocol, API docs, a sample JSON answer if possible).
2. Firmware version (WebSocket ≥ 5.041, `trace/warning/error` ≥ 5.030, switch / select UI ≥ 5.150).
3. Device IDs of HC3 devices the QA reads or drives. If the user can export an inventory, use it instead of asking
   ID by ID: `scripts/export-inventory.js` (paste in the browser console on the HC3 page) produces a JSON with
   devices, rooms, sections, scenes, users, and **no secrets**.
4. How to notify (phones, users, notification centre) — see `references/notifications.md`.
5. Credentials needed (they go in QA variables, never in code, never in a repo).

If the user keeps a configuration file describing their installation (IPs, IDs, conventions), read it first and
never ask again for something it already answers.

## 2. Choose the device type

Pick the type that makes the QA useful in scenes, the mobile app and voice assistants:

| Need | Type | `value` |
|---|---|---|
| On/off actuator | `com.fibaro.binarySwitch` | boolean; actions `turnOn`, `turnOff` |
| Dimmer / level | `com.fibaro.multilevelSwitch` | 0–99 (some 100); `setValue` |
| Shutter | `com.fibaro.rollerShutter` | 0 closed – 99/100 open; `open`, `close`, `stop`, `setValue` |
| Alarm / problem flag | `com.fibaro.binarySensor` | boolean (good scene trigger) |
| Temperature / humidity / other measure | `com.fibaro.temperatureSensor`, `humiditySensor`, `multilevelSensor` + `unit` | number |
| Thermostat | `com.fibaro.hvacSystemAuto` / `hvacSystemHeat` | see `references/qa-lua-api.md` |
| Hub, gateway, dashboard without a natural state | `com.fibaro.deviceController` (+ children) | none |

A `deviceController` has **one** icon image only; to show a state, swap icons by ID (pattern in
`references/patterns.md`). Several measured values → one parent + child devices, one child per value.

## 3. Structure of `main.lua`

Start from `assets/template-main.lua` (polling sensor) and keep this order: header comment (name, version,
type, variables, UI) → constants → local helpers → `onInit` → main loop → public actions → network → UI handlers →
notifications. Rules that prevent most bugs:

- **One** recursive timer per loop (`fibaro.setTimeout(ms, fn)` re-armed at the end of each cycle, previous ref
  cleared), body wrapped in `pcall` — errors inside timers are often silent on the HC3.
- Every `json.decode` under `pcall`; every HTTP request has an `error` callback; retry with back-off.
- Read variables with an `optionalVariable` helper; `getVariable` returns `""` (not nil) when missing.
- Update properties only when they change (`setIfChanged`): each update fires scene triggers and fills history.
- Every `function QuickApp:xxx()` is a public action callable by scenes and REST: keep internals `local` or clearly
  named; expose what scenes need (`setMode`, `refresh`…).
- Never `api.put("/devices/<own id>")` from the QA itself: the HC3 restarts the QA. Use `self:updateProperty`.
- No blocking: no `while` waiting loops, no long `fibaro.sleep`.
- No secret in code; IPs, IDs and thresholds in variables with sensible defaults so the QA starts even if a
  variable is missing.
- Show clear, short status in labels (emoji + value), put full sentences in notifications and the console.
- Messages must say *which* device and *where* (name + room + floor), never just an ID:
  pattern "describe a device in clear text" in `references/patterns.md`.

Read `references/qa-lua-api.md` for the API (QuickApp methods, `fibaro.*`, `api.*`, `net.*`, UI events, children)
and `references/patterns.md` for tested building blocks (children, notifications, relay verification, snapshot /
restore, dynamic icon, daily report…).

## 4. Check the REST API before using it

Inside a QA, `api.get/post/put/delete("/path")` calls the HC3 REST API without the `/api` prefix and returns
`data, httpCode`. Verify every path, parameter and response shape in `references/rest-api.md` (summary of the
official swagger of firmware 5.2xx + useful undocumented endpoints; full list in `references/rest-api-index.md`).
For another firmware, or to see the exact parameters of an endpoint: the user pastes `scripts/export-swagger.js` in
the browser console on `http://<hc3>/swagger`, then `python3 scripts/swagger_index.py hc3-swagger.json [--grep x |
--detail "POST /icons"]`.

## 5. Test locally before the box

Run the logic in the offline simulator: `lua scripts/hc3sim.lua main.lua scenario.lua` (Lua 5.3/5.4). It mocks
`QuickApp`, children, variables, `fibaro.*`, `api.*` (devices, rooms, notification centre, push), `net.HTTPClient`
and a **virtual clock**, so a day of timers runs in a second. Write a scenario per behaviour (normal, device offline,
threshold crossed, button pressed, midnight rollover…) with `sim.expect`. Example: `assets/template-scenario.lua`.
Say clearly in the delivery what was simulated and what still needs a test on the box.

## 6. Deliverables

For each QA, produce (in a folder `quickapps/<qa-name>/` if the user keeps a repository):

1. `main.lua` — complete, commented, version number in the header.
2. **Device type** to choose at creation.
3. **Variables** table: name, example, role, default (all optional when possible; secrets left empty).
4. **UI** table: element ID, type (label / button / slider / switch / select), text, method (`onReleased`,
   `onChanged`, `onToggled`).
5. **Install steps** (Settings → Devices → + → Other device → Quick App, or import the `.fqa`).
6. **Test plan**: action → expected console line / label / notification.
7. Icons for every device the QA creates (skill `hc3-icons`), and the `.fqa` + install / update scripts
   (skill `hc3-packaging`).
8. Clearly marked assumptions that could not be verified.

## 7. Quality checklist (run it before answering)

- [ ] No HC2 API; no secret in code or default variables
- [ ] Each `json.decode` in `pcall`; each request has `error`; network retry with back-off
- [ ] Exactly one loop timer; `onInit` safe to run again (it runs after every save)
- [ ] Variables read with defaults; `""` handled; numbers through `tonumber`
- [ ] `setIfChanged` for properties; labels short; notifications explicit (device, room, value, action)
- [ ] Public methods = intended actions only; children recreated / re-linked on restart
- [ ] Simulated scenarios pass; untested points listed

When something misbehaves on the box (no notification, device "dead", QA restarting, UI not updating), read
`references/troubleshooting.md`.
