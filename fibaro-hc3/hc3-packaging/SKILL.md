---
name: hc3-packaging
description: Package Fibaro HC3 QuickApps for one-click install and safe updates — build the .fqa file (import in the HC3), a bash/curl script that replaces the code of an installed QuickApp without losing its id and variables, and a script that uploads and applies its icons. Use this skill whenever the user wants to import, export, install, deploy, update, share or back up a QuickApp, mentions a .fqa file, asks how to put new code on the box, or after creating / modifying a QuickApp (deliver the .fqa with the code).
---

# Packaging HC3 QuickApps

Answer in the user's language. The target user often copies code by hand into the HC3 editor; packaging removes
that error-prone step.

## Folder convention
```
<qa-name>/
  main.lua        code (version in the header: "Version 1.2.0")
  qa.json         manifest — see references/qa-json.md
  README.md       type, variables, UI, install, test plan
  icons/*.png     optional, referenced by qa.json "icons"
```

## Build
```
python3 scripts/build_fqa.py <qa-folder> [--out DIR] [--icons DIR]
```
Produces in `<qa-folder>/dist/` (or `--out`):
| File | What the user does |
|---|---|
| `<qa>.fqa` | HC3 web UI: Settings → Devices → **+** → Other device → Quick App → **Upload file**. Creates a **new** device (new id) with type, UI, callbacks, variables. Then fill the empty variables (secrets) and save |
| `<qa>-update.sh` | `bash <qa>-update.sh` on macOS / Linux: asks address, user, password, QA id; checks the device type matches; asks confirmation; replaces the Lua files (`PUT /api/quickApp/<id>/files/<name>`). Id, variables, icon and scene references are kept; the QA restarts |
| `<qa>-icons.sh` | uploads each icon set (`POST /api/icons`) and applies it to the QA (`applyToQA`) or its children (`applyToChildren`); otherwise prints the icon id to choose by hand |

The build refuses to run if: a variable whose name looks secret (password, token, apikey, secret…) has a value; a
UI element calls a method absent from the code; HC2 API calls are found; UI ids are duplicated. Keep it that way:
a `.fqa` is easily shared, secrets must never be inside.

## Security rules for the scripts (keep them if you modify the generator)
- Never hard-code the HC3 address, user or password; prompt each time (an `HC3` environment variable may pre-fill the
  address). Password read with `read -s`, passed to curl via a temporary `-K` config file deleted by `trap`, so it
  does not appear in the process list or shell history.
- Verify the target device type before replacing code, and ask for confirmation.
- Uploading icons twice creates duplicates: say so in the output.

## Windows users
The scripts need bash + curl: use WSL or Git Bash. Alternative without scripts: import the `.fqa`, and for updates
open the QA → Edit → paste `main.lua` → Save (variables are kept).

## Without Python at hand
The `.fqa` format is plain JSON (`references/fqa-format.md`): it can be written directly. Prefer the generator: the UI
part (two layouts + callbacks) is easy to get wrong by hand.

## Other ways in
- Export an installed QA: device → Advanced → Download (or `GET /api/quickApp/export/<id>`).
- Install by API: `POST /api/quickApp/` with the `.fqa` JSON as body (returns the new device).
- Community tools (plua, fibaro-flua, hc3emu) can also upload from VS Code.

## Delivery checklist
- [ ] `.fqa` rebuilt after every code change (stale packages are a classic source of "the fix did not work")
- [ ] Version number bumped in `main.lua` (the update script shows it)
- [ ] README tells: import the `.fqa` → fill secret variables → run the icons script → how to update later
- [ ] Icons listed in `qa.json` with the exact `deviceTemplate` (type) of each device that uses them
