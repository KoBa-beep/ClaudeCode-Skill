---
name: hc3-lua-scenes
description: Write and debug Lua scenes for the Fibaro Home Center 3 / Yubii Home (HC3, firmware 5.x) — declarations (triggers and conditions — device, cron, sunrise/sunset, global variables, custom events, central scene buttons), actions code, sourceTrigger, scene variables, restart option, and the choice between a scene and a QuickApp. Use this skill whenever the user wants an automation, a rule, a "when X then Y" on an HC3, converts a block scene to Lua, asks why a scene does not start, or mentions fibaro scenes, even without the word "Lua".
---

# HC3 Lua scenes

Answer in the user's language; keep identifiers in English. Explain to beginners where to click.

## Scene or QuickApp?
| Need | Scene | QuickApp |
|---|---|---|
| React to an event (button, door, time, variable) with a few actions | ✅ | heavier |
| Keep state in memory, run permanently, talk to a device (HTTP, TCP, MQTT) | ❌ starts from scratch each run | ✅ |
| Buttons / labels in the UI | ❌ | ✅ |
Rule of thumb: QuickApps are the drivers, scenes chain actions by calling QA methods
(`fibaro.call(qaId, "setMode", "Away")`). For QuickApps use the `hc3-quickapp` skill.

## Two parts
1. **Declarations** (conditions / triggers): a Lua *table*, not code — *when* the scene starts.
2. **Actions**: Lua code executed at each start.
Tip for users: build the scene in **block mode**, then "Convert to Lua": the HC3 writes exact declarations (property
names, weekday numbers). Conversion is one-way.

## Declarations
```lua
{
  operator = "all",               -- "all" (AND) | "any" (OR); groups can be nested
  conditions = {
    { type = "device", id = 201, property = "value", operator = "==", value = true, isTrigger = true },
    { type = "date", property = "cron", operator = "match", value = {"*", "*", "*", "*", "*", "*"}, isTrigger = false },
  }
}
```
- `isTrigger = true`: a **change** of this condition starts the scene (then all conditions are evaluated);
  `false`: filter only. At least one trigger is needed or the scene never starts by itself.
- Operators: `==`, `!=`, `>`, `>=`, `<`, `<=`, `anyValue` (any change), `match` (dates).
- `duration = 60` in a device condition: must stay true 60 s **[V]** (visible in converted block scenes).
Condition types and examples: `references/declarations.md` (device, central scene button, cron, sunrise/sunset,
global variable, custom event, alarm, location, weather, HC3 start).

## Actions
```lua
fibaro.debug("MyScene", json.encode(sourceTrigger))      -- first line while developing: see what started it
if sourceTrigger.type == "device" then                    -- .id, .property, .value
elseif sourceTrigger.type == "date" then
elseif sourceTrigger.type == "user" then                  -- started by hand (Run button, app)
end
```
Functions: `fibaro.call`, `fibaro.getValue`, `fibaro.get` (value + timestamp), `fibaro.getGlobalVariable` /
`setGlobalVariable` (strings), `fibaro.getSceneVariable` / `setSceneVariable` (persist between runs of the same scene),
`fibaro.alert`, `fibaro.emitCustomEvent`, `fibaro.scene("execute"|"kill", {ids})`, `fibaro.profile`, `fibaro.alarm`,
`fibaro.setTimeout(ms, fn)`, `api.*`, `net.HTTPClient`, `json`. Logs need a **tag**: `fibaro.debug("Tag", "msg")`.
Notifications: same rules as QuickApps (users vs phone IDs, no critical push) — see the `hc3-quickapp` skill,
`references/notifications.md`.

## Traps (read before answering "my scene does not work")
1. No memory between runs → scene variables or global variables.
2. **"Allow restarting a running scene"** option: *Yes* = a new trigger kills the running instance (pending
   `setTimeout` lost) and starts again — right for "light off 5 min after the last motion"; *No* = triggers are
   ignored while it runs (including while a `setTimeout` waits).
3. Manual mode ignores declarations.
4. Triggers fire on **changes** only: same value again → nothing.
5. Value types: switch `true/false`, dimmer / shutter 0–99, sensor number; global variables are always strings
   (`== "1"`, not `== 1`); in declarations write `value = true` without quotes.
6. A scene that changes its own trigger device can loop: filter with `sourceTrigger`.
7. Only device **properties** trigger scenes; a QuickApp's internal variable does not (a global variable does, and
   QA property updates like `value` do).
8. Avoid `while true` / long `fibaro.sleep`: use triggers, `setTimeout`, or a QuickApp.
9. Weekday numbering in cron and some property names vary: check a converted block scene **[V]**.

## Deliverable
Declarations block + actions block (separately, ready to paste), the scene options to set (restart yes/no,
automatic mode, room), the IDs to replace (`ID_DOOR_SENSOR`…) or real IDs from the user's inventory, and a test
procedure ("open the door, the console of the scene shows …"). Worked examples: `references/examples.md`.
