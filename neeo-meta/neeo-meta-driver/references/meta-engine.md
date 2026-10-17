# The meta engine: architecture, operation, hosting, known bugs

## Context

- **NEEO**: universal remote + **Brain** (local hub, HTTP API on port `3000`). The company was bought by Control4 and the cloud is gone; the Brain keeps working locally. SDK drivers run on another machine (Node.js) and register with the Brain.
- **NEEO SDK** (`NEEOInc/neeo-sdk`, last version 0.53.8): Node.js library defining the vocabulary (device types, recognized button names, widgets, discovery, state updates). meta is built on it.
- **meta** (`jac459/meta`, branch `Release`): a *driver runtime*. It reads JSON device files and generates one SDK driver per file. One code base runs all drivers.
- **meta-core** (`jac459/meta-core`, file `metaCore.json`): a JSON driver that shows up as a device on the remote and administers meta (driver library, restart, update, browse rooms/devices/macros, network scan).
- **metadriver** (`jac459/metadriver`): meta v1. Its tutorials remain the best syntax documentation; v2 added `discover`/`template`, `register`, `initcommandset`, the variable vault.

```
NEEO app / remote <-> Brain (API :3000) <-> meta (Node.js, port 4016) <-> devices (HTTP, WS, MQTT, CLI...)
                                               |
                          active/*.json   MQTT broker (required)   Node-RED :1880 (optional)
```

## Source files (useful when checking behaviour in code)

| File | Role |
|---|---|
| `meta.js` | NEEO API glue: builds components, discovery with the Brain, per-instance MQTT client (`enableMQTT`) |
| `metaController.js` | Interprets the driver JSON (`evalwrite`, `evaldo`, `evalnext`, special buttons) |
| `ProcessingManager.js` | Protocols (one processor per command type) and extraction (JSONPath, XPath, regex) |
| `variablesVault.js` | Variables (observer pattern), substitution (`readVariables`), persistence |
| `labelHelper.js`, `sliderHelper.js`, `switchHelper.js`, `imageHelper.js`, `sensorHelper.js`, `directoryHelper.js` | Component builders |
| `settings.js` | Global settings: `mqtt: 'localhost'`, `mqtt_topic: 'meta/'`, `mqttClientId: 'meta'`, `driverPrefix: '.meta2 '`, `defaultPort: '4016'`, `activeLibrary: './active'` |
| `config.js` | Brain IP/port learnt at first start (delete it if the Brain moved, then restart) |

The name shown in the NEEO app is `<manufacturer> <driverPrefix><name>` (e.g. "JAC459 .meta2 metaCore"). Search "meta" or the driver name in *Add device*.

## Folders and lifecycle

- `library/`: downloaded, inactive drivers. `active/`: every `*.json` here is loaded at start.
- `active/<driver>-DataStore.json`: persisted variables. Deleting it resets the driver (remove the device from the Brain first).
- Deploy a hand-written driver: copy it to `active/` -> restart meta (about 1 min of unavailability) -> NEEO app *Add device* -> search the name. `AVRECEIVER` devices are hidden in rooms by default: in *Recipes*, *Show* the device and add shortcuts (directories are only reachable through shortcuts).
- pm2: `pm2 list`, `pm2 restart meta`, `pm2 logs meta`, `pm2 save`. Official installer (Pi/Linux): `bash <(wget -qO- https://raw.githubusercontent.com/jac459/meta/Release/installMeta.sh)`; update: `update.sh` from the meta folder.
- Verbose run (stop pm2 first): `node meta '{"LogSeverity":"INFO","Components":["meta","metaController"]}'`; force the Brain: `'{"Brain":"<ip>","LogSeverity":"INFO"}'`. `[code v1.2.0]` `LogSeverity` accepts `VERBOSE`, `INFO`, `WARNING`, `QUIET` (not `ERROR`, despite `settings.js`). `Components`: `meta`, `metaController`, `variablesVault`, `processingManager`, `sensorHelper`, `sliderHeper` (sic), `switchHelper`, `imageHelper`, `directoryHelper`. `VERBOSE` is very slow.
- meta-core: install `metaCore.json` in `active/`, add it as a device, add the **Settings** shortcut. *Devices and Actions* triggers any macro without a shortcut (great for testing). It assumes meta, Node-RED and the broker run under pm2.
- Variant fork: `Ton-O/NEEO-Meta-Plus` (PythonManager, ADB...). Drivers relying on it are not guaranteed on `jac459/meta`.

## MQTT exposed by meta `[code v1.2.0]`

- meta **requires** an MQTT broker **without authentication** (`settings.mqtt` is appended to `mqtt://`, so `host` or `host:port`).
- Each press of a **visible** button publishes `meta/<driver>/<deviceId>/button/<BUTTON>` = `PRESSED`.
- Control from outside: publish on `meta/<driver>/<deviceId>/<button|slider|switch|image|label>/<component>/set` (exactly 6 segments). `<driver>` is the driver `name` without the prefix. A label `set` pushes straight to the Brain without any listener: perfect to test the meta -> Brain -> remote chain.
- Do **not** drive an image through `.../image/<name>/set`: the MQTT `Buffer` is stored as is and the Brain receives `{"type":"Buffer",...}`. Feed images from a listener (string URL).
- Every label update is mirrored to `meta/<driver>/<id>/label/<name>`, built by string concatenation (hence the sanitizing rules).
- Per-instance client: when the Brain asks for an instance, `enableMQTT` connects a client named `meta/<driver> - <deviceId>`. Seeing it in the broker log proves the Brain activated the instance.

## Hosting in Docker / on a NAS `[code v1.2.0, tested in a sandbox]`

- **Host networking is mandatory**: the Brain calls meta back on `http://<ip>:4016`, discovery uses mDNS/ARP.
- The SDK announces the **first non-local IPv4** of the machine, with no notion of subnet: on a NAS it can be `docker0` or a virtual bridge. Patch `neeo-sdk/dist/lib/device/validation/ipHelper.js` (or force the IP through an env var in your image). `$MetaIP` takes `eth0`, then `en0`, then `wlan0`: same issue.
- meta **exits** (code 1) if the Brain is unreachable at start: supervise it (`pm2-runtime`, `restart: unless-stopped`).
- metaCore drives `pm2`: inside a container use `pm2-runtime` so "Restart meta" works; "Restart Node-RED/MQTT" only works if they share the container.
- System dependencies: `arp` (net-tools) for the scan; `curl`, `wget`, `sed`, `xargs` for metaCore `cli` commands; **`git`** (an indirect npm dependency is fetched from GitHub; without git: `npm error ... spawn git ENOENT`).
- Containers on host networking share loopback: meta reaches a local service at `http://127.0.0.1:<port>` (prefer `127.0.0.1` to `localhost`, which may resolve to `::1`).
- Node-RED 4+/5 needs Node >= 18/22; meta v1.2.0 runs fine on Node 20. Keep them in separate containers if versions differ. Protect the Node-RED editor with credentials (it executes code); flow HTTP routes stay public on the LAN.

## Known meta v1.2.0 bugs (MQTT) and their effect `[code v1.2.0 + observed]`

| Where | Defect | Symptom |
|---|---|---|
| `mqttProcessor.startListen` | Each start of an `mqtt` listener adds a `message` handler on the shared client and never removes the previous one (`stopListen` only unsubscribes). A rebuilt instance (new controller) adds another | `Value to EvalWrite` lines repeated N times for one message |
| `enableMQTT` (`meta.js`) | A rebuilt instance opens a second client with the same id without closing the first: mutual kick-out loop | Broker log: `New client connected ... as meta/<driver> - <id>` then `session taken over`, every second |
| `mqttProcessor.process` | An empty message (`""`, e.g. a label emptied) goes to the error branch, which references an undefined `err`: unhandled rejection, **meta stops** | `Meta Error: Your command MQTT seems incorrect` then meta restarts |
| `labelHelper.update` | Label text with `"`, `\` or a newline produces invalid JSON in the MQTT mirror; the rejection is not caught and meta has no `unhandledRejection` handler | meta stops on a title such as `The "Experts"` |

Driver-side mitigations always apply (guard, `" "` instead of `""`, sanitizing). An engine patch can also fix them: key the handler on the shared MQTT client by `listenerName|topic|deviceId` (a restart or rebuild replaces it instead of adding one), close the previous client in `enableMQTT`, accept `""` in `process` and resolve instead of referencing `err`. Such a patch is overwritten by any meta update; check file sizes against the analysed version before replacing files, keep backups.

Not fixed by any patch: the Brain decides to rebuild instances (at meta restart, often twice, and after a `version` change). Each rebuild creates a new controller with initial variables; the `ListenerOn` guard restarts listening at the first press.
