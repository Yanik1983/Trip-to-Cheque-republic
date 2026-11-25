#!/usr/bin/env python3
"""Print the VERSIONS.md table rows of the versions that are in the app now (totals against the previous snapshot).

usage: versions_md.py <snapshot-dir>      e.g. versions_md.py tools/data/2026-11-19"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAMES = {"cz": "Czechia", "hu": "Hungary", "pl": "Poland", "ro": "Romania", "si": "Slovenia", "ge": "Georgia", "de": "Black Forest"}
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def main(snapdir):
    print("| Destination | Version | Dates | Folder | Flights (out · back) | Estimated total | Before |")
    print("|---|---|---|---|---|---|---|")
    for cc, name in NAMES.items():
        D = json.load(open(os.path.join(ROOT, "app", f"trip-data-{cc}.json"), encoding="utf8"))
        B = json.load(open(os.path.join(snapdir, "base", f"trip-data-{cc}.json"), encoding="utf8"))
        a, b = (datetime.date.fromisoformat(D["trip"]["dates"][k]) for k in ("start", "end"))
        o, r = D["flights"]["chosen"]
        v = D["version"]["id"]
        print(f"| {name} | {v} | {WD[a.weekday()]} {a.day} – {WD[b.weekday()]} {b.day} Aug 2027 | `{cc}/{v}/` | {o['flight']} {o['dep']} €{o['price_eur']:,} · "
              f"{r['flight']} {r['dep']} €{r['price_eur']:,} | about €{int(D['budget']['total_eur'] + 0.5):,} | {B['version']['id']}: €{int(B['budget']['total_eur'] + 0.5):,} |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__))
