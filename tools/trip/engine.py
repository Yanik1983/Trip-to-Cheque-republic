#!/usr/bin/env python3
"""Price comparison for the trips: cheapest flights that fit the plan, hotel totals per start date, cheapest dates.

usage: engine.py <snapshot-dir> [cc ...]        e.g. engine.py tools/data/2026-11-19 cz hu
Reads <snapshot-dir>/base/trip-data-<cc>.json (the plan as published before the update), <snapshot-dir>/flights.json (Google Flights lists, see
tools/flights/snapshot.py) and <snapshot-dir>/hotel_matrix_<cc>.jsonl (Booking.com totals per stay and date) and prints,
for every start date that has flight lists for both directions, the cheapest combination.

The rules (the same ones the plans were built on):
  flights   total price for 2 adults + 2 children, two one-way tickets, at most 1 stop, no departure before 04:00 when
            there is a connection, and the flight has to land on the day it leaves
  outbound  evening shape: lands 16:00 or later and early enough to be in bed by about midnight
            (landing + 1 h + the drive to the first bed; no limit when the first bed is at or next to the airport)
  bags      estimate per direction: Wizz Air 200 EUR, other airlines 160 EUR
  hotels    live total for the stays of that start date, free cancellation, air-conditioned
  car       the plan's estimate (the same for every date)."""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# stays of the evening-arrival shape: (hotel id, first night offset, check-out offset) counted from the start date
TRIPS = {
    "cz": dict(airport="PRG", stays=[("hotel_hiair", 0, 1), ("hotel_jedeme", 1, 5), ("hotel_nova", 5, 9)]),
    "hu": dict(airport="BUD", stays=[("hotel_ibisair", 0, 1), ("hotel_forras", 1, 5), ("hotel_westside", 5, 9)]),
    "pl": dict(airport="KRK", stays=[("hotel_hampton", 0, 1), ("hotel_goralski", 1, 5), ("hotel_playroom", 5, 9)]),
    "ro": dict(airport="OTP", stays=[("hotel_carpathia", 0, 5), ("hotel_maison", 5, 9)]),
    "si": dict(airport="LJU", stays=[("hotel_bled", 0, 5), ("hotel_lj", 5, 9)]),
    "ge": dict(airport="TBS", stays=[("hotel_tb1", 0, 1), ("hotel_bj", 1, 5), ("hotel_tb2", 5, 9)]),
    "de": dict(airport="ZRH", stays=[("hotel_schluchsee", 0, 5), ("hotel_rust", 5, 9)]),
}
START_DAYS = range(14, 23)                      # start dates 14-22 Aug 2027 (the trip ends 23-31 Aug)
WIZZ = {"W6", "W4", "W9", "5W"}
NIGHTS = 9


def day(n):
    return datetime.date(2027, 8, n)


def label(frm, to, date):
    return f"{frm}-{to}_{date.month:02d}{date.day:02d}"


def carriers(f):
    return {p.split(" ")[0] for p in f["fn"].split(" + ") if p}


def bags(f):
    return 200 if carriers(f) & WIZZ else 160


def hm(t):
    return int(t[:2]) * 60 + int(t[3:])


def latest_arrival(D):
    """Latest landing time for the evening shape, as minutes after midnight."""
    r = D["days"][0].get("route")
    drive = r["minutes"] if r else 0
    return 24 * 60 - 1 if drive <= 25 else 24 * 60 - 60 - drive


def basic(f):
    return f["stops"] <= 1 and not (f["stops"] >= 1 and hm(f["dep"]) < 240)


def fit_out(f, latest, shape="eve"):
    if not basic(f) or f["plus"]:
        return False
    a = hm(f["arr"])
    return 16 * 60 <= a <= latest if shape == "eve" else 7 * 60 <= a <= 14 * 60 + 30


def fit_back(f):
    return basic(f) and not f["plus"]


def cheapest(flights, pred):
    ok = [f for f in flights if pred(f)]
    return min(ok, key=lambda f: (f["price"] + bags(f), f["dur"])) if ok else None


class Trip:
    def __init__(self, cc, snapdir):
        self.cc, self.cfg = cc, TRIPS[cc]
        base = os.path.join(snapdir, "base", f"trip-data-{cc}.json")      # the plan as published before this update
        self.D = json.load(open(base if os.path.exists(base) else os.path.join(ROOT, "app", f"trip-data-{cc}.json"), encoding="utf8"))
        self.F = json.load(open(os.path.join(snapdir, "flights.json"), encoding="utf8"))
        self.M = {}
        for line in open(os.path.join(snapdir, f"hotel_matrix_{cc}.jsonl"), encoding="utf8"):
            r = json.loads(line)
            self.M[(r["id"], r["checkin"], r["checkout"])] = r
        self.latest = latest_arrival(self.D)
        self.car = sum(l[1] for l in self.D["car"]["lines"])
        self.start0 = datetime.date.fromisoformat(self.D["trip"]["dates"]["start"])

    def lists(self, start):
        ap, end = self.cfg["airport"], start + datetime.timedelta(days=NIGHTS)
        return self.F.get(label("TLV", ap, start)), self.F.get(label(ap, "TLV", end))

    def stays(self, start):
        out = []
        for sid, a, b in self.cfg["stays"]:
            ci, co = start + datetime.timedelta(days=a), start + datetime.timedelta(days=b)
            out.append((sid, ci, co, self.M.get((sid, ci.isoformat(), co.isoformat()))))
        return out

    def option(self, start):
        """Cheapest combination for one start date, or None when a flight list or a hotel price is missing."""
        lo, lb = self.lists(start)
        stays = self.stays(start)
        if not lo or not lb:
            return None
        o, b = cheapest(lo["flights"], lambda f: fit_out(f, self.latest)), cheapest(lb["flights"], fit_back)
        missing = [s[0] for s in stays if not s[3] or s[3]["price"] is None]
        if not o or not b or missing:
            return dict(start=start, out=o, back=b, missing=missing, total=None)
        hotels = round(sum(s[3]["price"] for s in stays), 2)
        fl = o["price"] + bags(o) + b["price"] + bags(b)
        return dict(start=start, end=start + datetime.timedelta(days=NIGHTS), out=o, back=b, hotels=hotels, car=self.car, flights_bags=fl,
                    total=round(fl + hotels + self.car, 2), stays=stays, full=(lo["full"], lb["full"]), missing=[])

    def options(self):
        rows = [self.option(day(n)) for n in START_DAYS]
        return [r for r in rows if r]

    def morning(self, start):
        """Cheapest outbound that lands 07:00-14:30 (the daytime-arrival shape), for information."""
        lo, _ = self.lists(start)
        return cheapest(lo["flights"], lambda f: fit_out(f, self.latest, "day")) if lo else None


def fl_str(f):
    return f"{f['airline'][:18]:18} {f['fn']:17} {f['dep']}→{f['arr']} €{f['price']}+{bags(f)}" if f else "— no flight that fits —"


def main(argv):
    snapdir, ccs = argv[0], argv[1:] or list(TRIPS)
    for cc in ccs:
        t = Trip(cc, snapdir)
        print(f"== {cc}  current start {t.start0}  latest evening landing {t.latest // 60:02d}:{t.latest % 60:02d}  car €{t.car}")
        rows = t.options()
        best = min((r["total"] for r in rows if r["total"] is not None), default=None)
        for r in sorted(rows, key=lambda r: (r["total"] is None, r["total"] or 0)):
            s = r["start"]
            mark = ("*" if s == t.start0 else " ") + ("<" if r["total"] is not None and r["total"] == best else " ")
            if r["total"] is None:
                print(f"  {mark}{s:%a %d}  out {fl_str(r['out'])} | back {fl_str(r['back'])} | missing hotel price: {r['missing']}")
                continue
            m = t.morning(s)
            print(f"  {mark}{s:%a %d}→{r['end']:%a %d}  out {fl_str(r['out'])} | back {fl_str(r['back'])} | hotels {r['hotels']:8.2f} | "
                  f"total {r['total']:8.2f}" + (f" | morning out: {m['fn']} {m['dep']}→{m['arr']} €{m['price']}" if m else ""))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
