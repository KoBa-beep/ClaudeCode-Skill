--[[
QA - TEMPLATE  —  Version 1.0.0
Skeleton of a polling QuickApp (HTTP JSON → temperature sensor) showing the recommended structure:
constants → helpers → onInit → loop → actions → network → UI → notifications.

Device type: com.fibaro.temperatureSensor
Variables (all optional, default in brackets):
  url          JSON endpoint returning {"temperature": 21.5}            ("")
  interval     seconds between two polls, minimum 10                    (60)
  alertAbove   send a notification above this temperature, empty = off  ("")
  notifyUsers  user IDs for fibaro.alert("push") fallback, "1,2"        ("")
  notifyPhones mobile device IDs (type iOS_device, Android included)    ("")
UI: labelStatus (label), btnRefresh (button, onReleased = onRefreshClicked)
--]]

local VERSION = "1.0.0"
local MIN_INTERVAL = 10
local RETRY_S = { 10, 30, 60 }          -- back-off after network errors

------------------------------------------------------------------------ helpers
local function trim(s) return (tostring(s or ""):match("^%s*(.-)%s*$")) end

local function idList(text)              -- "12, 15,x" -> {12, 15}
    local t = {}
    for n in tostring(text or ""):gmatch("%d+") do t[#t + 1] = tonumber(n) end
    return t
end

-- Update a property only when it changes (avoids useless scene triggers and event-history noise)
local function setIfChanged(device, property, value)
    device.cache = device.cache or {}
    if device.cache[property] ~= value then
        device:updateProperty(property, value)
        device.cache[property] = value
    end
end

------------------------------------------------------------------------ start
function QuickApp:onInit()
    self:debug(self.name, "version", VERSION, "id", self.id)
    self.url = trim(self:optionalVariable("url"))
    self.interval = math.max(MIN_INTERVAL, tonumber(self:optionalVariable("interval")) or 60)
    self.alertAbove = tonumber(self:optionalVariable("alertAbove"))
    self.users = idList(self:optionalVariable("notifyUsers"))
    self.phones = idList(self:optionalVariable("notifyPhones"))
    self.http = net.HTTPClient({ timeout = 8000 })
    self.failures = 0
    self:updateProperty("unit", "°C")
    if self.url == "" then
        self:updateView("labelStatus", "text", "⚠️ Set the 'url' variable")
        self:warning("Variable 'url' is empty: nothing to poll")
        return
    end
    fibaro.setTimeout(2000, function() self:loop() end)
end

-- Reads a variable WITHOUT creating it and without the "" vs nil ambiguity of getVariable
function QuickApp:optionalVariable(name)
    for _, v in ipairs(self.properties.quickAppVariables or {}) do
        if v.name == name then return tostring(v.value or "") end
    end
    return ""
end

------------------------------------------------------------------------ main loop (one recursive timer)
function QuickApp:loop()
    if self.loopRef then fibaro.clearTimeout(self.loopRef) end
    local ok, err = pcall(function() self:poll() end)
    if not ok then self:error("poll:", tostring(err)) end
end

function QuickApp:scheduleNext(delay)
    if self.loopRef then fibaro.clearTimeout(self.loopRef) end     -- never two loops (e.g. button pressed mid-request)
    self.loopRef = fibaro.setTimeout(delay * 1000, function() self:loop() end)
end

------------------------------------------------------------------------ network
function QuickApp:poll()
    self.http:request(self.url, {
        options = { method = "GET", headers = { Accept = "application/json" } },
        success = function(resp)
            if resp.status == 200 then
                local ok, data = pcall(json.decode, resp.data)
                if ok and type(data) == "table" and tonumber(data.temperature) then
                    self.failures = 0
                    self:apply(tonumber(data.temperature))
                    return self:scheduleNext(self.interval)
                end
                self:warning("Unexpected answer:", tostring(resp.data):sub(1, 120))
            else
                self:warning("HTTP", resp.status)
            end
            self:onFailure()
        end,
        error = function(msg)
            self:warning("Network error:", tostring(msg))
            self:onFailure()
        end,
    })
end

function QuickApp:onFailure()
    self.failures = self.failures + 1
    local delay = RETRY_S[math.min(self.failures, #RETRY_S)]
    self:updateView("labelStatus", "text", string.format("⚠️ No answer (%d) · retry in %d s", self.failures, delay))
    if self.failures == 5 then self:notify(self.name .. ": no answer from the device for 5 attempts", "warning") end
    self:scheduleNext(delay)
end

function QuickApp:apply(temp)
    setIfChanged(self, "value", temp)
    self:updateView("labelStatus", "text", string.format("🌡️ %.1f °C · %s", temp, os.date("%H:%M")))
    local high = self.alertAbove and temp > self.alertAbove
    if high and not self.alerted then
        self:notify(string.format("%s: %.1f °C (above %s °C)", self.name, temp, self.alertAbove), "alert")
    end
    self.alerted = high
end

------------------------------------------------------------------------ UI
function QuickApp:onRefreshClicked()
    self:debug("Manual refresh")
    self:loop()
end

------------------------------------------------------------------------ notifications
-- Direct push to each phone (most reliable), fallback fibaro.alert("push") by user, plus the HC3 notification centre.
function QuickApp:notify(text, priority)
    self:warning(text)
    api.post("/notificationCenter", { type = "GenericDeviceNotification", priority = priority or "warning",
        wasRead = false, canBeDeleted = true, data = { deviceId = self.id, title = self.name, text = text } })
    local sent = 0
    for _, phone in ipairs(self.phones) do
        local _, code = api.post("/devices/" .. phone .. "/action/sendGlobalPushNotifications", { args = { text, "false" } })
        if tostring(code):match("^2") then sent = sent + 1 end
    end
    if sent == 0 and #self.users > 0 then pcall(fibaro.alert, "push", self.users, text) end
end
