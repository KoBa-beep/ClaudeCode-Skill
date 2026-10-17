# Badges in icon_kit.py

Usage in a catalogue row: `device_drawing(state) + B(p_glyph(...), "colour_key")`.

## Colours (`BADGE`)
| Key | Hex | Meaning |
|---|---|---|
| `off` | #8A94A3 | idle, off, closed, nothing to report (grey) |
| `on` | #16A34A | on, OK, open/accepted |
| `alert` | #DC2626 | alarm, fault, refused |
| `warn` | #F08C00 | warning, pre-alert, low battery |
| `heat` / `cool` / `auto` / `dry` / `fan` | #F2622D / #0EA5E9 / #7C3AED / #0D9488 / #2563EB | HVAC modes |
| `temp` / `outdoor` | #E8453C / #F07A1A | indoor / outdoor temperature |
| `humidity` / `rain` / `cloud` | #1E88E5 / #1D4ED8 / #3B82F6 | water-related measures |
| `co2` / `noise` / `pressure` / `wind` | #059669 / #8B34E0 / #4B5E7A / #0F8A7E | air-quality and weather |
| `energy` / `light` | #E08A00 / #E9A800 | consumption, lights |
| `shutter` | #3A5BD9 | position / level |

Keep one meaning per colour across all of a user's icons: grey always means "rest".

## Glyphs (white, drawn in a 128 box then scaled into the badge)
| Function | Picture |
|---|---|
| `p_power()` | power symbol |
| `p_check()`, `p_cross()`, `p_excl()` | ✓, ✗, ! |
| `p_arrow(up)` | arrow up / down |
| `p_text("50", size)` , `p_letter("A")` | number or letter (level %, mode letter) |
| `p_thermo()`, `p_thermo_sun()`, `p_thermo_up()` | thermometer, outdoor thermometer, fast temperature rise |
| `p_drop()`, `p_rain()`, `p_snow()`, `p_cloud()` | humidity, rain, frost, cloud |
| `p_flame()`, `p_smoke()` | heating / fire, smoke |
| `p_fan()`, `p_swing()` | fan, swing / oscillation |
| `p_wind(gust)`, `p_compass()`, `p_gauge()` | wind, gusts, direction, pressure |
| `p_bolt()`, `p_battery_low()` | energy, low battery |
| `p_bell()`, `p_speaker()`, `p_play()`, `p_pause()`, `p_mute()` | call / alarm, sound, media states |
| `p_lock(locked)`, `p_contact(opened)` | lock, door contact |
| `p_bulb()`, `p_tap()` | light, hot water |
| `p_slide("open"|"close")`, `p_walker()` | gate opening / closing, pedestrian opening |

Smoke vs other "cloud" shapes: users read a single round puff as something else entirely — use wavy vertical lines
(`p_smoke`) or a speech-bubble cloud, and add "CO" text for carbon monoxide.
