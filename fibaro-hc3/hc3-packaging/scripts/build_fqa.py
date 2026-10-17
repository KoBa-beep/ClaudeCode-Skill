#!/usr/bin/env python3
"""
build_fqa.py — package a Fibaro HC3 QuickApp folder into ready-to-use files.

Input: a folder containing
  qa.json   name, device type, variables (default values, NEVER secrets), UI (rows of labels / buttons / sliders /
            switches / selects with their methods), optional interfaces, extra Lua files, icons to upload
  main.lua  the code (+ the other Lua files listed in qa.json "files")

Output (in --out, default: <folder>/dist):
  <qa>.fqa          import in the HC3: Settings → Devices → + → Other device → Quick App → Upload file
  <qa>-update.sh    replaces the CODE of an already installed QA (PUT /api/quickApp/<id>/files/<name>), keeping its id,
                    variables, icon and scene references; checks the device type and asks for confirmation first
  <qa>-icons.sh     (if qa.json has "icons") uploads the icon sets (POST /api/icons, like the web UI) and can apply
                    them to the QA or to its child devices

The shell scripts run on macOS / Linux (bash + curl). They ask for the HC3 address, user and password at each run;
the password is never displayed, never stored, and is passed to curl through a temporary config file (not visible in
the process list), deleted on exit.

Usage:
  python3 build_fqa.py path/to/qa-folder [more folders…] [--out DIR] [--icons DIR]
    --icons DIR   where "<name>.png" icons referenced in qa.json are looked up
                  (default: <folder>/icons, then <folder>)
"""
import argparse
import base64
import json
import os
import re
import sys

EVENT = {"button": "onReleased", "select": "onToggled", "slider": "onChanged", "switch": "onReleased"}
ROW_WEIGHT = {1: "1.0", 2: "0.5", 3: "0.33", 4: "0.25", 5: "0.2"}
SECRET_WORDS = ("password", "passwd", "secret", "token", "authcode", "apikey", "api_key", "clientsecret")


# ------------------------------------------------------------------ UI, legacy format (viewLayout)
def legacy_component(e, weight):
    c = {"name": e["id"], "style": {"weight": weight}, "text": e.get("text", ""), "type": e["type"], "visible": True}
    if e["type"] == "select":
        c.update(options=[], selectionType="single", values=[])
    return c


def view_layout(ui):
    items = []
    for row in ui:
        width = ROW_WEIGHT.get(len(row), "0.2")
        comps = [legacy_component(e, width if len(row) > 1 else "1.2") for e in row]
        content = ({"components": comps, "style": {"weight": "1.2"}, "type": "horizontal"} if len(row) > 1 else comps[0])
        items.append({"components": [content, {"style": {"weight": "0.5"}, "type": "space"}],
                      "style": {"weight": "1.2"}, "type": "vertical"})
    return {"$jason": {"body": {"header": {"style": {"height": str(len(ui) * 50)}, "title": "quickApp_device_0"},
                                "sections": {"items": items}},
                       "head": {"title": "quickApp_device_0"}}}


# ------------------------------------------------------------------ UI, current format (uiView)
def binding(element_id, event, with_value):
    return [{"params": {"actionName": "UIAction", "args": [event, element_id] + (["$event.value"] if with_value else [])},
             "type": "deviceAction"}]


def ui_view(ui):
    rows = []
    for row in ui:
        weight = ROW_WEIGHT.get(len(row), "0.2")
        comps = []
        for e in row:
            c = {"name": e["id"], "style": {"weight": weight}, "text": e.get("text", ""), "type": e["type"], "visible": True}
            if e["type"] == "button":
                c["eventBinding"] = {ev: binding(e["id"], ev, False)
                                     for ev in ("onReleased", "onLongPressDown", "onLongPressReleased")}
            elif e["type"] == "select":         # options are filled at runtime with updateView(id, "options", …)
                c.update(options=[], selectionType="single", values=[],
                         eventBinding={"onToggled": binding(e["id"], "onToggled", True)})
            elif e["type"] == "slider":
                c.update(min=str(e.get("min", 0)), max=str(e.get("max", 100)), step=str(e.get("step", 1)), value="0",
                         eventBinding={"onChanged": binding(e["id"], "onChanged", True)})
            comps.append(c)
        rows.append({"components": comps, "style": {"weight": "1.0"}, "type": "horizontal"})
    return rows


def ui_callbacks(ui):
    cbs = []
    for row in ui:
        for e in row:
            ev = EVENT.get(e["type"])
            if ev and e.get(ev):
                cbs.append({"callback": e[ev], "eventType": ev, "name": e["id"]})
    return cbs


# ------------------------------------------------------------------ checks
def check(folder, m):
    errors = []
    for key in ("name", "type"):
        if not m.get(key):
            errors.append(f"qa.json: '{key}' is missing")
    for v in m.get("variables", []):
        if any(w in v["name"].lower() for w in SECRET_WORDS) and str(v.get("value", "")).strip():
            errors.append(f"variable '{v['name']}' has a value: secrets must never be shipped (leave it empty)")
    ids = [e["id"] for row in m.get("ui", []) for e in row]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"duplicate UI ids: {', '.join(sorted(dup))}")
    code = "\n".join(open(os.path.join(folder, f), encoding="utf-8").read() for f in m.get("files", ["main.lua"]))
    for row in m.get("ui", []):
        for e in row:
            cb = e.get(EVENT.get(e["type"], ""), "")
            if cb and not re.search(r"function\s+QuickApp:" + re.escape(cb) + r"\s*\(", code):
                errors.append(f"UI element '{e['id']}' calls {cb}() but no 'function QuickApp:{cb}(' in the code")
    if re.search(r"fibaro:(call|getValue|setGlobal|getGlobal|debug|sleep)", code):
        errors.append("HC2 API found (fibaro:call / fibaro:getValue …): use fibaro.call / fibaro.getValue on the HC3")
    return errors


# ------------------------------------------------------------------ build
def build(folder, out_dir, icon_dirs):
    with open(os.path.join(folder, "qa.json"), encoding="utf-8") as f:
        m = json.load(f)
    errors = check(folder, m)
    if errors:
        sys.exit(f"{folder}:\n  - " + "\n  - ".join(errors))
    slug = os.path.basename(os.path.normpath(folder))
    files = []
    for i, fname in enumerate(m.get("files", ["main.lua"])):
        with open(os.path.join(folder, fname), encoding="utf-8") as f:
            content = f.read()
        files.append({"name": "main" if i == 0 else os.path.splitext(fname)[0], "isMain": i == 0, "isOpen": i == 0,
                      "type": "lua", "content": content})
    ui = m.get("ui", [])
    fqa = {
        "name": m["name"],
        "type": m["type"],
        "apiVersion": "1.3",
        "initialInterfaces": m.get("interfaces", []),
        "initialProperties": {
            "viewLayout": view_layout(ui),
            "uiView": ui_view(ui),
            "uiCallbacks": ui_callbacks(ui),
            "quickAppVariables": [{"name": v["name"], "value": v.get("value", "")} for v in m.get("variables", [])],
            "typeTemplateInitialized": True,
        },
        "files": files,
    }
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, slug + ".fqa")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(fqa, f, ensure_ascii=False, indent=1)
    icons = build_icon_script(slug, m, out_dir, icon_dirs + [os.path.join(folder, "icons"), folder])
    build_update_script(slug, m, files, out_dir)
    return out, len(ui_callbacks(ui)), len(fqa["initialProperties"]["quickAppVariables"]), icons


# ------------------------------------------------------------------ shared shell header
SCRIPT_HEAD = r'''set -u
HC3="${HC3:-}"
read -r -p "HC3 address (IP or name)${HC3:+ [$HC3]}: " a; HC3="${a:-$HC3}"
[ -z "$HC3" ] && { echo "No address given."; exit 1; }
read -r -p "HC3 user [admin]: " U; U="${U:-admin}"
read -r -s -p "HC3 password: " P; echo
CFG=$(mktemp); TMP=$(mktemp -d); trap 'rm -rf "$CFG" "$TMP"' EXIT
printf 'user = "%%s:%%s"\n' "$U" "$P" > "$CFG"; unset P   # credentials reach curl through a temp file only
code=$(curl -s -o /dev/null -w "%%{http_code}" -K "$CFG" "http://$HC3/api/rooms")
if [ "$code" != "200" ]; then echo "Cannot reach the HC3 (HTTP $code): check address, user, password."; exit 1; fi
'''

# ------------------------------------------------------------------ code update script
UPDATE_SCRIPT = r'''#!/bin/bash
# Updates the CODE of the QuickApp "%(qa)s" already installed on the HC3 (generated by build_fqa.py — do not edit).
# The QA keeps its id, variables, icon and scene references; it restarts with the new code.
# Usage (macOS / Linux Terminal):   bash %(file)s
# Endpoint (not in the swagger, used by community tools): PUT /api/quickApp/<id>/files/<name>
''' + SCRIPT_HEAD + r'''read -r -p "Id of the QuickApp \"%(qa)s\" to update: " QA_ID
dev=$(curl -s -K "$CFG" "http://$HC3/api/devices/$QA_ID")
name=$(printf '%%s' "$dev" | sed -n 's/^{"id":[0-9]*,"name":"\([^"]*\)".*/\1/p')
if ! printf '%%s' "$dev" | grep -q '"type":"%(type)s"'; then
  echo "Device $QA_ID (\"$name\") is not of type %(type)s: wrong QuickApp. Nothing changed."; exit 1
fi
read -r -p "Replace the code of \"$name\" (id $QA_ID) with version %(version)s? (y/N) " ok
case "$ok" in y|Y|yes|YES|o|O|oui) ;; *) echo "Cancelled."; exit 0;; esac
files=$(curl -s -K "$CFG" "http://$HC3/api/quickApp/$QA_ID/files")
%(files)s
echo "Done. Open the QA console to check that the new version starts."
'''

UPDATE_FILE = r'''
base64 --decode > "$TMP/%(name)s.json" <<'B64'
%(b64)s
B64
if printf '%%s' "$files" | grep -q '"name":"%(name)s"'; then
  c=$(curl -s -o "$TMP/r.txt" -w "%%{http_code}" -K "$CFG" -X PUT -H "Content-Type: application/json" \
      --data-binary @"$TMP/%(name)s.json" "http://$HC3/api/quickApp/$QA_ID/files/%(name)s")
else
  c=$(curl -s -o "$TMP/r.txt" -w "%%{http_code}" -K "$CFG" -X POST -H "Content-Type: application/json" \
      --data-binary @"$TMP/%(name)s.json" "http://$HC3/api/quickApp/$QA_ID/files")
fi
case "$c" in 2*) echo "    file \"%(name)s\" updated (HTTP $c)";; *) echo "    FAILED \"%(name)s\" (HTTP $c): $(cat "$TMP/r.txt")";; esac
'''


def build_update_script(slug, m, files, out_dir):
    fname = slug + "-update.sh"
    version = "?"
    for line in files[0]["content"].splitlines()[:8]:
        found = re.search(r"[Vv]ersion\s*:?\s*([0-9][0-9A-Za-z.\-]*)", line)
        if found:
            version = found.group(1)
            break
    parts = []
    for f in files:
        payload = {"name": f["name"], "isMain": f["isMain"], "type": "lua", "isOpen": False, "content": f["content"]}
        b64 = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode()
        b64 = "\n".join(b64[i:i + 76] for i in range(0, len(b64), 76))
        parts.append(UPDATE_FILE % {"name": f["name"], "b64": b64})
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(UPDATE_SCRIPT % {"qa": m["name"], "file": fname, "type": m["type"], "version": version,
                                 "files": "".join(parts)})
    os.chmod(path, 0o755)
    return path


# ------------------------------------------------------------------ icon upload script
ICON_HEAD = r'''#!/bin/bash
# Uploads the icons of the QuickApp "%(qa)s" to the HC3 (generated by build_fqa.py — do not edit).
# Usage (macOS / Linux Terminal):   bash %(file)s
# POST /api/icons (multipart: type=device, deviceTemplate, icon0 / icon100 …, fileExtension=png), like the web UI.
# Running it again creates NEW icon sets (duplicates): delete old ones in Settings → Icons if needed.
''' + SCRIPT_HEAD + r'''read -r -p "Id of the QuickApp \"%(qa)s\" (empty = upload only, apply by hand): " QA_ID
'''

ICON_SET = r'''
echo "--- %(label)s (%(template)s)"
%(decode)s
resp=$(curl -s -K "$CFG" -F type=device -F deviceTemplate=%(template)s %(fields)s -F fileExtension=png "http://$HC3/api/icons")
id=$(printf '%%s' "$resp" | sed -n 's/.*"id"[^0-9]*\([0-9][0-9]*\).*/\1/p')
if [ -z "$id" ]; then
  echo "    UPLOAD FAILED: $resp"
else
  echo "    icon set created: id $id"
  if [ "%(apply)s" = "qa" ] && [ -n "$QA_ID" ]; then
    c=$(curl -s -o /dev/null -w "%%{http_code}" -K "$CFG" -X PUT -H "Content-Type: application/json" \
        -d "{\"properties\":{\"deviceIcon\":$id}}" "http://$HC3/api/devices/$QA_ID")
    echo "    applied to QA $QA_ID (HTTP $c; the QA restarts, this is normal)"
  elif [ "%(apply)s" = "children" ] && [ -n "$QA_ID" ]; then
    kids=$(curl -s -K "$CFG" "http://$HC3/api/devices?parentId=$QA_ID" | grep -o '{"id":[0-9]*' | grep -o '[0-9][0-9]*')
    [ -z "$kids" ] && echo "    no child device found for QA $QA_ID"
    for k in $kids; do
      c=$(curl -s -o /dev/null -w "%%{http_code}" -K "$CFG" -X PUT -H "Content-Type: application/json" \
          -d "{\"properties\":{\"deviceIcon\":$id}}" "http://$HC3/api/devices/$k")
      echo "    applied to child device $k (HTTP $c)"
    done
  else
    echo "    apply it to \"%(label)s\": device → General → Icon (set $id)%(hint)s"
  fi
fi
'''


def find_icon(name, dirs):
    for d in dirs:
        for cand in (os.path.join(d, name + ".png"), os.path.join(d, "png", name + ".png")):
            if os.path.isfile(cand):
                return cand
    sys.exit(f"icon '{name}.png' not found in: {', '.join(dirs)}")


def build_icon_script(slug, m, out_dir, icon_dirs):
    icons = m.get("icons")
    if not icons:
        return None
    fname = slug + "-icons.sh"
    out = [ICON_HEAD % {"qa": m["name"], "file": fname}]
    for k, s in enumerate(icons):
        decode, fields = [], []
        for state, icon in s["states"].items():
            with open(find_icon(icon, icon_dirs), "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            path = f'"$TMP/{k}_{state}.png"'
            decode.append(f"base64 --decode > {path} <<'B64'\n{b64}\nB64")
            fields.append(f'-F icon{state}=@{path}')
        apply = "qa" if s.get("applyToQA") else ("children" if s.get("applyToChildren") else "")
        hint = s.get("hint", "")
        out.append(ICON_SET % {"label": s["label"], "template": s["template"], "decode": "\n".join(decode),
                               "fields": " ".join(fields), "apply": apply, "hint": (" — " + hint) if hint else ""})
    out.append('\necho "Done. Reload the HC3 page (F5) to see the icons."\n')
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(out))
    os.chmod(path, 0o755)
    return path


def main():
    ap = argparse.ArgumentParser(description="Build .fqa + update / icon install scripts for HC3 QuickApps")
    ap.add_argument("folders", nargs="+", help="QuickApp folder(s) containing qa.json and main.lua")
    ap.add_argument("--out", help="output folder (default: <folder>/dist)")
    ap.add_argument("--icons", action="append", default=[], help="folder where icon PNGs are looked up (repeatable)")
    a = ap.parse_args()
    for folder in a.folders:
        out_dir = a.out or os.path.join(folder, "dist")
        out, cbs, nvars, icons = build(folder, out_dir, a.icons)
        print(f"{out}: {nvars} variable(s), {cbs} UI callback(s)" + (f" + {os.path.basename(icons)}" if icons else ""))


if __name__ == "__main__":
    main()
