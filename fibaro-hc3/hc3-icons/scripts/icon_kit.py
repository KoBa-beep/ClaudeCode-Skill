#!/usr/bin/env python3
"""
HC3 icon kit — draws "realistic device + status badge" icons for Fibaro HC3 devices / QuickApps.

Each icon = an illustration of the real device on a 100 % transparent background (128 x 128)
+ a small round badge in the bottom-right corner showing the state (on/off, open/closed… ; grey = idle)
or the measured quantity (temperature, humidity…). One file per state, readable on light AND dark UI.

Outputs (next to this script, or --out DIR):
  svg/<name>.svg      editable vector
  png/<name>.png      128 x 128, transparent, ready to upload to the HC3
  preview.png         contact sheet: each icon once, on a background split light / dark (diagonal)

Usage:  pip install cairosvg pillow
        python3 icon_kit.py [--out DIR]

How to extend: write one drawing function per device (SVG fragment in a 128 x 128 box, keep the bottom-right
corner (x, y > 75) free for the badge), then add one (name, title, body) tuple per state to ICONS.
"""
import argparse
import math
import os
import shutil

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SIZE = 128

BADGE = {
    "off": "#8A94A3", "on": "#16A34A", "heat": "#F2622D", "cool": "#0EA5E9", "auto": "#7C3AED",
    "dry": "#0D9488", "fan": "#2563EB", "temp": "#E8453C", "outdoor": "#F07A1A", "humidity": "#1E88E5",
    "co2": "#059669", "noise": "#8B34E0", "pressure": "#4B5E7A", "rain": "#1D4ED8", "wind": "#0F8A7E",
    "energy": "#E08A00", "alert": "#DC2626", "warn": "#F08C00", "cloud": "#3B82F6", "shutter": "#3A5BD9", "light": "#E9A800",
}


# ============================================================ SVG helpers
def lin(id_, stops, x1=0, y1=0, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def rad(id_, stops, cx=0.5, cy=0.5, r=0.5):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'


def shadow(cx=64, cy=114, rx=44, ry=7):
    return (f'<defs>{rad("sh", [(0, "#000000", 0.35), (1, "#000000", 0)])}</defs>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#sh)"/>')


def stroke_g(content, width=7, color="#FFFFFF"):
    return (f'<g fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-linejoin="round">{content}</g>')


def fill_g(content, color="#FFFFFF"):
    return f'<g fill="{color}" stroke="none">{content}</g>'


# ============================================================ badge glyphs
# Drawn white in a 128 x 128 box centred on (64, 64), then scaled down into the badge.
def p_thermo():
    return stroke_g('<path d="M54 30 a10 10 0 0 1 20 0 v40 a20 20 0 1 1 -20 0 Z"/>', 9) + \
        fill_g('<circle cx="64" cy="86" r="11"/><rect x="60" y="44" width="8" height="40" rx="4"/>')


def p_thermo_sun():
    rays = "".join(f'<line x1="{96 + 14 * math.cos(math.radians(a)):.1f}" y1="{34 + 14 * math.sin(math.radians(a)):.1f}" '
                   f'x2="{96 + 22 * math.cos(math.radians(a)):.1f}" y2="{34 + 22 * math.sin(math.radians(a)):.1f}"/>' for a in range(0, 360, 45))
    return stroke_g('<path d="M40 30 a10 10 0 0 1 20 0 v40 a20 20 0 1 1 -20 0 Z"/>', 9) + \
        fill_g('<circle cx="50" cy="86" r="11"/><rect x="46" y="44" width="8" height="40" rx="4"/>') + \
        stroke_g(f'<circle cx="96" cy="34" r="8"/>{rays}', 7)


def p_drop():
    return fill_g('<path d="M64 24 C76 42 92 58 92 76 A28 28 0 0 1 36 76 C36 58 52 42 64 24 Z"/>')


def p_flame():
    return fill_g('<path d="M64 20 C80 38 92 50 92 72 C92 90 80 104 64 104 C48 104 36 90 36 72 C36 58 46 50 52 40 '
                  'C54 52 58 58 64 60 C66 46 64 32 64 20 Z"/>')


def p_snow():
    parts = []
    for a in range(0, 180, 60):
        r_ = math.radians(a)
        dx, dy = 34 * math.cos(r_), 34 * math.sin(r_)
        parts.append(f'<line x1="{64 - dx:.1f}" y1="{64 - dy:.1f}" x2="{64 + dx:.1f}" y2="{64 + dy:.1f}"/>')
        for sgn in (1, -1):
            bx, by = 64 + sgn * dx * 0.55, 64 + sgn * dy * 0.55
            for t in (55, -55):
                rr = math.radians(a + t)
                parts.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx + sgn * 13 * math.cos(rr):.1f}" y2="{by + sgn * 13 * math.sin(rr):.1f}"/>')
    return stroke_g("".join(parts), 9)


def p_letter(ch):
    return (f'<text x="64" y="88" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
            f'font-weight="bold" font-size="68" fill="#FFFFFF">{ch}</text>')


def p_power():
    return stroke_g('<path d="M42 42 A32 32 0 1 0 86 42"/><line x1="64" y1="24" x2="64" y2="62"/>', 11)


def p_fan():
    parts = ['<circle cx="64" cy="64" r="7" fill="#FFFFFF"/>']
    for a in (0, 120, 240):
        parts.append(f'<path transform="rotate({a} 64 64)" d="M64 56 C50 44 54 22 70 24 C82 26 80 44 70 58"/>')
    return stroke_g("".join(parts), 9)


def p_swing():
    return stroke_g('<path d="M64 24 v80"/><path d="M44 42 l20 -20 l20 20"/><path d="M44 86 l20 20 l20 -20"/>', 11)


def p_bolt():
    return fill_g('<path d="M74 14 L34 70 H60 L50 114 L96 52 H70 Z"/>')


def p_bell():
    return stroke_g('<path d="M36 86 v-24 a28 28 0 0 1 56 0 v24 l10 10 h-76 Z"/><path d="M54 104 a10 10 0 0 0 20 0"/>', 9)


def p_lock(locked):
    shackle = '<path d="M44 58 v-14 a20 20 0 0 1 40 0 v14"/>' if locked else '<path d="M44 58 v-14 a20 20 0 0 1 39 -7"/>'
    return stroke_g(shackle, 10) + fill_g('<rect x="30" y="56" width="68" height="50" rx="10"/>')


def p_check():
    return stroke_g('<path d="M34 66 l20 20 l40 -42"/>', 14)


def p_cross():
    return stroke_g('<path d="M40 40 l48 48"/><path d="M88 40 l-48 48"/>', 14)


def p_excl():
    return stroke_g('<path d="M64 30 v40"/><path d="M64 94 v1"/>', 14)


def p_arrow(up):
    return stroke_g('<path d="M64 102 V28"/><path d="M36 56 L64 28 L92 56"/>' if up else
                    '<path d="M64 26 V100"/><path d="M36 72 L64 100 L92 72"/>', 13)


def p_text(t, size=50):
    return (f'<text x="64" y="{64 + size * 0.36:.0f}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
            f'font-weight="bold" font-size="{size}" fill="#FFFFFF">{t}</text>')


def p_speaker():
    return fill_g('<path d="M22 50 h18 l26 -22 v72 l-26 -22 h-18 Z"/>') + \
        stroke_g('<path d="M80 46 a24 24 0 0 1 0 36"/><path d="M94 32 a44 44 0 0 1 0 64"/>', 9)


def p_gauge():
    return stroke_g('<path d="M22 88 A44 44 0 1 1 106 88"/><line x1="64" y1="76" x2="88" y2="48"/>', 10) + \
        fill_g('<circle cx="64" cy="76" r="9"/>')


def p_rain():
    return stroke_g('<path d="M36 64 h52 a16 16 0 0 0 0 -32 a22 22 0 0 0 -42 -6 a16 16 0 0 0 -10 38 Z"/>'
                    '<line x1="46" y1="80" x2="38" y2="100"/><line x1="66" y1="80" x2="58" y2="100"/><line x1="86" y1="80" x2="78" y2="100"/>', 9)


def p_wind(gust=False):
    if gust:
        return stroke_g('<path d="M20 44 h44"/><path d="M20 64 h56"/><path d="M20 84 h40"/>', 10) + \
            fill_g('<path d="M100 16 L78 64 H94 L82 112 L114 54 H98 L108 16 Z"/>')
    return stroke_g('<path d="M20 48 h56 a13 13 0 1 0 -13 -13"/><path d="M20 70 h72 a14 14 0 1 1 -14 14"/><path d="M20 92 h30"/>', 10)


def p_compass():
    return stroke_g('<circle cx="64" cy="64" r="40"/>', 9) + fill_g('<path d="M64 30 L78 70 L64 62 L50 70 Z"/>')


def p_cloud():
    return fill_g('<path d="M36 90 h58 a20 20 0 0 0 0 -40 a28 28 0 0 0 -54 -6 a20 20 0 0 0 -4 46 Z"/>')


def p_contact(opened):
    """Small door: closed (rectangle + handle) or open (leaf in perspective)."""
    frame = stroke_g('<path d="M34 108 V22 h60 v86"/><line x1="22" y1="108" x2="106" y2="108"/>', 9)
    if opened:
        return frame + fill_g('<path d="M34 22 L66 32 V100 L34 108 Z"/>')
    return frame + fill_g('<circle cx="82" cy="66" r="7"/>')


def badge(glyph, color):
    """Small round badge in the bottom-right corner (centre 100,100; radius ~22)."""
    return (f'<circle cx="100" cy="100" r="25" fill="#FFFFFF"/>'
            f'<circle cx="100" cy="100" r="21.5" fill="{color}"/>'
            f'<g transform="translate(100 100) scale(0.26) translate(-64 -64)">{glyph}</g>')


def p_play():
    return fill_g('<path d="M44 28 L96 64 L44 100 Z"/>')


def p_pause():
    return fill_g('<rect x="38" y="30" width="18" height="68" rx="4"/><rect x="72" y="30" width="18" height="68" rx="4"/>')


def p_mute():
    return fill_g('<path d="M16 50 h18 l26 -22 v72 l-26 -22 h-18 Z"/>') + \
        stroke_g('<path d="M76 46 L108 82"/><path d="M108 46 L76 82"/>', 10)


def p_thermo_up():
    """Thermometer + upward arrow (fast temperature rise)."""
    return stroke_g('<path d="M38 30 a10 10 0 0 1 20 0 v40 a20 20 0 1 1 -20 0 Z"/>', 9) + \
        fill_g('<circle cx="48" cy="86" r="11"/><rect x="44" y="44" width="8" height="40" rx="4"/>') + \
        stroke_g('<path d="M94 96 V30"/><path d="M78 46 L94 28 L110 46"/>', 11)


def p_smoke():
    return stroke_g('<path d="M40 104 C28 88 52 80 40 64 C30 50 50 40 44 24"/><path d="M66 104 C54 88 78 80 66 64 C56 50 76 40 70 24"/>'
                    '<path d="M92 104 C80 88 104 80 92 64 C82 50 102 40 96 24"/>', 9)


def p_battery_low():
    return stroke_g('<rect x="18" y="40" width="80" height="48" rx="8"/><line x1="108" y1="56" x2="108" y2="72"/>', 9) + \
        fill_g('<rect x="28" y="50" width="16" height="28" rx="3"/>')


def p_bulb():
    """Light bulb (light on)."""
    return (fill_g('<path d="M64 16 C42 16 30 32 30 50 C30 64 38 72 44 80 C48 85 48 90 48 94 H80 C80 90 80 85 84 80 '
                   'C90 72 98 64 98 50 C98 32 86 16 64 16 Z"/><rect x="48" y="100" width="32" height="8" rx="3"/>'
                   '<rect x="54" y="112" width="20" height="6" rx="3"/>'))


def p_tap():
    """Tap (domestic hot water)."""
    return fill_g('<rect x="30" y="34" width="44" height="14" rx="5"/><rect x="46" y="22" width="12" height="16" rx="3"/>'
                  '<path d="M66 40 H86 A10 10 0 0 1 96 50 V58 H82 V52 H66 Z"/><rect x="36" y="18" width="32" height="8" rx="4"/>') + \
        fill_g('<path d="M89 70 C95 80 99 86 99 92 A10 10 0 0 1 79 92 C79 86 83 80 89 70 Z"/>')


def p_slide(direction):
    """Motion arrow: 'open' (to the right) or 'close' (to the left)."""
    if direction == "open":
        return stroke_g('<path d="M22 64 H96"/><path d="M76 42 L98 64 L76 86"/>', 12)
    return stroke_g('<path d="M106 64 H32"/><path d="M52 42 L30 64 L52 86"/>', 12)


def p_walker():
    """Pedestrian (partial opening)."""
    return fill_g('<circle cx="66" cy="22" r="10"/>') + \
        stroke_g('<path d="M62 36 L56 70 L42 104"/><path d="M56 70 L72 102"/><path d="M60 44 L42 58"/><path d="M62 44 L80 56"/>', 11)


# ============================================================ device drawings (example)
def roof_window(pct):
    """Roof window in perspective (match the angle of the user's photo of the real model):
    anthracite frame, light wood lining visible on the right and bottom, roller-shutter box on top
    (right end visible), shutter slats coming down over the glass.
    pct: shutter opening (0 = closed, 100 = open)."""
    closed = 1 - pct / 100
    gx, gy, gw, gh = 29, 30, 64, 72
    edge = gy + gh * closed
    slats = ""
    if closed > 0:
        slats = f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh * closed:.1f}" fill="url(#vsl)"/>'
        y = gy + 4
        while y < edge - 1:
            slats += f'<line x1="{gx}" y1="{y:.1f}" x2="{gx + gw}" y2="{y:.1f}" stroke="#5A6068" stroke-width="0.9"/>'
            y += 4.2
        if pct > 0:
            slats += f'<rect x="{gx - 0.5}" y="{edge - 2.2:.1f}" width="{gw + 1}" height="3" fill="#24282C"/>'
    window = (
        # light wood lining (visible on the right and bottom)
        f'<path d="M100 22 L109 27 V117 H30 L22 110 H100 Z" fill="url(#vwd)"/>'
        f'<path d="M100 110 L109 117 H30 L22 110 Z" fill="#E7C98F"/>'
        # anthracite frame
        f'<rect x="22" y="20" width="78" height="90" rx="2.5" fill="url(#vfr)"/>'
        f'<rect x="26" y="26" width="70" height="80" rx="1.5" fill="#23272B"/>'
        # glass + reflection
        f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" fill="url(#vgl)"/>'
        f'<path d="M{gx} {gy + 44} L{gx + 44} {gy} H{gx + 58} L{gx} {gy + 58} Z" fill="#FFFFFF" opacity="0.35"/>'
        + slats +
        # roller-shutter box (cylinder) with its right end
        f'<rect x="18" y="9" width="86" height="16" rx="8" fill="url(#vbx)"/>'
        f'<ellipse cx="104" cy="17" rx="4.5" ry="8" fill="#5E646B" stroke="#2C3035" stroke-width="0.8"/>'
        f'<rect x="22" y="12" width="78" height="2.5" rx="1.2" fill="#FFFFFF" opacity="0.18"/>'
    )
    return (shadow(66, 118, 42, 4) +
            f'<defs>{lin("vwd", [(0, "#F4DEAE"), (1, "#D9AE6E")], 0, 0, 1, 1)}'
            f'{lin("vfr", [(0, "#5B6168"), (1, "#33373C")], 0, 0, 1, 1)}'
            f'{lin("vgl", [(0, "#F4FAFE"), (0.55, "#D7ECF9"), (1, "#A9D2EE")], 0, 0, 0.6, 1)}'
            f'{lin("vsl", [(0, "#4B5157"), (1, "#3A3F45")])}'
            f'{lin("vbx", [(0, "#6B7178"), (0.45, "#43484E"), (1, "#2A2E33")])}</defs>'
            f'<g transform="translate(60 60) rotate(3) skewX(-26) scale(0.84 1.0) translate(-64 -64)">{window}</g>')


def svg(title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">'
            f'<title>{title}</title>{body}</svg>')


def B(glyph, color):
    return badge(glyph, BADGE[color])


# ============================================================ catalogue (example: roof window / roller shutter, 11 states)
# HC3 state conventions (see SKILL.md): binary devices = 2 images (icon0 idle, icon100 active);
# multilevel devices (shutters, dimmers) = 11 images (icon0, icon10 … icon100); deviceController = 1 image.
ICONS = [
    ("shutter-000", "Shutter closed", roof_window(0) + B(p_arrow(False), "off")),
] + [
    (f"shutter-{v:03d}", f"Shutter {v} %", roof_window(v) + B(p_text(str(v), 52 if v < 100 else 40), "shutter"))
    for v in range(10, 101, 10)
] + [
    ("sensor-temperature", "Temperature measure (example badge)", roof_window(50) + B(p_thermo(), "temp")),
]


def main():
    svg_dir, png_dir = os.path.join(ROOT, "svg"), os.path.join(ROOT, "png")
    for d in (svg_dir, png_dir):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    for name, title, body in ICONS:
        content = svg(title, body)
        with open(os.path.join(svg_dir, name + ".svg"), "w", encoding="utf-8") as f:
            f.write(content)
        cairosvg.svg2png(bytestring=content.encode("utf-8"), write_to=os.path.join(png_dir, name + ".png"),
                         output_width=SIZE, output_height=SIZE)
    make_preview()
    print(f"{len(ICONS)} icons written to {svg_dir} and {png_dir}")


def make_preview():
    """Contact sheet: each icon ONCE, on a background split diagonally (light / dark)
    to check it stays readable in both UI themes."""
    cols, cell_w, cell_h = 8, 170, 180
    rows = math.ceil(len(ICONS) / cols)
    sheet = Image.new("RGB", (cols * cell_w + 40, rows * cell_h + 40), "#F3F4F6")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    for i, (name, _, _) in enumerate(ICONS):
        x = 20 + (i % cols) * cell_w
        y = 20 + (i // cols) * cell_h
        bx, by, bw = x + (cell_w - 144) // 2, y + 4, 144
        draw.rounded_rectangle((bx, by, bx + bw, by + bw), 14, fill="#FFFFFF")
        draw.polygon([(bx + bw, by), (bx + bw, by + bw), (bx, by + bw)], fill="#1F2937")
        icon = Image.open(os.path.join(ROOT, "png", name + ".png")).convert("RGBA")
        sheet.paste(icon, (bx + 8, by + 8), icon)
        tw = draw.textlength(name, font=font)
        draw.text((x + (cell_w - tw) / 2, y + 154), name, fill="#374151", font=font)
    sheet.save(os.path.join(ROOT, "preview.png"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate HC3 icons (PNG + SVG + preview)")
    ap.add_argument("--out", default=ROOT, help="output directory (default: next to this script)")
    ROOT = ap.parse_args().out
    main()
