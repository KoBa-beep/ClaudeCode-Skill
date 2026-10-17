# Logic, command types and result extraction

## `evalwrite`: write variables

```json
"evalwrite": [
  { "variable": "MyStatus", "value": "DYNAMIK (\"$Result\"==\"success\") ? \"OK\" : \"Failed\"" },
  { "variable": "Power", "value": "$Result" }
]
```

Executed **in order**. `value`: literal (`true`, `0`, `"text"`), `$Result`, or `DYNAMIK`. Available on buttons, list rows, listeners, `initcommandset` commands.

## `evaldo`: press other buttons

```json
"evaldo": [
  { "test": "DYNAMIK \"$Result\"==\"success\"", "then": "__OK", "or": "__FALLBACK" },
  { "test": true, "then": "__OTHER" }
]
```

- `test`: boolean or `DYNAMIK` string. `then` if true, `or` if false (optional, `""` = nothing).
- **Every** entry is evaluated. Targets are usually hidden `__` buttons.
- Enables chains (`__SETUP0` -> `__SETUP1`...) and loops (a button calling itself while a counter is below a limit). Always give loops a stop condition.
- Old tutorials sometimes write `do`: use `then`.
- Order on a button: command -> `queryresult` -> `evalwrite` -> `evaldo`.

## `evalnext`: list navigation

On list rows, `then` names the next **feeder**. All tests are evaluated:

```json
"evalnext": [
  { "test": "DYNAMIK JSON.parse(\"$Result\").navigation == \"Artists\"", "then": "Artists", "or": "" },
  { "test": true, "then": "Devices", "or": "Rooms" }
]
```

## Special buttons `[code v1.2.0]`

| Button | Effect |
|---|---|
| `POWER ON` / `POWER OFF` | NEEO power keys. The Brain sends `POWER OFF` at **every recipe change**, and does **not** resend `POWER ON` after a meta restart if the recipe is already on |
| `__INITIALISE` | Binds labels, sliders, switches, images and sensors to their variables, opens connections, starts the device's listeners. **No protection against repeated calls** (each call restarts listeners; an `mqtt` listener then stacks a handler). Call it once per session through the `ListenerOn` guard |
| `__CLEANUP` | Stops this device's listeners and connections. **Never on an `mqtt` listener** (the handler is not removed, every stop/start stacks one) |
| `__PERSIST` | Writes `persistedvariables` to `<driver>-DataStore.json` |
| `__WRAPUP` | Not special in the engine (no-op unless defined) |
| `__` prefix | Hidden button. Visible buttons also publish an MQTT `PRESSED` message |

## Command types

`type` values are **case-sensitive and compared exactly** `[code v1.2.0]`; an unknown type logs `The commandtype to process is not defined`.

| `type` | `command` format | Notes |
|---|---|---|
| `static` | literal (string, boolean, JSON array, `"."`, `""`), or `"$MyList"` | No network: `$Result` = the value. Logic relay, constant, fixed list source |
| `http-get` | URL (basic auth: `http://user:pass@host:port/...`) | Fast and simple. `[code v1.2.0]` uses `got`: a refused connection is retried (2 times, ~3 s total) before `$Result` = `"undefined"`; any error -> `"undefined"` |
| `http-rest` | JSON **string** (or object returned by `DYNAMIK`): `{"verb":"get\|post\|put","call":"URL","message":{...},"headers":{...}}` | JSON or **XML** APIs (XML becomes JSON whose nodes are **arrays**: `.Power[0].value[0]`). `message` may be a string (e.g. a SOAP envelope with a `soapaction` header) |
| `http-post`, `http-get-soap` | legacy (v1) | Prefer `http-rest` |
| `webSocket` | `{"connection":"ws(s)://host:port","message":<object or string>}` | Send result contains `readystate` (`1` = connected) -> reconnection pattern. Listener: `{"connection":"...","message":"message"}` |
| `socketIO` | `{"call":"eventName","message":...}` | Host given by `"socketIO": "<host>"` in the template. Listener: `command` = event name |
| `mqtt` | button: JSON string `{"topic":"...","message":"..."}` (string published as is, object serialised; optional `"options":"{\"retain\":true}"`); listener: the **topic as a literal** (no `$` substitution in listener topics) | Local broker without auth. Empty/falsy message refused (and crashes v1.2.0, see `meta-engine.md`). In a listener `$Result` = payload text; use `queryresult: ""` then `JSON.parse("$Result")`. A retained message arrives at subscription |
| `cli` | shell command | Runs **on the meta host**; `$Result` = stdout. Powerful and dangerous |
| `wol` | MAC address | Wake-on-LAN |
| `mDNS` | `""` + `queryresult` | Queries meta's network scan results (`discovery.md`) |
| `android` | objects: `{"remoteKeyCode":23,"remoteDirection":3}`, `{"appLink":"..."}`, `{"register":true,"message":"$Code"}` | Android TV / Shield remote protocol, code pairing + persisted certificate. Android `KeyEvent` codes: 19/20/21/22 d-pad, 23 center, 4 back, 3 home, 82 menu, 24/25 volume, 164 mute, 85 play/pause, 89/90 rewind/forward, 26 power |
| `jsontcp`, `repl` | JSON over TCP / persistent interactive shell | Exist in the engine, format not documented `[to verify in ProcessingManager.js]`. For raw TCP protocols prefer a companion service |

**Controlling NEEO itself** (trigger a macro of another device, IR through another driver): Brain API, e.g. `http://<BrainIP>:3000/v1/projects/home/rooms/<roomKey>/devices/<deviceKey>/macros/<macroKey>/trigger` (list keys with `.../rooms/`, `.../rooms/<k>/devices`, `.../devices/<k>/macros`). metaCore's *Devices and Actions* is a ready-made explorer.

## `queryresult`: extract the useful part

| Form | Example | Effect |
|---|---|---|
| Empty | `""` | Raw response |
| JSONPath | `"$.msg"`, `"$.data.AppInfo[*]"`, `"$..success.username"` | Value or **array**. An array in a list = one row per element |
| Everything | `"$."`, `"$.*"` | Whole / all children |
| Filter chain | `["$.*~", "$..name"]` | Applied in cascade; `~` = property name |
| Advanced filters | `"$[?(@.mac&&@.ip&&@.short)][?(@property === 'name' && @.match(/webos/i))]^"` | `jsonpath-plus` ^5: `?()`, `@property`, `.match(/re/i)`, parent `^` |
| Regex | `["/(.*)./gm"]` | `[observed]` regex extraction (e.g. `cli` output) |
| XML | `"$.Device_Info"` | After XML -> JSON conversion |

Precautions:

- Whether `$Result` is an object or a one-element array depends on the expression. Safe idiom: `let r = JSON.parse(\"$Result\"); if (Array.isArray(r)) { r = r[0]; };`.
- On failure `$Result` is `"undefined"` or `"Command failed:..."`: guard before `JSON.parse`.
- **Button vs action feeder** `[code v1.2.0]`: a button unwraps a one-element array (`$Result` = `ok`); a directory action feeder does not (`["ok"]`). A failure test valid for both: `DYNAMIK "$Result" != "ok" && "$Result" != '["ok"]'` (true = failure).
- Build expressions against the real response (fetch it with `curl`, try it in a JSONPath evaluator), then write the `DYNAMIK`.

## Testing `DYNAMIK` before delivery

Reproduce meta's substitution in Node and evaluate the expression on hostile inputs (double quotes, backslashes, accents, `$`, `undefined`, empty string, arrays):

```js
const vars = { Result: 'some "quoted" title', Level: 42 };
// meta escapes $Result (\ and ", newlines removed) before evaluating; other variables are inserted raw
const esc = v => String(v).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/[\r\n]/g, '');
const sub = s => s.replace(/\$([A-Za-z0-9]+)/g, (m, k) => (k in vars ? (k === 'Result' ? esc(vars[k]) : String(vars[k])) : m));
const evalDyn = expr => eval(sub(expr.replace(/^DYNAMIK /, '')));
// expr is the value as read by JSON.parse from the driver file, e.g. 'DYNAMIK JSON.parse("$Result").title'
```
