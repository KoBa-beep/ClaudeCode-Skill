// HC3 inventory export — paste into the browser console while on the HC3 web page (http://<hc3-ip>, F12 → Console).
// Downloads hc3-inventory.json: devices (id, name, exact type, room, parent node, interfaces, actions, a WHITELIST of
// properties), rooms, sections, scenes (names only), global variable names, users (id, name, type), firmware.
// Privacy by design: no QuickApp variables (they hold passwords / tokens), no scene code, no e-mails, no serial number,
// no network settings. The password is asked only if the browser session is not already logged in, and never stored.
(async () => {
  let auth = {};
  const get = async (path) => {
    let r = await fetch("/api" + path, { headers: auth });
    if (r.status === 401 && !auth.Authorization) {
      const u = prompt("HC3 user", "admin"), p = prompt("HC3 password (not stored)");
      auth = { Authorization: "Basic " + btoa(u + ":" + p) };
      r = await fetch("/api" + path, { headers: auth });
    }
    return r.ok ? r.json() : [];
  };
  const KEEP = ["value", "state", "dead", "batteryLevel", "deviceIcon", "manufacturer", "model", "zwaveCompany",
    "zwaveVersion", "categories", "unit", "configured", "deviceRole", "isLight", "lastLoggedUser", "productInfo",
    "userDescription", "energy", "power"];
  const devices = (await get("/devices")).map(d => {
    const props = {};
    for (const k of KEEP) if (d.properties && d.properties[k] !== undefined) props[k] = d.properties[k];
    return { id: d.id, name: d.name, type: d.type, baseType: d.baseType, roomID: d.roomID, parentId: d.parentId,
      enabled: d.enabled, visible: d.visible, interfaces: d.interfaces, actions: Object.keys(d.actions || {}),
      properties: props };
  });
  const rooms = (await get("/rooms")).map(r => ({ id: r.id, name: r.name, sectionID: r.sectionID }));
  const sections = (await get("/sections")).map(s => ({ id: s.id, name: s.name }));
  const scenes = (await get("/scenes")).map(s => ({ id: s.id, name: s.name, type: s.type, roomId: s.roomId,
    enabled: s.enabled, mode: s.mode }));
  const globals = (await get("/globalVariables")).map(g => ({ name: g.name, isEnum: g.isEnum }));
  const users = (await get("/users")).map(u => ({ id: u.id, name: u.name, type: u.type }));
  const info = await get("/settings/info");
  const out = { exportedAt: new Date().toISOString(), hc3: { softVersion: info.softVersion },
    sections, rooms, devices, scenes, globalVariables: globals, users };
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "hc3-inventory.json"; a.click();
  console.log(`Done: ${devices.length} devices, ${rooms.length} rooms, ${scenes.length} scenes → hc3-inventory.json`);
})();
