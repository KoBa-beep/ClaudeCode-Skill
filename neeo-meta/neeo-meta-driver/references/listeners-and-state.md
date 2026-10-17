# Listeners and device state

A listener updates variables (hence labels, sliders, switches, images) when the **device** changes, not only when a key is pressed.

```json
"listeners": {
  "DeviceStatus": {
    "type": "http-get",
    "command": "http://$DeviceIP/api/status",
    "pooltime": "3000",
    "poolduration": "",
    "queryresult": "$.",
    "isHub": false,
    "evalwrite": [ { "variable": "Volume", "value": "DYNAMIK Math.round(Number(JSON.parse(\"$Result\").volume) * 100 / 161)" } ]
  },
  "DeviceEvents": {
    "type": "socketIO", "command": "pushState", "queryresult": "",
    "evalwrite": [ { "variable": "Title", "value": "DYNAMIK JSON.parse(\"$Result\").title" } ]
  }
}
```

- **Events over polling**: `socketIO`, `webSocket`, `mqtt`. Polling: `http-get`, `http-rest`, `static` (a `static` listener with `pooltime` is a timer, e.g. a progress bar).
- `pooltime` in ms (default 1000; use >= 3000). The remote is only updated on value change through a slow API; faster polling only costs CPU and battery.
- `isHub` (also written `ishub`): `true` = one listener shared by all instances (hub: one request for N lamps, each instance filters its own data); `false` = one per instance.
- meta logs `Listener will listen to command: <topic or command>` (INFO) at each start. No such line = the listener is not running.

## The `ListenerOn` guard (mandatory pattern)

Why: `__INITIALISE` has no protection against repeated calls, and an `mqtt` listener stacks one more `message` handler at each start (`__CLEANUP` only unsubscribes). The Brain sends `POWER OFF` at every recipe change and does not resend `POWER ON` after a meta restart. So:

- starting listeners from `POWER ON` alone leaves labels frozen after a meta restart;
- `POWER OFF` -> `__CLEANUP`, then `POWER ON` -> `__INITIALISE` makes the same state message processed N times (observed: 19 times).

Pattern:

```json
"variables": { "ListenerOn": false },
"buttons": {
  "__LISTEN": {
    "type": "static", "command": ".",
    "evalwrite": [ { "variable": "ListenerOn", "value": true } ],
    "evaldo": [ { "test": true, "then": "__INITIALISE" } ]
  },
  "CURSOR UP": {
    "type": "http-get", "command": "http://$DeviceIP/key/up",
    "evaldo": [ { "test": "DYNAMIK !$ListenerOn", "then": "__LISTEN" } ]
  },
  "POWER OFF": {
    "type": "http-get", "command": "http://$DeviceIP/power/off"
  }
}
```

- Add `{ "test": "DYNAMIK !$ListenerOn", "then": "__LISTEN" }` to the `evaldo` of **every** visible button, slider and switch, and to directory action commands, so that the first gesture of the session starts listening, once.
- `POWER OFF` never calls `__CLEANUP` and never resets `ListenerOn` when the listener is `mqtt`.
- For non-MQTT listeners (`webSocket`, `socketIO`, polling) stopping on `POWER OFF` is possible, but the same guard logic keeps things simple and safe.
- Residual limit: when the Brain rebuilds the instance (meta restart, version change), meta creates a new controller with fresh variables and a fresh guard: one more handler per rebuild on unpatched meta v1.2.0 (see `meta-engine.md`).
- Check with `node scripts/simulate_guard.js driver.json`.

## MQTT listener specifics `[code v1.2.0]`

- `command` = topic, literal (no variable substitution). `$Result` = payload as text. `queryresult: ""`.
- A **retained** message is delivered on subscription: publish state retained so the driver gets the current state as soon as it listens.
- A listener sees every message, even identical ones: publish only on change on the producer side (each message re-runs all `evalwrite`).

## Bursty state sources

Some sources (e.g. Apple TV through pyatv-based tools) emit bursts: ~25 messages in 2 s where fields empty and refill several times, the last message fully empty, then nothing until the next burst. Writing each message to labels empties them permanently.

- Never deduce "nothing is playing" from an empty field or from the absence of events.
- Merge **upstream** of meta (Node-RED function node or the bridge): an empty field does not replace the last known value; a different app resets the content fields; publish a content change after a short quiet time (~250 ms, max 1 s) and an "empty" state only after a longer one (~1.5 s, max 5 s) to absorb transient idle states (asymmetric debounce).
- Measure the real source before choosing delays (log raw vs published messages with timestamps); a fix based on a wrong assumption about emission frequency fails.

## Instance rebuilds

Each construction of an instance (Brain asks for the device again: meta restart, often twice; after a `version` change) creates a new controller with initial variables, unbound labels and the listener not started until a key is pressed. Count constructions in meta logs (`creating the driver: <instanceId> - <name> - <version>`) and in the broker log (`New client connected ... as meta/<driver> - <id>`).
