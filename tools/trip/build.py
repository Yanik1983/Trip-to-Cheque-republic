#!/usr/bin/env python3
"""Publish new versions of the plan pages from the app data files.

usage: build.py cc:ver [cc:ver ...]      e.g. build.py cz:v9 hu:v4
For every cc:ver (app/trip-data-<cc>.json must already carry that version id) it writes
  <cc>/<ver>/index.html                   the bilingual plan page (render.py)
  <cc>/<ver>/trip-research-<cc>-<ver>.json  the data behind the page
  <cc>/<ver>/img/                         the photos (copied from the previous version)
and then, for the whole site: the destination tabs of every page (latest version + current total of each trip), the
totals and plan-page links in app/index.html and the root index.html. Older versions are never removed."""
import copy
import datetime
import glob
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORDER = ["cz", "hu", "pl", "ro", "si", "ge", "de"]
TAB = {"cz": ("צ'כיה", "Czechia"), "hu": ("הונגריה", "Hungary"), "pl": ("פולין", "Poland"), "ro": ("רומניה", "Romania"),
       "si": ("סלובניה", "Slovenia"), "ge": ("גאורגיה", "Georgia"), "de": ("היער השחור", "Black Forest")}
APP_ONLY = ("approved", "map", "points_of_interest_types", "route_modes", "ui")


def data(cc):
    return json.load(open(os.path.join(ROOT, "app", f"trip-data-{cc}.json"), encoding="utf8"))


def vnum(v):
    return int(v.lstrip("v"))


def latest_dir(cc, below=None):
    vs = [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, cc, "v*", "index.html"))]
    vs = [v for v in vs if below is None or vnum(v) < vnum(below)]
    return max(vs, key=vnum) if vs else None


def version_options(D, cc, ver, prev):
    """This version first (Hebrew, English), then the previous one with its date, then the older ones by name only."""
    d = datetime.date.fromisoformat(D["version"]["date"])
    name = D["country"]["name"]
    opts = [("#he", f"{name['he']} {ver} · עברית · {d.day}.{d.month}.{d.year} (latest, in the app)"),
            ("#en", f"{name['en']} {ver} · English · {d.day} {d:%b} {d.year} (latest, in the app)")]
    if not prev:
        return opts
    page = open(os.path.join(ROOT, cc, prev, "index.html"), encoding="utf8").read()
    bar = re.search(r'<nav class="vbar".*?</nav>', page, re.S).group(0)
    old = [(html.unescape(v), html.unescape(l)) for v, l in re.findall(r'<option value="([^"]*)">(.*?)</option>', bar)]
    for (v, l), lang in zip(old[:2], ("he", "en")):
        opts.append((f"../{prev}/index.html#{lang}", l.replace(" (latest, in the app)", "").replace(" (latest)", "")))
    for v, l in old[2:]:
        opts.append((v, l.split(" · ")[0]))
    return opts


def dests(depth, latest, totals):
    up = "../" * depth
    return [{"id": cc, "he": TAB[cc][0], "en": TAB[cc][1], "href": f"{up}{cc}/{latest[cc]}/index.html", "total": totals[cc]} for cc in ORDER]


def research_json(D):
    R = copy.deepcopy({k: v for k, v in D.items() if k not in APP_ONLY})

    def fix(x):
        if isinstance(x, dict):
            if isinstance(x.get("file"), str) and x["file"].startswith("img/"):
                x["file"] = "img/" + os.path.basename(x["file"])
            for v in x.values():
                fix(v)
        elif isinstance(x, list):
            for v in x:
                fix(v)
    fix(R)
    return R


def main(argv):
    new = dict(a.split(":") for a in argv)
    latest = {cc: new.get(cc) or latest_dir(cc) for cc in ORDER}
    totals = {cc: data(cc)["budget"]["total_eur"] for cc in ORDER}
    for cc, ver in new.items():
        D = data(cc)
        if D["version"]["id"] != ver:
            sys.exit(f"{cc}: app data is {D['version']['id']}, not {ver} – run update.py first")
        prev = latest_dir(cc, below=ver)
        out = os.path.join(ROOT, cc, ver)
        os.makedirs(out, exist_ok=True)
        if prev and not os.path.isdir(os.path.join(out, "img")):
            shutil.copytree(os.path.join(ROOT, cc, prev, "img"), os.path.join(out, "img"))
        page = render.render_page(D, version_options(D, cc, ver, prev), dests(2, latest, totals))
        open(os.path.join(out, "index.html"), "w", encoding="utf8").write(page)
        json.dump(research_json(D), open(os.path.join(out, f"trip-research-{cc}-{ver}.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
        missing = [m for m in re.findall(r'<img src="(img/[^"]+)"', page) if not os.path.exists(os.path.join(out, m))]
        print(f"built {cc}/{ver}: {len(page):,} chars, photos missing: {sorted(set(missing)) or 'none'}")

    # destination tabs on every page (old versions included): latest version and current total of each trip
    n = 0
    for path in glob.glob(os.path.join(ROOT, "*", "index.html")) + glob.glob(os.path.join(ROOT, "*", "*", "index.html")):
        rel = os.path.relpath(path, ROOT).split(os.sep)
        if rel[0] in ("app", "tools"):
            continue
        page = open(path, encoding="utf8").read()
        m = re.search(r'<nav class="dbar".*?</nav>', page, re.S)
        if not m:
            continue
        cur = rel[0] if rel[0] in ORDER else "cz"          # the root-level v2…v6 folders are the first Czech versions
        bar = render.dest_bar(cur, dests(len(rel) - 1, latest, totals))
        if bar != m.group(0):
            open(path, "w", encoding="utf8").write(page[:m.start()] + bar + page[m.end():])
            n += 1
    print(f"destination tabs refreshed on {n} pages")

    # the app: totals and plan-page links of the destination chooser
    p = os.path.join(ROOT, "app", "index.html")
    app = open(p, encoding="utf8").read()
    for cc in ORDER:
        app, k = re.subn(r"(\{id:'%s',.*?total:)[\d.]+(,.*?report:')[^']*(')" % cc, lambda m: f"{m.group(1)}{totals[cc]}{m.group(2)}../{cc}/{latest[cc]}/index.html{m.group(3)}", app, count=1)
        if k != 1:
            sys.exit(f"app/index.html: destination {cc} not found")
    open(p, "w", encoding="utf8").write(app)

    # root page: open the latest Czech plan, list everything
    lines = []
    for cc in ORDER:
        vs = sorted([os.path.basename(os.path.dirname(x)) for x in glob.glob(os.path.join(ROOT, cc, "v*", "index.html"))], key=vnum, reverse=True)
        links = [f'<a href="{cc}/{vs[0]}/">{TAB[cc][0]} – {TAB[cc][1]} ({vs[0]}, latest)</a>'] + [f'<a href="{cc}/{v}/">{v}</a>' for v in vs[1:]]
        if cc == "cz":
            links += [f'<a href="{v}/">{v}</a>' for v in ("v6", "v5", "v4", "v3", "v2")] + ['<a href="phase1/">v1</a>']
        lines.append("<p>" + " · ".join(links) + "</p>")
    lines.append('<p><a href="app/">Trip app</a> · <a href="VERSIONS.md">Versions</a></p>')
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf8").write(
        '<!doctype html>\n<html lang="he" dir="rtl">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>Czech Family Road Trip</title>\n<meta http-equiv="refresh" content="0; url=cz/{latest["cz"]}/">\n</head>\n<body>\n' + "\n".join(lines) + "\n</body>\n</html>\n")
    print("app totals/links and root index updated:", {cc: (latest[cc], totals[cc]) for cc in ORDER})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
