#!/usr/bin/env python3
"""Static checks for a meta (jac459/meta) NEEO driver file.

Usage: check_driver.py DRIVER.json [--previous OLD.json]

Errors (exit code 1) are things that break the driver, the remote or meta; warnings deserve a look.
--previous compares visible components with the installed version (version bump, removals needing a reinstall).
"""
import json
import re
import sys

TYPES = {"http-get", "http-rest", "http-post", "http-get-soap", "static", "cli", "repl", "webSocket", "socketIO",
         "jsontcp", "mqtt", "wol", "mDNS", "android"}
DEVICE_TYPES = {"ACCESSORY", "AUDIO", "AVRECEIVER", "DVB", "DVD", "GAMECONSOLE", "HDMISWITCH", "LIGHT", "MEDIAPLAYER",
                "MUSICPLAYER", "PROJECTOR", "TUNER", "TV", "VOD", "SOUNDBAR"}
SENSOR_KINDS = ("labels", "switches", "sliders", "images", "sensors")
SPECIAL = {"__INITIALISE", "__CLEANUP", "__PERSIST", "__WRAPUP"}
SYSTEM_VARS = {"Result", "RegistrationCode", "NeeoBrainIP", "MetaIP", "LocalDevices", "LocalByMacDevices", "ListIndex"}
ALNUM = re.compile(r"^[A-Za-z0-9]+$")
VAR_REF = re.compile(r"\$([A-Za-z][A-Za-z0-9]*)")

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def commands(node, path):
    """Yield (path, command dict) for every object that carries a command 'type'."""
    if isinstance(node, dict):
        if isinstance(node.get("type"), str) and ("command" in node or "queryresult" in node):
            yield path, node
        for k, v in node.items():
            yield from commands(v, path + "/" + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from commands(v, "%s[%d]" % (path, i))


def strings(node, path, skip=("queryresult",)):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in skip:
                continue
            yield from strings(v, path + "/" + str(k), skip)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from strings(v, "%s[%d]" % (path, i), skip)
    elif isinstance(node, str):
        yield path, node


def scopes(d):
    """The root, plus the template when there is one (v2 drivers put components in the template)."""
    out = [("", d)]
    if isinstance(d.get("template"), dict):
        out.append(("template", d["template"]))
    return out


def visible_components(d):
    comps = set()
    for _, s in scopes(d):
        for kind in SENSOR_KINDS + ("directories",):
            for name in (s.get(kind) or {}):
                comps.add("%s:%s" % (kind, name))
        for name in (s.get("buttons") or {}):
            if not name.startswith("__"):
                comps.add("buttons:" + name)
    return comps


def presses(btn):
    return [t for e in (btn.get("evaldo") or []) for t in (e.get("then"), e.get("or")) if t]


def check(d, filename):
    if "-flow" in filename.lower():
        err("file name contains '-flow': reserved for Node-RED flows, a meta driver must not carry it")
    for key in ("name", "manufacturer", "type", "version"):
        if key not in d:
            err("missing top-level key '%s'" % key)
    if "type" in d and d["type"] not in DEVICE_TYPES:
        err("unknown NEEO device type %r (valid: %s)" % (d["type"], ", ".join(sorted(DEVICE_TYPES))))
    if "version" in d and not isinstance(d["version"], int):
        err("'version' must be an integer")

    tpl = d.get("template")
    if tpl is not None:
        for key in ("dynamicname", "dynamicid"):
            if key not in tpl:
                err("template: missing '%s' (mandatory)" % key)
        if "discover" not in d:
            err("a template needs a 'discover' section")
    if "register" in d and "discover" not in d:
        err("'register' requires 'discover'")

    # variables
    declared = {}
    for _, s in scopes(d):
        for kind in ("variables", "persistedvariables"):
            for k, v in (s.get(kind) or {}).items():
                declared[k] = v
    names = sorted(declared)
    for a in names:
        for b in names:
            if a != b and b.startswith(a):
                warn("variable '%s' is a prefix of '%s': '$%s' may be read as '$%s' + text" % (a, b, b, a))

    # components
    bound = {}
    for where, s in scopes(d):
        for kind in SENSOR_KINDS:
            for name, comp in (s.get(kind) or {}).items():
                if not ALNUM.match(name):
                    err("%s '%s': component names must be letters and digits only (the remote crashes at sync)" % (kind, name))
                if kind == "labels" and isinstance(comp, dict):
                    for k in ("listen", "actionlisten"):
                        if comp.get(k):
                            bound[comp[k]] = name
        for name in (s.get("buttons") or {}):
            if "+" in name or re.search(r"[^\x00-\x7f]", name):
                warn("button '%s': avoid '+' and accents in button names (keep them in 'label')" % name)

    for var, label in bound.items():
        if var not in declared:
            warn("label '%s' listens to undeclared variable '%s'" % (label, var))

    # evalwrite values into label variables (an initial "" is harmless: labelHelper starts at '' and only pushes changes;
    # going back from a text to "" is what stops meta v1.2.0)
    for path, node in _evalwrites(d, ""):
        var, value = node.get("variable"), node.get("value")
        if var in bound:
            if value == "":
                err("%s: writes \"\" into '%s' (label '%s'): stops meta v1.2.0, write \" \"" % (path, var, bound[var]))
            elif isinstance(value, str) and value.startswith("DYNAMIK") and re.search(r'(\?|:)\s*""\s*(:|;|$)|""\s*;?\s*$', value):
                warn("%s: this DYNAMIK can return \"\" into '%s' (label '%s'); return \" \" instead" % (path, var, bound[var]))
            elif isinstance(value, str) and "$Result" in value and "replace" not in value:
                warn("%s: external text written to '%s' (label '%s') without sanitizing (\" \\ $ and control characters), unless the source already does it" % (path, var, bound[var]))

    # command types and polling
    for path, cmd in commands(d, ""):
        t = cmd.get("type")
        if t not in TYPES:
            hint = [x for x in TYPES if x.lower() == str(t).lower()]
            err("%s: unknown command type %r%s" % (path or "/", t, " (did you mean %r? types are case-sensitive)" % hint[0] if hint else ""))
        if "pooltime" in cmd:
            try:
                if int(cmd["pooltime"]) < 3000:
                    warn("%s: pooltime %s ms < 3000" % (path, cmd["pooltime"]))
            except (TypeError, ValueError):
                warn("%s: pooltime is not a number" % path)

    # button graph
    for where, s in scopes(d):
        buttons = s.get("buttons") or {}
        if not buttons:
            continue
        for name, btn in buttons.items():
            for target in presses(btn):
                if target not in buttons and target not in SPECIAL:
                    err("button '%s' presses unknown button '%s'" % (name, target))
        listeners = s.get("listeners") or {}
        if listeners:
            check_guard(s, buttons, listeners)
        for dname, directory in (s.get("directories") or {}).items():
            feeders = (directory or {}).get("feeders") or {}
            for path, row in commands(directory, "directories/" + dname):
                for target in [row.get("itemaction")] + [e.get("then") for e in (row.get("evalnext") or [])] + [e.get("or") for e in (row.get("evalnext") or [])]:
                    if target and target != "." and target not in feeders:
                        err("%s: feeder '%s' does not exist in directory '%s'" % (path, target, dname))
                for target in presses(row):
                    if target not in buttons and target not in SPECIAL:
                        err("%s: presses unknown button '%s'" % (path, target))

    # variable references
    known = set(declared) | SYSTEM_VARS
    seen = set()
    for path, text in strings(d, ""):
        for ref in VAR_REF.findall(text):
            if ref not in known and ref not in seen:
                seen.add(ref)
                glued = [k for k in known if ref.startswith(k)]
                warn("%s: '$%s' is not a declared variable%s" % (path, ref, (" (glued to text after '$%s'?)" % max(glued, key=len)) if glued else ""))


def _evalwrites(node, path):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "evalwrite" and isinstance(v, list):
                for i, e in enumerate(v):
                    if isinstance(e, dict):
                        yield "%s/evalwrite[%d]" % (path, i), e
            else:
                yield from _evalwrites(v, path + "/" + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _evalwrites(v, "%s[%d]" % (path, i))


def reaches(buttons, start, goal, seen=None):
    seen = seen or set()
    if start in seen:
        return False
    seen.add(start)
    for t in presses(buttons.get(start) or {}):
        if t == goal or (t in buttons and reaches(buttons, t, goal, seen)):
            return True
    return False


def check_guard(s, buttons, listeners):
    has_mqtt = any((l or {}).get("type") == "mqtt" for l in listeners.values())
    variables = s.get("variables") or {}
    if "ListenerOn" not in variables or "__LISTEN" not in buttons:
        warn("listeners without the ListenerOn guard (variable 'ListenerOn' + button '__LISTEN'): they will not start after a meta restart, or will start several times")
    else:
        lis = buttons["__LISTEN"]
        if not any(w.get("variable") == "ListenerOn" and w.get("value") is True for w in lis.get("evalwrite") or []) or "__INITIALISE" not in presses(lis):
            err("'__LISTEN' must set ListenerOn to true and press __INITIALISE")
        unguarded = [n for n, b in buttons.items() if not n.startswith("__") and "__LISTEN" not in presses(b)]
        for kind in ("sliders", "switches"):
            unguarded += ["%s %s" % (kind[:-1], n) for n, c in (s.get(kind) or {}).items() if "__LISTEN" not in presses(c or {})]
        if unguarded:
            warn("%d visible control(s) do not start the listener guard (add {\"test\":\"DYNAMIK !$ListenerOn\",\"then\":\"__LISTEN\"}): %s"
                 % (len(unguarded), ", ".join(unguarded[:12]) + (" ..." if len(unguarded) > 12 else "")))
    for name, btn in buttons.items():
        if name != "__LISTEN" and "__INITIALISE" in presses(btn):
            warn("button '%s' presses __INITIALISE directly: go through the guard (__LISTEN) so listeners start once" % name)
    if has_mqtt:
        for name in buttons:
            if not name.startswith("__") and reaches(buttons, name, "__CLEANUP"):
                err("button '%s' leads to __CLEANUP while an mqtt listener exists: each stop/start stacks a message handler" % name)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    try:
        d = json.load(open(path, encoding="utf-8"))
    except ValueError as e:
        print("ERROR invalid JSON: %s" % e)
        return 1
    if isinstance(d, list):
        print("ERROR this is a JSON list: a Node-RED flow (import it into Node-RED, name it *-flow.json), not a meta driver")
        return 1
    if not isinstance(d, dict):
        print("ERROR a meta driver is a JSON object")
        return 1
    check(d, path.rsplit("/", 1)[-1])
    if "--previous" in argv:
        old = json.load(open(argv[argv.index("--previous") + 1], encoding="utf-8"))
        added, removed = visible_components(d) - visible_components(old), visible_components(old) - visible_components(d)
        if added and not (isinstance(d.get("version"), int) and isinstance(old.get("version"), int) and d["version"] > old["version"]):
            err("visible components added without a version bump: %s" % ", ".join(sorted(added)))
        if removed:
            warn("visible components removed or renamed (the Brain keeps them until the device is deleted and re-added): %s" % ", ".join(sorted(removed)))
        if added:
            warn("new components: check in the Brain (/v1/projects/home) that they really appear after the update")
    for m in errors:
        print("ERROR   " + m)
    for m in warnings:
        print("WARNING " + m)
    print("%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
