#!/usr/bin/env python3
"""Google Flights reader that uses ONE plain HTTPS request per search (no browser, no login, no CAPTCHA solving).

It opens the same public, shareable result page a person gets in the browser and saves the HTML; parse_html.py reads the
flight rows out of it.

usage: gget.py <outdir> [--pace 30] [--stops 1] JOB ... | @jobs.txt
  JOB = "label|FROM|TO|YYYY-MM-DD"   canonical search URL (2 adults + 2 children, economy, one way); --stops N keeps flights
                                      with at most N stops
      = "label|free text query"      Google's natural-language form, e.g. "Flights from TLV to PRG on 2027-08-21 one way 2 adults 2 children"
A label that already has a saved page is skipped, so the same command can be run again later for the missing ones.
Meant for a handful of look-ups at a time, the way a person would check a few dates: one request, a pause, the next.
If Google answers 429 ("unusual traffic") the script stops at once (exit code 3) – wait and try later, do not hammer."""
import base64
import os
import random
import re
import subprocess
import sys
import time
from urllib.parse import quote

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://www.google.com/travel/flights"
TAIL = "hl=en&gl=IL&curr=EUR"
# 'tfu' is the page's own view-state parameter. Without it Google sends only the empty page frame and the browser
# fetches the list afterwards; with it the list is already in the page, which is what a plain request needs.
TFU = {"cheapest": "EgoIABAAGAAgAigB", "best": "EgoIABAAGAAgAigB"}


def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _v(field, value):
    return _varint(field << 3) + _varint(value)


def _m(field, payload):
    return _varint(field << 3 | 2) + _varint(len(payload)) + payload


def tfs(frm, to, date, adults=2, children=2, max_stops=None):
    """The 'tfs' URL parameter of a one-way economy search, as the Google Flights page writes it into its own address."""
    airport = lambda code: _v(1, 1) + _m(2, code.encode())
    leg = _m(2, date.encode()) + (_v(5, max_stops) if max_stops is not None else b"") + _m(13, airport(frm)) + _m(14, airport(to))
    msg = (_v(1, 28) + _v(2, 2) + _m(3, leg) + _v(8, 1) * adults + _v(8, 2) * children + _v(9, 1) + _v(14, 1)
           + _m(16, _v(1, 2 ** 64 - 1)) + _v(19, 2))
    return base64.urlsafe_b64encode(msg).decode().rstrip("=")


assert tfs("PRG", "TLV", "2027-08-30") == "CBwQAhoeEgoyMDI3LTA4LTMwagcIARIDUFJHcgcIARIDVExWQAFAAUACQAJIAXABggELCP___________wGYAQI"


def url_for(job, opt):
    parts = job.split("|")
    if len(parts) == 4:
        _, frm, to, date = parts
        stops = None if opt["stops"] is None else int(opt["stops"])
        tfu = TFU[opt["tab"]]
        return f"{BASE}/search?tfs={tfs(frm, to, date, max_stops=stops)}" + (f"&tfu={tfu}" if tfu else "") + "&" + TAIL
    return f"{BASE}?{TAIL}&q={quote(parts[1])}"


def fetch(url, tmp):
    r = subprocess.run(["curl", "-sS", "-L", "--compressed", "--max-time", "75", "-A", UA, "-H", "Accept-Language: en-US,en;q=0.9",
                        "-o", tmp, "-w", "%{http_code} %{url_effective}", url], capture_output=True, text=True)
    code, _, final = r.stdout.partition(" ")
    return code, final, r.stderr.strip()


def n_rows(html):
    return len(re.findall(r'aria-label="From \d[\d,]* euros', html))


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    outdir, opt, jobs = argv[0], {"pace": 30.0, "stops": None, "tab": "best"}, []
    a = argv[1:]
    while a:
        x = a.pop(0)
        if x.startswith("--"):
            v = a.pop(0)
            opt[x[2:]] = v if x == "--tab" else float(v)
        elif x.startswith("@"):
            jobs += [l.strip() for l in open(x[1:], encoding="utf8") if "|" in l]
        else:
            jobs.append(x)
    os.makedirs(outdir, exist_ok=True)
    todo = [j for j in jobs if not os.path.exists(os.path.join(outdir, j.split("|", 1)[0] + ".html"))]
    print(time.strftime("%H:%M:%S"), f"jobs {len(jobs)}, to do {len(todo)}", flush=True)
    first = True
    for job in todo:
        label = job.split("|", 1)[0]
        path = os.path.join(outdir, label + ".html")
        tmp = path + ".tmp"
        tries = 0
        while tries < 2:
            if not first:
                time.sleep(opt["pace"] * random.uniform(0.75, 1.25))
            first = False
            code, final, err = fetch(url_for(job, opt), tmp)
            if code == "429" or "/sorry/" in final:
                print(time.strftime("%H:%M:%S"), label, "BLOCKED by Google (429) - stopping; try again later", flush=True)
                if os.path.exists(tmp):
                    os.remove(tmp)
                sys.exit(3)
            tries += 1
            html = open(tmp, encoding="utf8", errors="replace").read() if os.path.exists(tmp) else ""
            n = n_rows(html)
            if code == "200" and n > 0:
                os.replace(tmp, path)
                print(time.strftime("%H:%M:%S"), label, f"ok rows={n} bytes={len(html)}", flush=True)
                break
            print(time.strftime("%H:%M:%S"), label, f"no rows (http {code}, bytes {len(html)}) {err[:80]}", flush=True)
            if code == "200" and html:
                os.replace(tmp, path + ".norows")      # kept for inspection; not counted as done
        else:
            print(time.strftime("%H:%M:%S"), label, "FAILED", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
