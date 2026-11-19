// Google Flights reader with a real (headless) browser, for the FULL result list of a search: it opens the public
// result page and presses "View more flights", exactly as a person would. Search only: it never books, logs in or
// solves CAPTCHAs. For the short first-page list a plain request is enough – see gget.py, which is much lighter.
//
// usage: node gfl.js <outdir> [--pace 50] [--stops 1] "label|FROM|TO|YYYY-MM-DD" ... | @jobs.txt
// Writes <outdir>/<label>.json = { label, from, to, date, url, rows: [{summary, itin}], more, at }.
// A label that already has a file with rows is skipped, so re-running the same command only retries the failures.
// Meant for a handful of look-ups: one tab, one search at a time, a pause between searches, telemetry requests switched
// off. If Google answers with its "unusual traffic" page (HTTP 429) it stops at once (exit code 3) - wait and try later.
const fs = require('fs');
const { execFileSync } = require('child_process');
let chromium;
for (const p of ['/opt/node22/lib/node_modules/playwright', '/opt/node-tools/node_modules/playwright', 'playwright']) {
  try { ({ chromium } = require(p)); break; } catch (e) { /* try the next location */ }
}
if (!chromium) { console.error('playwright not found'); process.exit(2); }

const args = process.argv.slice(2);
const outdir = args.shift();
const opt = { pace: 50, stops: 1 };
const jobs = [];
while (args.length) {
  const a = args.shift();
  if (a.startsWith('--')) opt[a.slice(2)] = Number(args.shift());
  else if (a.startsWith('@')) fs.readFileSync(a.slice(1), 'utf8').split('\n').filter(l => l.split('|').length === 4).forEach(l => jobs.push(l.trim()));
  else jobs.push(a);
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
const done = f => { try { const j = JSON.parse(fs.readFileSync(f, 'utf8')); return Array.isArray(j.rows) && j.rows.length > 0; } catch (e) { return false; } };
const stamp = () => new Date().toISOString().slice(11, 19);
// the search URL is built by gget.py (one place that knows the address format)
const urlFor = job => execFileSync('python3', ['-c',
  'import sys,os;sys.path.insert(0,os.path.dirname(sys.argv[1]));import gget;print(gget.url_for(sys.argv[2],{"stops":int(sys.argv[3]),"tab":"best"}))',
  __filename, job, String(opt.stops)], { encoding: 'utf8' }).trim();

(async () => {
  fs.mkdirSync(outdir, { recursive: true });
  const todo = jobs.filter(j => !done(`${outdir}/${j.split('|')[0]}.json`));
  console.log(stamp(), `jobs: ${jobs.length}, to do: ${todo.length}`);
  if (!todo.length) return;
  const launch = process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {};
  const browser = await chromium.launch(launch);
  const ctx = await browser.newContext({ locale: 'en-US', timezoneId: 'Asia/Jerusalem', viewport: { width: 1400, height: 2200 } });
  // telemetry, ads and helper frames are not needed to read the list – do not send them at all
  await ctx.route(/(play\.google\.com|ogads-pa|googletagmanager|doubleclick|csp\.withgoogle|google\.com\/log|generate_204|\/browserinfo|\/bscframe|gen_204)/, r => r.abort());
  const page = await ctx.newPage();
  let nreq = 0; page.on('request', r => { if (/\/\/www\.google\.com/.test(r.url())) nreq++; });
  const count = () => page.$$eval('li', lis => lis.filter(li => li.querySelector('[aria-label^="From "]')).length);
  let first = true;
  for (const job of todo) {
    const [label, from, to, date] = job.split('|');
    const file = `${outdir}/${label}.json`;
    let result = null, attempt = 0;
    while (!result && attempt < 2) {
      attempt++;
      if (!first) await sleep(opt.pace * 1000 * (0.75 + 0.5 * Math.random()));
      first = false;
      nreq = 0;
      let blocked = false;
      try {
        const resp = await page.goto(urlFor(job), { waitUntil: 'domcontentloaded', timeout: 60000 });
        if ((resp && resp.status() === 429) || page.url().includes('/sorry/')) blocked = true;
        let n = 0;
        for (let i = 0; i < 15 && !blocked; i++) {
          await page.waitForTimeout(1500);
          if (page.url().includes('/sorry/')) { blocked = true; break; }
          n = await count();
          if (n > 0) break;
        }
        if (!blocked && n > 0) {
          await page.waitForTimeout(1500);
          let more = 0;
          const btn = page.getByRole('button', { name: /more flights/i });
          if (await btn.count()) {
            await btn.first().click().catch(() => {});
            // the list is re-drawn after the click: wait until the row count stops changing
            let prev = -1;
            for (let i = 0; i < 14; i++) { await page.waitForTimeout(1500); const c = await count(); if (c > 0 && c === prev) break; prev = c; }
            more = 1;
          }
          if (page.url().includes('/sorry/')) blocked = true;
          const rows = await page.$$eval('li', lis => lis.map(li => {
            const a = li.querySelector('[aria-label^="From "]');
            if (!a) return null;
            const e = li.querySelector('[data-travelimpactmodelwebsiteurl]');
            return { summary: a.getAttribute('aria-label'), itin: e ? (e.getAttribute('data-travelimpactmodelwebsiteurl').split('itinerary=')[1] || '') : '' };
          }).filter(Boolean));
          if (!blocked && rows.length > 0) result = { label, from, to, date, stops_filter: opt.stops, url: page.url(), rows, more, at: new Date().toISOString() };
        }
      } catch (e) { console.log(stamp(), label, 'error', String(e).slice(0, 120)); }
      if (blocked) {
        console.log(stamp(), label, 'BLOCKED by Google (429) - stopping; try again later');
        await browser.close();
        process.exit(3);
      }
    }
    if (result) fs.writeFileSync(file, JSON.stringify(result, null, 1));
    console.log(stamp(), label, result ? `ok rows=${result.rows.length} more=${result.more} requests=${nreq}` : 'FAILED');
  }
  await browser.close();
})();
