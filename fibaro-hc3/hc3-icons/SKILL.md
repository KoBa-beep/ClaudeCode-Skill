---
name: hc3-icons
description: Create device icons for the Fibaro Home Center 3 / Yubii Home — realistic illustration of the real device on a transparent background with a small round state badge, one PNG 128×128 (+ SVG) per state, readable in light and dark mode — and upload / apply them on the HC3 (POST /api/icons, icon0…icon100, deviceIcon). Use this skill whenever the user wants icons for a QuickApp, a Z-Wave module, child devices, shutters (11 positions), sensors, or asks why an icon does not change with the state, even if they only say "make it look nicer" or "an image for my device".
---

# HC3 device icons

Answer in the user's language. Generate icons with `scripts/icon_kit.py` (Python, `pip install cairosvg pillow`):
it contains the style helpers (gradients, soft shadow, badge, ~35 badge glyphs), an example device drawing (roof
window with roller shutter, 11 positions) and the preview generator.

## Style (what makes these icons fit the HC3 UI)
- **Realistic drawing of the real device** (shape, colours, materials, viewing angle). Ask the user for a photo of
  the exact model and reproduce it; never trace a photo or copy a manufacturer logo / trademark (also keeps the icons
  shareable). If the user explicitly wants a brand logo for private use, keep that icon out of anything published.
- **Transparent background, one file per state** — no light / dark variants. To stay readable on both themes, give
  dark devices a light edge (`stroke="#FFFFFF"` 1–2 px or a lighter bevel) and never paint a background plate.
- **Small round badge, bottom-right** (centre 100,100, radius ~22, white ring): the *state* (green on, grey idle /
  off, red alarm, orange warning, blue open / level, purple auto…) or the *measured quantity* (thermometer,
  drop, CO₂, wind…). The device drawing keeps that corner free.
- 128 × 128 viewBox, drawing within ~10–118 px, soft elliptic shadow under floor-standing devices.
- Check the preview (`preview.png`: each icon once on a light / dark diagonal background) before delivering.

## How many images per device (HC3 rules)
| Device type | Images in one icon set | Upload fields |
|---|---|---|
| Binary (switch, binarySensor, door/window, motion, smoke…) | 2: idle / active | `icon0`, `icon100` |
| Multilevel (dimmer, roller shutter, valve level) | 11: `0`, `10` … `100` | `icon0` … `icon100` |
| deviceController, most QuickApp parents, multilevelSensor / temperature… | 1 | `icon0` |
A one-image type cannot change its picture by itself. For a state-dependent QA icon (OK / warning / alarm, or a mode),
upload one set per state and switch from Lua: `self:updateProperty("deviceIcon", tonumber(self:optionalVariable("iconAlarm")))`
(ids pasted in variables; pattern in the `hc3-quickapp` skill, `references/patterns.md` §5).
Make **one icon per useful state** and icons for **every** device a QuickApp creates (parent and children).

## Workflow
1. List the devices (parent, each child, each Z-Wave sub-device) and their exact `type` (`api.get("/devices/<id>")`,
   e.g. `com.fibaro.FGR224` for a Fibaro roller shutter module, `com.fibaro.rollerShutter` for a QA child).
2. Ask for photos of the real models; agree on the states and badge meanings.
3. Copy `scripts/icon_kit.py`, write one drawing function per device (SVG fragment in the 128 box, see
   `roof_window(pct)`), add `(name, title, body)` rows to `ICONS` — one per state — and run
   `python3 icon_kit.py --out icons/`. Naming: `<device>-<state>` (`shutter-000`…`shutter-100`, `boiler-on`,
   `boiler-off`), so a README table can say which icon goes where.
4. Show `preview.png`; iterate on the user's remarks (shape, colour, emoji-like badge clarity).
5. Upload: list the sets in the QA's `qa.json` `icons` section and let `build_fqa.py` (skill `hc3-packaging`)
   generate `<qa>-icons.sh`, or upload by hand: Settings → Devices → device → icon → Add.

## Upload API (observed on 5.2xx)
`POST /api/icons`, `multipart/form-data`: `type=device`, `deviceTemplate=<exact device type>`, one file per state
(`icon0`, `icon100` or `icon0`…`icon100`), `fileExtension=png` (svg accepted). Answer **201**
`{"id": 1055, "iconSetName": "User1055", "fileExtension": "png"}`. Apply: `PUT /api/devices/<id>`
`{"properties": {"deviceIcon": 1055}}` (from outside — never on a QA's own id from inside the QA, it restarts; use
`self:updateProperty`). Delete: `DELETE /api/icons?id=&type=device&name=&fileExtension=png`. User icon ids start
around 1000. `GET /api/icons` lists them (two response shapes exist across firmwares: accept both).
Room and scene icons exist too (`type=room` / `type=scene` probable **[V]**).

`references/badges.md` lists the badge colours and glyphs available in the kit.
