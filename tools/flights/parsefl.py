#!/usr/bin/env python3
"""Parse a gfl.js result file into a compact list of flights, cheapest first.
usage: parsefl.py file.json [maxstops] [limit]
Each flight: price (EUR, total for the passengers searched), stops, airline, dep/arr ('6:25 PM'), depday/arrday
('Saturday, August 21'), dur ('3 hr 10 min'), fn ('QS 1285' or 'LH 681 + LH 1626'), via ('FRA')."""
import json, re, sys


def _norm(s):
    return s.replace(" ", " ").replace(" ", " ")


def parse(path, maxstops=1, limit=12):
    d = json.load(open(path))
    seen = {}; out = []
    for r in d.get('rows') or []:
        s = _norm(r['summary']); text = _norm(r['text'])
        m = re.match(r'From ([\d,]+) euros', s)
        if not m: continue
        price = int(m.group(1).replace(',', ''))
        st = re.search(r'(\d+) stops? flight', s)
        stops = 0 if 'Nonstop' in s else int(st.group(1)) if st else 9
        airline = re.search(r'flight with (.+?)\. Leaves', s)
        airline = airline.group(1) if airline else '?'
        dep = re.search(r'Leaves (.+?) at (\d+:\d+ [AP]M) on (\w+, \w+ \d+) and arrives at (.+?) at (\d+:\d+ [AP]M) on (\w+, \w+ \d+)', s)
        dur = re.search(r'Total duration ([^.]+)\.', s)
        fns = []
        for line in text.split('\n'):
            if 'Economy' in line or 'economy' in line:
                mm = re.search(r'([A-Z0-9]{2}) (\d{1,4})\s*$', line.strip())
                if mm: fns.append(mm.group(1) + ' ' + mm.group(2))
        via = re.findall(r'layover\s*([A-Za-z \-]+?) \((\w{3})\)', text)
        key = (airline, dep.group(2) if dep else s[:80], price)
        if key in seen: continue
        seen[key] = 1
        if stops > maxstops: continue
        out.append(dict(price=price, stops=stops, airline=airline, dep=dep.group(2) if dep else '', depday=dep.group(3) if dep else '',
                        arr=dep.group(5) if dep else '', arrday=dep.group(6) if dep else '', dur=dur.group(1) if dur else '',
                        fn=' + '.join(dict.fromkeys(fns)), via=','.join(v[1] for v in via)))
    out.sort(key=lambda x: x['price'])
    return out[:limit]


if __name__ == '__main__':
    p = sys.argv[1]; ms = int(sys.argv[2]) if len(sys.argv) > 2 else 1; lim = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    for x in parse(p, ms, lim):
        nd = f" ({x['arrday']})" if x['arrday'] != x['depday'] else ''
        print(f"€{x['price']:>5} | {x['stops']}st | {x['airline'][:38]:38} | {x['dep']:>8} → {x['arr']:>8}{nd} | {x['dur']:>13} | {x['fn']} | via {x['via']}")
