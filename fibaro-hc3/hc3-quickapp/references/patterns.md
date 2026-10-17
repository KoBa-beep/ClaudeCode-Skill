# Tested QuickApp patterns

Building blocks validated on real HC3 boxes (5.2xx) and in the offline simulator. Copy, then adapt names and texts
to the user's language.

## Contents
1. Variables: optional values, ID lists, mappings · 2. setIfChanged · 3. Loop, back-off, daily job ·
4. Children keyed by role · 5. Dynamic icon (deviceController) · 6. Describe a device in clear text ·
7. Actuator: verify the relay, count real transitions, anti short-cycle · 8. Unreachable modules and batteries ·
9. Fast rise detection (sliding window) · 10. Alarm: repeat, stop, snapshot / restore · 11. Daily report and journal ·
12. Calling another QuickApp

## 1. Variables
```lua
local function trim(s) return (tostring(s or ""):match("^%s*(.-)%s*$")) end
local function idList(text) local t = {} for n in tostring(text or ""):gmatch("%d+") do t[#t + 1] = tonumber(n) end return t end
local function contains(list, x) for _, v in ipairs(list) do if v == x then return true end end return false end

-- "Living=93+166, Bedroom=96" -> { {name="Living", ids={93,166}}, {name="Bedroom", ids={96}} }
local function parseMap(text)
    local out = {}
    for item in tostring(text or ""):gmatch("[^,;]+") do
        local name, ids = item:match("^%s*(.-)%s*=%s*(.-)%s*$")
        if name and name ~= "" then out[#out + 1] = { name = name, ids = idList(ids) } end
    end
    return out
end
```
Rules: every variable optional with a default; `tonumber` + bounds (`math.max(5, …)`); state the defaults in the
README; secrets stay empty in shipped defaults; a variable written by the QA (e.g. `lastReport`, `snapshot`) is
documented as "filled automatically".

## 2. setIfChanged
```lua
local function setIfChanged(device, property, value)
    device.cache = device.cache or {}
    if device.cache[property] ~= value then
        device:updateProperty(property, value)
        device.cache[property] = value
    end
end
```
Works on `self` and on children. Same idea for labels (`updateView` only on change) if they refresh every few seconds.

## 3. Loop, back-off, daily job
```lua
function QuickApp:loop()
    local ok, err = pcall(function() self:tick(os.time()) end)
    if not ok then self:error("tick:", tostring(err)) end
    if self.loopRef then fibaro.clearTimeout(self.loopRef) end
    self.loopRef = fibaro.setTimeout(self.interval * 1000, function() self:loop() end)
end

function QuickApp:tick(now)
    -- … work …
    local today = os.date("%Y-%m-%d", now)
    if os.date("%H:%M", now) >= self.reportTime and self:optionalVariable("lastReport") ~= today then
        self:setVariable("lastReport", today)          -- persisted: a restart will not resend it
        self:sendDailyReport()
    end
end
```
Network back-off: on failure retry after 10 s, 30 s, 60 s, then the normal interval; notify once after N failures,
and once when it recovers (keep a boolean so you never notify every cycle).

## 4. Children keyed by role
Store a role key in each child (`kind`) and rebuild an index at start-up, so renaming or moving a child never breaks
the QA and missing children are recreated:
```lua
local KINDS = {
    { kind = "fire", name = "Safety - Fire", type = "com.fibaro.binarySensor" },
    { kind = "co",   name = "Safety - CO",   type = "com.fibaro.binarySensor" },
}
class 'RoleChild' (QuickAppChild)
function RoleChild:__init(device) QuickAppChild.__init(self, device) end

function QuickApp:setupChildren()
    self:initChildDevices({ ["com.fibaro.binarySensor"] = RoleChild })
    self.kids = {}
    for _, child in pairs(self.childDevices) do
        local k = child:getVariable("kind")
        if k ~= "" then self.kids[k] = child end
    end
    for _, def in ipairs(KINDS) do
        if not self.kids[def.kind] then
            local c = self:createChildDevice({ name = def.name, type = def.type,
                initialProperties = {}, initialInterfaces = {} }, RoleChild)
            c:setVariable("kind", def.kind)
            self.kids[def.kind] = c
        end
    end
end
```

## 5. Dynamic icon for a deviceController
A `deviceController` icon set holds one image, so state cannot be shown by the HC3 itself. Upload one icon per state
(each gives an ID), let the user paste the IDs into variables, and switch:
```lua
-- variables iconOk / iconWarning / iconAlarm = icon IDs (empty = keep the current icon)
function QuickApp:updateIcon(state)            -- "Ok" | "Warning" | "Alarm"
    local id = tonumber(self:optionalVariable("icon" .. state))
    if id then setIfChanged(self, "deviceIcon", id) end
end
```
Same for any type when the icon must follow a *mode* (Auto / Away / Off) rather than `value`.
Never `api.put("/devices/<own id>")` to change it: the QA restarts.

## 6. Describe a device in clear text
Users do not know IDs. Build "what — room (floor)" once and cache it; use the full form in notifications, a short
form (emoji + room) in labels:
```lua
function QuickApp:loadRooms()
    local sections = {}
    for _, s in ipairs(api.get("/sections") or {}) do sections[s.id] = s.name end
    self.rooms = {}
    for _, r in ipairs(api.get("/rooms") or {}) do self.rooms[r.id] = { name = r.name, floor = sections[r.sectionID] } end
end

function QuickApp:info(id)
    self.infoCache = self.infoCache or {}
    if self.infoCache[id] then return self.infoCache[id] end
    local d = api.get("/devices/" .. id)
    local res = { what = "device " .. id, place = "unknown room", icon = "❔" }
    if type(d) == "table" and d.name then
        local t, role = tostring(d.type), tostring((d.properties or {}).deviceRole or "")
        if role == "SmokeSensor" or t:find("smoke") then res.what, res.icon = "smoke detector", "💭"
        elseif role == "CODetector" then res.what, res.icon = "carbon monoxide (CO) detector", "💭CO"
        elseif t:find("temperatureSensor") then res.what, res.icon = "temperature probe", "🌡️"
        else res.what = d.name end
        local r = self.rooms[d.roomID]
        if r then res.place = r.name .. (r.floor and (" (" .. r.floor .. ")") or "") end
    end
    local custom = self.customNames and self.customNames[id]      -- optional override variable "names": "146=Hall smoke"
    if custom then res.what = custom end
    res.full = res.what .. " — " .. res.place
    self.infoCache[id] = res
    return res
end
```
For a temperature child of a multi-sensor, read the hidden parent node (`d.parentId`, its `properties.model`) to say
"temperature probe of the smoke detector". Log the resolved names at start-up so the user can check them.

## 7. Actuator: verify, count real transitions, anti short-cycle
Commands to Z-Wave relays can be lost. Command → check the real state a few seconds later → retry once → alert.
Count "starts" on the **observed** off→on transition, not on commands (otherwise retries and manual actions count twice):
```lua
local function isOn(v) return v == true or v == "true" or (tonumber(v) or 0) > 0 end

function QuickApp:command(on, reason, retry)
    fibaro.call(self.relayId, on and "turnOn" or "turnOff")
    self.wanted, self.lastChange, self.pending = on, os.time(), true
    if on then self.lastReason = reason end
    fibaro.setTimeout(15000, function()
        self.pending = nil
        if isOn(fibaro.getValue(self.relayId, "value")) ~= on then
            if not retry then return self:command(on, reason, true) end
            self:notify("Relay " .. self.relayId .. " did not follow the command", "alert")
        end
    end)
end

function QuickApp:observe(now)                  -- called every tick
    local actual = isOn(fibaro.getValue(self.relayId, "value"))
    if actual and not self.relayOn and (not self.relayOffAt or now - self.relayOffAt >= 60) then
        self:countStart(now, self.lastReason or "manual")     -- ignores sub-minute flickers
        self.lastReason = nil
    elseif not actual and self.relayOn then
        self.relayOffAt = now
    end
    self.relayOn = actual
end
```
Anti short-cycle (boilers, compressors): refuse ON if `now - lastChange < minOff`, refuse OFF if `< minOn`; show
"start in 4 min (minimum off time)" in the label instead of silently waiting.

## 8. Unreachable modules and batteries
```lua
local all = api.get("/devices") or {}
local byId = {} for _, d in ipairs(all) do byId[d.id] = d end
local function moduleKey(d)                       -- one Z-Wave module = hidden parent node + visible children
    local p = d.parentId and byId[d.parentId]
    if p and d.parentId > 1 and p.visible == false then return d.parentId end
    return d.id
end
```
- Report a module once (key = parent node), named after its first visible child + room ("(+2)" for the others).
- `dead == true` for more than N minutes (ignore short glitches), then a "back online" message.
- Battery: `batteryLevel <= threshold` or `== 255` (low-battery alarm). Battery devices that sleep can be marked
  dead until their next wake-up: `fibaro.wakeUpDeadDevice(id)` only helps mains-powered nodes.
- Let the user ignore devices (`ignoreIds`) — a module unplugged on purpose must not alert forever.

## 9. Fast rise detection (sliding window)
```lua
-- keep (time, value) samples per sensor for `windowMin` minutes; alert if value - min(window) >= riseC
function QuickApp:feed(id, v, now)
    local h = self.hist[id] or {}; self.hist[id] = h
    h[#h + 1] = { t = now, v = v }
    while h[1] and now - h[1].t > self.windowMin * 60 do table.remove(h, 1) end
    local low = v for _, s in ipairs(h) do low = math.min(low, s.v) end
    return v - low >= self.riseC, v - low
end
```
Combine with an absolute threshold (e.g. ≥ 45 °C) and a frost threshold. Sensors report on change only: also treat
"no report for hours" as a health issue.

## 10. Alarm: repeat, stop, snapshot / restore
- Repeat the push every N minutes while active (cap the duration), stop on a "Stop alarm" button or when all sources
  are back to normal. Avoid jargon such as "acknowledge" in the UI: "Stop the alarm", "Restore everything".
- Before acting (lights to 99 %, shutters open, siren, heating off), save the previous state in a variable as JSON
  (`snapshot`), only if no snapshot exists yet; "Restore" replays it and clears it:
```lua
function QuickApp:takeSnapshot()
    if self:optionalVariable("snapshot") ~= "" then return end
    local snap = { lights = {}, shutters = {} }
    for _, id in ipairs(self.lightIds) do snap.lights[tostring(id)] = fibaro.getValue(id, "value") end
    for _, id in ipairs(self.shutterIds) do snap.shutters[tostring(id)] = fibaro.getValue(id, "value") end
    self:setVariable("snapshot", json.encode(snap))
end
```
  JSON object keys are strings: convert back with `tonumber(k)`.
- Colour devices: save `color` ("r,g,b,w") and `value`; blink with a timer, cap the blinking duration.
- Provide test buttons ("Test fire") that run the full chain with a "TEST" prefix in every message.

## 11. Daily report and journal
Keep daily counters in a JSON variable (`stats = {date, starts, runSeconds, log = {"07:12 room X"}}`), reset when the
date changes, cap list lengths (e.g. 40 lines). A "Today's log" button prints to the console **and** sends it as a
notification (users read their phone, not the console). Send the daily summary only when there is a problem, unless
the user opts in (`reportAlways = 1`).

## 12. Calling another QuickApp
`fibaro.call(otherQaId, "setMode", "Away")` calls its Lua method (asynchronous, no return value). To read its state,
read its properties (`fibaro.getValue(id, "value")`) or its variables:
```lua
local d = api.get("/devices/" .. id)
for _, v in ipairs(d and d.properties.quickAppVariables or {}) do if v.name == "mode" then return v.value end end
```
Check the target type first (`d.type`) and log a clear error when the configured ID is not the expected QA.
