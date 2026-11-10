// Exporte chaque svg/*.svg en PNG transparent : png/40/ (taille native) et png/16/ (arbre classique).
// Usage : node export_png.js   (nécessite Playwright + Chromium)
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const SIZES = [40, 16];
(async () => {
  const dir = path.join(__dirname, 'svg');
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.svg')).sort();
  const browser = await chromium.launch();
  for (const size of SIZES) {
    const out = path.join(__dirname, 'png', String(size));
    fs.mkdirSync(out, { recursive: true });
    const page = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
    for (const f of files) {
      const svg = fs.readFileSync(path.join(dir, f), 'utf8');
      await page.setContent(`<html><body style="margin:0;background:transparent">
        <img src="data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}" width="${size}" height="${size}" style="display:block"></body></html>`);
      await page.waitForFunction(() => document.images[0].complete);
      await page.screenshot({ path: path.join(out, f.replace('.svg', '.png')), omitBackground: true, clip: { x: 0, y: 0, width: size, height: size } });
    }
    await page.close();
  }
  await browser.close();
  console.log(`${files.length} icônes exportées en ${SIZES.join(' et ')} px`);
})();
