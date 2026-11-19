// Google Flights scraper (headless Chromium via Playwright). Search only: it never books or logs in.
// usage: node gfl.js <outdir> "label|query" "label|query" ...
//   e.g. node gfl.js out "TLV-PRG_0821|Flights from TLV to PRG on 2027-08-21 one way 2 adults 2 children"
// Writes <outdir>/<label>.json = { label, q, state, url, rows: [{summary, text}], header }.
// A label whose file already holds rows is skipped, so re-running the same command retries only the failures.
const fs = require('fs');
let chromium;
for (const p of ['/opt/node22/lib/node_modules/playwright', '/opt/node-tools/node_modules/playwright', 'playwright']) {
  try { ({ chromium } = require(p)); break; } catch (e) { /* try the next location */ }
}
if (!chromium) { console.error('playwright not found'); process.exit(2); }

const done = f => { try { const j = JSON.parse(fs.readFileSync(f, 'utf8')); return Array.isArray(j.rows) && (j.rows.length > 0 || j.state === 'none-found'); } catch (e) { return false; } };

(async () => {
  const outdir = process.argv[2]; fs.mkdirSync(outdir, { recursive: true });
  const jobs = process.argv.slice(3).map(s => { const i = s.indexOf('|'); return [s.slice(0, i), s.slice(i + 1)]; });
  const launch = process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {};
  const browser = await chromium.launch(launch);
  const ctx = await browser.newContext({ locale: 'en-US', timezoneId: 'Asia/Jerusalem', viewport: { width: 1400, height: 2200 } });
  await ctx.route(/(play\.google\.com|ogads-pa|googletagmanager|doubleclick|csp\.withgoogle)/, r => r.abort());
  for (const [label, q] of jobs) {
    const file = `${outdir}/${label}.json`;
    if (done(file)) { console.log(label, 'cached'); continue; }
    let attempt = 0, result = null;
    while (attempt < 3 && !result) {
      attempt++;
      const page = await ctx.newPage();
      try {
        await page.goto('https://www.google.com/travel/flights?hl=en&gl=IL&curr=EUR&q=' + encodeURIComponent(q), { waitUntil: 'domcontentloaded', timeout: 60000 });
        let state = 'none';
        for (let i = 0; i < 25; i++) {
          await page.waitForTimeout(2000);
          const n = await page.$$eval('[aria-label]', els => els.filter(e => (e.getAttribute('aria-label') || '').startsWith('From ')).length);
          if (n > 0) { state = 'ok'; break; }
          const body = await page.innerText('body');
          if (body.includes('something went wrong')) { state = 'oops'; break; }
          if (/No (options|flights|results) (match|found)/i.test(body)) { state = 'none-found'; break; }
        }
        if (state === 'oops') { await page.close(); continue; }
        await page.waitForTimeout(3000);
        const more = page.getByRole('button', { name: /more flights/i });
        if (await more.count()) { await more.first().click().catch(() => {}); await page.waitForTimeout(5000); }
        // expand the details of the first rows (flight numbers and layovers are only in the expanded text)
        const btns = page.locator('button[aria-label^="Flight details"]');
        const nb = await btns.count();
        for (let i = 0; i < Math.min(nb, 40); i++) { await btns.nth(i).click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(250); }
        await page.waitForTimeout(1500);
        const rows = await page.$$eval('li', lis => lis.map(li => {
          const a = li.querySelector('[aria-label^="From "]');
          return a ? { summary: a.getAttribute('aria-label'), text: li.innerText } : null;
        }).filter(Boolean));
        const header = (await page.innerText('body')).slice(0, 1500);
        result = { label, q, state, url: page.url(), rows, header };
        if (rows.length === 0 && state !== 'none-found') result = null;
      } catch (e) { result = null; }
      await page.close();
    }
    fs.writeFileSync(file, JSON.stringify(result || { label, q, err: 'failed' }, null, 1));
    console.log(label, result ? `${result.state} rows=${result.rows.length}` : 'FAILED');
  }
  await browser.close();
})();
