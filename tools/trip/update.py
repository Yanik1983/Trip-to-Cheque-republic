#!/usr/bin/env python3
"""Apply a fresh price snapshot to a trip: new flights, flight choices, hotel prices, budget, date table and notes.

usage: update.py <snapshot-dir> <checked YYYY-MM-DD> <cc> <new version id> [--start YYYY-MM-DD] [--out file.json]
  e.g. update.py tools/data/2026-11-19 2026-11-19 hu v4
Reads <snapshot-dir>/base/trip-data-<cc>.json (the plan as published before the update) and writes app/trip-data-<cc>.json.
Optional files in the snapshot folder are applied on top: alt_<cc>.json (re-priced hotel alternatives, {hotel id: {en, he}})
and patch_<cc>.json (hand-written texts, {"dotted.path": value}).
The dates of the plan are kept; pass --start only for the date that the plan texts were already moved to.
What it cannot do is rewrite prose that depends on a flight time – it prints those lines so they can be checked by hand."""
import copy
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine  # noqa: E402
from render import AIRLINE_HE  # noqa: E402

WD_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WD_HE = ["ב'", "ג'", "ד'", "ה'", "ו'", "ש'", "א'"]
HE_AIR = dict(AIRLINE_HE, **{"KLM": "KLM", "Iberia": "איבריה", "SKY express": "סקיי אקספרס", "Condor": "קונדור", "LOT": "לוט",
                             "Air Baltic": "אייר בלטיק", "Turkish Airlines": "טורקיש", "ITA": "ITA", "Eurowings": "יורווינגס",
                             "British Airways": "בריטיש איירווייז", "Air France": "אייר פראנס", "Tap Air Portugal": "TAP", "Arkia": "ארקיע"})
MAX_CHOICES = 14


def he_air(name):
    return HE_AIR.get(name, name)


def dur(mins):
    return f"{mins // 60}h" + (f" {mins % 60}m" if mins % 60 else "")


def dur_long(mins, L):
    h, m = mins // 60, mins % 60
    if L == "en":
        return f"{h} hr" + (f" {m} min" if m else "")
    return f"{h} שע׳" + (f" {m} דק׳" if m else "")


def money(x):
    return f"€{x:,.0f}"


def dmy(iso):
    d = datetime.date.fromisoformat(iso)
    return {"en": f"{d.day} {d:%b} {d.year}", "he": f"{d.day}.{d.month}.{d.year}"}


def wd(d):
    return {"en": WD_EN[d.weekday()], "he": WD_HE[d.weekday()]}


def when(d):
    return {"en": f"{WD_EN[d.weekday()]} {d.day} Aug", "he": f"{WD_HE[d.weekday()]} {d.day} באוגוסט"}


def span(a, b, year=False):
    y = " 2027" if year else ""
    return {"en": f"{WD_EN[a.weekday()]} {a.day} – {WD_EN[b.weekday()]} {b.day} Aug{y}",
            "he": f"{WD_HE[a.weekday()]} {a.day} – {WD_HE[b.weekday()]} {b.day} באוגוסט{y}"}


def fl_short(f, L, arrow=True):
    """'Wizz Air W6 2306 20:55→23:25' (Hebrew text runs right to left, so its arrow points the other way)."""
    a = f["airline"] if L == "en" else he_air(f["airline"])
    return f"{a} {f['fn']} {f['dep']}{'→' if L == 'en' else '←'}{f['arr']}" if arrow else f"{a} {f['fn']}"


def choice(f, fits, default):
    return {"id": f"{f['fn']}@{f['dep']}", "fn": f["fn"], "airline": f["airline"], "airline_he": he_air(f["airline"]), "dep": f["dep"], "arr": f["arr"],
            "duration": dur(f["dur"]), "stops": f["stops"], "via": ", ".join(f["via"]), "next_day": bool(f["plus"]), "price_eur": f["price"],
            "bags_eur": engine.bags(f), "fit": fits, "default": default}


def what(f):
    stop_en = "nonstop" if not f["stops"] else "1 stop" + (f" in {', '.join(f['via'])}" if f["via"] else "")
    stop_he = "ישירה" if not f["stops"] else "עצירה" + (f" ב-{', '.join(f['via'])}" if f["via"] else "")
    t = f"{f['dep']} → {f['arr']}" + (" (+1)" if f["plus"] else "")
    return {"en": f"{f['airline']} {f['fn']} · {t} · {stop_en}", "he": f"{he_air(f['airline'])} {f['fn']} · {t} · {stop_he}"}


def note(f, chosen, kind, latest):
    d = f["price"] - chosen["price"]
    en = "Same price" if d == 0 else f"€{abs(d)} more" if d > 0 else f"€{abs(d)} cheaper"
    he = "אותו מחיר" if d == 0 else f"יקרה ב-{abs(d)} €" if d > 0 else f"זולה ב-{abs(d)} €"
    if f["stops"]:
        en += f"; {dur_long(f['dur'], 'en')} with a connection"
        he += f"; {dur_long(f['dur'], 'he')} עם קונקשן"
    if f["plus"]:
        en, he = en + "; arrives the next day", he + "; נוחתת למחרת"
    elif kind == "out" and engine.hm(f["arr"]) < 16 * 60:
        en, he = en + "; lands too early for this plan (it is built on an evening arrival)", he + "; נוחתת מוקדם מדי לתוכנית (שבנויה על נחיתה בערב)"
    elif kind == "out" and engine.hm(f["arr"]) > latest:
        en, he = en + "; lands too late for the drive to the first base", he + "; נוחתת מאוחר מדי לנסיעה לבסיס הראשון"
    if f["stops"] and engine.hm(f["dep"]) < 240:
        en, he = en + "; leaves before 04:00", he + "; ממריאה לפני 04:00"
    return {"en": en + ".", "he": he + "."}


CHOSEN_NOTE = {"en": "Chosen: the cheapest flight that fits the plan (flight + estimated bags).",
               "he": "נבחרה: הזולה ביותר שמתאימה לתוכנית (טיסה + הערכת כבודה)."}


def option_rows(flights, chosen, kind, date, latest, fits, n=7):
    others = [f for f in flights if engine.basic(f) and f is not chosen]
    others.sort(key=lambda f: (not fits(f), f["price"] + engine.bags(f), f["dur"]))
    rows = [{"what": what(chosen), "when": when(date), "price_eur": chosen["price"], "note": CHOSEN_NOTE, "best": True}]
    rows += [{"what": what(f), "when": when(date), "price_eur": f["price"], "note": note(f, chosen, kind, latest), "best": False} for f in others[:n - 1]]
    return rows


def choices(flights, chosen, fits):
    ok = [f for f in flights if engine.basic(f)]
    ok.sort(key=lambda f: (f["price"] + engine.bags(f), f["dur"]))
    ok = ok[:MAX_CHOICES] if chosen in ok[:MAX_CHOICES] else ok[:MAX_CHOICES - 1] + [chosen]
    out, seen = [], set()
    for f in ok:
        c = choice(f, fits(f), f is chosen)
        if c["id"] in seen:                      # same flight numbers and departure, another connection day
            c["id"] += f"→{f['arr']}+{f['plus']}"
        seen.add(c["id"])
        out.append(c)
    return out


BAG_GENERIC = {"en": "Checked-bag rules differ by fare and airline; for the 2 suitcases and 2 cabin trolleys I assume about €160 per direction "
                     "(estimate – check the fare conditions when booking).",
               "he": "כללי הכבודה משתנים לפי תעריף וחברה; ל-2 המזוודות ו-2 הטרולים אני מניח כ-160 € לכיוון (הערכה – לבדוק בתנאי התעריף בזמן ההזמנה)."}
BAG_WIZZ = {"en": "Wizz Air fares include only a small under-seat bag. Your 2 cabin trolleys need WIZZ Priority (≈ €10–59 each) and the 2 suitcases "
                  "a 20 kg checked bag each (≈ €13–87), per direction; August prices sit at the top of the range, so ≈ €200 per direction (estimate).",
            "he": "במחיר של וויז אייר כלול רק תיק קטן מתחת למושב. 2 הטרולים שלכם צריכים WIZZ Priority (כ-10–59 € כל אחד) ו-2 המזוודות מזוודה רשומה "
                  "של 20 ק\"ג כל אחת (כ-13–87 €), לכל כיוון; באוגוסט המחירים בקצה העליון, אז כ-200 € לכיוון (הערכה)."}


def baggage_text(o, b):
    wizz = [f for f in (o, b) if engine.bags(f) == 200]
    total = engine.bags(o) + engine.bags(b)
    parts_en = ([BAG_WIZZ["en"]] if wizz else []) + ([BAG_GENERIC["en"]] if len(wizz) < 2 else [])
    parts_he = ([BAG_WIZZ["he"]] if wizz else []) + ([BAG_GENERIC["he"]] if len(wizz) < 2 else [])
    return {"en": " ".join(parts_en) + f" Total ≈ €{total}.", "he": " ".join(parts_he) + f" סה\"כ כ-{total} €."}


def find(flights, fn):
    return next((f for f in flights if f["fn"] == fn), None)


def shape_text(D0):
    """The plan shape as the published notes call it, e.g. ('evening arrival + airport night', 'נחיתה בערב + לילה בשדה')."""
    out = {}
    for L, lead in (("en", "Dates "), ("he", "תאריכים ")):
        item = next((c[L] for c in D0["changes"] if c[L].startswith(lead)), "")
        m = re.search(r"\(([^)]*)\):", item)
        out[L] = m.group(1) if m else ""
    return out


def change_notes(t, D0, D, opt, rows, checked, ver, start, prev_checked="2026-11-09"):
    """The 'how this plan was chosen' list for a version that only refreshes prices."""
    o, b = opt["out"], opt["back"]
    old_o, old_b = D0["flights"]["chosen"]
    lo, lb = t.lists(start)
    c, pc = dmy(checked), dmy(prev_checked)
    pc = {"en": pc["en"].rsplit(" ", 1)[0], "he": pc["he"].rsplit(".", 1)[0]}          # "9 Nov" / "9.11"
    n = int(ver.lstrip("v"))
    sh = shape_text(D0)
    en, he = [], []

    # flights
    def leg(kind_en, kind_he, f, old, lst):
        if f["fn"] == old["flight"] and f["dep"] == old["dep"]:
            d = f["price"] - old["price_eur"]
            how_en = "unchanged" if d == 0 else f"€{abs(d)} {'more' if d > 0 else 'less'} than on {pc['en']}"
            how_he = "בלי שינוי" if d == 0 else f"{abs(d)} € {'יותר' if d > 0 else 'פחות'} מאשר ב-{pc['he']}"
            return (f"{kind_en}: the same {fl_short(f, 'en')}, now {money(f['price'])} ({how_en}).",
                    f"{kind_he}: אותה טיסה, {fl_short(f, 'he')}, עכשיו {f['price']:,} € ({how_he}).")
        now = find(lst["flights"], old["flight"])
        was_en = (f"the {old['airline']} {old['flight']} of the previous version now costs {money(now['price'])} (was {money(old['price_eur'])})" if now
                  else f"the {old['airline']} {old['flight']} of the previous version ({money(old['price_eur'])}) is no longer on Google's first results page")
        was_he = (f"הטיסה מהגרסה הקודמת, {he_air(old['airline'])} {old['flight']}, עולה עכשיו {now['price']:,} € (הייתה {old['price_eur']:,} €)" if now
                  else f"הטיסה מהגרסה הקודמת, {he_air(old['airline'])} {old['flight']} ({old['price_eur']:,} €), כבר לא מופיעה בעמוד התוצאות הראשון של גוגל")
        return (f"{kind_en}: {was_en}, so the cheapest flight that fits is now {fl_short(f, 'en')} for {money(f['price'])}"
                + (" – a nonstop." if not f["stops"] else "."),
                f"{kind_he}: {was_he}, ולכן הזולה ביותר שמתאימה היא עכשיו {fl_short(f, 'he')} ב-{f['price']:,} €" + (" – טיסה ישירה." if not f["stops"] else "."))
    le, lh = zip(leg("Outbound", "הלוך", o, old_o, lo), leg("Return", "חזור", b, old_b, lb))

    # hotels
    moved = [(h0, h) for h0, h in zip(D0["hotels"], D["hotels"]) if abs(h["total_eur"] - h0["total_eur"]) >= 15]
    h_old, h_new = sum(h["total_eur"] for h in D0["hotels"]), sum(h["total_eur"] for h in D["hotels"])
    det_en = "; ".join(f"{h['name']} {money(h0['total_eur'])} → {money(h['total_eur'])}" for h0, h in moved)
    det_he = "; ".join(f"{h['name']} {h0['total_eur']:,.0f} € ← {h['total_eur']:,.0f} €" for h0, h in moved)
    hot_en = (f"Hotels (the same ones, free cancellation, air-conditioned): {money(h_old)} → {money(h_new)}" + (f" ({det_en})." if moved else " – practically unchanged."))
    hot_he = (f"מלונות (אותם מלונות, ביטול חינם, ממוזגים): {h_old:,.0f} € ← {h_new:,.0f} €" + (f" ({det_he})." if moved else " – כמעט בלי שינוי."))
    tot_old, tot_new = D0["budget"]["total_eur"], D["budget"]["total_eur"]
    en.append(f"What changed in {ver}: every price was re-checked on {c['en']} – flights on Google Flights, hotels on Booking.com. {' '.join(le)} {hot_en} "
              f"The estimated total is now about {money(tot_new)} (it was {money(tot_old)}). The plan itself – dates, places and days – is the same.")
    he.append(f"מה השתנה בגרסה {n}: כל המחירים נבדקו מחדש ב-{c['he']} – טיסות ב-Google Flights, מלונות ב-Booking.com. {' '.join(lh)} {hot_he} "
              f"הסכום המשוער הוא עכשיו כ-{tot_new:,.0f} € (היה {tot_old:,.0f} €). התוכנית עצמה – תאריכים, מקומות וימים – לא השתנתה.")

    # dates
    sp = span(start, opt["end"], True)
    four = opt["total"]
    others = [r for r in rows if r["start"] != start]
    m = t.morning(start)
    morn_en = morn_he = ""
    if m:
        d = m["price"] + engine.bags(m) - o["price"] - engine.bags(o)
        if d > 0:
            morn_en = f" A morning arrival on the same day would cost {money(d)} more for the flight ({fl_short(m, 'en')}, {money(m['price'])})."
            morn_he = f" נחיתה בבוקר באותו יום הייתה מייקרת את הטיסה ב-{d:,} € ({fl_short(m, 'he')}, {m['price']:,} €)."
    if others:
        days = ", ".join(str(r["start"].day) for r in sorted(rows, key=lambda r: r["start"]))
        best = min(rows, key=lambda r: r["total"])
        verdict_en = "still the cheapest" if best["start"] == start else "kept"
        verdict_he = "עדיין הזולים" if best["start"] == start else "נשארים"
        en.append(f"Dates {sp['en']} ({sh['en']}): {verdict_en} of the {len(rows)} start dates I could re-price for flights on {c['en']} ({days} Aug) – the flights that fit the plan, "
                  f"estimated bags, hotels with free cancellation and the car together ≈ {money(four)}. Hotels were re-priced for every start date 14–22 Aug.{morn_en}")
        he.append(f"תאריכים {sp['he']} ({sh['he']}): {verdict_he} מבין {len(rows)} תאריכי ההתחלה שהצלחתי לתמחר להם טיסות ב-{c['he']} ({days} באוגוסט) – הטיסות שמתאימות לתוכנית, "
                  f"הערכת כבודה, מלונות עם ביטול חינם והרכב יחד כ-{four:,.0f} €. המלונות תומחרו מחדש לכל תאריך התחלה 14–22 באוגוסט.{morn_he}")
    else:
        en.append(f"Dates {sp['en']} ({sh['en']}) are kept: the flights that fit the plan, estimated bags, hotels with free cancellation and the car together ≈ {money(four)}. "
                  f"Hotels were re-priced for every start date 14–22 Aug, but Google limited automated flight searches on {c['en']}, so flights could be re-priced only for "
                  f"these dates and the date comparison of {pc['en']} was not repeated.{morn_en}")
        he.append(f"התאריכים {sp['he']} ({sh['he']}) נשארים: הטיסות שמתאימות לתוכנית, הערכת כבודה, מלונות עם ביטול חינם והרכב יחד כ-{four:,.0f} €. "
                  f"המלונות תומחרו מחדש לכל תאריך התחלה 14–22 באוגוסט, אבל גוגל הגבילה חיפושי טיסות אוטומטיים ב-{c['he']}, ולכן טיסות תומחרו רק לתאריכים האלה "
                  f"והשוואת התאריכים מ-{pc['he']} לא חזרה על עצמה.{morn_he}")
    en.append(f"Cheapest flights at any time of day, as you asked (at most one stop, no overnight connections). Out: {fl_short(o, 'en')}; back: {fl_short(b, 'en')}.")
    he.append(f"הטיסות הזולות בכל שעה, כמו שביקשת (עד עצירה אחת, בלי קונקשן לילי). הלוך: {fl_short(o, 'he')}; חזור: {fl_short(b, 'he')}.")
    for r in sorted(others, key=lambda r: r["total"])[:2]:
        d = r["total"] - four
        s2 = span(r["start"], r["end"])
        sign = "+" if d >= 0 else "−"
        en.append(f"{'Next best' if d >= 0 else 'Cheaper on paper'}: {s2['en']} ({sh['en']}), flights + bags + hotels + car ≈ {money(r['total'])} ({sign}{money(abs(d))}); "
                  f"out {fl_short(r['out'], 'en')}, back {fl_short(r['back'], 'en')}.")
        he.append(f"{'הבא בתור' if d >= 0 else 'זול יותר על הנייר'}: {s2['he']} ({sh['he']}), טיסות + כבודה + מלונות + רכב כ-{r['total']:,.0f} € ({sign}{abs(d):,.0f} €); "
                  f"הלוך {fl_short(r['out'], 'he')}, חזור {fl_short(r['back'], 'he')}.")
    notes = [{"en": a, "he": b_} for a, b_ in zip(en, he)]
    rules = [x for x in D0["changes"] if x["en"].startswith("Same rules")]
    return notes + rules


def apply(t, checked, ver, start=None):
    """Return (new data, report lines) for trip t (an engine.Trip) with today's prices on the given start date."""
    D0, D = t.D, copy.deepcopy(t.D)
    start = start or t.start0
    opt = t.option(start)
    if not opt or opt["total"] is None:
        raise SystemExit(f"{t.cc}: no complete price set for {start}")
    o, b, end = opt["out"], opt["back"], opt["end"]
    lo, lb = t.lists(start)
    fit_o, fit_b = (lambda f: engine.fit_out(f, t.latest)), engine.fit_back
    ap, name = t.cfg["airport"], D["country"]["name"]
    old_o, old_b = D0["flights"]["chosen"]
    rep = []

    # ---- version
    n = int(ver.lstrip("v"))
    D["version"] = {"id": ver, "date": checked, "label": {"en": f"{name['en']} {ver}", "he": f"{name['he']} גרסה {n}"}}
    D["approved"] = {"version": f"{t.cc} {ver}", "approved_on": checked, "by": "traveller"}

    # ---- flights
    for i, (f, date, frm, to) in enumerate([(o, start, "TLV", ap), (b, end, ap, "TLV")]):
        c = D["flights"]["chosen"][i]
        c.update(date=date.isoformat(), wd=wd(date), flight=f["fn"], airline=f["airline"], dep=f["dep"], arr=f["arr"], duration=dur(f["dur"]), price_eur=f["price"])
        c["from"], c["to"] = frm, to
    D["flights"]["choices"]["out"] = choices(lo["flights"], o, fit_o)
    D["flights"]["choices"]["back"] = choices(lb["flights"], b, fit_b)
    D["flights"]["evening_outbound_options"] = option_rows(lo["flights"], o, "out", start, t.latest, fit_o)
    D["flights"]["return_options"] = option_rows(lb["flights"], b, "back", end, t.latest, fit_b)
    D["flights"]["baggage_eur"] = engine.bags(o) + engine.bags(b)
    D["flights"]["baggage_text"] = baggage_text(o, b)
    c_en, c_he = dmy(checked)["en"], dmy(checked)["he"]
    D["flights"]["note"] = {
        "en": f"Live Google Flights prices found {c_en}, total for 2 adults + 2 children, cheapest fare, bags not included. The options are the ones "
              f"on Google's first results page for each date; flights with more than one stop are left out.",
        "he": f"מחירים חיים מ-Google Flights מ-{c_he}, סה\"כ ל-2 מבוגרים + 2 ילדים, התעריף הזול ביותר, ללא כבודה. האפשרויות הן אלה שמופיעות "
              f"בעמוד התוצאות הראשון של גוגל לכל תאריך; טיסות עם יותר מעצירה אחת לא נכללו."}
    for d in D["days"]:
        for p in d["plan"]:
            if p.get("flight") == "out":
                p["en"] = f"{o['dep']} {o['airline']} {o['fn']} from TLV, landing at {ap} {o['arr']}."
                city = (D["country"]["airport"].get("city") or D["country"]["city"])["he"]      # where the plane lands
                p["he"] = f"{o['dep']} {he_air(o['airline'])} {o['fn']} מנתב\"ג, נחיתה ב{city} ב-{o['arr']}."
            elif p.get("flight") == "back":
                p["en"] = f"{b['airline']} {b['fn']} departs {b['dep']} and lands in TLV at {b['arr']}."
                p["he"] = f"{he_air(b['airline'])} {b['fn']} ממריאה ב-{b['dep']} ונוחתת בנתב\"ג ב-{b['arr']}."

    # ---- hotels
    by_id = {h["id"]: h for h in D["hotels"]}
    for sid, ci, co, row in opt["stays"]:
        h = by_id[sid]
        if (h["checkin"], h["checkout"]) != (ci.isoformat(), co.isoformat()):
            rep.append(f"!! {sid}: stay dates in the plan ({h['checkin']}→{h['checkout']}) differ from {ci}→{co}")
        nights = (co - ci).days
        h.update(total_eur=row["price"], price_per_night_eur=round(row["price"] / nights, 2), nights=nights)
        if row.get("score"):
            h["booking_score"], h["booking_reviews"] = row["score"], row["reviews"]
            for r in h["ratings"]:
                if r["source"].startswith("Booking"):
                    r["score"], r["reviews"] = row["score"], row["reviews"]
    hotels_total = round(sum(h["total_eur"] for h in D["hotels"]), 2)

    # ---- budget
    for l in D["budget"]["lines"]:
        if l["key"] == "flights":
            l["eur"] = o["price"] + b["price"]
            l["label"] = {"en": f"Flights – {fl_short(o, 'en', False)} + {fl_short(b, 'en', False)}, 4 passengers",
                          "he": f"טיסות – {fl_short(o, 'he', False)} + {fl_short(b, 'he', False)}, 4 נוסעים"}
        elif l["key"] == "bags":
            l["eur"] = engine.bags(o) + engine.bags(b)
        elif l["key"] == "hotels":
            l["eur"] = hotels_total
    D["budget"]["total_eur"] = round(sum(l["eur"] for l in D["budget"]["lines"]), 2)
    D["budget"]["live_part_eur"] = round(sum(l["eur"] for l in D["budget"]["lines"] if l["status"] == "live"), 2)

    # ---- date table (every start date that has today's flight lists for both directions)
    rows = [r for r in t.options() if r["total"] is not None]
    rows.sort(key=lambda r: r["total"])
    D["date_options"] = [{
        "total_eur": r["total"], "plan": D0["flights"]["choices"].get("variant", "eve"), "start": r["start"].isoformat(), "end": r["end"].isoformat(),
        "out": {"eur": r["out"]["price"], "bags_eur": engine.bags(r["out"]), "airline": r["out"]["airline"], "flight": r["out"]["fn"], "dep": r["out"]["dep"], "arr": r["out"]["arr"]},
        "back": {"eur": r["back"]["price"], "bags_eur": engine.bags(r["back"]), "airline": r["back"]["airline"], "flight": r["back"]["fn"], "dep": r["back"]["dep"], "arr": r["back"]["arr"]},
        "hotels_eur": r["hotels"], "car_eur": r["car"], "chosen": r["start"] == start} for r in rows]

    D["changes"] = change_notes(t, D0, D, opt, rows, checked, ver, start)

    # ---- texts that follow from the numbers
    for L in ("en", "he"):
        U = D["ui"][L]
        U["home"] = f"Home: TLV {b['arr']}" if L == "en" else f"בבית: נתב\"ג {b['arr']}"
        U["eyebrow"] = (f"{name['en']} {ver} research · prices checked {c_en} · awaiting your approval" if L == "en"
                        else f"{name['he']} גרסה {n} · מחירים נבדקו {c_he} · ממתין לאישורך")
        U["legend"] = re.sub(r"LIVE = live price/rating found [^·]*·", f"LIVE = live price found {c_en} (ratings: Oct–Nov 2026) ·", U["legend"]) if L == "en" \
            else re.sub(r"חי = מחיר/דירוג חי מ-[^·]*·", f"חי = מחיר חי מ-{c_he} (דירוגים: אוקטובר–נובמבר 2026) ·", U["legend"])
        U["next_t"] = re.sub(r" v\d+ is in the mobile", f" {ver} is in the mobile", U["next_t"]) if L == "en" \
            else re.sub(r" גרסה \d+ נמצאת", f" גרסה {n} נמצאת", U["next_t"])
        U["dates2"] = (f"Dates compared on {c_en} (flights that fit the plan + estimated bags, hotels with free cancellation, car)" if L == "en"
                       else f"השוואת תאריכים מ-{c_he} (טיסות שמתאימות לתוכנית + הערכת כבודה, מלונות עם ביטול חינם, רכב)")

    # ---- report
    rep.append(f"{t.cc} {ver}: {start} → {end}")
    for kind, f, old, lst in (("out ", o, old_o, lo), ("back", b, old_b, lb)):
        same = f["fn"] == old["flight"] and f["dep"] == old["dep"]
        now_old = find(lst["flights"], old["flight"])
        rep.append(f"  {kind} {f['airline']} {f['fn']} {f['dep']}→{f['arr']} €{f['price']}" + (f" (same flight, was €{old['price_eur']})" if same else
                   f"  [CHANGED from {old['airline']} {old['flight']} {old['dep']}→{old['arr']} €{old['price_eur']}; that one today: "
                   f"{'€%d' % now_old['price'] if now_old else 'not on the first results page'}]"))
    for h0, h in zip(D0["hotels"], D["hotels"]):
        rep.append(f"  hotel {h['name'][:40]:40} €{h0['total_eur']:.2f} → €{h['total_eur']:.2f}")
    rep.append(f"  total €{D0['budget']['total_eur']:.2f} → €{D['budget']['total_eur']:.2f}")
    return D, rep, opt


def apply_hotels_only(t, checked, ver):
    """No flight lists for this trip in the snapshot: refresh the hotels and the budget, keep the published flights and say so."""
    D0, D = t.D, copy.deepcopy(t.D)
    start = t.start0
    end = start + datetime.timedelta(days=engine.NIGHTS)
    name, n = D["country"]["name"], int(ver.lstrip("v"))
    c, pc = dmy(checked), dmy(D0["version"]["date"])
    D["version"] = {"id": ver, "date": checked, "label": {"en": f"{name['en']} {ver}", "he": f"{name['he']} גרסה {n}"}}
    D["approved"] = {"version": f"{t.cc} {ver}", "approved_on": checked, "by": "traveller"}
    by_id = {h["id"]: h for h in D["hotels"]}
    for sid, ci, co, row in t.stays(start):
        h, nights = by_id[sid], (co - ci).days
        h.update(total_eur=row["price"], price_per_night_eur=round(row["price"] / nights, 2))
        if row.get("score"):
            h["booking_score"], h["booking_reviews"] = row["score"], row["reviews"]
            for r in h["ratings"]:
                if r["source"].startswith("Booking"):
                    r["score"], r["reviews"] = row["score"], row["reviews"]
    h_old, h_new = sum(h["total_eur"] for h in D0["hotels"]), round(sum(h["total_eur"] for h in D["hotels"]), 2)
    for l in D["budget"]["lines"]:
        if l["key"] == "hotels":
            l["eur"] = h_new
    D["budget"]["total_eur"] = round(sum(l["eur"] for l in D["budget"]["lines"]), 2)
    D["budget"]["live_part_eur"] = round(sum(l["eur"] for l in D["budget"]["lines"] if l["status"] == "live"), 2)
    D["date_options"] = []                                   # the old table no longer matches today's hotel prices
    o, b = D["flights"]["chosen"]
    D["flights"]["note"] = {
        "en": f"Flight prices are from {pc['en']} (Google Flights, total for 2 adults + 2 children, cheapest fare, bags not included). On {c['en']} Google did not "
              f"answer automated searches for this route, so they could not be re-checked – look at them again before booking.",
        "he": f"מחירי הטיסות הם מ-{pc['he']} (Google Flights, סה\"כ ל-2 מבוגרים + 2 ילדים, התעריף הזול ביותר, ללא כבודה). ב-{c['he']} גוגל לא ענתה לחיפושים "
              f"אוטומטיים בקו הזה, ולכן לא נבדקו מחדש – כדאי לבדוק אותם שוב לפני ההזמנה."}
    moved = [(h0, h) for h0, h in zip(D0["hotels"], D["hotels"]) if abs(h["total_eur"] - h0["total_eur"]) >= 15]
    det_en = "; ".join(f"{h['name']} {money(h0['total_eur'])} → {money(h['total_eur'])}" for h0, h in moved)
    det_he = "; ".join(f"{h['name']} {h0['total_eur']:,.0f} € ← {h['total_eur']:,.0f} €" for h0, h in moved)
    sh, sp = shape_text(D0), span(start, end, True)
    tot_old, tot_new = D0["budget"]["total_eur"], D["budget"]["total_eur"]
    D["changes"] = [
        {"en": f"What changed in {ver}: the hotels were re-priced on {c['en']} on Booking.com (the same ones, free cancellation, air-conditioned): {money(h_old)} → {money(h_new)}"
               + (f" ({det_en})." if moved else " – practically unchanged.") + f" The flights are the ones priced on {pc['en']}: Google did not answer automated searches "
               f"for this route on {c['en']}, so their prices could not be re-checked. The estimated total is now about {money(tot_new)} (it was {money(tot_old)}). "
               f"The plan itself – dates, places and days – is the same.",
         "he": f"מה השתנה בגרסה {n}: המלונות תומחרו מחדש ב-{c['he']} ב-Booking.com (אותם מלונות, ביטול חינם, ממוזגים): {h_old:,.0f} € ← {h_new:,.0f} €"
               + (f" ({det_he})." if moved else " – כמעט בלי שינוי.") + f" הטיסות הן אלה שתומחרו ב-{pc['he']}: גוגל לא ענתה לחיפושים אוטומטיים בקו הזה ב-{c['he']}, "
               f"ולכן המחירים שלהן לא נבדקו מחדש. הסכום המשוער הוא עכשיו כ-{tot_new:,.0f} € (היה {tot_old:,.0f} €). התוכנית עצמה – תאריכים, מקומות וימים – לא השתנתה."},
        {"en": f"Dates {sp['en']} ({sh['en']}) are kept. Hotels were re-priced for every start date 14–22 Aug; the date comparison for flights is the one of {pc['en']}.",
         "he": f"התאריכים {sp['he']} ({sh['he']}) נשארים. המלונות תומחרו מחדש לכל תאריך התחלה 14–22 באוגוסט; השוואת התאריכים לטיסות היא זו מ-{pc['he']}."},
        {"en": f"Flights (prices of {pc['en']}): out {o['airline']} {o['flight']} {o['dep']}→{o['arr']}; back {b['airline']} {b['flight']} {b['dep']}→{b['arr']}.",
         "he": f"טיסות (מחירים מ-{pc['he']}): הלוך {he_air(o['airline'])} {o['flight']} {o['dep']}←{o['arr']}; חזור {he_air(b['airline'])} {b['flight']} {b['dep']}←{b['arr']}."},
    ] + [x for x in D0["changes"] if x["en"].startswith("Same rules")]
    for L in ("en", "he"):
        U = D["ui"][L]
        if L == "en":
            U["eyebrow"] = f"{name['en']} {ver} research · hotels checked {c['en']}, flights {pc['en']} · awaiting your approval"
            U["legend"] = re.sub(r"LIVE = live price/rating found [^·]*·", f"LIVE = live price (hotels {c['en']}, flights {pc['en']}; ratings Oct–Nov 2026) ·", U["legend"])
            U["next_t"] = re.sub(r" v\d+ is in the mobile", f" {ver} is in the mobile", U["next_t"])
        else:
            U["eyebrow"] = f"{name['he']} גרסה {n} · מלונות נבדקו {c['he']}, טיסות {pc['he']} · ממתין לאישורך"
            U["legend"] = re.sub(r"חי = מחיר/דירוג חי מ-[^·]*·", f"חי = מחיר חי (מלונות {c['he']}, טיסות {pc['he']}; דירוגים אוקטובר–נובמבר 2026) ·", U["legend"])
            U["next_t"] = re.sub(r" גרסה \d+ נמצאת", f" גרסה {n} נמצאת", U["next_t"])
    rep = [f"{t.cc} {ver}: {start} → {end}  (HOTELS ONLY – no flight lists in the snapshot)"]
    rep += [f"  hotel {h['name'][:40]:40} €{h0['total_eur']:.2f} → €{h['total_eur']:.2f}" for h0, h in zip(D0["hotels"], D["hotels"])]
    rep.append(f"  total €{tot_old:.2f} → €{tot_new:.2f}")
    return D, rep, None


def time_mentions(D0, D):
    """Plan / car / hotel prose that quotes a time of the previous flights (to be checked by hand when a flight changed)."""
    old = {x for c in D0["flights"]["chosen"] for x in (c["dep"], c["arr"])}
    new = {x for c in D["flights"]["chosen"] for x in (c["dep"], c["arr"])}
    gone = old - new
    hits = []

    def walk(x, path):
        if isinstance(x, dict):
            if x.get("flight") in ("out", "back") and "en" in x:
                return
            for k, v in x.items():
                walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, str) and any(g in x for g in gone):
            hits.append((path, x))
    for key in ("days", "car", "hotels", "driving_notes", "trip"):
        walk(D[key], key)
    return hits


def patch(D, patches):
    """Hand-written texts for this update: {"dotted.path": value}. A list step may be an index, a hotel id or a day number
    (e.g. "hotels.hotel_nova.alt", "days.10.plan.1", "car.text")."""
    for path, value in patches.items():
        if path == "changes+":                       # extra notes, placed before the closing "Same rules" note
            at = next((i for i, x in enumerate(D["changes"]) if x["en"].startswith("Same rules")), len(D["changes"]))
            D["changes"][at:at] = value
            continue
        node, steps = D, path.split(".")
        for i, step in enumerate(steps):
            last = i == len(steps) - 1
            if isinstance(node, list):
                idx = next((k for k, x in enumerate(node) if isinstance(x, dict) and (x.get("id") == step or str(x.get("day")) == step)), None)
                if idx is None:
                    idx = int(step)
                key = idx
            else:
                key = step
            if last:
                if isinstance(node, list) and key == len(node):
                    node.append(value)
                else:
                    node[key] = value
            else:
                node = node[key]
    return D


def main(argv):
    if len(argv) < 4:
        sys.exit(__doc__)
    snapdir, checked, cc, ver = argv[:4]
    start = datetime.date.fromisoformat(argv[argv.index("--start") + 1]) if "--start" in argv else None
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(engine.ROOT, "app", f"trip-data-{cc}.json")
    t = engine.Trip(cc, snapdir)
    if all(t.lists(start or t.start0)):
        D, rep, _ = apply(t, checked, ver, start)
    else:
        D, rep, _ = apply_hotels_only(t, checked, ver)
    for name in (f"alt_{cc}.json", f"patch_{cc}.json"):                 # re-priced hotel alternatives, hand-written texts
        f = os.path.join(snapdir, name)
        if os.path.exists(f):
            P = json.load(open(f, encoding="utf8"))
            patch(D, {f"hotels.{k}.alt": v for k, v in P.items()} if name.startswith("alt_") else P)
            rep.append(f"  applied {name} ({len(P)} entries)")
    print("\n".join(rep))
    for path, s in time_mentions(t.D, D):
        print(f"  CHECK {path}: {s[:200]}")
    json.dump(D, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("written", out)


if __name__ == "__main__":
    main(sys.argv[1:])
