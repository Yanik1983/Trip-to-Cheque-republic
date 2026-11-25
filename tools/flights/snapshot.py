#!/usr/bin/env python3
"""Turn Google Flights result pages saved by gget.py (HTML) or gfl.js (JSON rows) into one compact price snapshot.

usage: snapshot.py <snapshot.json> <dir> [<dir> ...]   add every <label>.html / <label>.json of the folders to the snapshot
                                                       (searches already in the file and not in the folders are kept)
       snapshot.py <dir>/<label>.html|.json            print the flights of one saved search

Snapshot: { "<FROM>-<TO>_<MMDD>": { "from", "to", "date", "pax", "fetched", "full", "flights": [ flight, ... ] } }, cheapest first.
  full = true when the list is Google's complete list (after "View more flights"), false for the first results page only
  flight: price (EUR, total for all passengers, cheapest fare, bags not included), stops, airline, fn ("QS 1285" or
          "LH 681 + LH 1626"), dep / arr ("18:25", local time), plus (days after departure that it lands), dur (minutes),
          via (connection airports), lay (layover minutes)."""
import datetime
import html as htmlmod
import json
import os
import re
import sys

MONTHS = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}
YEAR = 2027


def _t24(s):
    m = re.match(r"(\d+):(\d+) ([AP])M", s)
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "P" else 0)
    return f"{h:02d}:{m.group(2)}"


def _mins(s):
    h = re.search(r"(\d+) hr", s)
    m = re.search(r"(\d+) min", s)
    return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)


def _day(s):
    m = re.match(r"\w+, (\w+) (\d+)", s)
    return datetime.date(YEAR, MONTHS[m.group(1)], int(m.group(2)))


def key(f):
    return (f["fn"] or f["airline"], f["dep"], f["arr"], f["plus"])


def flight(summary, itin):
    """One flight from the row's spoken summary ("From 711 euros. Nonstop flight with …") and its itinerary code."""
    s = htmlmod.unescape(summary).replace(" ", " ").replace(" ", " ")
    p = re.match(r"From ([\d,]+) euros", s)
    st = re.search(r"(\d+) stops? flight", s)
    stops = 0 if "Nonstop" in s else int(st.group(1)) if st else None
    al = re.search(r"flight with (.+?)\. Leaves", s)
    t = re.search(r"Leaves (.+?) at (\d+:\d+ [AP]M) on (\w+, \w+ \d+) and arrives at (.+?) at (\d+:\d+ [AP]M) on (\w+, \w+ \d+)", s)
    du = re.search(r"Total duration ([^.]+)\.", s)
    if not (p and t and al and du and stops is not None):
        return None
    legs = [x.split("-") for x in (itin or "").split(",") if x.count("-") >= 4]
    d1, d2 = _day(t.group(3)), _day(t.group(6))
    airline = re.sub(r"\. Operated by .*", "", al.group(1))
    return dict(price=int(p.group(1).replace(",", "")), stops=stops, airline=airline, fn=" + ".join(f"{l[2]} {l[3]}" for l in legs),
                dep=_t24(t.group(2)), arr=_t24(t.group(5)), plus=(d2 - d1).days, dur=_mins(du.group(1)), via=[l[1] for l in legs[:-1]],
                lay=[_mins(x) for x in re.findall(r"is an? (.+?) (?:overnight )?layover at", s)], date=d1.isoformat())


def read(path):
    """Return (flights, passengers, full) of one saved search."""
    out, seen, pax, full = [], set(), None, False
    if path.endswith(".json"):
        d = json.load(open(path, encoding="utf8"))
        pairs, pax, full = [(r["summary"], r.get("itin", "")) for r in d["rows"]], 4, bool(d.get("more"))
    else:
        text = open(path, encoding="utf8", errors="replace").read()
        pairs = []
        for chunk in text.split("<li ")[1:]:
            m = re.search(r'aria-label="(From \d[\d,]* euros[^"]*)"', chunk)
            if m:
                it = re.search(r"itinerary=([A-Z0-9,\-]+)", chunk)
                pairs.append((m.group(1), it.group(1) if it else ""))
                p = re.search(r'data-passengers="(\d+)"', chunk)
                pax = int(p.group(1)) if p else pax
    for summary, itin in pairs:
        f = flight(summary, itin)
        if f and key(f) not in seen:            # the same flight is listed under "Top" and "Other"
            seen.add(key(f))
            out.append(f)
    out.sort(key=lambda x: (x["price"], x["dur"]))
    return out, pax, full


def build(snap_path, dirs):
    """Searches found in the folders are (re)built from their saved pages; other searches already in the snapshot stay."""
    old = json.load(open(snap_path, encoding="utf8")) if os.path.exists(snap_path) else {}
    snap = {}
    for d in dirs:
        for name in sorted(os.listdir(d)):
            m = re.match(r"([A-Z]{3})-([A-Z]{3})_(\d\d)(\d\d)\.(html|json)$", name)
            if not m:
                continue
            label, path = name.rsplit(".", 1)[0], os.path.join(d, name)
            flights, pax, full = read(path)
            date = f"{YEAR}-{m.group(3)}-{m.group(4)}"
            if pax != 4 or any(f["date"] != date for f in flights) or not flights:
                print(f"!! {path}: unexpected content (passengers={pax}, rows={len(flights)}) – skipped")
                continue
            fetched = datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
            e = snap.setdefault(label, {"from": m.group(1), "to": m.group(2), "date": date, "pax": pax, "fetched": fetched, "full": False, "flights": []})
            later = fetched >= e["fetched"]
            e["fetched"], e["full"] = max(e["fetched"], fetched), e["full"] or full
            have = {key(f): f for f in e["flights"]}
            for f in flights:
                del f["date"]
                if key(f) not in have:
                    e["flights"].append(f)
                elif later:                        # two readings of the same flight: keep the later price
                    have[key(f)]["price"] = f["price"]
            e["flights"].sort(key=lambda x: (x["price"], x["dur"]))
    kept = [k for k in old if k not in snap]
    snap.update({k: old[k] for k in kept})
    with open(snap_path, "w", encoding="utf8") as fh:
        fh.write("{\n" + ",\n".join(
            f' {json.dumps(k)}: {{"from": {json.dumps(v["from"])}, "to": {json.dumps(v["to"])}, "date": {json.dumps(v["date"])}, "pax": {v["pax"]}, '
            f'"fetched": {json.dumps(v["fetched"])}, "full": {json.dumps(v["full"])}, "flights": [\n'
            + ",\n".join("   " + json.dumps(f, ensure_ascii=False) for f in v["flights"]) + "\n ]}" for k, v in sorted(snap.items())) + "\n}\n")
    print(f"{len(snap)} searches in {snap_path}" + (f" ({len(kept)} kept from the existing file)" if kept else ""))
    return snap


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        build(sys.argv[1], sys.argv[2:])
    elif len(sys.argv) == 2:
        fl, pax, full = read(sys.argv[1])
        print("passengers:", pax, "| complete list" if full else "| first page")
        for f in fl:
            print(f"€{f['price']:>5} {f['stops']}st {f['airline'][:26]:26} {f['fn']:22} {f['dep']}→{f['arr']}{'+%d' % f['plus'] if f['plus'] else '  '} "
                  f"{f['dur'] // 60}h{f['dur'] % 60:02d} via {','.join(f['via']) or '-'} lay {f['lay']}")
    else:
        sys.exit(__doc__)
