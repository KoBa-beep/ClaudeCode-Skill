// HC3 swagger export — open http://<hc3-ip>/swagger, log in, then paste this into the console (F12 → Console).
// Downloads hc3-swagger.json = { "<area>": <OpenAPI document>, … } (API description only, no personal data).
// Index it with:  python3 swagger_index.py hc3-swagger.json
(async () => {
  let urls = [];
  try { urls = (window.ui && ui.getConfigs().urls) || []; } catch (e) { /* not a multi-spec swagger page */ }
  if (!urls.length) {
    // fallback: every spec file the page already loaded
    urls = performance.getEntriesByType("resource").map(r => r.name)
      .filter(u => /\/assets\/docs\/.*\.(json|ya?ml)$/.test(u)).map(u => ({ url: u, name: u }));
  }
  if (!urls.length) { console.log("No spec list found: use F12 → Network instead (see swagger_index.py --how)."); return; }
  const out = {};
  for (const u of urls) {
    const name = (u.name || u.url).replace(/^.*\/assets\/docs\/hc\//, "").replace(/\.(json|ya?ml)$/, "");
    try {
      const r = await fetch(u.url);
      const text = await r.text();
      try { out[name] = JSON.parse(text); } catch (e) { out[name] = { yaml: text }; }
    } catch (e) { console.log("skip " + u.url + ": " + e); }
  }
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "hc3-swagger.json"; a.click();
  console.log(`Done: ${Object.keys(out).length} API areas → hc3-swagger.json`);
})();
