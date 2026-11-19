"""Render a plan page (<cc>/<ver>/index.html) from a trip data file (app/trip-data-<cc>.json).

The data file is the single source of truth: the app reads it directly and this module turns the same data into the
static bilingual plan page. page_head.html / page_tail.html hold the fixed shell (CSS, scripts)."""
import datetime
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
E = lambda s: html.escape(str(s), quote=True)
ALT_LABEL = {"en": "Alternatives", "he": "חלופות"}
AIRLINE_HE = {"Wizz Air": "וויז אייר", "El Al": "אל על", "Smartwings": "סמארטווינגס", "Israir Airlines": "ישראייר", "Arkia": "ארקיע",
              "Aegean": "אגיאן", "SWISS": "סוויס", "Austrian": "אוסטריאן", "Lufthansa": "לופטהנזה", "TAROM": "טארום",
              "Brussels Airlines": "בריסל איירליינס"}


def t(x, L):
    return x[L] if isinstance(x, dict) else x


def money(x):
    return f"€{int(x + 0.5):,}"            # halves round up, as in the app (JavaScript Math.round)


def m2(x):
    return f"€{x:,.2f}"


def hm(mins, L):
    mins = int(round(mins))
    if mins < 60:
        return f"{mins} min" if L == "en" else f"{mins} דק'"
    return f"{mins // 60}h {mins % 60:02d}m" if L == "en" else f"{mins // 60}:{mins % 60:02d} ש'"


def d_(iso):
    return datetime.date.fromisoformat(iso)


def tag(kind, U):
    cls = {"live": "live", "est": "est", "estimate": "est", "mixed": "mix", "checked": "live"}[kind]
    key = {"live": "live", "est": "est", "estimate": "est", "mixed": "mixed", "checked": "checked"}[kind]
    return f'<span class="tag {cls}">{U[key]}</span>'


def ext(label, url):
    return f'<a href="{E(url)}" target="_blank" rel="noopener">{label}</a>'


def fig(photo, alt, cls="ph"):
    src = "img/" + os.path.basename(photo["file"])
    return (f'<figure class="{cls}"><img src="{src}" width="{photo["w"]}" height="{photo["h"]}" alt="{E(alt)}" loading="lazy" decoding="async" '
            f'onerror="this.onerror=null;this.closest(\'figure\').classList.add(\'noimg\')">'
            f'<figcaption>{ext(E(photo["credit"]), photo["source_page"])}</figcaption></figure>')


def stars(sc, out, rev, src, url):
    if sc is None or rev is None:
        return f'<a class="rating" href="{E(url)}" target="_blank" rel="noopener"><span>{src}</span></a>'
    return f'<a class="rating" href="{E(url)}" target="_blank" rel="noopener"><b>{sc}</b>/{out} <span>{src} · {rev:,}</span></a>'


def airline_l(name, L):
    return AIRLINE_HE.get(name, name) if L == "he" else name


def taxi_mode(D, d, legacy=False):
    """'all' = the whole day's route is by taxi, 'last' = the car goes back and the last leg is a taxi, '' = own car.
    Driven by route_modes ('car' / 'taxi' / 'car to XXX, then taxi'). legacy=True reproduces the rule of the pages published
    up to 9 Nov 2026 (day 6 = car return, any later route = taxi), which was wrong for trips that keep the car to the end."""
    r = d.get("route")
    if not r:
        return ""
    if legacy:
        return "last" if d["day"] == 6 and len(r["legs"]) > 1 else ("all" if d["day"] >= 7 else "")
    mode = (D.get("route_modes") or {}).get(f'D{d["day"]}', "car")
    return "all" if mode == "taxi" else ("last" if "then taxi" in mode else "")


def render_lang(D, L, legacy=False):
    U = D["ui"][L]
    ap = D["country"]["airport"]["code"]
    B = D["budget"]
    hotels = {h["id"]: h for h in D["hotels"]}
    fl = D["flights"]["chosen"]
    P = []
    live_of = U["live_of"].replace("{x}", money(B["live_part_eur"]))

    # ---- header
    P.append(f'<div class="lang-{L}" dir="{U["dir"]}" lang="{L}" data-lang="{L}"><header class="top"><p class="eyebrow">{E(U["eyebrow"])}</p>'
             f'<h1>{E(t(D["trip"]["title"], L))}</h1><p class="lede">{E(t(D["trip"]["lede"], L))}</p>'
             f'<div class="facts"><div><span>{U["total"]}</span><b>{money(B["total_eur"])}</b><small>{live_of}</small></div>'
             f'<div><span>{U["flights"]}</span><b>{ap} ⇄ {ap}</b><small>{fl[0]["flight"]} {fl[0]["dep"]} · {fl[1]["flight"]} {fl[1]["dep"]}</small></div>'
             f'<div><span>{U["bases"]}</span><b>{U["bases_v"]}</b><small>{U["bases_s"]}</small></div>'
             f'<div><span>{U["driving"]}</span><b>{D["car_km"]:,.0f} {U["km"]}</b><small>{U["drive_s"]}</small></div></div>'
             f'<p class="legend">{U["legend"]}</p></header>')

    # ---- how the plan was chosen
    P.append(f'<section><h2>{U["changes"]}</h2><ul class="changes">' + "".join(f"<li>{E(t(c, L))}</li>" for c in D["changes"]) + "</ul></section>")

    # ---- flights
    cards = ""
    for f in fl:
        dt = d_(f["date"])
        cards += (f'<div class="flight"><div class="fl-top"><span>{t(f["dir"], L)}</span><span class="fl-no">{f["flight"]}</span></div>'
                  f'<div class="fl-times"><div><b>{f["dep"]}</b><span>{f["from"]}</span></div><div class="fl-line"><span>{f["duration"]}</span></div>'
                  f'<div><b>{f["arr"]}</b><span>{f["to"]}</span></div></div>'
                  f'<div class="fl-foot"><span>{E(t(f["wd"], L))} {dt.day}.{dt.month}.{dt.year} · {airline_l(f["airline"], L)}</span>'
                  f'<b>{money(f["price_eur"])} {tag("live", U)}</b></div></div>')
    fl_sum = sum(f["price_eur"] for f in fl) + D["flights"]["baggage_eur"]

    def opt_table(title, rows):
        body = "".join(f'<tr class="{"best" if r["best"] else ""}"><th scope="row">{E(t(r["what"], L))}</th><td>{E(t(r["when"], L))}</td>'
                       f'<td class="num">{money(r["price_eur"])}</td><td>{E(t(r["note"], L))}</td></tr>' for r in rows)
        return (f'<details class="alts"><summary><h3>{title}</h3></summary><div class="tbl"><table><thead><tr><th>{U["option"]}</th><th>{U["when"]}</th>'
                f'<th>{U["price4"]}</th><th>{U["notes"]}</th></tr></thead><tbody>{body}</tbody></table></div></details>')

    def dl(iso):
        x = d_(iso)
        return f'{WD[L][x.weekday()]} {x.day}'

    drows = ""
    for w in D.get("date_options", [])[:6]:
        o, b = w["out"], w["back"]
        drows += (f'<tr class="{"best" if w["chosen"] else ""}"><th scope="row">{dl(w["start"])} → {dl(w["end"])}<br><small>{U["plan_eve" if w["plan"] == "eve" else "plan_day"]}</small></th>'
                  f'<td>{o["airline"]} {o["dep"]}→{o["arr"]}<br>{b["airline"]} {b["dep"]}→{b["arr"]}</td>'
                  f'<td class="num">{money(o["eur"] + o["bags_eur"] + b["eur"] + b["bags_eur"])}</td><td class="num">{m2(w["hotels_eur"])}</td>'
                  f'<td class="num">{money(w["car_eur"])}</td><td class="num"><b>{m2(w["total_eur"])}</b></td></tr>')
    dates = (f'<details class="alts"><summary><h3>{U["dates2"]}</h3></summary><div class="tbl"><table><thead><tr><th>{U["start"]}</th><th>{U["flights"]}</th>'
             f'<th>{U["fl_bags"]}</th><th>{U["sec_hotels"]}</th><th>{U["car_short"]}</th><th>{U["both"]}</th></tr></thead><tbody>{drows}</tbody></table></div></details>') if drows else ""
    P.append(f'<section><h2>{U["sec_flights"]}</h2><div class="flights">{cards}</div>'
             f'<div class="bag"><h4>{U["bags"]}</h4><p>{E(t(D["flights"]["baggage_text"], L))} {tag("est", U)}</p>'
             f'<p class="sum">{U["fl_total"]}: <b>{money(fl_sum)}</b></p></div>'
             + opt_table(U["out_opts"], D["flights"]["evening_outbound_options"]) + opt_table(U["ret_opts"], D["flights"]["return_options"]) + dates
             + f'<p class="note">{E(t(D["flights"]["note"], L))}</p></section>')

    # ---- day by day
    trails = "".join(f'<span><span class="blaze b-{c}" aria-hidden="true"><i></i></span> {E(U["trails"][c])}</span>' for c in ("red", "blue", "green", "yellow") if U["trails"].get(c))
    days = ""
    for d in D["days"]:
        dt = d_(d["date"])
        r = d.get("route")
        if r:
            names = " → ".join(p["name"] for p in r["points"])
            mode = taxi_mode(D, d, legacy)
            tn = ""
            if mode == "all":
                tn = f' <small>{U["taxi_note"]}</small>'
            elif mode == "last":
                tn = f' <small>{ap} → {E(r["legs"][-1]["to"])}: {U["taxi_note"]}</small>'
            route = (f'<p class="route"><b>{r["km"]:.0f} {U["km"]} · {hm(r["minutes"], L)}</b> <span>{E(names)}</span> '
                     f'{ext(U["open_route"], r["google_maps_url"])}{tn}</p>')
        else:
            nd = U["no_drive_air"] if d["day"] == 1 else (U["no_drive_base"] if d["day"] < 6 else U["no_drive_city"])
            route = f'<p class="route"><b>{U["no_drive"]}</b> <span>{nd}</span></p>'
        plan = "".join(f"<li>{E(t(p, L))}</li>" for p in d["plan"])
        night = (f'<p class="night">{U["overnight"]}: <b>{E(hotels[d["overnight"]]["name"])}</b></p>' if d.get("overnight")
                 else f'<p class="night">{U["home"]}</p>')
        atts = ""
        for aid in d["attractions"]:
            a = D["attractions"][aid]
            g = a["google"]
            opt = a.get("optional")
            links = [ext(U["nav"], g["nav_url"]), ext(U["gmaps"], g["maps_url"])] + [ext(E(s[0]), s[1]) for s in a.get("sources", [])[:2]]
            atts += (f'<article class="att{" opt" if opt else ""}">{fig(a["photo"], t(a["name"], L))}<div class="att-body">'
                     f'<h4>{E(t(a["name"], L))}{(" " + tag_opt(U)) if opt else ""}</h4>'
                     f'{stars(a["rating"]["score"], 5, a["rating"]["reviews"], "Google", a["rating"]["url"])}'
                     f'<dl><dt>{U["hours"]}</dt><dd>{E(t(a["hours"], L))}</dd><dt>{U["fprice"]}</dt><dd>{E(t(a["price_text"], L))} {tag("est" if a["estimate"] else "checked", U)}</dd>'
                     f'<dt>{U["tneed"]}</dt><dd>{E(t(a["time"], L))}</dd></dl><p class="kids">{E(t(a["kids"], L))}</p>'
                     f'<p class="links">{" · ".join(links)}</p></div></article>')
        days += (f'<section class="day"><header class="day-h"><span class="blaze b-{d["trail"]}" aria-hidden="true"><i></i></span><div>'
                 f'<p class="eyebrow">{U["day"]} {d["day"]} · {E(t(d["weekday"], L))} {dt.day}.{dt.month}</p><h3>{E(t(d["title"], L))}</h3></div></header>'
                 f'{route}<ul class="plan">{plan}</ul>{night}' + (f'<div class="atts">{atts}</div>' if atts else "") + "</section>")
    P.append(f'<section><h2>{U["sec_days"]}</h2><p class="trails">{trails}<small> {U["trail_note"]}</small></p>{days}</section>')

    # ---- hotels
    rows = ""
    cards = ""
    for h in D["hotels"]:
        ci, co = d_(h["checkin"]), d_(h["checkout"])
        bk = next(r for r in h["ratings"] if r["source"].startswith("Booking"))
        gg = next((r for r in h["ratings"] if r["source"].startswith("Google")), None)
        rate = stars(bk["score"], 10, bk["reviews"], "Booking.com", bk["url"]) + (("<br>" + stars(gg["score"], 5, gg["reviews"], "Google", gg["url"])) if gg else "")
        ac_s = f'<br><small class=acs>❄ {U["ac_short"]}</small>' if h.get("ac") else ""
        rows += (f'<tr><td class="hph">{fig(h["photos"][0], h["name"], "ph sm")}</td><th scope="row">{ext(E(h["name"]), h["booking_url"])}{ac_s}</th>'
                 f'<td>{E(t(h["area"], L))}</td><td>{rate}</td><td class="num">{h["nights"]}<br><small>{ci.day}–{co.day}.{co.month}</small></td>'
                 f'<td class="num">{m2(h["price_per_night_eur"])}</td><td class="num"><b>{m2(h["total_eur"])}</b> {tag("live", U)}</td></tr>')
        note = f'<p><small>{E(t(h["google_note"], L))}</small></p>' if h.get("google_note") else ""
        ac = f'<p class="ac">❄ <b>{U["ac"]}:</b> {E(t(h["ac"], L))}</p>' if h.get("ac") else ""
        cards += (f'<article class="hotel"><div class="hotel-ph">{"".join(fig(p, h["name"]) for p in h["photos"])}</div><div class="hotel-body">'
                  f'<h4>{E(h["name"])}</h4><p>{E(t(h["room"], L))}</p>{ac}{note}'
                  f'<details class="alts"><summary>{ALT_LABEL[L]}</summary><p class="alt">{E(t(h["alt"], L))}</p></details>'
                  f'<p class="links">{ext(U["book"], h["booking_url"])} · {ext(U["nav"], h["google"]["nav_url"])}</p></div></article>')
    hot_total = sum(h["total_eur"] for h in D["hotels"])
    P.append(f'<section><h2>{U["sec_hotels"]}</h2><div class="tbl"><table class="hotels"><thead><tr><th>{U["photo"]}</th><th>{U["name"]}</th><th>{U["location"]}</th>'
             f'<th>{U["rating"]}</th><th>{U["nights"]}</th><th>{U["per_night"]}</th><th>{U["both"]}</th></tr></thead><tbody>{rows}</tbody>'
             f'<tfoot><tr><th colspan="6">{len(D["hotels"])} · {sum(h["nights"] for h in D["hotels"])}</th><td class="num"><b>{m2(hot_total)}</b></td></tr></tfoot></table></div>{cards}</section>')

    # ---- car
    C = D["car"]
    crow = "".join(f'<tr><th scope="row">{E(t(l[0], L))}</th><td class="num">{money(l[1])}</td><td>{tag("est" if l[2] else "live", U)}</td></tr>' for l in C["lines"])
    notes = "".join(f"<li>{E(t(n, L))}</li>" for n in D["driving_notes"])
    P.append(f'<section><h2>{U["sec_car"]}</h2><div class="cols"><div><p>{E(t(C["text"], L))}</p><ul class="changes">{notes}</ul></div>'
             f'<div><div class="tbl"><table><tbody>{crow}</tbody><tfoot><tr><th></th><td class="num"><b>{money(sum(l[1] for l in C["lines"]))}</b></td><td></td></tr></tfoot></table></div></div></div></section>')

    # ---- driving routes
    rrows = ""
    for d in D["days"]:
        r = d.get("route")
        if not r:
            nd = U["no_drive_air"] if d["day"] == 1 else (U["no_drive_base"] if d["day"] < 6 else U["no_drive_city"])
            rrows += f'<tr><th scope="row">{U["day"]} {d["day"]}</th><td colspan="4">{nd}</td></tr>'
            continue
        for i, leg in enumerate(r["legs"]):
            head = (f'<th scope="row" rowspan="{len(r["legs"])}">{U["day"]} {d["day"]}<br><small>{r["km"]:.1f} {U["km"]} · {hm(r["minutes"], L)}</small></th>' if i == 0 else "")
            rrows += f'<tr>{head}<td>{E(leg["from"])}</td><td>{E(leg["to"])}</td><td class="num">{leg["km"]:.1f}</td><td class="num">{hm(leg["min"], L)}</td></tr>'
    RT = D["routes_total"]
    P.append(f'<section><h2>{U["sec_routes"]}</h2><div class="tbl"><table><thead><tr><th>{U["day"]}</th><th>{U["from"]}</th><th>{U["to"]}</th><th>{U["km"]}</th><th>{U["time"]}</th></tr></thead>'
             f'<tbody>{rrows}</tbody><tfoot><tr><th colspan="3">{U["whole"]}</th><td class="num"><b>{RT["km"]:,.0f}</b></td><td class="num"><b>{hm(RT["minutes"], L)}</b></td></tr></tfoot></table></div>'
             f'<p class="note">{U["routes_note"]}</p></section>')

    # ---- budget
    brow = "".join(f'<tr><th scope="row">{E(t(l["label"], L))}</th><td class="num">{money(l["eur"])}</td><td>{tag(l["status"], U)}</td></tr>' for l in B["lines"])
    P.append(f'<section><h2>{U["sec_budget"]}</h2><div class="tbl"><table><thead><tr><th>{U["item"]}</th><th>EUR</th><th>{U["src"]}</th></tr></thead><tbody>{brow}</tbody>'
             f'<tfoot><tr><th>{U["total"]}</th><td class="num"><b>{money(B["total_eur"])}</b></td><td><small>{live_of}</small></td></tr></tfoot></table></div>'
             f'<p class="note">{E(U["excluded"])}</p><div class="next"><h3>{U["next"]}</h3><p>{E(U["next_t"])}</p></div></section></div>')
    return "".join(P)


WD = {"en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "he": ["ב'", "ג'", "ד'", "ה'", "ו'", "ש'", "א'"]}


def tag_opt(U):
    return f'<span class="tag mix">{U["optional"]}</span>'


def version_bar(options):
    """options: list of (href, label); the first two are '#he' and '#en' of this version."""
    opts = "".join(f'<option value="{E(v)}">{E(l)}</option>' for v, l in options)
    return f'<nav class="vbar" aria-label="Version"><label for="ver">Version / גרסה <select id="ver">{opts}</select></label></nav>'


def dest_bar(current, dests):
    """dests: list of dicts {id, he, en, href, total}."""
    a = []
    for x in dests:
        cur = ' aria-current="page"' if x["id"] == current else ""
        price = f'<span class="dprice" dir="ltr">{money(x["total"])}</span>' if x.get("total") else ""
        a.append(f'<a class="dest" href="{x["href"]}"{cur}><span lang="he">{x["he"]}</span><span lang="en">{x["en"]}</span>{price}</a>')
    return f'<nav class="dbar" aria-label="Destination / יעד">{"".join(a)}</nav>'


def render_page(D, version_options, dests):
    head = open(os.path.join(HERE, "page_head.html"), encoding="utf8").read().rstrip("\n")
    tail = open(os.path.join(HERE, "page_tail.html"), encoding="utf8").read()
    title = f'{D["country"]["name"]["en"]} Family Trip'
    return "\n".join([head.replace("{{TITLE}}", title), dest_bar(D["country"]["id"], dests), version_bar(version_options),
                      render_lang(D, "he"), render_lang(D, "en"), tail])
