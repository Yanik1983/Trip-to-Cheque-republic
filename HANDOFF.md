# Handoff – family trip plans and trip app

State on **25 Nov 2026**, branch `ccr-7acfb66a-ovk7zf`, commit `32391d1` plus this file. Written for whoever (a person or a
new Claude session) continues the work. Read this first, then `VERSIONS.md` (history of every version) and
`tools/README.md` (how the pages are produced).

---

## 1. What this project is

Seven alternative plans for **one** family trip, so the family can compare them and pick one:

- 2 adults + 2 children aged **5 and 7**, flying from **Tel Aviv (TLV)**.
- **10 days / 9 nights in the second half of August 2027.**
- Destinations: Czechia (`cz`), Hungary (`hu`), Poland (`pl`), Romania (`ro`), Slovenia (`si`), Georgia (`ge`),
  Black Forest in Germany via Zurich (`de`).

Each plan exists as a bilingual page (Hebrew + English) and inside a mobile web app. Nothing has been booked.

### Rules the owner set (all still in force)

| Rule | Detail |
|---|---|
| Cheapest dates and flights | Flights at any hour of the day. Each trip sits on its cheapest dates; the default flight is always the cheapest one that fits the plan. |
| Flights | At most 1 stop, no overnight connections, total price for 2 adults + 2 children, two one-way tickets. |
| Kids first | At least two kid activities on every full day; little hiking (2 km at most); short days. |
| Driving | At most about 2.5 hours on a day with a hotel move. No car in the big city. |
| Hotels | Few hotel changes (max 3 hotels; Black Forest max 2). **Free cancellation on every hotel.** |
| Air conditioning | **A must in every hotel and in every alternative that is offered.** |
| Black Forest | Landing at a nearby airport across the border is allowed to make flights cheaper (hence Zurich). |
| Languages | Hebrew and English on every page and in the app. |
| Versions | Every change is a **new version**; nothing is ever deleted. Every page has a version menu. |
| App | Built only from the approved data; prices shown in shekels with a live EUR→ILS rate; total on each destination tab; flight drop-down. |

---

## 2. Where everything is

| What | Where |
|---|---|
| Repository | `Yanik1983/Trip-to-Cheque-republic` |
| Working branch | `ccr-7acfb66a-ovk7zf` (all work is here) |
| Pull request | #1, open, mergeable, into `ccr-8b60fb15-nv8dn3`: https://github.com/Yanik1983/Trip-to-Cheque-republic/pull/1 |
| Live site | https://yanik1983.github.io/Trip-to-Cheque-republic/ (opens the latest Czech plan) |
| Live app | https://yanik1983.github.io/Trip-to-Cheque-republic/app/ (`?d=cz`, `?d=hu`, … opens one destination) |

**GitHub Pages deploys from the working branch on every push.** A push is live about a minute later, so never push a
half-finished state of `app/` or of a version folder. Every deployment so far succeeded (workflow "pages build and
deployment" in the Actions tab; check it after a push).

### Repository layout

```
app/index.html                  single-file mobile app (Leaflet map, Hebrew/English, shekel conversion, flight picker)
app/trip-data-<cc>.json         THE data of each trip – single source of truth (the app reads it, the pages are rendered from it)
app/img/<cc>/, app/*.geojson    photos and country outlines for the app
<cc>/<version>/index.html       plan page of one version   (cz/v7…v9, hu/v1…v4, pl/v1…v6, ro/v1…v5, si/v1…v4, ge/v1…v4, de/v1…v3)
<cc>/<version>/trip-research-<cc>-<version>.json   the data behind that page
<cc>/<version>/img/             photos of that version
v2/ v3/ v4/ v5/ v6/ phase1/     the first Czech versions (v1 = phase1), kept as they were
index.html                      redirects to the latest Czech plan and lists every version
VERSIONS.md                     history: what each version is and why it exists
tools/                          the scripts that produce everything (see section 5)
tools/data/2026-11-19/          the price snapshot of the last update (hotels, flights, texts written by hand)
.claude/skills/google-flights/  a third-party skill (skillhq/flight-search) that drives Google Flights with a browser
```

---

## 3. Current state of the seven trips

All seven versions below are live in the app. Prices in EUR; "total" is the whole estimated budget
(flights, estimated bags, car, fuel, transfers, hotels, attractions).

| Trip | Version | Dates (Aug 2027) | Outbound | Return | Hotels | Total | Flights priced | Hotels priced |
|---|---|---|---|---|---|---|---|---|
| Czechia | v9 | Sat 21 – Mon 30 | Smartwings QS 1285 18:25→21:35 €711 | Smartwings QS 1284 12:45→17:35 €916 | €1,439.93 | **€4,434.93** | 19 Nov | 19 Nov |
| Hungary | v4 | Tue 17 – Thu 26 | Wizz Air W6 2306 20:55→23:25 €600 | Israir 6H 728 11:40→15:50 €946 | €1,750.50 | **€4,584.50** | 19 Nov | 19 Nov |
| Poland | v6 | Tue 17 – Thu 26 | Lufthansa LH 681 + LH 1626 17:05→23:30 €993 | Lufthansa LH 1363 + LH 690 11:10→23:15 €932 | €1,475.08 | **€5,067.08** | 19 Nov | 19 Nov |
| Romania | v5 | Thu 19 – Sat 28 | Wizz Air W4 3254 16:45→19:35 €720 | TAROM RO 155 20:45→23:20 €798 | €1,429.11 | **€4,424.11** | 19 Nov | 19 Nov |
| Slovenia | v4 | Sun 15 – Tue 24 | Lufthansa LH 695 + LH 1462 08:00→21:50 €1,015 | Aegean A3 791 + A3 926 09:20→19:00 €984 | €1,739.30 | **€5,286.30** | **9 Nov (not re-checked)** | 19 Nov |
| Georgia | v4 | Sun 15 – Tue 24 | Israir 6H 891 19:40→23:15 €925 | Aegean A3 897 + A3 924 04:35→12:50 €795 | €1,242.53 | **€4,034.53** | 19 Nov | 19 Nov |
| Black Forest | v3 | Sun 15 – Tue 24 | Aegean A3 459 + A3 448 07:15→19:45 €818 | Iberia IB 628 + IB 1873 11:55→23:20 €796 | €2,057.35 | **€5,706.35** | 19 Nov | 19 Nov |

Bag estimate per direction: Wizz Air €200, every other airline €160 (so €360 for Hungary and Romania, €320 elsewhere).

### Hotels (stay, price on 19 Nov, how to find it on Booking.com)

Common search parameters (Booking.com connector, tool `accommodations_search`): `children_ages [5, 7]`,
`cancellation_type "free_cancellation"`, `currency "EUR"`, `user_country_code "il"`, `user_locale "en"`, 2 adults (default).
The price is `accommodations[].price.book` = total for the stay.

| Trip | Stay id | Property (Booking id) | Nights | Price | Search with |
|---|---|---|---|---|---|
| cz | `hotel_hiair` | Holiday Inn Prague Airport by IHG (77174) | 21→22 | €206.93 | `hotel_names ["Holiday Inn Prague Airport"]`, `destination "PRG"` |
| cz | `hotel_jedeme` | Jedeme Lipno (14475148) | 22→26 | €477.00 | name, `destination "Lipno nad Vltavou, Czech Republic"` |
| cz | `hotel_nova` | The Nova Apart Hotel (16113463) | 26→30 | €756.00 | name, `destination "Prague, Czech Republic"` |
| hu | `hotel_ibisair` | ibis Styles Budapest Airport (2815587) | 17→18 | €234.80 | name, `destination "BUD"` |
| hu | `hotel_forras` | Landhaus Forrás (623125) | 18→22 | €918.80 | **does not resolve by name** – `coordinates {46.969608, 17.890809, radius 0.15}` + `facilities ["AIR_CONDITIONING"]`; take "Landhaus Forrás", not "Landhaus Forrás 2" (7087224) |
| hu | `hotel_westside` | WestSide Garden Apartments by FirstHost (11462324) | 22→26 | €596.90 | `["WestSide Garden Apartments"]`, `destination "Budapest, Hungary"` |
| pl | `hotel_hampton` | Hampton by Hilton Krakow Airport (7692353) | 17→18 | €251.05 | name, `destination "KRK"` |
| pl | `hotel_goralski` | Góralski Resort Pool & SPA (9765443) | 18→22 | €859.67 | name, `destination "Białka Tatrzańska, Poland"` (not "Góralski Resort 2 z Basenem") |
| pl | `hotel_playroom` | PlayRoom Aparthotel (1496273) | 22→26 | €364.36 | name, `destination "Kraków, Poland"` |
| ro | `hotel_carpathia` | Hotel Carpathia, Sinaia (242964) | 19→24 | €780.70 | **does not resolve by name** – `coordinates {45.346357, 25.546826, radius 0.1}` + `facilities ["AIR_CONDITIONING"]` |
| ro | `hotel_maison` | Maison Bucarest Apartments by Olala Homes (11634704) | 24→28 | €648.41 | `["Maison Bucarest Apartments"]`, `destination "Bucharest, Romania"` |
| si | `hotel_bled` | Apartment Muznik, Bled (1135194) | 15→20 | €1,030.00 | name, `destination "Bled, Slovenia"` |
| si | `hotel_lj` | Absolutum Apartments, Ljubljana (9975558) | 20→24 | €709.30 | name, `destination "Ljubljana, Slovenia"` |
| ge | `hotel_tb1` | Ramada by Wyndham Tbilisi Old City (7671953) | 15→16 | €117.45 | name, `destination "Tbilisi, Georgia"` |
| ge | `hotel_bj` | Steel Tower Borjomi (15479512) | 16→20 | €671.24 | `["Steel Tower"]`, `destination "Borjomi, Georgia"` |
| ge | `hotel_tb2` | Ramada by Wyndham Tbilisi Old City (7671953) | 20→24 | €453.84 | as `hotel_tb1` |
| de | `hotel_schluchsee` | Schönhier - Design Apartment mit Pool, Sauna (13512968) | 15→20 | €1,297.75 | `["Schönhier Design Apartment mit Pool, Sauna"]`, `destination "Schluchsee, Germany"` |
| de | `hotel_rust` | Ferienwohnungen Busch`s Gästehaus (6443040) | 20→24 | €759.60 | `["Ferienwohnungen Busch's Gästehaus"]`, `destination "Rust, Germany"` |

Shape of the stays, counted from the start date S:

- `cz`, `hu`, `pl`: airport hotel S→S+1, base S+1→S+5, city S+5→S+9. Car on Days 2–6.
- `ro`, `si`: base S→S+5, city S+5→S+9. Car from the airport on arrival to Day 6.
- `ge`: Tbilisi S→S+1, Borjomi S+1→S+5, Tbilisi S+5→S+9. Car delivered on Day 2, returned on Day 6.
- `de`: Schluchsee S→S+5, Rust S+5→S+9. Car all 10 days (Zurich Airport).

---

## 4. Open items – what is not finished

### 4.1 Slovenia's flights are still unverified

Slovenia v4 carries the flight prices of 9 Nov; the page and the app say so. Google Flights refused every
Ljubljana search on 19 Nov (all afternoon) and again on 25 Nov (first try, HTTP 429). Reason and options in section 6.

To finish it, two searches are needed (and two more for the one-day-later option, see 4.3):

```
node tools/flights/gfl.js <scratch>/full "TLV-LJU_0815|TLV|LJU|2027-08-15"
node tools/flights/gfl.js <scratch>/full "LJU-TLV_0824|LJU|TLV|2027-08-24"
node tools/flights/gfl.js <scratch>/full "TLV-LJU_0816|TLV|LJU|2027-08-16"     # one day later
node tools/flights/gfl.js <scratch>/full "LJU-TLV_0825|LJU|TLV|2027-08-25"
```

One try per search, at least 5 minutes apart, stop at the first block. The plain reader (`gget.py`) does not work for
Ljubljana (Google sends an empty page frame for routes it has not cached).

When the lists arrive, publish the result as **Slovenia v5** (keep v4). Because it will be a different day, start a new
snapshot folder instead of reusing `2026-11-19` (section 5.2), re-price Slovenia's two hotels the same day so that one
date is true for everything, and fix known issues (a) and (b) of section 7 first.

The fastest alternative is for the owner to look the two flights up by hand on Google Flights:
Lufthansa LH 695 + LH 1462 on Sun 15 Aug (was €1,015 for four) and Aegean A3 791 + A3 926 on Tue 24 Aug (was €984).

### 4.2 The cheapest-dates comparison was not repeated for flights

On 19 Nov hotels were priced for **every** start date 14–22 Aug, but flights only for the dates of each plan
(Google's limits, section 6). So no trip was moved and the date tables on the pages have a single row. The owner's
standing rule is "each trip on its cheapest dates", so this is still owed.

Hotel totals per start date on 19 Nov (evening-arrival shape; (p) = the plan's date, bold = cheapest):

| Trip | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|
| cz | 1541 | 1498 | 1413 | 1369 | 1383 | 1448 | 1482 | 1440 (p) | **1339** |
| hu | 1858 | 1860 | 1810 | **1750** (p) | 1766 | 1826 | 1870 | 1855 | 1860 |
| pl | 1459 | 1476 | n/a | 1475 (p) | 1449 | n/a | 1407 | **1366** | 1390 |
| ro | 1613 | 1541 | 1431 | 1398 | **1388** | 1429 (p) | 1496 | 1488 | 1448 |
| si | 1739 | 1739 (p) | **1609** | 1609 | 1609 | 1609 | 1609 | 1609 | 1609 |
| ge | 1255 | 1243 (p) | 1224 | 1213 | **1209** | 1213 | 1222 | 1220 | 1214 |
| de | 2057 | 2057 (p) | 2057 | 2057 | 2057 | 2057 | 2057 | 2057 | 2057 |

`n/a` for Poland: PlayRoom Aparthotel had no free-cancellation offer for 21→25 and 24→28 Aug.

The alternative dates I meant to check first (two flight searches each, outbound on S and return on S+9):
`si` 16, 17, 18 · `cz` 22, 17, 18 · `pl` 21, 20 · `de` 14, 18 · `ro` 18, 17 · `hu` 20, 16 · `ge` 17, 18.
Returns on 30–31 Aug tend to be the most expensive (end of the Israeli school holiday).

**Moving a trip is not a mechanical step** – see section 5.4.

### 4.3 Decisions waiting for the owner (hotels and one flight)

I kept every chosen hotel; these were reported to the owner on 19 Nov and are written into the plan notes.

| Where | Chosen | Cheaper option found on 19 Nov | Saving |
|---|---|---|---|
| Prague, 26–30 Aug | The Nova Apart Hotel €756 (Booking 9.4, Prague 2) | Louren Apartments, Holešovice €618 (9.2, 2 bedrooms, metro 700 m) | €138 |
| Bucharest, 24–28 Aug | Maison Bucarest €648 (rose from €459; 2 bedrooms, full kitchen) | Bucur Accommodation €468 (9.0, no kitchen listed); Mercure City Center €572 | €181 / €77 |
| Tbilisi, 1 + 4 nights | Ramada Old City €117 + €454 (chosen for its two pools) | Kindli Boutique Hotel €90 + €293 (9.0, no pool) | €189 |
| Bled, 15–20 Aug | Apartment Muznik €1,030 (rose from €900; 300 m from the lake) | Apartmaji Sparakel €889 (8.9, 1.1 km from the lake), **or** start one day later: Muznik is still €900 from 16 Aug | €141 / €130 |
| Black Forest outbound | Aegean via Heraklion, 13.5 h, lands 19:45, €818 | Iberia IB 1874 + IB 629 05:30→14:00, €889: €71 more but lands at 14:00 (selectable in the app, marked as not fitting the evening plan) | – |

Smaller ones, not raised as decisions: Kraków airport – Balice Apartamenty Premium €217 against Hampton €251;
Budapest airport – Hotel Stáció €211 against ibis Styles €235 (needs the shuttle).

### 4.4 An unanswered question from the owner

On 19 Nov the owner asked: *"If we take into account that there will be only 2 devices in the area, how accurate it
will be?"* Nothing in this project depends on the number of devices nearby, so I asked what "it" refers to (a tracker
tag, live traffic, "popular times", the phone's own location, or another chat). **No answer yet.** Do not guess; ask
again if it comes up.

### 4.5 Pull request

PR #1 is open and mergeable. It was created at the owner's request; merging it is the owner's call. Its description
was brought up to date on 19 Nov.

---

## 5. How the pages and the app are produced

Everything is generated from `app/trip-data-<cc>.json`. The scripts used before 19 Nov lived outside the repository and
were **lost when the cloud container was reset**; the tools below were rebuilt from the published pages and are
checked against them. **Keep every script and every data snapshot in the repository** – the scratch folder is not durable.

| Script | What it does |
|---|---|
| `tools/trip/render.py` | Data file → bilingual plan page (`page_head.html` / `page_tail.html` are the fixed shell). |
| `tools/trip/golden.py` | Proves the renderer reproduces the seven pages published on 9 Nov character for character (from `tools/data/2026-11-19/base`). |
| `tools/trip/engine.py` | The comparison: cheapest flights that fit, hotel totals per start date, sums. |
| `tools/trip/update.py` | Applies a price snapshot to a trip: flights, flight choices, hotel prices, budget, date table, notes, version. |
| `tools/trip/build.py` | Publishes versions: page, data, photos; refreshes the destination tabs on every page, the app's totals and links, the root page. |
| `tools/trip/verify.js` | Headless check of the pages and the app (no script errors, photos load, totals and default flights match). |
| `tools/trip/versions_md.py` | Prints the table of the versions in the app for `VERSIONS.md`. |
| `tools/flights/gget.py` | Google Flights, one plain request per search (first results page). |
| `tools/flights/gfl.js` | Google Flights in a headless browser, presses "View more flights" (complete list). |
| `tools/flights/snapshot.py` | Saved result pages → `flights.json` (keeps searches already in the file). |
| `tools/hotels/addrow.py` | Appends one Booking.com price to a `.jsonl` file. |

### 5.1 The fit rules (in `engine.py`)

- At most 1 stop; with a connection, no departure before 04:00; the flight must land on the day it leaves.
- Outbound, evening shape (all seven plans): lands 16:00 or later, and early enough to be in bed by about midnight
  (landing + 1 h + the Day 1 drive; no limit when the first bed is at or near the airport). Latest landing:
  `ro` 21:16, `si` 22:27, `de` 21:49, the others 23:59.
- Cheapest = flight price + bag estimate; ties go to the shorter journey.
- The app's flight drop-down lists up to 14 options per direction; the default is the cheapest that fits, the others
  are marked ⚠ when they do not fit.
- The morning-arrival shape is not priced as a plan; the notes only state how much more the cheapest morning flight costs.

### 5.2 A price update, step by step

```
D=tools/data/<YYYY-MM-DD>
mkdir -p $D/base && cp app/trip-data-*.json $D/base/          # the "before" – update.py always starts from here

# hotels: one line per stay and start date, written with tools/hotels/addrow.py
#   -> $D/hotel_matrix_<cc>.jsonl          (fields: cc, id, checkin, checkout, price, score, reviews, booking_id, name)
# flights: save result pages into scratch folders, then
python3 tools/flights/snapshot.py $D/flights.json <scratch>/raw <scratch>/full
python3 tools/trip/engine.py $D                                # the comparison table for every trip

# optional, on top of the automatic update:
#   $D/alt_<cc>.json     {hotel id: {"en", "he"}}  re-priced "alternatives" texts
#   $D/patch_<cc>.json   {"dotted.path": value}    texts written by hand; "changes+" adds notes
python3 tools/trip/update.py $D <YYYY-MM-DD> <cc> <new version>   # writes app/trip-data-<cc>.json
python3 tools/trip/build.py cz:v10 hu:v5 ...                      # version folders, tabs, app totals, root page

python3 tools/trip/golden.py
python3 -m http.server 8765 --bind 127.0.0.1 &                   # in the repository root
NO_PROXY=localhost,127.0.0.1 node tools/trip/verify.js http://127.0.0.1:8765 cz:v10 hu:v5 ...
python3 tools/trip/versions_md.py $D                             # table for VERSIONS.md (edit the file by hand)
```

`update.py` falls back to "hotels only" when a trip has no flight lists for both directions: it keeps the published
flights, says so in the notes, legend and flight note, and empties the date table. That is how Slovenia v4 was made.

How the 19 Nov update was actually run, for scale:

- **Hotel matrix** (162 searches): five background agents on the small model, each given the exact parameters and the
  list of date pairs, saving with `addrow.py`. All 18 control values matched my own readings. About a minute each.
- **Alternatives** (the short "alternatives" text of every hotel, English + Hebrew): one background agent per trip on
  the mid-size model; it re-prices the named properties for the stay dates and rewrites both texts into `alt_<cc>.json`.
- **Texts by hand**: `patch_cz.json` (the last day and the Prague apartment text for the new 12:45 return),
  `patch_de.json` (landing city Zurich), `changes+` notes in `patch_cz/ro/ge/si.json` (the hotel decisions of 4.3).

### 5.3 The data file

`app/trip-data-<cc>.json` – main keys: `country`, `version`, `trip` (dates, title, lede), `changes` (the "how this plan
was chosen" notes), `flights` (`chosen`, `choices`, option tables, baggage, note), `date_options` (the date table),
`hotels` (prices, ratings, `room`, `alt`, `ac`), `attractions`, `days` (plan lines, route, `trail` colour),
`car`, `driving_notes`, `routes_total`, `budget`, `ui` (every label, per language), `route_modes`
(`car` / `taxi` / `car to XXX, then taxi` per day – drives the taxi notes). `render.py` and `update.py` are the
reference for every field. Plan lines with `"flight": "out" | "back"` are generated (the app rewrites them when
another flight is picked).

### 5.4 Moving a trip to other dates is real work

`update.py --start` only prices the stays of another date; it does **not** move a plan. A move needs:

1. The structured dates: `trip.dates`, `days[].date` / `weekday`, `hotels[].checkin` / `checkout`,
   `car.pickup.when` / `dropoff.when`, the flight dates.
2. The prose: about 40 fragments per trip mention a weekday or a date – the lede, day titles ("(Sun 29)"), the car
   line and car text, hotel `room` texts, opening hours, plan lines ("Monday is calmer", "Sunday: a queue is possible").
3. A check of every weekday-dependent fact. Example, Slovenia: the House of Experiments is closed Mon, Tue and Fri.
   One day later keeps it on a Sunday (open); two days later puts it on a Monday (closed) and the Ljubljana days
   would have to be re-ordered. Slovenia's Day 1 text is about a Sunday that is also a public holiday (15 Aug) and
   about the €50 out-of-hours car pick-up; on a Monday the Enterprise desk is open until 23:00.

On 9 Nov the trips were moved with scripts that no longer exist. Before moving one again, write the shift for the
structured fields, let an agent propose the prose as a `patch_<cc>.json`, and read the result.

---

## 6. Google Flights – what works, what does not, and the limits

Observed from this cloud environment on 19 and 25 Nov 2026. Google sees all traffic of this environment as one
shared network address ("unusual traffic from your computer network"), so the limits are shared with other users of
the same cloud and cannot be controlled from here.

| Fact | Detail |
|---|---|
| Plain request, natural-language address | `…/travel/flights?hl=en&gl=IL&curr=EUR&q=Flights from TLV to PRG on 2027-08-21 one way 2 adults 2 children` returns the first results page (about 9–12 distinct flights, "Top" + the visible "Other" flights) **only for searches Google already has cached** – it worked for PRG, BUD, KRK, OTP, TBS, ZRH and never for LJU. |
| Hidden flights | The rest ("View more flights", often 100+) is not in that page. It can contain cheaper flights with long connections. |
| The page's own address (`tfs=` parameter) | Built in `gget.py` (`tfs()`), used by `gfl.js`. A plain request to it returned the list in the one test that had the `tfu` state parameter and no filter (a cached route); without `tfu`, and with a stops filter, it returned an empty frame. So plain requests use the natural-language address. |
| Browser reader | Gets the complete list sorted by price (160 rows for Prague → Tel Aviv). Blocked far more often than the plain request. |
| Rate | Roughly one successful request per 5 minutes on the afternoon of 19 Nov; once, nine plain requests 25 s apart went through and then blocks followed. A block is HTTP 429 with a redirect to `/sorry/`, or the page says "Oops, something went wrong". |
| Flight numbers | Read from each row's itinerary attribute (`…lookup/flight?itinerary=TLV-PRG-QS-1285-20270821`), no clicking needed. |

**Rules for whoever continues – please keep them:**

- One try per search, a long pause between searches, stop at the first block. No loops that retry through blocks.
- Never solve a CAPTCHA and do not disguise the browser.
- Do **not** call Google's internal results endpoint directly, and do not run bulk sweeps (the 126-search run and the
  direct endpoint call were both refused by the session's permission checks as unauthorised access – that refusal is
  the intended outcome, not an obstacle to route around).
- The `google-flights` skill in `.claude/skills/` drives the same site with a browser and hits the same limits.

**Better ways to get the remaining flight data:**

1. Run the two readers from the owner's own computer (home network, not the shared cloud address).
2. The owner checks the few flights by hand (section 4.1).
3. Connect a flight-search connector and use that instead.

The Expedia connector was tested and is **not** a substitute: it returns the 3 cheapest itineraries per call in USD
(about 7,000 tokens per call), extra parameters made it fail ("Unknown error"), it does not list Smartwings or Israir,
its Wizz Air price was well above Google's, and no exchange-rate source is reachable from this environment.

---

## 7. Known issues and loose ends in the tools

| | Issue | Where | What to do |
|---|---|---|---|
| a | The legend is rewritten with a pattern that only matches the wording used up to 9 Nov ("LIVE = live price/rating found …"). The legends now read "LIVE = live price found 19 Nov 2026 (ratings: Oct–Nov 2026)", so **the next update would leave the old date in the legend**. | `tools/trip/update.py` lines 343–344 and 418–422 | Match `LIVE = live price[^·]*·` and `חי = מחיר[^·]*·`; the "ratings: Oct–Nov 2026" text is hard-coded too. |
| b | The "previous check" date in the notes is a fixed default, 9 Nov. | `change_notes(…, prev_checked="2026-11-09")`, `update.py` line 162 | Pass the date the base prices were checked. Careful with Slovenia: v4 is dated 19 Nov but its flights are from 9 Nov. |
| c | `--start` does not move a plan (section 5.4). | `update.py` | Write the date shift before the next move. |
| d | The morning-arrival shape is not priced. | `engine.py` | Needs 5-night base prices for `cz`, `hu`, `pl`, `ge` and the alternative Day 1 texts. |
| e | Most flight lists are first pages only (complete lists: Prague → Tel Aviv 30 Aug, Tel Aviv → Tbilisi 15 Aug). | `tools/data/2026-11-19/flights.json`, field `full` | A cheaper long-connection flight may exist; the flight note on the pages says the options are Google's first page. |
| f | `update.py` prints "CHECK" lines for prose that quotes a time of a replaced flight; many are false alarms (any "09:30"). | `time_mentions()` | Read them, do not trust them. |
| g | `VERSIONS.md` is edited by hand; `versions_md.py` only prints the table. | – | – |
| h | Old pages keep their old version menu (they do not list newer versions); only their destination tabs are refreshed. | `build.py` | By design so far. |
| i | `approved` in the data is not read by the app, and the page header still says "awaiting your approval" although the versions are in the app. | `update.py` | Wording inherited from earlier versions; change only if the owner asks. |
| j | Slovenia v4 has no date table (`date_options` is empty). | hotels-only fallback | Fills in when its flights are priced. |
| k | `golden.py` is tied to the 9 Nov pages and switches two intended differences back for the comparison: taxi notes (`legacy=True`) and half-euro rounding. | `golden.py` | Keep it as the regression test of the renderer. |

Fixed in the 19 Nov versions, in case it is asked about: the Black Forest page showed "taxi leg" on days with the
rental car; its Hebrew flight line said the plane lands in Rust; the date tables of 9 Nov mixed in returns that land
the next day (negative "+€" figures); totals ending in .50 were rounded differently on the pages and in the app.

---

## 8. Working agreements and environment notes

- **Commits**: end every commit message with the attribution lines used in this repository's history
  (`Co-Authored-By: …` and `Claude-Session: …`). The session's stop hook expects everything committed and pushed.
- **Pull requests**: do not open one unless the owner asks. PR #1 exists.
- **Push = publish** (section 2).
- **Privacy**: never put the owner's name, e-mail or other personal details into requests to outside services.
  Booking.com searches use only `user_country_code "il"`. For the Expedia connector, do not pass the conversation as
  `query_text`.
- **Third-party code**: `ofeklevy11/flight-agent-webinar` was reviewed as inspiration; it has no licence, so none of
  its code was copied – keep it that way.
- **Network**: outbound traffic goes through a proxy with an allow-list. Blocked here: the exchange-rate services the
  app uses (`api.frankfurter.dev`, `open.er-api.com`) – so the shekel conversion cannot be tested from this
  environment, it works on the owner's phone – and `play.google.com`. Do not route around policy refusals.
- **Browser**: Chromium with Playwright is pre-installed (`require('playwright')`, or `/opt/node22/lib/node_modules/playwright`).
- **Cost**: the owner has usage limits. Use the small model for mechanical look-ups and background agents for bulk
  Booking.com work; keep large tool results out of the main conversation.
- **Scheduled tasks**: none pending. The one retry for Slovenia's flights fired and ended.

### The app in two paragraphs

`app/index.html` is one file: destination chooser (`DESTS`, with each total and the link to the plan page), tabs
(overview, map, days, flights, hotels, car, budget), Hebrew/English switch. Money is shown in EUR with a shekel value
from a live ECB rate (cached in `localStorage` key `trip-fx-ils`).

The flights tab has two drop-downs built from `flights.choices`; the choice is stored per destination
(`trip-flights-<cc>`), the budget and the tab total follow it, and warnings appear when the picked flight lands or
leaves at another time than the plan assumes. `build.py` rewrites the totals and plan-page links in `DESTS`; the Czech
footer links (v9, v8, …) are written by hand in the file.

---

## 9. Suggested next steps, in order

1. Get the owner's answers to 4.3 (hotel switches, Black Forest outbound) and 4.4 (the "2 devices" question).
2. Price Slovenia's two flights (4.1) and publish Slovenia v5. Check the one-day-later option at the same time and
   offer the move with numbers rather than doing it silently.
3. Fix issues (a) and (b) before running `update.py` again.
4. When flight searches are possible at a reasonable pace (ideally from the owner's computer), repeat the
   cheapest-dates comparison (4.2) and move only the trips where the saving is clear and the weekdays still work.
5. Before any booking: re-check every price on the day, and the free-cancellation deadline of each hotel.
