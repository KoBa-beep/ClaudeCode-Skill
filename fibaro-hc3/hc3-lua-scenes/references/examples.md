# Worked scene examples (replace the ID_… placeholders)

## a) Doorbell → chime on a speaker QuickApp + push
Declarations:
```lua
{ operator = "any", conditions = {
    { type = "device", id = ID_DOORBELL, property = "value", operator = "==", value = true, isTrigger = true },
} }
```
Actions:
```lua
fibaro.call(ID_SPEAKER_QA, "playSound", "http://<nas>/sounds/chime.mp3", 45)   -- method exposed by the speaker QA
fibaro.alert("push", { ID_USER_1, ID_USER_2 }, "Someone is at the door (" .. os.date("%H:%M") .. ")")
```

## b) Leaving home: heating Away, everything off — by hand or by a global variable
```lua
{ operator = "any", conditions = {
    { type = "global-variable", property = "Presence", operator = "==", value = "Away", isTrigger = true },
} }
```
```lua
fibaro.call(ID_HEATING_QA, "setMode", "Away")
fibaro.call(ID_MEDIA_QA, "pause")
fibaro.debug("Leaving", "House set to away (" .. sourceTrigger.type .. ")")
```

## c) Sunset − 15 min: close the shutters
```lua
{ operator = "all", conditions = {
    { type = "date", property = "sunset", operator = "==", value = -15, isTrigger = true },
} }
```
```lua
for _, id in ipairs({ ID_SHUTTER_1, ID_SHUTTER_2, ID_SHUTTER_3 }) do fibaro.call(id, "close") end
```

## d) Stair light off 5 min after the last motion (option "allow restart" = Yes)
```lua
{ operator = "any", conditions = {
    { type = "device", id = ID_MOTION, property = "value", operator = "==", value = true, isTrigger = true },
} }
```
```lua
fibaro.call(ID_STAIR_DIMMER, "setValue", 60)
fibaro.setTimeout(5 * 60 * 1000, function() fibaro.call(ID_STAIR_DIMMER, "turnOff") end)
```

## e) Remember between runs: one CO alert per day
```lua
local today = os.date("%Y-%m-%d")
if fibaro.getSceneVariable("lastAlert") ~= today then
    fibaro.setSceneVariable("lastAlert", today)
    fibaro.alert("push", { ID_USER_1 }, "Abnormal CO level!")
end
```

## f) One scene, several triggers
```lua
{ operator = "any", conditions = {
    { type = "device", id = ID_BUTTON, property = "centralSceneEvent", operator = "==",
      value = { keyId = 1, keyAttribute = "Pressed2" }, isTrigger = true },
    { type = "date", property = "cron", operator = "match", value = { "0", "23", "*", "*", "*", "*" }, isTrigger = true },
} }
```
```lua
if sourceTrigger.type == "device" then
    fibaro.debug("Night", "double press")
else
    fibaro.debug("Night", "23:00")
end
for _, id in ipairs({ ID_LIGHT_1, ID_LIGHT_2 }) do fibaro.call(id, "turnOff") end
```
