// Headless check of the published pages and the app (served locally, e.g. python3 -m http.server 8765 in the repo root).
// usage: node verify.js http://localhost:8765 cz:v9 hu:v4 ...   [--shots <dir>]
// For every plan page: no script errors, no broken photos, both languages present, version menu and tabs sane.
// For the app: every destination opens without errors, shows the total of its data file and the default flights.
const fs = require('fs');
let chromium;
for (const p of ['/opt/node22/lib/node_modules/playwright', '/opt/node-tools/node_modules/playwright', 'playwright']) {
  try { ({ chromium } = require(p)); break; } catch (e) { /* next */ }
}
const args = process.argv.slice(2);
const base = args.shift();
const shots = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null;
const pages = args.filter(a => /^[a-z]{2}:v\d+$/.test(a));
(async () => {
  const browser = await chromium.launch();
  let bad = 0;
  const note = (ok, msg) => { if (!ok) bad++; console.log((ok ? 'ok   ' : 'FAIL ') + msg); };
  for (const pv of pages) {
    const [cc, ver] = pv.split(':');
    for (const lang of ['he', 'en']) {
      const ctx = await browser.newContext({ viewport: { width: 412, height: 900 }, deviceScaleFactor: 1 });
      await ctx.route(u => !u.href.startsWith(base), r => r.abort());      // no outside requests: only our own files are checked
      const page = await ctx.newPage();
      const errs = [];
      page.on('pageerror', e => errs.push(String(e)));
      await page.goto(`${base}/${cc}/${ver}/index.html#${lang}`, { waitUntil: 'load' });
      await page.waitForTimeout(400);
      const r = await page.evaluate(async (lang) => {
        const vis = el => !!(el && el.offsetParent);
        const block = document.querySelector('.lang-' + lang), other = document.querySelector('.lang-' + (lang === 'he' ? 'en' : 'he'));
        const imgs = Array.from(block.querySelectorAll('img'));
        await Promise.all(imgs.map(i => i.complete ? 0 : new Promise(res => { i.onload = i.onerror = res; i.loading = 'eager'; })));
        return { shown: vis(block), otherHidden: !vis(other), imgs: imgs.length, broken: imgs.filter(i => !i.naturalWidth).map(i => i.getAttribute('src')),
                 opts: Array.from(document.querySelectorAll('#ver option')).map(o => o.value + ' | ' + o.textContent), cur: (document.querySelector('.dest[aria-current]') || {}).textContent,
                 tabs: document.querySelectorAll('.dbar .dest').length, total: (block.querySelector('.facts b') || {}).textContent, h1: block.querySelector('h1').textContent,
                 days: block.querySelectorAll('section.day').length, wide: document.documentElement.scrollWidth > window.innerWidth + 2 };
      }, lang);
      note(!errs.length && r.shown && r.otherHidden && !r.broken.length && r.days === 10 && r.tabs === 7 && !r.wide,
        `${cc}/${ver} [${lang}] total ${r.total} · ${r.days} days · ${r.imgs} photos (${r.broken.length} broken) · tabs ${r.tabs} (${r.cur}) · versions ${r.opts.length}` +
        (errs.length ? ' · errors: ' + errs.join('; ') : '') + (r.broken.length ? ' · broken: ' + r.broken.join(',') : '') + (r.wide ? ' · page scrolls sideways' : ''));
      if (lang === 'en') console.log('       ' + r.opts.slice(0, 4).join('  ||  '));
      if (shots) await page.screenshot({ path: `${shots}/${cc}_${ver}_${lang}.png` });
      await ctx.close();
    }
  }
  // the app: first the destination table in its source, then every destination opened for real
  const src = fs.readFileSync(`${__dirname}/../../app/index.html`, 'utf8');
  const ctx = await browser.newContext({ viewport: { width: 412, height: 900 }, deviceScaleFactor: 1 });
  await ctx.route(u => !u.href.startsWith(base) && !u.hostname.endsWith('cdnjs.cloudflare.com'), r => r.abort());   // map library only
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  await page.goto(`${base}/app/index.html`, { waitUntil: 'load' });
  await page.waitForTimeout(1500);
  for (const m of src.matchAll(/\{id:'(\w+)',[^}]*?data:'([^']+)',total:([\d.]+),[^}]*?report:'([^']+)'\}/g)) {
    const [, id, file, total, report] = m;
    const want = JSON.parse(fs.readFileSync(`${__dirname}/../../app/${file}`, 'utf8'));
    const o = want.flights.choices.out.filter(c => c.default)[0], b = want.flights.choices.back.filter(c => c.default)[0];
    await page.click(`#dsel [data-dest="${id}"]`);
    await page.waitForTimeout(700);
    await page.click('[data-tab="flights"]');
    await page.waitForTimeout(500);
    const r = await page.evaluate(() => ({ text: document.body.innerText, opts: Array.from(document.querySelectorAll('select[data-fsel] option')).map(x => x.textContent),
                                           pressed: (document.querySelector('#dsel [aria-pressed="true"]') || {}).textContent }));
    const starred = r.opts.filter(x => x.startsWith('★'));
    const okFlights = starred.length === 2 && starred[0].includes(o.fn) && starred[1].includes(b.fn) && r.text.includes(o.fn) && r.text.includes(b.fn);
    const okTotal = Math.abs(Number(total) - want.budget.total_eur) < 0.005 && (r.pressed || '').includes(Math.round(want.budget.total_eur).toLocaleString('en-US'));
    const okLink = report.includes(`/${id}/${want.version.id}/`) && fs.existsSync(`${__dirname}/../../app/${report}`);
    note(okFlights && okTotal && okLink, `app ${id}: ${want.version.id} · total ${total} (data ${want.budget.total_eur}) · tab "${(r.pressed || '').replace(/\s+/g, ' ')}" · plan page ${report}` +
      ` · choices ${want.flights.choices.out.length}/${want.flights.choices.back.length} · default ${o.fn} ${o.dep} + ${b.fn} ${b.dep}` + (okFlights ? '' : ' · FLIGHT PICKER MISMATCH ' + JSON.stringify(starred)));
    if (shots) await page.screenshot({ path: `${shots}/app_${id}.png` });
  }
  note(!errs.length, 'app script errors: ' + (errs.join('; ') || 'none'));
  await browser.close();
  console.log(bad ? `${bad} problem(s)` : 'all checks passed');
  process.exit(bad ? 1 : 0);
})();
