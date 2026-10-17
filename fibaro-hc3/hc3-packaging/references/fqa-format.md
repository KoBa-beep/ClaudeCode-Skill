# .fqa format (QuickApp export / import file)

JSON document:
```json
{
  "name": "QA - EXAMPLE",
  "type": "com.fibaro.binarySwitch",
  "apiVersion": "1.3",
  "initialInterfaces": [],
  "initialProperties": {
    "viewLayout": { "$jason": { "...": "legacy layout, see below" } },
    "uiView": [ { "type": "horizontal", "style": { "weight": "1.0" }, "components": [ ... ] } ],
    "uiCallbacks": [ { "callback": "onRefreshClicked", "eventType": "onReleased", "name": "btnRefresh" } ],
    "quickAppVariables": [ { "name": "interval", "value": "60" } ],
    "typeTemplateInitialized": true
  },
  "files": [ { "name": "main", "isMain": true, "isOpen": true, "type": "lua", "content": "-- code" } ]
}
```

## uiView components (current format)
```json
{ "name": "btnRefresh", "type": "button", "text": "Refresh", "visible": true, "style": { "weight": "0.5" },
  "eventBinding": {
    "onReleased":          [ { "type": "deviceAction", "params": { "actionName": "UIAction", "args": ["onReleased", "btnRefresh"] } } ],
    "onLongPressDown":     [ { "type": "deviceAction", "params": { "actionName": "UIAction", "args": ["onLongPressDown", "btnRefresh"] } } ],
    "onLongPressReleased": [ { "type": "deviceAction", "params": { "actionName": "UIAction", "args": ["onLongPressReleased", "btnRefresh"] } } ]
  } }
```
- Slider: `"min","max","step","value"` as strings; `onChanged` args `["onChanged", "<id>", "$event.value"]`.
- Select: `"options": [], "selectionType": "single", "values": []`; `onToggled` args with `"$event.value"`.
- Label: no binding.
- Row weights: 1 element `1.0`, 2 → `0.5`, 3 → `0.33`, 4 → `0.25`, 5 → `0.2`.

## viewLayout (legacy format, still written for compatibility)
`{"$jason": {"head": {"title": "quickApp_device_0"}, "body": {"header": {"title": "quickApp_device_0",
"style": {"height": "<rows*50>"}}, "sections": {"items": [ <one vertical item per row> ]}}}}` — each row item is
`{"type": "vertical", "style": {"weight": "1.2"}, "components": [ <element or horizontal group>, {"type": "space",
"style": {"weight": "0.5"}} ]}`.

## Behaviour
- Import always creates a new device (new id). Scenes referencing the old id must be updated → prefer the update
  script for new versions.
- `uiCallbacks` maps element + event → method name; without it the buttons do nothing.
- A `.fqa` carries no icon: icons are uploaded separately (`POST /api/icons`).
- Community tools (TQAE, plua, flua) use the same format; `flua unpack x.fqa` extracts the Lua files.
