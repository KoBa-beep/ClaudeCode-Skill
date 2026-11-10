#!/usr/bin/env python3
"""Génère la série d'icônes 40x40 SVG pour l'arborescence IDBS Polar.

Convention graphique :
  - Dossiers : silhouette de dossier (onglet foncé + face claire) + pictogramme blanc.
  - Couleur = famille fonctionnelle (organisation, utilisateur, rangement, temps, axes...).
  - Éléments spéciaux (ROOT, TRASH, LANDING_PAGE) : forme propre, même palette et trait.
Usage : python3 generate.py   -> écrit svg/*.svg et preview.html
"""
from pathlib import Path

OUT = Path(__file__).parent / "svg"
def w(sw=2, extra=""):
    return f'stroke="#fff" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" fill="none"{extra}'


W = w()
F = 'fill="#fff"'


def svg(body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">'
            f'<title>{title}</title>{body}</svg>\n')


def folder(main, dark, glyph="", title=""):
    body = (f'<path d="M3 9.5A2.5 2.5 0 0 1 5.5 7h9.2a2 2 0 0 1 1.5.7L18.4 10H34.5A2.5 2.5 0 0 1 37 12.5V16H3z" fill="{dark}"/>'
            f'<rect x="3" y="13" width="34" height="21" rx="2.5" fill="{main}"/>'
            f'<rect x="3" y="13" width="34" height="2" fill="#fff" opacity=".25"/>'
            f'{glyph}')
    return svg(body, title)


def doc(main, dark, glyph="", title=""):
    """Page à coin plié : réservée aux expériences et documents."""
    body = (f'<path d="M9.5 2.5H25l8.5 8.5v24a2.5 2.5 0 0 1-2.5 2.5H9.5A2.5 2.5 0 0 1 7 35V5a2.5 2.5 0 0 1 2.5-2.5z" fill="{main}"/>'
            f'<path d="M25 2.5V9a2 2 0 0 0 2 2h6.5z" fill="{dark}"/>'
            f'{glyph}')
    return svg(body, title)


# ---------- pictogrammes (zone utile ~ x 11-29 / y 16-32) ----------
person = lambda cx, cy, s=1.0: (f'<circle cx="{cx}" cy="{cy - 3.2*s:.1f}" r="{2.8*s:.1f}" {F}/>'
                                f'<path d="M{cx - 5.2*s:.1f} {cy + 5.5*s:.1f}a{5.2*s:.1f} {5.2*s:.1f} 0 0 1 {10.4*s:.1f} 0z" {F}/>')

G = {
    "group": person(14, 24, .75) + person(26, 24, .75) + f'<circle cx="20" cy="20" r="3.6" fill="#fff" stroke="#c62828" stroke-width="1.2"/>'
             f'<path d="M13.6 31a6.4 6.4 0 0 1 12.8 0z" fill="#fff" stroke="#c62828" stroke-width="1.2"/>',
    "category": f'<path d="M12.5 18.5h9l6.5 5.5-6.5 5.5h-9z" {W}/><circle cx="16" cy="24" r="1.6" {F}/>',
    "web_search": f'<circle cx="18.5" cy="22.5" r="5" {W}/><path d="M22.2 26.2 27 31" {w(2.6)}/>'
                  f'<path d="M13.5 22.5h10M18.5 17.5c-2.4 2.8-2.4 7.2 0 10M18.5 17.5c2.4 2.8 2.4 7.2 0 10" {w(1.1)}/>',
    "project": f'<rect x="12" y="20" width="16" height="10.5" rx="1.8" {W}/><path d="M16.5 20v-2.2a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1V20M12 24.5h16" {W}/>',
    "user": person(20, 24, 1.05),
    "templates_folder": f'<rect x="16.5" y="16.5" width="11" height="14" rx="1.2" {w(2, ' opacity=".6"')}/>'
                        f'<rect x="12.5" y="18.5" width="11" height="13" rx="1.2" fill="#6a1b9a" stroke="#fff" stroke-width="2"/>'
                        f'<path d="M15.5 22h5M15.5 25h5M15.5 28h3" {w(1.6)}/>',
    "templates_sub_folder": f'<rect x="15" y="17" width="12" height="14.5" rx="1.2" {W}/>'
                            f'<rect x="17.5" y="20" width="7" height="3" rx=".5" {F}/><path d="M17.5 26h7M17.5 28.8h4.5" {w(1.6)}/>',
    "folder": "",
    "subfolder": f'<path d="M14 18v8.5h10" {w(2.4)}/><path d="M21.5 23.5l3 3-3 3" {w(2.4)}/>',
    "subsubfolder": f'<path d="M12.5 17.5v5h6M18.5 22.5v6h9" {w(2.2)}/><path d="M25 26l2.8 2.5-2.8 2.5" {w(2.2)}/>'
                    f'<circle cx="12.5" cy="17.5" r="1.6" {F}/><circle cx="18.5" cy="22.5" r="1.6" {F}/>',
    "shared_group": person(16.5, 24, .85) + f'<circle cx="25.5" cy="21" r="2.4" {F} opacity=".85"/>'
                    f'<path d="M21.8 30.5a4.6 4.6 0 0 1 8.4-1.2" {w(1.8)}/>'
                    f'<path d="M27 29.5l3 .2-.3-3" {w(1.6)}/>',
    "year": f'<rect x="12" y="17.5" width="16" height="14" rx="1.5" {W}/><path d="M12 21.5h16M15.5 16v3M24.5 16v3" {W}/>'
            + "".join(f'<rect x="{14 + c*3.2:.1f}" y="{23.3 + r*2.8:.1f}" width="2" height="1.8" {F}/>' for r in range(3) for c in range(4)),
    "month": f'<rect x="12" y="17.5" width="16" height="14" rx="1.5" {W}/><path d="M12 21.5h16M15.5 16v3M24.5 16v3" {W}/>'
             f'<text x="20" y="30" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="7.5" fill="#fff">31</text>',
    "gamme": f'<path d="M20 16.5l8 3.8-8 3.8-8-3.8z" {F}/><path d="M12 24.3l8 3.8 8-3.8M12 28.1l8 3.8 8-3.8" {w(1.8)}/>',
    "axis_domain": f'<rect x="16.5" y="16.5" width="7" height="5" rx="1" {F}/><rect x="11.5" y="26.5" width="7" height="5" rx="1" {F}/>'
                   f'<rect x="21.5" y="26.5" width="7" height="5" rx="1" {F}/><path d="M20 21.5v2.5M15 26.5V24h10v2.5" {w(1.6)}/>',
    "domain": f'<circle cx="20" cy="24" r="7" {W}/><circle cx="20" cy="24" r="3.6" {w(1.6)}/><circle cx="20" cy="24" r="1.3" {F}/>',
    "axis": f'<path d="M13 31V17.5M13 31h15" {W}/><path d="M10.8 19.5 13 17.2l2.2 2.3M26 28.8l2.3 2.2-2.3 2.2" {w(1.8)}/>'
            f'<path d="M15.5 28l4-4.5 3 2.5 4.5-6" {w(1.8)}/>',
    "collaboration_idbs": f'<circle cx="16.5" cy="24" r="5.2" {W}/><circle cx="23.5" cy="24" r="5.2" {W}/>'
                          f'<path d="M20 20.2a5.2 5.2 0 0 1 0 7.6 5.2 5.2 0 0 1 0-7.6z" {F}/>',
}

# pictogrammes des expériences / documents (zone utile ~ x 11-29 / y 13-33)
D = {
    "experiment_analytical": f'<path d="M11 31h18" {w(1.6)}/><path d="M11.5 30c2 0 2.5-1.5 3.3-6 .8-4.5 1.2-9 2.2-9s1.4 4.5 2.2 9c.8 4.5 1.3 6 3.3 6 1.4 0 1.8-1 2.5-3.5.6-2.2 1-3.5 1.6-3.5s1 1.3 1.4 3.5c.3 1.6.7 3.5 1.5 3.5" {w(2)}/>',
    "experiment_gps": f'<path d="M20 15a6.3 6.3 0 0 0-3.8 11.3c.8.6 1.3 1.4 1.3 2.3V29h5v-.4c0-.9.5-1.7 1.3-2.3A6.3 6.3 0 0 0 20 15z" {F}/>'
                      f'<path d="M17.8 30.8h4.4M18.6 33h2.8" {w(1.8)}/>'
                      f'<path d="M18 23.5l2-2.5 2 2.5" stroke="#039be5" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                      f'<path d="M11 18.5l2 1M29 18.5l-2 1M13.5 13.5l1.5 1.6M26.5 13.5L25 15.1" {w(1.6)}/>',
    "experiment_microbio": f'<ellipse cx="20" cy="24" rx="9" ry="8" {w(2)}/>'
                           f'<rect x="13.5" y="19" width="7" height="3.6" rx="1.8" transform="rotate(-25 17 20.8)" {F}/>'
                           f'<rect x="19.5" y="25" width="7" height="3.6" rx="1.8" transform="rotate(20 23 26.8)" {F}/>'
                           f'<circle cx="24" cy="20" r="1.4" {F}/><circle cx="15.5" cy="27.5" r="1.2" {F}/>',
    "experiment": f'<rect x="13" y="14" width="15" height="19" rx="1.5" {w(2)}/><path d="M11 18h4M11 22.5h4M11 27h4M11 31h4" {w(1.8)}/>'
                  f'<path d="M18.5 19h6M18.5 23h6M18.5 27h4" {w(1.6)}/>',
    "template": f'<rect x="12" y="14.5" width="16" height="5" rx="1" {F}/>'
                f'<rect x="12" y="22" width="7" height="10" rx="1" {w(1.6, ' stroke-dasharray="2 1.6"')}/>'
                f'<path d="M21.5 23h6.5M21.5 26.5h6.5M21.5 30h4.5" {w(1.8)}/>',
    "report": f'<path d="M11.5 32.5h17" {w(1.8)}/><rect x="12.5" y="24" width="3.6" height="7" rx=".6" {F}/>'
              f'<rect x="18.2" y="18.5" width="3.6" height="12.5" rx=".6" {F}/><rect x="23.9" y="21.5" width="3.6" height="9.5" rx=".6" {F}/>'
              f'<path d="M12 20.5l6-5 5 3 5.5-4.5" {w(1.6)}/>',
}

DOCS = [
    ("experiment_analytical", "EXPERIMENT_ANALYTICAL", "#283593", "#1a237e"),
    ("experiment_gps", "EXPERIMENT_GPS", "#039be5", "#0277bd"),
    ("experiment_microbio", "EXPERIMENT_MICROBIO", "#2e7d32", "#1b5e20"),
    ("experiment", "EXPERIMENT", "#5c7cfa", "#3b5bdb"),
    ("template", "TEMPLATE", "#78909c", "#546e7a"),
    ("report", "REPORT", "#f57c00", "#e65100"),
]

# (nom fichier, libellé, couleur face, couleur onglet)
FOLDERS = [
    ("group", "GROUP", "#e53935", "#b71c1c"),
    ("category", "CATEGORY", "#ef5350", "#c62828"),
    ("collaboration_idbs", "COLLABORATION_IDBS", "#00897b", "#00695c"),
    ("project", "PROJECT", "#546e7a", "#37474f"),
    ("user", "USER", "#fb8c00", "#e65100"),
    ("shared_group", "SHARED_GROUP", "#43a047", "#2e7d32"),
    ("web_search", "WEB_SEARCH", "#1e88e5", "#1565c0"),
    ("templates_folder", "TEMPLATES_FOLDER", "#8e24aa", "#6a1b9a"),
    ("templates_sub_folder", "TEMPLATES_SUB-FOLDER", "#ab47bc", "#7b1fa2"),
    ("folder", "FOLDER", "#fbc02d", "#f9a825"),
    ("subfolder", "SUBFOLDER", "#fbc02d", "#f9a825"),
    ("subsubfolder", "SUBSUBFOLDER", "#fbc02d", "#f9a825"),
    ("year", "YEAR", "#26a69a", "#00897b"),
    ("month", "MONTH", "#4db6ac", "#26a69a"),
    ("gamme", "GAMME", "#f4511e", "#d84315"),
    ("axis_domain", "AXIS_DOMAIN", "#3949ab", "#283593"),
    ("domain", "DOMAIN", "#5c6bc0", "#3949ab"),
    ("axis", "AXIS", "#7986cb", "#5c6bc0"),
]

SPECIAL = {
    "root": ("ROOT", '<circle cx="20" cy="20" r="16.5" fill="#455a64"/>'
             f'<circle cx="20" cy="20" r="11" {W}/><ellipse cx="20" cy="20" rx="4.8" ry="11" {W}/>'
             f'<path d="M9 20h22M10.8 14h18.4M10.8 26h18.4" {w(1.6)}/>'),
    "trash": ("TRASH", '<rect x="6" y="4" width="28" height="32" rx="5" fill="#424242"/>'
              f'<path d="M12 13h16M17.5 13v-2.2a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1V13" {W}/>'
              f'<path d="M13.8 13l1.2 16.5a1.5 1.5 0 0 0 1.5 1.4h7a1.5 1.5 0 0 0 1.5-1.4L26.2 13" {W}/>'
              f'<path d="M18 17.5v9M22 17.5v9" {w(1.6)}/>'),
    "landing_page": ("LANDING_PAGE", '<rect x="4" y="6" width="32" height="28" rx="3" fill="#0288d1"/>'
                     '<path d="M4 9a3 3 0 0 1 3-3h26a3 3 0 0 1 3 3v3H4z" fill="#01579b"/>'
                     f'<circle cx="8" cy="9" r="1.1" {F}/><circle cx="11.5" cy="9" r="1.1" {F}/><circle cx="15" cy="9" r="1.1" {F}/>'
                     f'<path d="M12.5 22.5 20 16l7.5 6.5" {w(2.2)}/><path d="M15 21v8.5h10V21" {w(2.2)}/>'
                     '<rect x="18.3" y="24.5" width="3.4" height="5" fill="#fff"/>'),
}


def main():
    OUT.mkdir(exist_ok=True)
    items = []
    for name, (label, body) in SPECIAL.items():
        (OUT / f"{name}.svg").write_text(svg(body, label)); items.append((name, label))
    for name, label, main_c, dark in FOLDERS:
        (OUT / f"{name}.svg").write_text(folder(main_c, dark, G[name], label)); items.append((name, label))
    for name, label, main_c, dark in DOCS:
        (OUT / f"{name}.svg").write_text(doc(main_c, dark, D[name], label)); items.append((name, label))
    order = ["root", "group", "category", "collaboration_idbs", "project", "user", "shared_group", "web_search",
             "templates_folder", "templates_sub_folder", "landing_page", "trash", "folder", "subfolder", "subsubfolder",
             "year", "month", "gamme", "axis_domain", "domain", "axis",
             "experiment_analytical", "experiment_gps", "experiment_microbio", "experiment", "template", "report"]
    lab = dict(items)
    cells = "".join(
        f'<figure><img src="svg/{n}.svg" width="40" height="40"><img src="svg/{n}.svg" width="20" height="20">'
        f'<img src="svg/{n}.svg" width="80" height="80"><figcaption>{lab[n]}<br><code>{n}.svg</code></figcaption></figure>'
        for n in order)
    (OUT.parent / "preview.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Icônes Polar</title><style>'
        'body{font:13px Segoe UI,Arial,sans-serif;background:#f5f5f5;margin:24px}'
        '.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}'
        'figure{margin:0;background:#fff;border:1px solid #ddd;border-radius:6px;padding:12px;display:flex;flex-wrap:wrap;align-items:end;gap:10px}'
        'figcaption{width:100%;font-weight:600}code{font-weight:400;color:#666}</style>'
        f'<h1>Icônes IDBS Polar — 40×40 SVG</h1><p>Tailles affichées : 40 px (natif), 20 px, 80 px.</p><div class="g">{cells}</div>')
    print(f"{len(items)} icônes générées dans {OUT}")


if __name__ == "__main__":
    main()
