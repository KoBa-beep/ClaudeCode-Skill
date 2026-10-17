#!/usr/bin/env python3
"""
swagger_index.py — turn the HC3 swagger (OpenAPI files downloaded from http://<hc3>/swagger) into something searchable.

The HC3 swagger page loads one OpenAPI document per API area (devices, rooms, icons, notificationCenter…).
Save them (browser DevTools → Network → each *.json / *.yml, or the console helper printed by --how) into a folder,
then:

  python3 swagger_index.py DIR                        markdown index: METHOD /api/path — summary (grouped by file)
  python3 swagger_index.py DIR --grep icons           only endpoints whose path or summary matches
  python3 swagger_index.py DIR --detail "POST /icons" parameters, request body and responses of one endpoint
  python3 swagger_index.py --how                      how to download the files from the HC3

Inputs accepted: a folder of .json/.yml files, single files, or one JSON file holding a list / dict of OpenAPI documents.
YAML needs PyYAML (pip install pyyaml); without it, .yml files are listed by path only.
No network access, no credentials: it only reads local files.
"""
import argparse
import json
import os
import re
import sys

METHODS = ("get", "post", "put", "delete", "patch")

HOW = """How to save the HC3 swagger files (they contain no personal data, only the API description):
Easiest: open http://<hc3-ip>/swagger in Chrome, log in, F12 → Console, paste scripts/export-swagger.js:
it downloads hc3-swagger.json (all API areas in one file). Then:
    python3 swagger_index.py hc3-swagger.json > hc3-api-index.md
Manual way: F12 → Network, reload, open each /assets/docs/hc/<area>.json (or .yml) and save it into one folder.
"""


def parse_yaml(text, label):
    try:
        import yaml
        data = yaml.safe_load(text)
    except ImportError:
        data = None
    except Exception as e:          # e.g. an HTML error page saved with a .yml name
        print(f"skip {label}: not valid YAML ({type(e).__name__})", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        data = {"paths": {p_: {} for p_ in re.findall(r"^  (/[^:\s]+):", text, re.M)}}
    return data


def load_docs(paths):
    docs = []
    for p in paths:
        files = []
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.endswith((".json", ".yml", ".yaml")):
                    files.append(os.path.join(p, f))
        else:
            files.append(p)
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0]
            text = open(f, encoding="utf-8").read()
            if f.endswith(".json"):
                try:
                    data = json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"skip {f}: {e}", file=sys.stderr)
                    continue
                if isinstance(data, list):
                    docs += [(f"{name}[{i}]", d) for i, d in enumerate(data) if isinstance(d, dict)]
                elif isinstance(data, dict) and "paths" not in data and all(isinstance(v, dict) for v in data.values()):
                    for k, v in data.items():          # bundle from export-swagger.js
                        v = parse_yaml(v["yaml"], k) if set(v) == {"yaml"} else v
                        if v is not None:
                            docs.append((k, v))
                else:
                    docs.append((name, data))
            else:
                data = parse_yaml(text, f)
                if data is not None:
                    docs.append((name, data))
    return docs


def endpoints(docs):
    for name, d in docs:
        base = ""
        for s in d.get("servers", []) or []:
            if isinstance(s, dict) and s.get("url", "").startswith("/"):
                base = s["url"].rstrip("/")
                break
        base = base or "/api"
        for path, ops in (d.get("paths") or {}).items():
            if not isinstance(ops, dict) or not any(m in ops for m in METHODS):
                yield name, "?", base + path, "(defined in a referenced file)", {}, d
                continue
            for m in METHODS:
                if m in ops:
                    op = ops[m] or {}
                    yield name, m.upper(), base + path, (op.get("summary") or op.get("description") or "").strip(), op, d


def resolve(ref, doc, depth=0):
    if depth > 6 or not isinstance(ref, str) or not ref.startswith("#/"):
        return {"$ref": ref}
    node = doc
    for part in ref[2:].split("/"):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return expand(node, doc, depth + 1)


def expand(node, doc, depth=0):
    if depth > 6:
        return node
    if isinstance(node, dict):
        if "$ref" in node:
            return resolve(node["$ref"], doc, depth)
        return {k: expand(v, doc, depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        return [expand(v, doc, depth + 1) for v in node]
    return node


def main():
    ap = argparse.ArgumentParser(description="Index / inspect the HC3 swagger (OpenAPI) files")
    ap.add_argument("inputs", nargs="*", help="folder(s) or file(s)")
    ap.add_argument("--grep", help="regex filter on path or summary (case-insensitive)")
    ap.add_argument("--detail", help='one endpoint, e.g. "GET /devices/{deviceID}" (with or without /api)')
    ap.add_argument("--how", action="store_true", help="explain how to download the swagger files")
    a = ap.parse_args()
    if a.how or not a.inputs:
        print(HOW)
        return
    docs = load_docs(a.inputs)
    if a.detail:
        method, _, path = a.detail.partition(" ")
        path = path.strip()
        for name, m, full, summary, op, d in endpoints(docs):
            if m == method.upper() and (full == path or full == "/api" + path or full.endswith(path)):
                print(f"{m} {full}  [{name}]\n{summary}\n")
                print(json.dumps(expand({k: op.get(k) for k in ("parameters", "requestBody", "responses") if k in op}, d),
                                 indent=1, ensure_ascii=False)[:20000])
                return
        sys.exit(f"not found: {a.detail}")
    rx = re.compile(a.grep, re.I) if a.grep else None
    current = None
    count = 0
    for name, m, full, summary, _, _ in endpoints(docs):
        if rx and not (rx.search(full) or rx.search(summary)):
            continue
        if name != current:
            print(f"\n### {name}\n\n| Method and path | Summary |\n|---|---|")
            current = name
        print(f"| `{m} {full}` | {summary.replace('|', '/').splitlines()[0] if summary else ''} |")
        count += 1
    print(f"\n{count} endpoint(s) from {len(docs)} document(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
