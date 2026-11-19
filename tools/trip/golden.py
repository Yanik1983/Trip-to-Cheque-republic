#!/usr/bin/env python3
"""Golden-master check of the page renderer: render the data a published page was built from and compare the two.

usage: golden.py [cc:ver ...]      (default: the versions published on 9 Nov 2026, with the data kept in BASE)
For every page it compares the Hebrew block, the English block and the page title. Exit code 1 if anything differs.
Two things the renderer does differently on purpose since then are switched back for the comparison: the taxi notes
(legacy=True) and the rounding of amounts that end in .50 (the old pages rounded those to the even euro)."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBLISHED = ["cz:v8", "hu:v3", "pl:v5", "ro:v4", "si:v3", "ge:v3", "de:v2"]
BASE = os.path.join(ROOT, "tools", "data", "2026-11-19", "base")
render.money = lambda x: f"€{x:,.0f}"


def first_diff(a, b, ctx=140):
    n = min(len(a), len(b))
    i = next((k for k in range(n) if a[k] != b[k]), n)
    return i, a[max(0, i - ctx):i + ctx], b[max(0, i - ctx):i + ctx]


def check(cc, ver, verbose=True):
    D = json.load(open(os.path.join(BASE, f"trip-data-{cc}.json"), encoding="utf8"))
    page = open(os.path.join(ROOT, cc, ver, "index.html"), encoding="utf8").read().split("\n")
    ok = True
    for L in ("he", "en"):
        want = next(l for l in page if l.startswith(f'<div class="lang-{L}"'))
        got = render.render_lang(D, L, legacy=True)
        if want != got:
            ok = False
            i, w, g = first_diff(want, got)
            if verbose:
                print(f"--- {cc}/{ver} [{L}] differs at {i} (published {len(want)} chars, rendered {len(got)})")
                print("  published:", w)
                print("  rendered :", g)
    title = re.search(r"<title>(.*?)</title>", "\n".join(page[:20])).group(1)
    mine = f'{D["country"]["name"]["en"]} Family Trip'
    if title != mine:
        ok = False
        print(f"--- {cc}/{ver} title: published {title!r}, rendered {mine!r}")
    if ok and verbose:
        print(f"OK  {cc}/{ver}")
    return ok


if __name__ == "__main__":
    targets = sys.argv[1:] or PUBLISHED
    res = [check(*t.split(":")) for t in targets]
    sys.exit(0 if all(res) else 1)
