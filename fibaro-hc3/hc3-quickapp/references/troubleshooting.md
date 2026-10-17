# Troubleshooting QuickApps on the HC3

## The QA does nothing / stops after a while
- Open the QA console (device → "Edit & preview" or the code editor's console). No line at all → `onInit` crashed:
  look for the first `[ERROR]`.
- An error inside a timer callback may be **silent** and kills the loop: wrap the body in `pcall`, re-arm the timer
  outside the `pcall`.
- Two loops running (log lines doubled): `onInit` ran again after a save while an old timer was pending, or a button
  started a second loop. Keep the timer reference and clear it before re-arming.
- `attempt to index a nil value (field 'properties')`: `api.get` returned nil (wrong id, 404) — check codes.
- `attempt to call a nil value (method 'xxx')`: a property in `self` shadows a method (e.g. `self.info = {}` hides
  `QuickApp:info`). Never reuse method names for data fields.
- `getVariable` returned `""`: the variable does not exist or has a different case. Use defaults.

## The QA restarts by itself
- `api.put("/devices/<own id>", …)` from inside the QA → restart. Use `self:updateProperty`.
- Saving variables in the UI restarts it (normal). `self:setVariable` does **not**.
- Out-of-memory loops (tables growing forever: history, logs) → cap list lengths.

## UI not updating
- Element IDs differ from the code (`button_ID_0_1` auto names). Rename in the editor or import a `.fqa`.
- Switch / select do not change their own visual state: `updateView` after handling.
- Select blanking after `updateView(..., "selectedItem", ...)` (observed 5.2xx): show the choice in a label.
- Mobile app caches the view: close / reopen the device.

## Notifications not received
See `notifications.md` § Diagnose. Typical: user IDs vs phone IDs confusion; phone logged in with another account;
the condition never transitioned.

## A Z-Wave module "dead", flapping, or a door sensor blinking
1. Read the device history to see what really happened:
   `GET /api/events/history?objectType=device&objectId=<id>&numberOfRecords=100` (as console snippet:
   `scripts/device-history.js`). Look at `dead` transitions, battery levels, wake-ups (`wakeUpDeadDevice`), value
   changes at odd hours.
2. Battery device: replace the battery with the exact type/voltage (many sensors use 3.6 V lithium, e.g. ER14250 —
   a 3 V CR battery will not work), wake it up (short press on the tamper / B button according to the manual),
   then "Reconfigure" the module.
3. Continuous LED blinking on some Fibaro sensors means "not in network / cannot reach the controller" or a failed
   wake-up: wake it close to the HC3, check the mesh (a mains-powered module nearby acts as a repeater).
4. Mains module: power-cycle, then `fibaro.wakeUpDeadDevice(id)`; if it persists, check range / repeaters.
5. Repeated problems on an old model → suggest the current generation of the module.
A health-monitoring QA (dead modules grouped by physical node, batteries, `/diagnostics`, console errors of the
last 24 h, daily summary) catches these before they matter: see `patterns.md` §8.

## HTTP problems
- `Operation canceled` / timeout → device asleep or wrong IP; increase `timeout`, retry with back-off.
- HTTPS to a device with a self-signed certificate → `checkCertificate = false`.
- 401 with a camera / intercom → Digest auth (implement the challenge), not Basic.
- Cloud API 429 → you poll too often: respect the provider's rate limits, cache tokens.

## Before blaming the box
Reproduce in `scripts/hc3sim.lua` with the same sequence of values (including restarts, midnight, a device going
offline), fix, then re-test on the HC3.
