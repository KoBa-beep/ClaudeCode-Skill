# Testing and debugging

## Test cycle

1. Validate: `python3 -m json.tool driver.json`, `python3 scripts/check_driver.py driver.json`, and `node scripts/simulate_guard.js driver.json` when there are listeners.
2. Copy to `active/`, restart meta, open the logs (`pm2 logs meta`, container logs, or a manual run with `LogSeverity` `INFO`).
3. Add the device in the NEEO app. Not found: container/template name, `dynamicid`, JSON validity, discovery result (mDNS shape?).
4. Test **one button at a time**; metaCore *Devices and Actions* triggers macros without shortcuts.
5. For an API: fetch the real response with `curl`, build the `queryresult` against it, then the `DYNAMIK`.
6. Debug trick: write intermediate results into a variable shown by a label (`MyStatus`).
7. Inconsistent behaviour: remove the device, delete the DataStore, bump `version`, restart, add again.
8. When a fix "does not work", ask for 20-30 timestamped lines of **raw and published** messages around the event instead of adjusting blindly.

When the user reports a bug, ask for: meta version (`package.json`), the driver and its `version`, the last ~30 meta log lines, the raw API response or message concerned, and when relevant the broker log and the Brain JSON.

## meta log signatures

| Line | Meaning |
|---|---|
| `creating the driver: default - <name> - <version> - <manufacturer>` | Driver loaded at start |
| `Driver running, you can search it on the neeo app.` | Start finished |
| `creating the driver: <instanceId> - <name> - <version>` | One construction of an instance by the Brain: count and timestamp them |
| `[CONTROLLER] - <NAME> - button pressed` (WARNING) | A key reached meta |
| `Listener will listen to command: ...` | A listener start (ideally one per session) |
| `Value to EvalWrite: ...` repeated N times in the same second | N stacked handlers (repeated listener starts or rebuilds) |
| `Meta Error: Your command MQTT seems incorrect` | A label received `""`; meta is about to stop: look for a restart right after |
| `Error: COMPONENTNAME_NOT_FOUND <name>` | The Brain does not know this component (version bump not applied, or name mismatch) |
| `The commandtype to process is not defined` | Wrong `type` (case!) |
| `Discovery updated` | Harmless |

## Broker (Mosquitto) log signatures

- `New client connected ... as meta/<driver> - <instanceId>`: the Brain activated the instance (absent after a meta restart = the instance is not usable until the Brain asks again or a key is pressed).
- That line followed by `disconnected: session taken over` every second: two controllers for the same instance (instance built twice on unpatched meta).
- Mosquitto timestamps are Unix seconds: convert before comparing with other logs.
- Reconnections of a Node-RED client id at each deploy are normal.

## Checking what the Brain really has

`GET http://<BrainIP>:3000/v1/projects/home` returns rooms, devices and recipes. For a device, check:

- `driverVersion`: the version the Brain recorded;
- the list of components: are the new ones present (pitfall 2)?
- each `textlabel` / `switch` / `slider`: `"sensor": null` while a `<NAME>_SENSOR` exists = broken link (name with a space or symbol, pitfall 4);
- recipes: which devices and shortcuts they really contain (steps disappear when a device is removed and re-added).

## Isolating a link

- Test a label without any listener: publish `TEST` on `meta/<driver>/<instanceId>/label/<labelName>/set`. If it shows on the remote, meta -> Brain -> remote works and the problem is the listener or `__INITIALISE`; otherwise the instance is not active.
- Test the companion service alone over HTTP (health route, one key), then the driver, then the remote.
- For state chains, log each hop with timestamps: key pressed (meta mirror `meta/<driver>/<id>/button/<NAME>`), raw device event, published state, label pushed (meta mirror `.../label/<name>`). The last hop (Brain -> remote) takes a few seconds on the remote, almost nothing in the phone app.

## Sandbox testing before delivering

- **Driver logic**: simulate meta's `evalwrite` / `evaldo` in Node (`scripts/simulate_guard.js` is a ready example for the listener guard); evaluate `DYNAMIK` with meta's substitution rules on hostile inputs (`logic-and-commands.md`).
- **SDK acceptance**: build the device with the real SDK (`npm i neeo-sdk@0.53.8`, `buildDevice(...).setType(...).addButton(...).build(...)`) to check names, labels and types.
- **Engine behaviour**: run the real meta (`git clone --branch Release`, `npm install`) with the driver; without a Brain it loads the files then exits, which still validates parsing. For MQTT behaviour, run the real functions against a real broker (`aedes` + `mqtt@4.3.8`, the version used by meta).
- **Node-RED flows**: execute a function node's real code with `new Function('msg','node','context','env', ..., code)` and fake `node.send`, `context`, sockets and status messages; or deploy into a real Node-RED (`POST /flows` with `Node-RED-Deployment-Type: full`, `POST /inject/<id>`).
- **Companion services**: fake device (fake pyatv objects, fake HTTP API), simulated clock for debounce logic, replay of the user's real logs to identify the installed version and predict a new one.
- A test that reproduces the original failure first, then passes with the fix, is the best evidence. Always tell the user what was only tested in the sandbox.
- Tooling traps: background processes may not survive between tool calls (start them with `setsid` in a script); `pkill -f <pattern>` kills your own shell if the pattern appears in the command line (use `pkill -x name` or `[p]attern`).
