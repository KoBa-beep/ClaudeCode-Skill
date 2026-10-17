# Directories (browsable lists)

Directories are lists with pagination, tiles, sub-lists and actions. They feed the "Shortcuts" slide (absent for `ACCESSORY`) and are reached through shortcuts.

## Structure

```
directories -> <DirectoryName> -> { label, feeders -> <FeederName> -> { label, commandset -> [ command, command... ] } }
```

- The **first feeder** is the entry point.
- A **list feeder** holds commands that produce rows (`item*` fields).
- An **action feeder** (named `ACTION_...` by convention) holds a command **without** `item*`; it runs when a row's `itemaction` names it.
- A static `"command": "."` without `queryresult` produces **one row** (header, tile, menu entry). A command whose result is an **array** produces one row per element, with `$Result` = the element.
- Fixed rows: `"command": [{"name":"A"},{"name":"B"}]` `[observed]` or a JSON string `"[$Shortcuts$Collection]"`.

## Row fields

| Field | Role |
|---|---|
| `itemname` | Title (often `DYNAMIK JSON.parse(\"$Result\").field`) |
| `itemlabel` | Subtitle |
| `itemimage` | Thumbnail URL (jpg/png). Variables **and** the row's `$Result` are substituted: `"DYNAMIK \"$IconBase\" + JSON.parse(\"$Result\").icon"`. Must be reachable from the Brain/app (never `127.0.0.1`) |
| `itemtype` | `listitem` (default), `tile` (big image, often first row), `button`, `info` `[observed]` |
| `itemaction` | Action feeder to run on click; `""` or `"."` = nothing |
| `itemUI` | After click: `"reload"`, `"close"`, `"goBack"`, `"goToRoot"`, `true` (non-clickable header with `itemtype:"button"`), `false`/`""`; can be `DYNAMIK` `[observed]` |
| `evalwrite` | Variables written on click (remember the chosen row) |
| `evaldo` | Buttons pressed on click |
| `evalnext` | Next feeder(s) (navigation) |
| `itembrowse` | Obsolete, do not use |

On click: `evalwrite` -> `evaldo` -> `evalnext` / `itemaction`. `[code v1.2.0]` Action feeder commands also accept `queryresult`, `evalwrite`, `evaldo` (so a fallback on failure); their `$Result` is a non-unwrapped array (`["ok"]`). Variables written by the clicked row are available to the action.

Hide a row: make `command` return `undefined` (`DYNAMIK $Cond ? "." : undefined`). Header rows shift `$ListIndex`.

## Example: list then action

```json
"directories": {
  "Programs": {
    "label": "Applications",
    "feeders": {
      "Programs": {
        "label": "Applications",
        "commandset": [
          {
            "type": "http-get",
            "command": "http://$DeviceIP:6095/controller?action=getinstalledapp&count=999",
            "queryresult": "$.data.AppInfo[*]",
            "itemname": "DYNAMIK JSON.parse(\"$Result\").AppName",
            "itemimage": "DYNAMIK JSON.parse(\"$Result\").IconURL",
            "itemaction": "ACTION_Launch",
            "evalwrite": [ { "variable": "PackageName", "value": "DYNAMIK JSON.parse(\"$Result\").PackageName" } ]
          }
        ]
      },
      "ACTION_Launch": {
        "label": "",
        "commandset": [
          { "type": "http-get", "command": "http://$DeviceIP:6095/controller?action=startapp&packagename=$PackageName" }
        ]
      }
    }
  }
}
```

Remember the `ListenerOn` guard on action commands when the driver has listeners: `"evaldo": [{ "test": "DYNAMIK !$ListenerOn", "then": "__LISTEN" }]`.

## Multi-level navigation

Each level stores the choice in a variable (`RoomKey`, `DeviceKey`) and chains with `evalnext`; the last level has `itemaction: "ACTION_..."`. Level n+1 uses level n's variable in its URL (`.../rooms/$RoomKey/devices`). Deep trees need duplicated feeders `Browse0...BrowseN` with `BrowseNUri` variables: generate such JSON with a script rather than by hand.

## Virtual keyboard

A feeder listing characters (`["0",...,"F"]`); each row does `evalwrite Code = "$Code$Result"` then `evalnext` to the **same** feeder with `itemUI: "reload"`; add "Delete" and "Shift" rows.
