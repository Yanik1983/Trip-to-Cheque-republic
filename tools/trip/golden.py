#!/usr/bin/env python3
"""Golden-master check: render each app/trip-data-<cc>.json and compare it with a published page.

usage: golden.py [cc:ver ...]      (default: the versions listed in PUBLISHED)
For every page it compares the Hebrew block, the English block and the page title. Exit code 1 if anything differs."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBLISHED = ["cz:v8", "hu:v3", "pl:v5", "ro:v4", "si:v3", "ge:v3", "de:v2"]


def first_diff(a, b, ctx=140):
    n = min(len(a), len(b))
    i = next((k for k in range(n) if a[k] != b[k]), n)
    return i, a[max(0, i - ctx):i + ctx], b[max(0, i - ctx):i + ctx]


def check(cc, ver, verbose=True):
    D = json.load(open(os.path.join(ROOT, "app", f"trip-data-{cc}.json"), encoding="utf8"))
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
