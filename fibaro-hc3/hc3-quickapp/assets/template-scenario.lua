-- Scenario for template-main.lua — run:  lua scripts/hc3sim.lua assets/template-main.lua assets/template-scenario.lua
local temp, online = 21.5, true
sim.http("sensor.local/status", function()
    if not online then return nil, "Operation timed out" end
    return 200, json.encode({ temperature = temp })
end)
sim.devices[301] = { name = "Phone A", type = "iOS_device" }
sim.quiet.VIEW = true

sim.step("Start")
local qa = sim.start({ name = "QA - TEMPLATE", type = "com.fibaro.temperatureSensor",
    variables = { url = "http://sensor.local/status", interval = "60", alertAbove = "30", notifyPhones = "301" } })
sim.run(5)
sim.expect(qa.properties.value == 21.5, "value = 21.5 after the first poll")

sim.step("Temperature rises above the threshold → one notification only")
temp = 31
sim.run(130)
sim.expect(#sim.pushes == 1, "exactly one push sent (got " .. #sim.pushes .. ")")

sim.step("Device offline → retries with back-off, warning after 5 failures")
online = false
sim.run(400)
sim.expect(qa.failures >= 5, "failures counted (" .. qa.failures .. ")")
sim.expect(#sim.pushes == 2, "one 'no answer' push")

sim.step("Back online")
online, temp = true, 22
sim.run(120)
sim.expect(qa.failures == 0 and qa.properties.value == 22, "recovered, value = 22")
sim.expect(sim.pendingTimers() == 1, "exactly one loop timer pending (no duplicates)")
sim.summary()
