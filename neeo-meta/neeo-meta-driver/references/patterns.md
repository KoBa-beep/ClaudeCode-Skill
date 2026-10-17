# Proven patterns

Fragments to insert in `template.buttons`, `template.directories`, etc. Each one comes from a real driver or a real installation.

**P1 - Volume: slider + buttons + scale conversion.** `VOLUME UP/DOWN` change the variable bound to the slider **then** call `__VOLUMESET`; the slider also calls `__VOLUMESET`; `__VOLUMESET` converts 0-100 to the device scale (e.g. `Math.round(161 * Number($Volume) / 100)`). A listener resyncs the variable when the volume changes on the device. See `assets/skeleton-static.json`. When a companion service owns the device connection, send `VOL=UP` / `VOL=DOWN` / `VOL=<n>` and let it enforce a **volume limit**.

**P2 - Reliable power on: WOL then connect** (WebSocket TVs).

```json
"POWER ON":  { "type": "wol", "command": "$DeviceMac",
               "evalwrite": [ { "variable": "MyStatus", "value": "Connecting..." } ],
               "evaldo":    [ { "test": true, "then": "__RESTART" } ] },
"__RESTART": { "type": "static", "command": ".",
               "evaldo": [ { "test": true, "then": "__SETUP" } ] }
```

**P3 - Power on without the risk of toggling off** (IR power is a toggle): query the API first; if it answers, the device is already on; otherwise fire the IR macro through the Brain API.

```json
"POWER ON": { "type": "http-get", "command": "http://$DeviceIP:6095/controller?action=status",
              "queryresult": "$.msg",
              "evaldo": [ { "test": "DYNAMIK \"$Result\"==\"success\"", "then": "", "or": "__POWERONIR" } ] },
"__POWERONIR": { "type": "http-get", "command": "http://$NeeoBrainIP:3000/v1/projects/home/rooms/<room>/devices/<dev>/macros/<macro>/trigger" }
```

**P4 - Temporary status bar**: label with `"listen":"Playing", "actionlisten":"DisplayVolume"`; the listener writes `DisplayVolume = DYNAMIK '||'.repeat(vol) + '--'.repeat(Math.round((100-vol)/3))`; the bar shows for a few seconds on volume change, then the title returns.

**P5 - Playback progress without polling the device**: a `static` listener with `pooltime:"3000"` presses `__REFRESHPROGRESS`, which computes `Progress` from `Date.now()`, a reference time and `Duration`; slider `PROGRESS` -> `__PROGRESSSET` (seek).

**P6 - Persistent favorites/shortcuts**: `persistedvariables {"MyShortcuts":""}`; a menu row writes `MyShortcuts` then goes through a feeder whose command is `{"type":"static","command":".","evaldo":[{"test":true,"then":"__PERSIST"}]}`. Re-inject into a list with `"command": "[$Shortcuts$Collection]"`. Escape the quotes of stored JSON.

**P7 - Conditional row**: `"command": "DYNAMIK $Cond ? \".\" : undefined"`.

**P8 - Sequential chain**: `__SETUP0` -> `__SETUP1` -> ... each with `evaldo: [{"test":true,"then":"__SETUPn+1"}]` (e.g. download, read, transform with `cli`, then feed a list).

**P9 - Iteration loop**: a button increments `Iterator` and calls itself while `Iterator < length`, then `__PERSIST` on exit. Always bounded.

**P10 - Virtual keyboard**: see `directories.md`.

**P11 - IR through an MQTT IR bridge** (Broadlink + Node-RED): per key `X`, three buttons: `X` (routes by a `Learning` variable), `__X LEARN` (publishes `{"action":"learn"}` and remembers the key), `__X PLAY` (publishes `{"action":"send","data":<IR code>}`). Learnt codes come back through an `mqtt` listener and are stored in a persisted variable; a switch toggles learning; a save button calls `__PERSIST`. Very repetitive: **generate the JSON with a script**.

**P12 - Trigger another NEEO recipe or macro**: HTTP call to the Brain API (`.../macros/<key>/trigger`) from a button or a list row.

**P13 - Fast local service + MQTT fallback.** meta calls a local companion service with `http-get` (`http://127.0.0.1:<port>/cmd/<key>`); the service keeps one persistent connection to the device (latency ~10 ms instead of ~1 s for a process per key). The service always answers **HTTP 200** with `{"status":"ok"|"error"|"unknown",...}` so that `queryresult: "$.status"` is simple. If the answer is not `ok`, a hidden `__FALLBACK` button replays the command on a slower path (MQTT -> Node-RED):

```json
"CURSOR UP": {
  "type": "http-get", "command": "http://127.0.0.1:8090/cmd/up", "queryresult": "$.status",
  "evalwrite": [ { "variable": "FallbackCmd", "value": "up" } ],
  "evaldo": [
    { "test": "DYNAMIK \"$Result\" != \"ok\" && \"$Result\" != '[\"ok\"]'", "then": "__FALLBACK" },
    { "test": "DYNAMIK !$ListenerOn", "then": "__LISTEN" }
  ]
},
"__FALLBACK": { "type": "mqtt", "command": "{\"topic\":\"mydevice/cmd\",\"message\":\"$FallbackCmd\"}" }
```

Drawbacks: ~3 s delay when the service is down (`got` retries), possible double execution after a timeout (harmless for idempotent commands such as power or app launch). The port is an example: pick an unusual one and make the service print an explicit message when it is taken.

**P14 - `ListenerOn` guard**: see `listeners-and-state.md`. Mandatory with any listener.

**P15 - State through a retained MQTT message.** The companion service publishes the full state as one JSON message, **retained**, **only when it changes**, plus once after each reconnection to the broker. The driver has one `mqtt` listener with `queryresult: ""` and one `evalwrite` per displayed value, each sanitized and never `""`:

```json
"listeners": {
  "DeviceState": {
    "type": "mqtt", "command": "mydevice/state", "queryresult": "",
    "evalwrite": [
      { "variable": "StatusText", "value": "DYNAMIK let s = {}; try { s = JSON.parse(\"$Result\"); } catch (e) {} let t = String(s.status || \"\").replace(/[\\u0000-\\u001f]/g, \" \").replace(/\\\\/g, \"/\").replace(/\"/g, \"'\").replace(/\\$/g, \"\\uFF04\"); t ? t : \" \";" }
    ]
  }
}
```

**P16 - App buttons and app directory** (streaming boxes): one button per favourite app (`http-get` to the service's `/launch/<id>`, fallback as P13) and an "Applications" directory fed by a variable or a service route returning `[{name, icon, id}]` (`queryresult "$.*"`, `itemname`, `itemimage`, `itemaction: "ACTION_Launch"`). Recognized names (`NETFLIX`, `AMAZON`, `YOU TUBE`...) land in the apps widget; other names are free and used through shortcuts. Icons: serve square JPEGs from the service over HTTP; generated placeholders (initials, no brand logos) when nothing is cached.

**P17 - Artwork of what is playing (image component).** Model: the Plex driver by jac459: `"images": {"AlbumCover": {"label": "", "size": "large", "listen": "DisplayedImage"}}`, the variable written only when something plays, with a URL where the **server resizes** the image. Rules:

- the Brain downloads the image itself: plain **HTTP** URL on the LAN; square JPEG 480x480 (`large`) or 100x100 (`small`), ~60 KB max; add a cache-busting query (`?v=<time>`) when the file name stays the same;
- produce the square image in the companion service (Pillow: `contain` with dark bars, `cover`, or `blur` background); never send a raw, non-square or unreadable image;
- never an empty URL: fall back to an app icon or a neutral image;
- an image component cannot be removed by a later version: test a new component type on a throw-away device or have a rollback plan;
- if the main driver is already installed, an auxiliary device (type `AVRECEIVER`) holding the image and added as a shortcut in the recipe avoids reinstalling the main device.

**P18 - Generate repetitive drivers.** IR sets, input lists, listening modes and per-key guard entries are better generated by a small script from a table than typed by hand; re-run `check_driver.py` on the output.
