# Scene declarations — condition types

**[S]** confirmed by several sources (tutorials, open-source emulators, observed boxes) · **[V]** verify on the box
(converted block scene).

| Type | Example | Notes |
|---|---|---|
| Device | `{type="device", id=201, property="value", operator="==", value=true, isTrigger=true}` | `property` mostly `value`; also `dead`, `batteryLevel`, `power`, `energy`… |
| Central scene (button events) | `{type="device", id=45, property="centralSceneEvent", operator="==", value={keyId=1, keyAttribute="Pressed"}, isTrigger=true}` | `keyAttribute`: `Pressed`, `Pressed2`, `Pressed3`, `HeldDown`, `Released`; requires scene activation enabled in the module parameters for many Fibaro modules |
| Time (cron) | `{type="date", property="cron", operator="match", value={"30","7","*","*","1,2,3,4,5","*"}, isTrigger=true}` | 6 fields: **minute, hour, day, month, weekday, year**. Weekday numbering **[V]** (emulators use 1 = Sunday … 7 = Saturday like `os.date`) |
| Sunrise / sunset | `{type="date", property="sunset", operator="==", value=-30, isTrigger=true}` | minutes: negative = before, positive = after; `sunrise` likewise |
| Global variable | `{type="global-variable", property="Presence", operator="==", value="Away", isTrigger=true}` | `property` = variable name; values are strings |
| Custom event | `{type="custom-event", property="BackHome", operator="==", isTrigger=true}` | fired by `fibaro.emitCustomEvent("BackHome")` from a scene or QA — handy to chain |
| Alarm | `{type="alarm", id=1, property="armed", operator="==", value=true, isTrigger=true}` | `id` = partition; `breached` = intrusion |
| Location | `{type="location", id=<userId>, property=<placeId>, operator="==", value="enter", isTrigger=true}` | `enter` / `leave` **[V]** |
| Weather | `{type="weather", property="Temperature", operator="<", value=0, isTrigger=true}` | HC3 weather **[V]** |
| HC3 start | `{type="se-start", property="start", operator="==", value=true, isTrigger=true}` | runs when the scene engine starts (box reboot) |

Nested groups:
```lua
{ operator = "all", conditions = {
    { type = "device", id = 12, property = "value", operator = "==", value = true, isTrigger = true },
    { operator = "any", conditions = {
        { type = "date", property = "sunset", operator = ">=", value = 0 },
        { type = "date", property = "sunrise", operator = "<", value = 0 },
    } },
} }
```
