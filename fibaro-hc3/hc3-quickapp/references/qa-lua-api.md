# HC3 QuickApp Lua API — reference

Markers: **[O]** official Fibaro "Quick Apps" manual · **[S]** confirmed by other sources (community emulators, forum,
observed on a 5.2xx box) · **[V]** to verify on the user's box.

## Contents
1. Concepts · 2. QuickApp class · 3. Device types and properties · 4. `fibaro.*` · 5. `api.*` · 6. Timers ·
7. Network (HTTP, TCP, UDP, WebSocket, MQTT) · 8. UI · 9. Child devices · 10. Driving a QA from outside ·
11. Development tools

## 1. Concepts
- A QA is a device programmed in Lua, loaded once and kept in memory (unlike a scene). `onInit` runs at start-up and
  **after every save** of the code or variables. **[O]**
- Code is object-oriented: `QuickApp` is the class, `self` the instance; `self` only exists inside methods. **[O]**
- Nothing loops by itself: loops are timers. **[O]**
- Each action sent to the device (scene, app, REST) calls the method of the same name; action args = method args.
  `fibaro.call(44, "setValue", 90)` → `QuickApp:setValue(90)`. **[O]**
- A QA can have several Lua files; one is `main`. All files and UI handlers share the same environment. **[O]**
- Timers do not survive a QA restart; persist what matters with `self:setVariable`. **[S]**

## 2. QuickApp class
| Method | Notes |
|---|---|
| `self:debug(...)`, `:trace`, `:warning`, `:error` | console; several args joined with spaces **[O]** |
| `self:getVariable(name)` | returns `""` if missing **[S]** |
| `self:setVariable(name, value)` | persistent; creates the variable if needed **[S]** |
| `self:updateProperty(prop, value)` | `value`, `log`, `unit`, `deviceIcon`, `batteryLevel`, `dead`… **[S]** |
| `self:updateView(element, prop, value)` | `text` (label/button), `value` (slider/switch, string), `options` / `selectedItem` (select) **[S]** |
| `self:createChildDevice(props, Class)` · `self:initChildDevices(map)` · `self:removeChildDevice(id)` · `self.childDevices` | see §9 |
| `self.id`, `self.name`, `self.type`, `self.properties` | `self.properties.quickAppVariables` = `{ {name, value} }` |

`optionalVariable` (read without side effect):
```lua
function QuickApp:optionalVariable(name)
    for _, v in ipairs(self.properties.quickAppVariables or {}) do
        if v.name == name then return tostring(v.value or "") end
    end
    return ""
end
```

## 3. Device types and properties
| Type | `value` | Usual actions |
|---|---|---|
| `com.fibaro.binarySwitch` | `true/false` | `turnOn`, `turnOff` |
| `com.fibaro.multilevelSwitch` | 0–99 | `turnOn`, `turnOff`, `setValue(v)` |
| `com.fibaro.rollerShutter` | 0–99/100 (closed → open) | `open`, `close`, `stop`, `setValue(v)` |
| `com.fibaro.binarySensor`, `doorSensor`, `windowSensor`, `motionSensor`, `floodSensor` | boolean | — |
| `com.fibaro.temperatureSensor`, `humiditySensor`, `lightSensor`, `multilevelSensor` | number (+ `unit`) | — |
| `com.fibaro.energyMeter`, `powerMeter` | number | — **[V]** |
| `com.fibaro.hvacSystemAuto` / `hvacSystemHeat` / `hvacSystemCool` | thermostat: `thermostatMode`, `heatingThermostatSetpoint`… | `setThermostatMode`, `setHeatingThermostatSetpoint` **[V]** read an existing device of that type |
| `com.fibaro.deviceController` | no state | custom actions |
| `com.fibaro.player` | media | `play`, `pause`, `stop`, `setVolume`, `setMute` **[V]** |

Cosmetic properties on almost every type: `log` (text under the device name), `unit`. Interfaces add features:
`battery` (`batteryLevel`), `energy`, `power`, `light`… (set at creation, or in the `.fqa`). **[S]**
To learn the exact properties/actions of a type, read a real device: `api.get("/devices/<id>")` → `properties`,
`actions`.

Z-Wave notes: one physical module creates several devices: a hidden parent node (`com.fibaro.zwaveDevice` or
`zwaveNode`, holds `dead`, `model`, `zwaveCompany`) and functional children (sensor, temperature, tamper…).
`batteryLevel = 255` = "battery low" alarm from some modules (treat as 0). `dead = true` = unreachable.

## 4. Global `fibaro.*` **[S]**
```
fibaro.call(id|{ids}, action, ...)        -- asynchronous, returns nothing
fibaro.get(id, prop)  -> value, lastModified        fibaro.getValue(id, prop)
fibaro.getName(id)  fibaro.getType(id)  fibaro.getRoomID(id)  fibaro.getRoomName(roomId)  fibaro.getRoomNameByDeviceID(id)
fibaro.getSectionID(id)  fibaro.getDevicesID(filter)  fibaro.getIds(devices)  fibaro.getAllDeviceIds()
fibaro.getGlobalVariable(name) -> string   fibaro.setGlobalVariable(name, value)
fibaro.scene("execute"|"kill", {ids})     fibaro.profile(...)   fibaro.alarm(partition, "arm"|"disarm")
fibaro.alert("push"|"email"|"simplePush", ids, text)   -- see notifications.md
fibaro.emitCustomEvent(name)              fibaro.wakeUpDeadDevice(id)
fibaro.setTimeout(ms, fn)  fibaro.clearTimeout(ref)  fibaro.setInterval(ms, fn)  fibaro.clearInterval(ref)
fibaro.debug(tag, ...)  fibaro.trace / warning / error(tag, ...)   -- the TAG is mandatory (scenes, helpers)
fibaro.sleep(ms)                          -- blocking: avoid
```
`hub.*` is an alias on recent firmwares (code generated by block scenes uses `hub.alert`). `json.encode/decode` are
global.

## 5. `api.*` (REST API from inside the box)
`api.get(path)`, `api.post(path, table)`, `api.put(path, table)`, `api.delete(path)` → `data, httpCode`. Path without
`/api`. Synchronous. See `rest-api.md` for endpoints. **[S]**
```lua
local d, code = api.get("/devices/" .. id)
if code == 200 then self:debug(d.name, d.properties.value) end
local kids = api.get("/devices?parentId=" .. self.id) or {}
```
Alternative: HTTP to `http://127.0.0.1/api/...` with Basic auth (official example). **[O]**

## 6. Timers
Official: `fibaro.setTimeout(ms, fn)` (**delay first**). Community globals `setTimeout(fn, ms)` (function first) exist
but are not in the manual: do not mix them up. **[O]/[S]**
Errors in timer callbacks are sometimes silent → `pcall`. Recursive loop:
```lua
function QuickApp:loop()
    local ok, err = pcall(function() self:tick() end)
    if not ok then self:error("tick:", tostring(err)) end
    if self.loopRef then fibaro.clearTimeout(self.loopRef) end
    self.loopRef = fibaro.setTimeout(self.interval * 1000, function() self:loop() end)
end
```
Daily jobs: compare `os.date("%H:%M")` with a target inside the loop and store the last run date in a variable
(`lastReport = "2026-01-05"`) so a restart does not send it twice.

## 7. Network
### HTTP — `net.HTTPClient({timeout = ms})` **[O]**
```lua
self.http = net.HTTPClient({ timeout = 8000 })
self.http:request(url, {
    options = { method = "POST", headers = { ["Content-Type"] = "application/json" },
                data = json.encode(body), checkCertificate = true },
    success = function(r) -- r.status, r.data (string), r.headers
    end,
    error = function(msg) end,
})
```
Always asynchronous. Reuse one client. Basic auth: `["Authorization"] = "Basic " .. base64(user..":"..pass)`;
there is no guaranteed native base64 → bundle a small Lua implementation. Self-signed HTTPS: `checkCertificate = false`.
Digest auth (some cameras, intercoms): implement the challenge (MD5 in pure Lua) — first request gets 401 +
`WWW-Authenticate`, then answer. OAuth2 cloud APIs: store refresh token in a variable, refresh before expiry,
handle 401 by refreshing once.

### TCP — `net.TCPSocket({timeout = ms})` **[O]**
`connect(ip, port, {success, error})`, `read({success(data), error})`, `readUntil(delim, cb)`, `write(data, cb)`,
`close()`. Use `write` (the manual's examples do). Re-create the socket on error, reconnect after 5 s, add a watchdog
(no traffic for N s → reconnect): zombie connections are reported.

### UDP — `net.UDPSocket({broadcast = bool, timeout = ms})` **[O]**
`sendTo(data, ip, port, cb)`, `receive({success(data), error})`, `close()`. `receive` gives data only (no sender).

### WebSocket — `net.WebSocketClient()` / `net.WebSocketClientTls()` (≥ 5.041) **[S]**
`addEventListener("connected"|"disconnected"|"error"|"dataReceived", fn)`, `connect(url)`, `send(text)`.

### MQTT — `mqtt.Client.connect(uri, {clientId, username, password})` **[S]**
`addEventListener("connected"|"message", fn)` (`ev.topic`, `ev.payload`), `subscribe(topic, {qos})`,
`publish(topic, payload, {retain})`, `disconnect()`. Wildcards `#`, `+`.

### Limits
A QA cannot listen on a port (no server, no SSE). For push from outside, the external system calls the HC3 REST API
(§10). No usable coroutines. **[S]**

## 8. UI
Elements: label, button, slider; switch and select since 5.150. Events: button `onReleased` (also
`onLongPressDown`, `onLongPressReleased`), slider `onChanged`, select `onToggled`, switch `onReleased`. **[O]/[S]**
Handler receives `event = {deviceId, elementName, eventType, values = {…}}`; slider / select value in
`event.values[1]` (convert with `tonumber`).
```lua
self:updateView("labelStatus", "text", "🌡️ 21.5 °C")
self:updateView("slider1", "value", "50")
self:updateView("switch1", "value", "true")          -- the switch does not update itself
self:updateView("select1", "options", { { type = "option", text = "Eco", value = "eco" } })
```
Observed on 5.2xx: setting `selectedItem` from code can blank the select's display → show the current choice in a
label instead. Element names are auto-generated in the editor (`button_ID_0_1`): use the real names, or import a
`.fqa` that defines them. Labels accept emoji and simple HTML is not reliable: keep text short (mobile app width).
Children have no custom UI.

Icon: `self:updateProperty("deviceIcon", <iconSetId>)` (user icons ≥ 1000; upload: skill `hc3-icons`).

## 9. Child devices **[S]**
```lua
class 'SensorChild' (QuickAppChild)
function SensorChild:__init(device)
    QuickAppChild.__init(self, device)        -- mandatory
end
function SensorChild:turnOn() self.parent:send(self:getVariable("uid"), "on") end

function QuickApp:onInit()
    self:initChildDevices({ ["com.fibaro.temperatureSensor"] = SensorChild,
                            ["com.fibaro.binarySwitch"] = SensorChild })
    -- index existing children by a stable key stored in a child variable
    self.byKey = {}
    for id, child in pairs(self.childDevices) do self.byKey[child:getVariable("kind")] = child end
    if not self.byKey.outdoor then
        local c = self:createChildDevice({ name = "Outdoor temperature", type = "com.fibaro.temperatureSensor",
            initialProperties = {}, initialInterfaces = {} }, SensorChild)
        c:setVariable("kind", "outdoor")
        self.byKey.outdoor = c
    end
end
```
- `initChildDevices` re-links existing children at every start (the HC3 also calls it after `onInit` if you did not).
- Store the provider's identifier / your role key in a child variable; never rely on child names (users rename
  them) or on creation order.
- Remove children whose source disappeared: `self:removeChildDevice(id)`.
- Child rooms: children are created in the parent's room; the user can move them.

## 10. Driving a QA from outside
Any method can be called over REST (Basic auth):
```
POST http://<hc3>/api/devices/<qaId>/action/<method>     body {"args": [arg1, arg2]}
```
From a scene or another QA: `fibaro.call(qaId, "method", arg1, arg2)`. This is how external systems push data into
a QA (expose e.g. `setData(jsonString)`).

## 11. Development tools (optional)
Community emulators to develop in VS Code: **plua** (`pip install plua`), **fibaro-flua**, **hc3emu**, older
**TQAE**. Lines `--%%name=…`, `--%%type=…`, `--%%var=…` are comments for them; the HC3 ignores them. This skill's
`scripts/hc3sim.lua` is a lighter, dependency-free alternative for logic tests.
