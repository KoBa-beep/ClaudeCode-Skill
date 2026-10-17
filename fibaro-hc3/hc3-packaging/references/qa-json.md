# qa.json — manifest read by build_fqa.py

```json
{
  "name": "QA - BOILER",
  "type": "com.fibaro.deviceController",
  "interfaces": [],
  "files": ["main.lua", "helpers.lua"],
  "variables": [
    { "name": "relayId", "value": "" },
    { "name": "interval", "value": "60" },
    { "name": "apiToken", "value": "" }
  ],
  "ui": [
    [ { "type": "label", "id": "labelStatus", "text": "Status" } ],
    [ { "type": "button", "id": "btnOn", "text": "On", "onReleased": "onOnClicked" },
      { "type": "button", "id": "btnOff", "text": "Off", "onReleased": "onOffClicked" } ],
    [ { "type": "slider", "id": "sliderTarget", "text": "Target", "min": 5, "max": 30, "step": 1, "onChanged": "onTargetChanged" } ],
    [ { "type": "select", "id": "selectMode", "text": "Mode", "onToggled": "onModeChosen" } ]
  ],
  "icons": [
    { "label": "Boiler", "template": "com.fibaro.deviceController", "applyToQA": true,
      "states": { "0": "boiler-idle" } },
    { "label": "Boiler zones", "template": "com.fibaro.binarySwitch", "applyToChildren": true,
      "states": { "0": "zone-off", "100": "zone-on" } },
    { "label": "Boiler — alarm (dynamic icon)", "template": "com.fibaro.deviceController",
      "hint": "put this id in the iconAlarm variable", "states": { "0": "boiler-alarm" } }
  ]
}
```

| Key | Meaning |
|---|---|
| `name` | device name at import |
| `type` | exact device type (`com.fibaro.binarySwitch`…) |
| `interfaces` | extra interfaces (`battery`, `energy`, `power`…) — optional |
| `files` | Lua files; the **first** is `main` |
| `variables` | defaults; **secrets empty** (the build refuses a value on secret-looking names) |
| `ui` | list of **rows**; each row is a list of 1–5 elements. Types: `label`, `button` (`onReleased`), `slider` (`onChanged`, `min`, `max`, `step`), `select` (`onToggled`, options filled at run time with `updateView(id, "options", …)`). Element `id` = name used by `updateView` |
| `icons` | icon sets to upload: `template` = exact type of the devices that will use it; `states` = `{ "<value>": "<png name>" }` — binary types `0` (idle) and `100` (active), multilevel types `0`,`10`…`100`, deviceController a single `0`; `applyToQA` / `applyToChildren` to apply automatically; `hint` printed otherwise |

Switch elements (firmware ≥ 5.150) are not generated: add them in the HC3 editor, or verify their `.fqa` format on a
QA exported from the box before adding support.
