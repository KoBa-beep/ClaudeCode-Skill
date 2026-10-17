# Notifications from a QuickApp

## What exists
| Channel | Call | Target IDs | Notes |
|---|---|---|---|
| Push to a phone (direct) | `api.post("/devices/<phoneId>/action/sendGlobalPushNotifications", {args = {text, "false"}})` → **202** | **mobile device** IDs (`type = "iOS_device"`, Android included) | Most reliable. Equivalent `fibaro.call(phoneId, "sendGlobalPushNotifications", text, "false")` (no return code) |
| Push by user | `fibaro.alert("push", {userIds}, text)` | **user** IDs | Converts users → phones whose `properties.lastLoggedUser` = that user. A phone logged in with another account (e.g. admin) gets **nothing, silently** |
| Block-scene style | `fibaro.alert("simplePush", {ids}, text, false, "", false)` | phone IDs (calls `sendPush` directly) | What block scenes generate (`hub.alert('simplePush', …)`); has failed on some boxes where the direct push works |
| E-mail | `fibaro.alert("email", {userIds}, text)` | user IDs | needs the user's e-mail configured on the HC3 |
| Notification centre (bell in the web UI / app) | `api.post("/notificationCenter", {...})` | — | not a push; priority colours |

There is **no "critical" push** on the HC3 (one that rings in silent mode). For that, use an external service over
HTTPS (e.g. Pushover priority 2 / iOS critical alerts, ntfy, Telegram) with its token in a QA variable.

List phones: `api.get("/devices?type=iOS_device")` → `id`, `name`, `properties.lastLoggedUser`.
Users: `api.get("/users")` (do not export or print e-mails).

## Notification centre
```lua
api.post("/notificationCenter", {
    type = "GenericDeviceNotification",
    priority = "alert",            -- "alert" (red) | "warning" (orange) | "info" (blue)
    wasRead = false, canBeDeleted = true,
    data = { deviceId = self.id, title = self.name, text = text },
})
```
Map severities: unreachable module / fire / relay failure → `alert`; summary with problems → `warning`;
back to normal / all good → `info`. Make it optional (`notifyCenter = 0`).

## Robust helper ("auto" mode)
Accept users and/or phones in one variable, resolve phones, push directly, fall back to `fibaro.alert("push")`:
```lua
-- notifyUsers = "2,5" (user IDs and/or phone IDs, as shown in a block scene's notification action)
function QuickApp:resolvePhones()
    local wanted, list = {}, {}
    for n in self:optionalVariable("notifyUsers"):gmatch("%d+") do wanted[tonumber(n)] = true end
    for _, p in ipairs(api.get("/devices?type=iOS_device") or {}) do
        local user = tonumber((p.properties or {}).lastLoggedUser)
        if wanted[p.id] or (user and wanted[user]) then list[#list + 1] = p.id end
    end
    return list, wanted
end

function QuickApp:notify(text, priority)
    self:warning(text)
    if self:optionalVariable("notifyCenter") ~= "0" then
        api.post("/notificationCenter", { type = "GenericDeviceNotification", priority = priority or "warning",
            wasRead = false, canBeDeleted = true, data = { deviceId = self.id, title = self.name, text = text } })
    end
    local phones, wanted = self:resolvePhones()
    local sent = 0
    for _, id in ipairs(phones) do
        local _, code = api.post("/devices/" .. id .. "/action/sendGlobalPushNotifications", { args = { text, "false" } })
        if tostring(code):match("^2") then sent = sent + 1
        else self:warning("Push refused for phone " .. id .. " (HTTP " .. tostring(code) .. ")") end
    end
    if sent == 0 then
        local users = {}
        for id in pairs(wanted) do users[#users + 1] = id end
        if #users > 0 then pcall(fibaro.alert, "push", users, text)
        else self:warning("No recipient: fill the notifyUsers variable") end
    end
end
```

## Diagnose "I receive nothing"
Add a "Test notifications" button that sends four numbered messages, one per method, and ask the user which ones
arrived:
- **A** `fibaro.alert("simplePush", ids, "A …", false, "", false)`
- **B** `fibaro.alert("push", userIds, "B …")`
- **C** `api.post(".../sendGlobalPushNotifications")` per phone
- **D** `fibaro.call(phoneId, "sendPush", "D …")` **[V]**
Then keep the method that works. Common causes: IDs are users where phones are expected (or the reverse); the phone
is logged in with another HC3 account; the app's notifications are disabled on the phone; the QA sends nothing because
the alert condition was already true at start-up (state machine never saw a transition).

## Writing good messages
- Full sentence: what, where, value, what the QA did, what to do: "🔥 Smoke detected — Living room (ground floor).
  Siren on, shutters opening. Press 'Stop the alarm' in the QA when it is safe."
- Prefix tests with "TEST —".
- One message per event, not per loop: notify on transitions (normal → problem, problem → normal) and repeat only on
  purpose (alarm repeat every N minutes, capped).
