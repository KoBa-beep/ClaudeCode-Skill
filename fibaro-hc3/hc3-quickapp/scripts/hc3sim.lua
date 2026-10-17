--[[
hc3sim.lua — tiny offline simulator to test a Fibaro HC3 QuickApp (or Lua scene) with plain Lua 5.3/5.4.

It mocks what most QuickApps use: QuickApp / QuickAppChild classes, class(), self:getVariable/setVariable,
updateProperty/updateView, fibaro.* (call, getValue, get, setTimeout/clearTimeout, setInterval, alert, emitCustomEvent,
getGlobalVariable/setGlobalVariable, debug…), api.get/post/put/delete, net.HTTPClient, json, and a VIRTUAL CLOCK
(os.time / os.date follow it), so hours of behaviour run in milliseconds.

It is NOT the HC3: it only checks your logic (timers, state machines, retries, notification texts). Always do the
final test on the box.

Usage:
    lua hc3sim.lua path/to/main.lua path/to/scenario.lua

Scenario file (plain Lua, runs after the QA file is loaded; `sim` is global):
    sim.devices[42] = { name = "Kitchen lamp", type = "com.fibaro.binarySwitch", roomID = 3, value = false }
    sim.rooms = { { id = 3, name = "Kitchen", sectionID = 1 } }
    sim.http("api.example.com/status", function(url, opts) return 200, '{"temp": 21.5}' end)
    sim.route("POST", "^/notificationCenter$", function(path, body) return {}, 200 end)
    local qa = sim.start({ name = "QA - TEST", type = "com.fibaro.binarySensor",
                           variables = { interval = "60", ids = "42" } })
    sim.run(5 * 60)                      -- advance the virtual clock 5 minutes, firing timers
    sim.devices[42].value = true         -- change the world…
    sim.run(60)
    qa:onSomeButton({ values = {} })     -- …or press a UI button
    sim.expect(sim.devices[42].value == true, "lamp should be on")
    sim.summary()
--]]

sim = { devices = {}, rooms = {}, sections = {}, globals = {}, calls = {}, pushes = {}, failures = 0 }
local unpack = table.unpack or unpack

------------------------------------------------------------------------ virtual clock
local clock = os.time({ year = 2026, month = 1, day = 5, hour = 8, min = 0, sec = 0 })   -- a Monday, 08:00
local realTime, realDate = os.time, os.date
os.time = function(t) if t then return realTime(t) end return math.floor(clock) end
os.date = function(f, t) return realDate(f, t or math.floor(clock)) end
os.clock = function() return clock end
function sim.setTime(t) clock = realTime(t) end          -- sim.setTime({year=2026, month=12, day=24, hour=21, min=0})
function sim.now() return clock end

------------------------------------------------------------------------ logging
local function fmt(...)
    local t = { ... }
    for i = 1, select("#", ...) do t[i] = tostring(t[i]) end
    return table.concat(t, " ")
end
function sim.log(kind, ...) print(realDate("%H:%M:%S", math.floor(clock)) .. " [" .. kind .. "] " .. fmt(...)) end
sim.quiet = {}   -- e.g. sim.quiet.DEBUG = true to hide self:debug lines

------------------------------------------------------------------------ json (enough for QuickApp payloads)
local function encode(v, out)
    local t = type(v)
    if t == "nil" then out[#out + 1] = "null"
    elseif t == "boolean" or t == "number" then out[#out + 1] = tostring(v)
    elseif t == "string" then
        out[#out + 1] = '"' .. v:gsub('[%c"\\]', function(c)
            local m = { ['"'] = '\\"', ["\\"] = "\\\\", ["\n"] = "\\n", ["\r"] = "\\r", ["\t"] = "\\t" }
            return m[c] or string.format("\\u%04x", c:byte())
        end) .. '"'
    elseif t == "table" then
        local n = #v
        local isArray = n > 0 or next(v) == nil
        if isArray then for k in pairs(v) do if type(k) ~= "number" then isArray = false break end end end
        if isArray then
            out[#out + 1] = "["
            for i = 1, n do if i > 1 then out[#out + 1] = "," end encode(v[i], out) end
            out[#out + 1] = "]"
        else
            out[#out + 1] = "{"
            local first = true
            for k, x in pairs(v) do
                if not first then out[#out + 1] = "," end
                first = false
                encode(tostring(k), out); out[#out + 1] = ":"; encode(x, out)
            end
            out[#out + 1] = "}"
        end
    else error("json.encode: cannot encode " .. t) end
end

local function decode(s)
    local i = 1
    local function ws() i = s:find("[^ \t\r\n]", i) or #s + 1 end
    local value
    local function str()
        local buf, j = {}, i + 1
        while true do
            local c = s:sub(j, j)
            if c == "" then error("json.decode: unterminated string") end
            if c == '"' then i = j + 1 return table.concat(buf) end
            if c == "\\" then
                local e = s:sub(j + 1, j + 1)
                local m = { n = "\n", r = "\r", t = "\t", b = "\b", f = "\f", ["/"] = "/", ["\\"] = "\\", ['"'] = '"' }
                if e == "u" then
                    local cp = tonumber(s:sub(j + 2, j + 5), 16)
                    buf[#buf + 1] = utf8 and utf8.char(cp) or "?"
                    j = j + 6
                else buf[#buf + 1] = m[e] or e; j = j + 2 end
            else buf[#buf + 1] = c; j = j + 1 end
        end
    end
    function value()
        ws()
        local c = s:sub(i, i)
        if c == "{" then
            local t = {}; i = i + 1; ws()
            if s:sub(i, i) == "}" then i = i + 1 return t end
            while true do
                ws(); local k = str(); ws()
                if s:sub(i, i) ~= ":" then error("json.decode: ':' expected at " .. i) end
                i = i + 1; t[k] = value(); ws()
                local d = s:sub(i, i); i = i + 1
                if d == "}" then return t elseif d ~= "," then error("json.decode: ',' expected at " .. i) end
            end
        elseif c == "[" then
            local t = {}; i = i + 1; ws()
            if s:sub(i, i) == "]" then i = i + 1 return t end
            while true do
                t[#t + 1] = value(); ws()
                local d = s:sub(i, i); i = i + 1
                if d == "]" then return t elseif d ~= "," then error("json.decode: ',' expected at " .. i) end
            end
        elseif c == '"' then return str()
        elseif s:sub(i, i + 3) == "true" then i = i + 4 return true
        elseif s:sub(i, i + 4) == "false" then i = i + 5 return false
        elseif s:sub(i, i + 3) == "null" then i = i + 4 return nil
        else
            local num = s:match("^-?%d+%.?%d*[eE]?[-+]?%d*", i)
            if not num or num == "" then error("json.decode: unexpected '" .. c .. "' at " .. i) end
            i = i + #num
            return tonumber(num)
        end
    end
    local v = value()
    return v
end

json = {
    encode = function(v) local out = {}; encode(v, out); return table.concat(out) end,
    decode = function(s) if type(s) ~= "string" then error("json.decode: string expected") end return decode(s) end,
}

------------------------------------------------------------------------ timers
local timers, timerSeq = {}, 0
local function addTimer(ms, fn, every)
    timerSeq = timerSeq + 1
    timers[timerSeq] = { at = clock + (ms or 0) / 1000, fn = fn, every = every, seq = timerSeq }
    return timerSeq
end
local function clearTimer(ref) if ref then timers[ref] = nil end end

-- Advance the virtual clock by `seconds`, firing every due timer in order. Errors inside timers are reported
-- (the real HC3 sometimes swallows them silently: wrap timer bodies in pcall in the QA).
function sim.run(seconds)
    local stop = clock + seconds
    while true do
        local nextT
        for _, t in pairs(timers) do
            if t.at <= stop and (not nextT or t.at < nextT.at or (t.at == nextT.at and t.seq < nextT.seq)) then nextT = t end
        end
        if not nextT then break end
        clock = math.max(clock, nextT.at)
        if nextT.every then nextT.at = clock + nextT.every / 1000 else timers[nextT.seq] = nil end
        local ok, err = pcall(nextT.fn)
        if not ok then sim.log("TIMER ERROR", err) end
    end
    clock = stop
end
function sim.pendingTimers() local n = 0 for _ in pairs(timers) do n = n + 1 end return n end

------------------------------------------------------------------------ devices
-- sim.devices[id] = { name, type, roomID, parentId, value, <any property>…, actions = { turnOn = function(dev, ...) end } }
local function dev(id)
    local d = sim.devices[tonumber(id)]
    return d
end

local function asApiDevice(id, d)
    local props = {}
    for k, v in pairs(d) do
        if k ~= "name" and k ~= "type" and k ~= "roomID" and k ~= "parentId" and k ~= "actions" and k ~= "baseType"
            and k ~= "interfaces" and k ~= "enabled" and k ~= "visible" then props[k] = v end
    end
    return { id = id, name = d.name or ("Device " .. id), type = d.type or "com.fibaro.binarySwitch",
             baseType = d.baseType or "", roomID = d.roomID or 0, parentId = d.parentId or 0,
             interfaces = d.interfaces or {}, enabled = d.enabled ~= false, visible = d.visible ~= false,
             properties = props }
end

local DEFAULT_ACTIONS = {
    turnOn = function(d) d.value = (type(d.value) == "number") and 99 or true end,
    turnOff = function(d) d.value = (type(d.value) == "number") and 0 or false end,
    setValue = function(d, v) d.value = tonumber(v) or v end,
    open = function(d) d.value = 99 end,
    close = function(d) d.value = 0 end,
}

local function callDevice(id, action, ...)
    id = tonumber(id)
    sim.calls[#sim.calls + 1] = { id = id, action = action, args = { ... }, time = clock }
    sim.log("CALL", id, action, fmt(...))
    local d = dev(id)
    if not d then return end
    if d.qa then                               -- another simulated QuickApp: call its method
        local f = d.qa[action]
        if f then f(d.qa, ...) end
        return
    end
    local f = (d.actions or {})[action] or DEFAULT_ACTIONS[action]
    if f then f(d, ...) end
end

-- Calls recorded since the start (or since sim.clearCalls()), optionally filtered.
function sim.callsTo(id, action)
    local out = {}
    for _, c in ipairs(sim.calls) do
        if (not id or c.id == id) and (not action or c.action == action) then out[#out + 1] = c end
    end
    return out
end
function sim.clearCalls() sim.calls = {} end

------------------------------------------------------------------------ api.*
local routes = {}
-- sim.route("GET", "^/weather$", function(path, body) return { Temperature = 12 }, 200 end)
function sim.route(method, pattern, handler) table.insert(routes, 1, { method = method, pattern = pattern, handler = handler }) end

local function query(path, key) return path:match("[?&]" .. key .. "=([^&]+)") end

local function builtin(method, path, body)
    if method == "GET" then
        local id = path:match("^/devices/(%d+)$")
        if id then
            local d = dev(id)
            if d then return asApiDevice(tonumber(id), d), 200 end
            return { type = "ERROR", reason = "Device not found" }, 404
        end
        if path:match("^/devices%??") then
            local out = {}
            local ids = {}
            for i in pairs(sim.devices) do ids[#ids + 1] = i end
            table.sort(ids)
            for _, i in ipairs(ids) do
                local a = asApiDevice(i, sim.devices[i])
                local ok = true
                if query(path, "type") and a.type ~= query(path, "type") then ok = false end
                if query(path, "parentId") and tostring(a.parentId) ~= query(path, "parentId") then ok = false end
                if query(path, "roomID") and tostring(a.roomID) ~= query(path, "roomID") then ok = false end
                if ok then out[#out + 1] = a end
            end
            return out, 200
        end
        if path == "/rooms" then return sim.rooms, 200 end
        if path == "/sections" then return sim.sections, 200 end
        if path:match("^/globalVariables/") then
            local n = path:match("^/globalVariables/(.+)$")
            if sim.globals[n] == nil then return nil, 404 end
            return { name = n, value = sim.globals[n] }, 200
        end
        if path:match("^/debugMessages") then return { nextLast = 0, messages = {} }, 200 end
        if path == "/diagnostics" then
            return { memory = { used = 40, free = 60, cache = 0, buffers = 0 }, storage = { internal = { { name = "user", used = 20 } } } }, 200
        end
    elseif method == "POST" then
        local id, action = path:match("^/devices/(%d+)/action/([%w_]+)$")
        if id then
            if action == "sendGlobalPushNotifications" or action == "sendPush" then
                local text = body and body.args and body.args[1]
                sim.pushes[#sim.pushes + 1] = { phone = tonumber(id), text = text, time = clock }
                sim.log("PUSH", "phone " .. id .. ": " .. tostring(text))
            else
                callDevice(id, action, unpack(body and body.args or {}))
            end
            return {}, 202
        end
        if path == "/notificationCenter" then
            sim.log("NOTIFICATION CENTER", "[" .. tostring(body and body.priority) .. "] " ..
                tostring(body and body.data and body.data.text))
            return {}, 201
        end
    elseif method == "PUT" then
        local id = path:match("^/devices/(%d+)$")
        if id and dev(id) and body and body.properties then
            for k, v in pairs(body.properties) do dev(id)[k] = v end
            return {}, 200
        end
    end
    return nil
end

local function apiCall(method, path, body)
    for _, r in ipairs(routes) do
        if (r.method == method or r.method == "*") and path:match(r.pattern) then
            local data, code = r.handler(path, body)
            sim.log("API", method, path, "->", code or 200)
            return data, code or 200
        end
    end
    local data, code = builtin(method, path, body)
    if code then return data, code end
    sim.log("API", method, path, "-> 404 (no route: add sim.route)")
    return nil, 404
end

api = {
    get = function(p) return apiCall("GET", p) end,
    post = function(p, b) return apiCall("POST", p, b) end,
    put = function(p, b) return apiCall("PUT", p, b) end,
    delete = function(p) return apiCall("DELETE", p) end,
}

------------------------------------------------------------------------ net.HTTPClient
local httpHandlers = {}
-- sim.http("example.com/api", function(url, options) return 200, '{"ok":true}', {headers} end)
-- Return nil, "error text" to simulate a network error. Handlers are tried newest first (Lua patterns on the URL).
function sim.http(pattern, handler) table.insert(httpHandlers, 1, { pattern = pattern, handler = handler }) end
sim.httpDelayMs = 200

net = {
    HTTPClient = function(opts)
        return {
            request = function(_, url, p)
                p = p or {}
                local o = p.options or {}
                sim.log("HTTP", o.method or "GET", url)
                addTimer(sim.httpDelayMs, function()
                    for _, h in ipairs(httpHandlers) do
                        if url:find(h.pattern, 1, true) or url:match(h.pattern) then
                            local status, data, headers = h.handler(url, o)
                            if status == nil then
                                if p.error then p.error(data or "Operation canceled") end
                            elseif p.success then
                                p.success({ status = status, data = data or "", headers = headers or {} })
                            end
                            return
                        end
                    end
                    if p.error then p.error("sim: no handler for " .. url) end
                end)
            end,
        }
    end,
}

------------------------------------------------------------------------ fibaro.*
local function logger(kind)
    return function(tag, ...)
        if not sim.quiet[kind] then sim.log(kind, tostring(tag) .. ":", ...) end
    end
end

fibaro = {
    debug = logger("DEBUG"), trace = logger("TRACE"), warning = logger("WARNING"), error = logger("ERROR"),
    call = function(id, action, ...)
        if type(id) == "table" then for _, i in ipairs(id) do callDevice(i, action, ...) end return end
        callDevice(id, action, ...)
    end,
    getValue = function(id, prop) local d = dev(id) if d then return d[prop or "value"] end end,
    get = function(id, prop) local d = dev(id) if d then return d[prop or "value"], d.modified or clock end end,
    getName = function(id) local d = dev(id) return d and d.name end,
    getType = function(id) local d = dev(id) return d and d.type end,
    getRoomID = function(id) local d = dev(id) return d and d.roomID end,
    getRoomName = function(roomId) for _, r in ipairs(sim.rooms) do if r.id == roomId then return r.name end end end,
    getRoomNameByDeviceID = function(id)
        local d = dev(id)
        for _, r in ipairs(sim.rooms) do if d and r.id == d.roomID then return r.name end end
    end,
    getGlobalVariable = function(n) return sim.globals[n] end,
    setGlobalVariable = function(n, v) sim.globals[n] = tostring(v); sim.log("GLOBAL", n, "=", v) end,
    setTimeout = function(ms, fn) return addTimer(ms, fn) end,
    clearTimeout = clearTimer,
    setInterval = function(ms, fn) return addTimer(ms, fn, ms) end,
    clearInterval = clearTimer,
    sleep = function(ms) clock = clock + ms / 1000 end,
    alert = function(kind, users, text)
        sim.pushes[#sim.pushes + 1] = { alert = kind, users = users, text = text, time = clock }
        sim.log("ALERT", kind, json.encode(users or {}), text)
    end,
    emitCustomEvent = function(n) sim.log("CUSTOM EVENT", n) end,
    scene = function(action, ids) sim.log("SCENE", action, json.encode(ids or {})) end,
    wakeUpDeadDevice = function(id) sim.log("WAKEUP", id) end,
}
-- community-style globals (function first, then delay)
setTimeout = function(fn, ms) return addTimer(ms, fn) end
clearTimeout = clearTimer
setInterval = function(fn, ms) return addTimer(ms, fn, ms) end
clearInterval = clearTimer
hub = fibaro

------------------------------------------------------------------------ classes
function class(name)
    return function(base)
        local c = {}
        c.__index = c
        setmetatable(c, {
            __index = base,
            __call = function(cls, ...)
                local o = setmetatable({}, cls)
                if o.__init then o:__init(...) end
                return o
            end,
        })
        _G[name] = c
        return c
    end
end

local Base = {}
Base.__index = Base

local function varList(self) self.properties.quickAppVariables = self.properties.quickAppVariables or {} return self.properties.quickAppVariables end
function Base:getVariable(name)
    for _, v in ipairs(varList(self)) do if v.name == name then return v.value end end
    return ""                                         -- like the HC3: "" (not nil) for a missing variable
end
function Base:setVariable(name, value)
    for _, v in ipairs(varList(self)) do if v.name == name then v.value = value return end end
    table.insert(varList(self), { name = name, value = value })
end
function Base:updateProperty(prop, value)
    self.properties[prop] = value
    local d = sim.devices[self.id]
    if d then d[prop] = value end
    sim.log("PROPERTY", self.id, prop, "=", type(value) == "table" and json.encode(value) or value)
end
function Base:updateView(element, prop, value)
    self.view = self.view or {}
    self.view[element] = self.view[element] or {}
    self.view[element][prop] = value
    if not sim.quiet.VIEW then sim.log("VIEW", element .. "." .. prop, "=", type(value) == "table" and json.encode(value) or value) end
end
for _, kind in ipairs({ "debug", "trace", "warning", "error" }) do
    local K = kind:upper()
    Base[kind] = function(self, ...) if not sim.quiet[K] then sim.log(K, ...) end end
end

QuickAppBase = Base
QuickApp = setmetatable({}, { __index = Base })
QuickApp.__index = QuickApp

QuickAppChild = setmetatable({}, { __index = Base })
QuickAppChild.__index = QuickAppChild
function QuickAppChild:__init(device)
    self.id, self.name, self.type = device.id, device.name, device.type
    self.properties = device.properties or {}
    self.parent = sim.qa
end

local nextChildId = 900
function QuickApp:createChildDevice(props, cls)
    nextChildId = nextChildId + 1
    local d = { id = nextChildId, name = props.name, type = props.type, properties = props.initialProperties or {} }
    d.properties.quickAppVariables = d.properties.quickAppVariables or {}
    sim.devices[d.id] = { name = d.name, type = d.type, parentId = self.id }
    local child = (cls or QuickAppChild)(d)
    sim.devices[d.id].qa = child
    self.childDevices[d.id] = child
    sim.log("CHILD", "created", d.id, d.name, d.type)
    return child
end
function QuickApp:initChildDevices(map)
    self.childClasses = map or {}
    for id, def in pairs(sim.existingChildren or {}) do
        local cls = (map or {})[def.type] or QuickAppChild
        local child = cls({ id = id, name = def.name, type = def.type, properties = def.properties or {} })
        sim.devices[id] = sim.devices[id] or { name = def.name, type = def.type, parentId = self.id }
        sim.devices[id].qa = child
        self.childDevices[id] = child
    end
end
function QuickApp:removeChildDevice(id) self.childDevices[id] = nil sim.devices[id] = nil sim.log("CHILD", "removed", id) end

------------------------------------------------------------------------ start / assertions
-- sim.start{ id=, name=, type=, variables = { k = "v" } | { {name=,value=} }, properties = {} } → the QuickApp instance
function sim.start(def)
    def = def or {}
    local vars = {}
    for k, v in pairs(def.variables or {}) do
        if type(k) == "number" then vars[#vars + 1] = v else vars[#vars + 1] = { name = k, value = v } end
    end
    table.sort(vars, function(a, b) return a.name < b.name end)
    local qa = setmetatable({}, QuickApp)
    qa.id, qa.name, qa.type = def.id or 500, def.name or "QA - TEST", def.type or "com.fibaro.binarySwitch"
    qa.properties = def.properties or {}
    qa.properties.quickAppVariables = vars
    qa.childDevices = {}
    sim.qa = qa
    sim.devices[qa.id] = sim.devices[qa.id] or { name = qa.name, type = qa.type }
    sim.devices[qa.id].qa = qa
    if qa.onInit then
        local ok, err = pcall(qa.onInit, qa)
        if not ok then sim.log("ONINIT ERROR", err) sim.failures = sim.failures + 1 end
    end
    return qa
end

function sim.expect(cond, message)
    if cond then print("  ✔ " .. message) else print("  ✘ " .. message) sim.failures = sim.failures + 1 end
end
function sim.step(title) print("\n=== " .. title) end
function sim.summary()
    print(sim.failures == 0 and "\nALL CHECKS PASSED" or ("\n" .. sim.failures .. " CHECK(S) FAILED"))
    os.exit(sim.failures == 0 and 0 or 1)
end

------------------------------------------------------------------------ main
if arg and arg[1] then
    local files = { arg[1], arg[2] }
    if not arg[2] then print("usage: lua hc3sim.lua main.lua scenario.lua") os.exit(2) end
    dofile(files[1])
    dofile(files[2])
end
