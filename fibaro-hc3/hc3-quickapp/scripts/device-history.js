// Device history — paste into the browser console on the HC3 web page (F12 → Console), then call:
//     hc3History(210)            last 100 events of device 210
//     hc3History(210, 300)       last 300
// Prints a table (time, property, old → new value) to diagnose a flapping / unreachable / battery module.
// Use the id of the functional device AND of its hidden parent node (parentId), both carry useful events.
window.hc3History = async (id, n = 100) => {
  const r = await fetch(`/api/events/history?objectType=device&objectId=${id}&numberOfRecords=${n}`);
  if (!r.ok) { console.log("HTTP " + r.status + " (log in to the HC3 page first)"); return; }
  const list = await r.json();
  const rows = (Array.isArray(list) ? list : list.events || []).map(e => ({
    time: new Date((e.timestamp || 0) * 1000).toLocaleString(),
    event: e.type,
    property: e.data && (e.data.property || e.data.propertyName),
    old: e.data && JSON.stringify(e.data.oldValue),
    new: e.data && JSON.stringify(e.data.newValue),
  }));
  console.table(rows);
  const d = await (await fetch(`/api/devices/${id}`)).json();
  console.log(`${d.name} — type ${d.type}, parent ${d.parentId}, dead=${d.properties.dead}, battery=${d.properties.batteryLevel}`);
  return rows.length;
};
console.log("Ready: hc3History(<deviceId>[, count])");
