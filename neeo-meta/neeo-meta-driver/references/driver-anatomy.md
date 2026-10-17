# Anatomy of a driver file

## Top-level keys

| Key | Role |
|---|---|
| `name` | Device name in the NEEO app (also the controller name in MQTT topics) |
| `manufacturer` | Brand shown / search keyword |
| `type` | NEEO device type (below): decides which widgets exist |
| `version` | Integer. **Increment** whenever a visible component is added |
| `compatible-meta` | `[observed]` minimum meta version, e.g. `"1.0.4"` |
| `variables`, `persistedvariables` | Variables (below) |
| `discover`, `register`, `template` | Discovery, code/IP entry, instance model (`discovery.md`) |
| `labels`, `images`, `switches`, `sliders`, `buttons`, `directories`, `listeners` | Components and logic. In v2 drivers they live **inside `template`** |

**NEEO version rules (inherited from the SDK)**: the Brain only adds new components; it never updates or deletes old ones. A component's **name** is its identity: renaming = new component. To rename/remove: delete the device in the NEEO app and add it again (and delete the DataStore if the structure changed). Hidden buttons (`__...`) are not components: no version bump needed for them.

## NEEO device types

`ACCESSORY`, `AUDIO`, `AVRECEIVER`, `DVB` (satellite/terrestrial receiver), `DVD`, `GAMECONSOLE`, `HDMISWITCH`, `LIGHT`, `MEDIAPLAYER`, `MUSICPLAYER`, `PROJECTOR`, `TUNER`, `TV`, `VOD` (streaming boxes), `SOUNDBAR`.

- `AVRECEIVER` is the most permissive type (accepts most components) but is hidden in rooms until *Show* in *Recipes*. A warning about missing `INPUT ...` buttons is harmless.
- The recipe view is generated from the type and the buttons present. Type-specific widgets (numeric pad, channel zapping) need the right type.
- Favorites view: only `TV`, `DVB`, `TUNER`, and it requires all ten `DIGIT 0`...`DIGIT 9` buttons. The SDK's `registerFavoriteHandlers` (whole favorite in one call) is **not exposed by meta** `[code v1.2.0]`.

## Recognized button names

| Capability / widget | Exact names | Types |
|---|---|---|
| Power | `POWER ON`, `POWER OFF` | all |
| Volume | `VOLUME UP`, `VOLUME DOWN`, optional `MUTE TOGGLE` | all |
| Numeric pad / favorites | `DIGIT 0` ... `DIGIT 9`, optional `INFO`, `GUIDE` | pad: `TV`, `DVB`; favorites: `TV`, `DVB`, `TUNER` |
| D-pad | `CURSOR ENTER`, `CURSOR UP`, `CURSOR DOWN`, `CURSOR LEFT`, `CURSOR RIGHT` | `TV`, `DVB`, `GAMECONSOLE`, `MEDIAPLAYER`, `VOD`, `DVD`, `PROJECTOR` |
| Color keys | `FUNCTION RED`, `FUNCTION GREEN`, `FUNCTION YELLOW`, `FUNCTION BLUE` | `TV`, `DVB`, `GAMECONSOLE`, `MEDIAPLAYER`, `PROJECTOR` |
| Menu / back | `MENU`, `BACK`, `MENU HOME`, `MENU DISC` | as d-pad |
| Zapping | `CHANNEL UP`, `CHANNEL DOWN` | `TV`, `DVB` |
| Tuner | `PRESET UP`/`PRESET DOWN` or `TUNING UP`/`TUNING DOWN` | `TUNER` |
| Transport | `PLAY`, `PAUSE`, `STOP` or `PLAY PAUSE TOGGLE` + `STOP` | as d-pad |
| Search / track | `REVERSE`, `FORWARD`, `PREVIOUS`, `NEXT`, `SKIP SECONDS BACKWARD`, `SKIP SECONDS FORWARD` | as d-pad |
| Recording | `MY RECORDINGS`, `RECORD`, `LIVE` | `TV`, `DVB` |
| Language | `SUBTITLE`, `LANGUAGE` | - |
| Disc | `OPEN/CLOSE`, `EJECT` | `DVD` |
| Inputs | `INPUT <NAME>` (`INPUT HDMI 1`...) | `TV`, `PROJECTOR`, `AVRECEIVER`, `SOUNDBAR`, `AUDIO`; `HDMISWITCH`: `INPUT HDMI*` |
| Apps | `AMAZON`, `CRACKLE`, `HULU`, `HULU PLUS`, `INPUT SPOTIFY`, `NETFLIX`, `GOOGLE PLAY`, `VIMEO`, `VUDU`, `YOU TUBE` | `TV`, `DVB`, `VOD`, `MEDIAPLAYER`, `PROJECTOR` |

The official list is incomplete. Any other name still works but only through a **shortcut**. Prefix `__` = hidden button, callable from logic. `[SDK 0.53.8]` names and labels are URL-encoded in the device description (`Disney+` -> `Disney%2B`); that is normal, but keep button *names* without `+` or accents and put the pretty text in `label`.

## Variables

```json
"variables":          { "MyStatus": " ", "Power": false, "Level": 0, "List": "[]" },
"persistedvariables": { "ClientKey": "", "MyShortcuts": "" }
```

- Native JSON types: booleans unquoted, numbers, strings. Arrays/objects are stored as **JSON strings** (`"[]"`).
- `persistedvariables` are written to `<driver>-DataStore.json` only when the special button `__PERSIST` runs.
- Instance variables can be initialised from discovery: `"DeviceIP": "DYNAMIK_INST_START DYNAMIK JSON.parse(\"$Result\").ip DYNAMIK_INST_END"`, or copied from the container level: `"BridgeIp": "$BridgeIp"`.
- A variable bound to a label must never be set back to `""` (meta v1.2.0 stops): write `" "`. `[code v1.2.0]` an initial `""` is never pushed (the label helper starts at `''` and only pushes changes), but initialising with `" "` keeps the rule simple.

### `$Name` substitution `[code v1.2.0, variablesVault.readVariables]`

Every string (`command`, `value`, `itemname`, `test`...) gets its `$Variables` replaced before use. Plain text replacement, **no escaping**, token by token, in a loop until nothing changes. Consequences:

- a value containing its own token (a title containing `$NowPlaying`) -> **infinite loop**;
- `"$Var"` inside `DYNAMIK` breaks as soon as the value contains a double quote;
- `$Result` *is* escaped (`\` and `"`, newlines removed) by `assignTo` before a `DYNAMIK` is evaluated, so `JSON.parse("$Result")` is safe, while re-reading another variable inside `DYNAMIK` is not;
- `$Var` followed by letters is a different variable: `$NavBase` + `up` -> `$NavBaseup`. Write URLs in full or separate with a non-alphanumeric character;
- never name a variable with a prefix of another (`$Level` / `$Level2`).

System variables:

| Variable | Content |
|---|---|
| `$Result` | Command result filtered by `queryresult`. **Always a string** |
| `$RegistrationCode` | Text typed by the user in the registration box |
| `$NeeoBrainIP` | Brain IP |
| `$MetaIP` | IPv4 of the meta host (`eth0`, else `en0`, else `wlan0`) |
| `$LocalDevices` | mDNS scan results (list of objects) |
| `$LocalByMacDevices` | `arp -a` results `{name, ip, mac}` |
| `$ListIndex` | Index of the clicked list row (header rows shift it) |

## `DYNAMIK` (evaluated JavaScript)

A value starting with `DYNAMIK ` is evaluated as JavaScript after substitution.

```json
"value": "DYNAMIK ($Result == 0) ? \"Receiver On\" : \"Command Failed\"",
"test":  "DYNAMIK $Result"
```

- String literals: `\"...\"`. Compare a text variable: `\"$Var\" == \"abc\"`. Use as number/boolean/object: no quotes (`$Power`, `$Level`).
- Read JSON: `JSON.parse(\"$Result\").field` (case-sensitive), guarded: `if (\"$Result\" != \"undefined\") {...}`.
- Several statements allowed; the **last expression is the value**: `DYNAMIK let a = ...; let b = ...; b;`.
- Returning `undefined` hides a list row or skips the write.
- Store JSON in a variable with `JSON.stringify(obj)`. Re-injecting stored JSON into another `DYNAMIK` needs extra escaping (`.replace(/\"/g,'\\\\\"')`, or double `JSON.stringify` then strip the outer quotes).
- `DYNAMIK_INST_START ... DYNAMIK_INST_END`: evaluated **once at instance creation** (discovery), with `$Result` = the discovered element. Literal text is accepted: `DYNAMIK_INST_START MyDevice01 DYNAMIK_INST_END`.
- In a `webSocket` message, `<__n__>` = newline.
- **Sanitize displayed text** (proven model for a label `evalwrite`):

```
DYNAMIK let s = JSON.parse("$Result"); const c = x => String(x || "").replace(/[\u0000-\u001f]/g, " ").replace(/\\/g, "/").replace(/"/g, "'").replace(/\$/g, "＄"); let t = c(s.title), a = c(s.artist); t ? (a ? t + " - " + a : t) : " ";
```

(In the JSON file the inner quotes and backslashes must be escaped once more.)

## UI components

| Component | Syntax | Notes |
|---|---|---|
| Label | `"labels": { "NowPlaying": { "label": "Now playing", "listen": "Var", "actionlisten": "TmpVar" } }` | Shows `Var`. `actionlisten`: shows another variable for a few seconds (e.g. volume bar) then returns to `listen` |
| Image | `"images": { "Cover": { "label": "", "size": "large", "listen": "UrlVar" } }` | `small` ~100x100, `large` ~480x480. The variable holds an **HTTP URL** that the **Brain** downloads (avoid HTTPS with private certificates). Serve square JPEG/PNG, ~60 KB max. Never an empty URL |
| Switch | `"switches": { "Name": { "label": "", "listen": "Var", "evaldo": [...] } }` | Boolean. Only `evaldo`. New value arrives in `$Result` as a **string**: `"test": "DYNAMIK $Result"` |
| Slider | `"sliders": { "VOLUME": { "label": "", "unit": "%", "listen": "Var", "evaldo": [...] } }` | NEEO scale **0-100**: convert to/from the device scale |
| Button | `"buttons": { "NAME": { "label": "", "type": "...", "command": ..., "queryresult": ..., "evalwrite": [...], "evaldo": [...] } }` | `static` with `"command": ""` is a pure logic relay |
| Directory | see `directories.md` | Browsable list, reachable through shortcuts |

Label behaviour `[code v1.2.0, labelHelper.js]`:

- `writeVariable` notifies observers on every write; `labelHelper.update` sends to the Brain **only if the value differs** from the last one displayed.
- Labels, sliders, switches, images and sensors are bound to their variables (`addObserver`) **only at `__INITIALISE`**: before that, nothing updates.
- `listen` reacts to changes: a variable never written shows nothing; write it at least once.
- The remote is updated through the slow NEEO API (battery saving): the phone app is instant, the remote takes a few seconds. Avoid useless writes to bound variables.
