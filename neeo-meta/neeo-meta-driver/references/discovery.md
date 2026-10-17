# `discover`, `register`, `template`: creating device instances

## Principle

- `template` is the real driver (buttons, lists...). It can be instantiated **N times** (once per discovered element).
- `discover.command` returns an **array**; each element becomes an instance. Inside the template, `$Result` = the discovered element (JSON string), used in `dynamicname`, `dynamicid` and variables initialised with `DYNAMIK_INST_START ... DYNAMIK_INST_END`.
- The Brain triggers discovery when the user searches for a device. With a target device id, meta builds only the requested instance.
- `dynamicname`: name shown to the user. `dynamicid`: **stable** identifier (change it and the Brain sees another device). Prefer a MAC or hardware id over a DHCP IP.
- Container name and template name: historical docs require them to be identical ("otherwise the driver does not answer and logs nothing"). Recent v2 drivers often omit `name` in the template; if the driver is silent, check this first.
- The container holds only `discover`/`register` (and shared/persisted variables); buttons and logic go in `template`. Container-level variables are copied into the template with `"Var": "$Var"`.
- `register` requires `discover` (not the opposite).

## Pattern 0: static single device (fixed address)

The pattern used by metaCore itself: a static `discover` producing one instance. See `assets/skeleton-static.json`.

```json
"discover": {
  "welcomeheadertext": "My Device",
  "welcomedescription": "powered by meta",
  "command": { "type": "static", "command": ".", "queryresult": "$.*" }
},
"template": {
  "dynamicname": "DYNAMIK_INST_START My Device DYNAMIK_INST_END",
  "dynamicid": "DYNAMIK_INST_START MyDevice01 DYNAMIK_INST_END",
  "variables": { "DeviceIP": "192.168.1.50" }
}
```

Shared drivers should not hard-code the address: prefer pattern B (user-entered IP) or mDNS.

## Pattern A: mDNS network discovery

```json
"discover": {
  "welcomeheadertext": "WebOS TV",
  "welcomedescription": "powered by meta",
  "command": { "type": "mDNS", "command": "", "queryresult": "$[?(@.mac&&@.ip&&@.short)][?(@property === 'name' && @.match(/webos/i))]^" }
},
"template": {
  "dynamicname": "DYNAMIK_INST_START DYNAMIK JSON.parse(\"$Result\").ip + \" - \" + JSON.parse(\"$Result\").name DYNAMIK_INST_END",
  "dynamicid": "DYNAMIK_INST_START DYNAMIK JSON.parse(\"$Result\").name + \".\" + JSON.parse(\"$Result\").mac DYNAMIK_INST_END",
  "variables": {
    "DeviceURI": "DYNAMIK_INST_START DYNAMIK JSON.parse(\"$Result\").ip + \":3001\" DYNAMIK_INST_END",
    "DeviceMac": "DYNAMIK_INST_START DYNAMIK JSON.parse(\"$Result\").mac DYNAMIK_INST_END"
  }
}
```

`[observed]` mDNS result fields: `name`, `short` (service type, e.g. `_googlecast._tcp.local`, `_airplay._tcp.local`), `ip`, `mac`, `port`. Filters seen: Volumio `$.[?(@.short=='_Volumio._tcp.local'&&@.port==3000)]`; NEEO Brain `[?(@.port==3000)][?(@property === "short" && @.match(/_neeo._tcp.local$/i))]^`; Hue `$.[?(@property === "name" && @.match(/_hue/i))]^`. Older docs describe another shape (`fullname`, `type{name,protocol}`, `host`, `addresses`): always check the real shape with metaCore's *Show Result of Network Scan* (`resultsDiscovery.json`). `$LocalByMacDevices` (`arp -a`) finds an IP from a MAC.

## Pattern B: the user types the IP, validated by a call

See `assets/skeleton-register-ip.json` (derived from Denon/Shelly/Yamaha drivers, to be tested on the real device).

- `register.command` static; the typed text arrives as `$RegistrationCode`.
- `discover.initcommandset`: copy `$RegistrationCode` into `DeviceIP`, call the device, append `{ip, name}` to the persisted list `MyDevices` if it answered, set `IsRegistered`, then `__PERSIST`.
- `discover.command`: `{"type":"static","command":"$MyDevices","queryresult":"$.*"}`: one instance per registered device.
- Legacy v1 syntax: `"register": {"registertype":"SECURITY_CODE", "registerheadertext":..., "registerdescription":..., "registrationcommand":{...}}`; registration loops while `IsRegistered` is not `true`.

## Pattern C: hub with several devices (Hue, Shelly, IR bridge)

1. `initcommandset`: find the hub (mDNS) and get rights (Hue: press the bridge button before "next", `POST /api` -> `queryresult "$..success.username"`); store hub IP and user in `persistedvariables`; `__PERSIST`.
2. `discover.command`: list the hub's devices (`queryresult ["$.*~","$..name"]` -> `[id, name]` pairs).
3. `template`: name and id from the pair; instance variable (`LightNumber`); **listener with `isHub: true`** reading all devices in one request, each instance filtering its own (`find(e => e[0] == "$LightNumber")`).

## Interactive pairing

- Android TV / Shield: a directory "Register" simulates a **keyboard** (list of characters) to type the code shown on screen, then `__REGISTER` (`android`, `register:true`), then `__SAVE` (`__PERSIST` + `__INITIALISE`).
- LG webOS: `__REQUESTKEY` (the TV prompts), the `client-key` received by the listener is copied into a persisted variable then persisted.
- Pairing that needs a PIN on stdin or a long-lived session is better done by a companion service with its own small web page.
