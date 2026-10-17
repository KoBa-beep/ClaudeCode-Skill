# Pitfalls (re-read before delivering)

## Structure and versions

1. **`version` not incremented** -> new components never show up.
2. **Version bumped, components still missing** `[observed, twice]`: the Brain stores the new `driverVersion` but does not add the new components to an already installed device. meta then logs `Error: COMPONENTNAME_NOT_FOUND <name>` at each update of that component. Check the Brain (`debugging.md`); if missing, try one more bump, then delete and re-add the device (recipes and shortcuts to redo).
3. **Renaming or removing a visible component** requires deleting and re-adding the device. The shortcut picker may show two components with the same text after a rename (old and new).
4. **Component name with a space or symbol** (label, switch, slider, image, sensor) -> `"sensor": null` in the Brain and "Fail to load interface" on the remote at sync once the component is a shortcut, while the app and the Brain API keep working. Immediate fix: remove the shortcut in the web UI; lasting fix: rename (new component, reinstall).
5. **Unstable `dynamicid`** (DHCP IP) -> the device "changes" when the IP changes.
6. **Container name different from template name** (historical drivers) -> complete silence, no log.
7. **Stale DataStore** after a structure change: remove the device, delete `<driver>-DataStore.json`, restart meta.
8. **Invalid JSON** (trailing comma, comment, unescaped quote) -> driver ignored or meta crash.
9. **Wrong type for the widgets**: `LIGHT` has no channel pad; `AVRECEIVER` is visible only after *Show* in *Recipes*; directories only through shortcuts.

## Values and expressions

10. **Booleans**: `true`/`false` unquoted. `$Result` is **always a string**: `DYNAMIK $Result` or compare to `"true"`.
11. **`$Result == "undefined"`** (or `"Command failed:..."`) on failure: guard `JSON.parse`.
12. **Quotes in `DYNAMIK`**: string literals as `\"...\"`, and escape again inside nested JSON strings (`{\"verb\":\"get\",...}`).
13. **Variable name prefix of another**, or `$Var` glued to letters (`$Baseup`).
14. **`$` in a value**: substitution loops (a title containing `$NowPlaying` -> infinite loop) and `String.replace` interprets `$&`, `$'`. Replace `$` by `＄`.
15. **Button vs action feeder result**: scalar `ok` vs `["ok"]`; a test written for one fires wrongly on the other.
16. **Slider scale** is 0-100 on the NEEO side.
17. **`$ListIndex`** is shifted by header rows.
18. **Unbounded `evaldo` loops** -> infinite CPU load.

## Labels and images (meta v1.2.0 crashes)

19. **`""` written into a label variable stops meta** (a label going from a text back to empty): `Meta Error: Your command MQTT seems incorrect`, then meta restarts. The remote shows the empty label (pushed before the crash), which hides the problem. Write `" "`.
20. **`"`, `\` or a newline in label text** -> invalid JSON in the label's MQTT mirror -> unhandled rejection -> meta stops (a live TV title like `The "Experts"` is enough). Sanitize in the driver and at the source.
21. **Image through `.../image/<name>/set`** -> the Brain receives a `Buffer` object. Feed images from a listener. Never an empty image URL.
22. **Images**: reachable HTTP URLs, square JPEG 480x480 (large) / 100x100 (small).
23. **`listen` only reacts to changes**: write the variable at least once; labels are bound only at `__INITIALISE`.

## Listeners and sessions

24. **Listeners started from `POWER ON` only**: after a meta restart the Brain does not resend `POWER ON`; labels stay frozen. Logs show no `button pressed`, no `Listener will listen to command`, no per-instance MQTT client. Use the `ListenerOn` guard.
25. **Repeated starts of an `mqtt` listener** (`__INITIALISE` again, or `__CLEANUP` + restart on each recipe change) -> each message processed N times (`Value to EvalWrite` repeated N times in the same second). Never `__CLEANUP` an `mqtt` listener.
26. **Instance rebuilt by the Brain** -> new controller, fresh variables, guard reset, one more handler on unpatched meta, and on old meta a second MQTT client with the same id (`session taken over` loop in the broker log).
27. **Polling below 3 s**: no benefit on the remote, more load.
28. **Bursty state sources**: never clear on a timer, never write each raw message to a label; merge upstream with an asymmetric debounce.
29. **Producer republishing unchanged state periodically** -> meta re-runs every `evalwrite` each time. Publish on change (retained) plus once on broker reconnection.
30. **Battery**: the remote is only solicited on value changes; avoid useless writes to bound variables.

## Companion services and flows

31. **Duplicated flows**: an old Node-RED tab left in place, two `mqtt in` nodes on the same command topic (each command runs twice), two broker config nodes with the same client id (mutual kick-out). When replacing a flow: delete the old tab **and** its config nodes, deploy, import, deploy.
32. **Hand-inserted wiring cannot be verified**: deliver complete flows with a visible status (counters) and, when useful, a self-test (a test event looped through a separate, non-retained topic).
33. **Node-RED `exec` node**: `msg.kill` without `pid` only kills when exactly one process runs; a redeploy can start a second copy (`address already in use`). Provide a clean HTTP stop route and make an extra copy exit by itself.
34. **Node-RED `http request` errors** go to `catch`, not to the output: without a wired `catch`, an `http in` route never answers.
35. **Partial network reads** (`resp.content.read(n)` in aiohttp may return less than the body): read by chunks with a size limit; write files atomically (temp file + rename).
36. **Cached connection parameters**: a device may change a dynamic port (Apple TV Companion does). On connection failure, forget the cached configuration and rescan immediately.
37. **Clearing the display before the command is sent**: if the command fails, the screen shows nothing while the content keeps playing. Clear only after success.

## Security

38. `DYNAMIK` and `cli` run code on the meta host; never expose meta outside the LAN, never run it as root/admin, never hard-code secrets in a shared driver (read them from a local secrets file or environment of the companion service).
