# Reference drivers, SDK mapping, sources

## Community drivers worth reading

The community library is described by `drivers.manifest` in `jac459/meta-core` (`driverLocation` = raw GitHub URLs, so a reference driver can be fetched and read).

| Driver (author) | What it teaches |
|---|---|
| metaCore (JAC459) | `cli`, `mDNS`, `http-get`, button chains, advanced directories, persisted variables, conditional rows, `itemUI` |
| Volumio (JAC459) | `socketIO`, listeners, sliders, images, labels with `actionlisten`, 5-level navigation, letter search, persistent favorites |
| Yamaha AVR (JAC459) | `mDNS` with a verification loop, HTTP listener, volume slider, input/DSP directories |
| WebOS LG TV (JAC459) | `webSocket`, `wol`, key pairing, reconnection, favorites/recents |
| Shield / Android TV (Tom & Jac) | `android` type, code pairing, virtual keyboard, app launcher |
| Broadlink TV / AC (JAC459) | IR over MQTT + Node-RED, learning mode, `http-rest` discovery |
| Hue Bulbs / Groups (JAC459) | hub, button registration, `http-rest` GET/POST/PUT, `isHub`, colour picker |
| Denon + Marantz AVR (stonie2oo4) | IP `register`, XML, multiple zones and listeners |
| Shelly (vistalba, MarkusM) | IP `register` with credentials, authenticated `http-rest`, switch, 10 s polling |
| Sony Bravia (Nelus) | `http-rest` POST with PSK header, SOAP IRCC |
| Plex (JAC459, `meta-plex`) | image component fed by the server's transcoder URL, `timeline/poll` polling, `AUDIO` type |
| Kodi, Roon, Naim, enigma2, Samsung, Yamaha MusicCast | further examples (some rely on Node-RED flows shipped with them) |

## NEEO SDK <-> meta mapping (to read SDK docs)

| SDK | meta JSON |
|---|---|
| `buildDevice(name)` / `setManufacturer` / `setType` | `name`, `manufacturer`, `type` |
| `setDriverVersion(n)` | `version` |
| `addButton({name,label})`, button groups | `buttons` (each name individually) |
| `addSlider`, `addSwitch`, `addTextLabel`, `addImageUrl`, `addSensor` | `sliders`, `switches`, `labels`, `images`, sensors `[to verify]` |
| `addDirectory` (getter / action handlers) | `directories` (list / action feeders) |
| `enableDiscovery` (+ dynamic device builder) | `discover` + `template` |
| registration (security code / credentials) | `register` |
| subscription / state notifications | `listeners` + `listen` |
| initialise / subscription handlers | `__INITIALISE` / `__CLEANUP` |
| component `X` + sensor | the SDK names the sensor `X_SENSOR` |

`[SDK 0.53.8]` `addImageUrl({name, label, size}, getter)`, capability `imageurl`. SDK documentation: `https://neeoinc.github.io/neeo-sdk/`.

## Sources

- NEEO SDK: `https://github.com/NEEOInc/neeo-sdk` (README: button names, capabilities, dynamic device builder; `widgetDocumentation.md`: widgets per type).
- meta: `https://github.com/jac459/meta` (branch `Release`; `installMeta.sh`, `update.sh`, `settings.js`).
- meta-core: `https://github.com/jac459/meta-core` (`metaCore.json`, `drivers.manifest`).
- metadriver (v1 tutorials): `https://github.com/jac459/metadriver` (`TUTORIALS.md`, `YAMAHARECEIVER-EXPLAINED.md`, `DISCOVERYPROCESS.md`).
- Drivers: `jac459/meta-volumio`, `jac459/meta-yamahaAVR`, `jac459/meta-webosLGTV`, `jac459/meta-shield`, `jac459/meta-broadlink`, `jac459/meta-hue`, `jac459/meta-denonAVR`, `jac459/meta-sonybravia`, `vistalba/meta-shelly-driver`.
- Fork: `Ton-O/NEEO-Meta-Plus`.
- Community: Telegram group linked from the meta README (the Discord is reported obsolete).

## Known gaps

Not verified: sensors (`sensorHelper.js`), exact `jsontcp` / `repl` formats, exact shape of `$LocalDevices` on every version, state topics published by meta beyond button `PRESSED` and `.../set` inputs. Third-party device APIs change with firmware: always confront a driver with the real device.
