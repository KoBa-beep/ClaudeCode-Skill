# HC3 REST API — what QuickApps actually use

From a QA: `api.get("/devices/12")` (no `/api` prefix) → `data, code`. From a computer:
`curl -u <user> http://<hc3>/api/devices/12` (Basic auth; prompt for the password, never write it in a file
or a command line that ends up in shell history). The full list of documented endpoints is in
`rest-api-index.md` (grep it); for parameters and response schemas of one endpoint run
`python3 scripts/swagger_index.py <swagger-folder> --detail "GET /devices/{deviceID}"` when the user has the files.

## Devices
| Call | Use |
|---|---|
| `GET /devices` | all devices; filters `?roomID=`, `?type=`, `?interface=`, `?parentId=`, `?property=[name,value]` (e.g. `?property=[lastLoggedUser,2]`) |
| `GET /devices/{id}` | `id, name, type, baseType, roomID, parentId, enabled, visible, interfaces, properties{…}, actions{…}` |
| `POST /devices/{id}/action/{action}` body `{"args": [...]}` | run an action / a QA method (**202**) |
| `PUT /devices/{id}` body `{"properties": {...}}` or `{"name": ..., "roomID": ...}` | change properties / name / room. **Not on the QA's own id from inside the QA** (restarts it) |
| `POST /devices/filter` | complex filters (see swagger) |
| `GET /devices?type=iOS_device` | phones / tablets registered for push (Android included) |

## Rooms, sections, users, settings
`GET /rooms` → `{id, name, sectionID, …}` · `GET /sections` → `{id, name}` (sections = floors / zones) ·
`GET /users` (do not export e-mails) · `GET /settings/info` (`softVersion`, `hcName`, `serialNumber` — do not publish
the serial) · `GET /settings/location` (`latitude`, `longitude`, `city`, `timezone`) · `GET /weather`
(`Temperature`, `Humidity`, `Wind`, `WeatherCondition`).

## Variables, scenes, profiles
`GET/PUT /globalVariables/{name}` body `{"value": "…"}` (values are strings) · `GET /scenes`,
`POST /scenes/{id}/execute` · `GET /profiles`, `POST /profiles/activeProfile/{id}`.

## Health and logs
| Call | Notes |
|---|---|
| `GET /diagnostics` | `memory {used, free, cache, buffers}`, `storage.internal = [{name, used}]` (used in %), `cpuLoad` |
| `GET /debugMessages?types=error&from=<epoch>&to=<epoch>&filter=<tags>&offset=-1` | `{nextLast, messages = [{id, timestamp, type, tag, message}]}`; the console keeps a limited number of messages |
| `GET /events/history?objectType=device&objectId=<id>&numberOfRecords=100` | device history (value changes, `dead`, battery, wake-ups). Best tool to diagnose a flapping / unreachable module |
| `GET/POST /zwaveReconfigurationTasks` | list / start a module reconfiguration (same as "Reconfigure" in the UI) |
| `GET /apps/com.fibaro.zwave/diagnostics/transmissions` | undocumented Z-Wave stats; often empty for battery nodes **[V]** |

## Notifications
`POST /notificationCenter` `{type="GenericDeviceNotification", priority="info|warning|alert", wasRead=false,
canBeDeleted=true, data={deviceId, title, text}}` → notification centre (bell), not a push. Push: see
`notifications.md`. Undocumented: `POST /mobile/push` (`mobileDevices`, `title`, `message`, `category`) **[V]**.

## Icons
`GET /icons` · `POST /icons` (multipart: `type=device`, `deviceTemplate=<exact device type>`, `icon0`…`icon100`,
`fileExtension=png|svg`) → **201** `{id, iconSetName "UserNNNN"}` · `DELETE /icons?id=&type=&name=&fileExtension=`.
The swagger describes `GET /icons` as `{device=[{deviceType, iconSetName, id}], room=[…], scene=[…]}` but boxes have
also returned a list of `{source, iconSet, type, files}`: accept both. Details: skill `hc3-icons`.

## QuickApps (undocumented in swagger, used by community tools — stable on 5.x)
| Call | Use |
|---|---|
| `POST /quickApp/` body = `.fqa` JSON | install a QA → new device (new id) |
| `GET /quickApp/export/{id}` | export as `.fqa` |
| `GET /quickApp/{id}/files` | list Lua files `[{name, isMain, type, isOpen}]` |
| `GET /quickApp/{id}/files/{name}` | read one file (with `content`) |
| `PUT /quickApp/{id}/files/{name}` body `{name, isMain, type="lua", isOpen=false, content}` | **replace code**: QA restarts, keeps id, variables, icon, scene references |
| `POST /quickApp/{id}/files` | add a file · `DELETE /quickApp/{id}/files/{name}` remove one |

## Backups
`POST /service/backups` `{action="create", params={type="local"|"remote", description=…}}`; downloading a backup is
not documented.

## Habits that avoid wrong guesses
- Read a real object before writing code that parses it (`api.get("/devices/<id>")` printed with `json.encode`).
- Types are strings like `com.fibaro.FGR224` (Z-Wave model-specific) — compare with `type:find(...)` or check
  `baseType` / `interfaces` / `properties.deviceRole` rather than one exact type.
- Codes: 200 OK, 201 created, 202 accepted (actions), 401 auth, 404 unknown id, 409 conflict.
