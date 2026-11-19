# Tools – how the plan pages and the app data are produced

Everything is built from one data file per trip, `app/trip-data-<cc>.json` (cz, hu, pl, ro, si, ge, de). The app reads
these files directly; the plan pages (`<cc>/<version>/index.html`) are rendered from the same data.

## A price update, step by step

1. **Snapshot folder** – `tools/data/<date>/`. Copy the published data files into `base/` first: they are the "before".
2. **Hotels** – Booking.com totals per stay and start date go into `hotel_matrix_<cc>.jsonl` (one line per stay and date,
   written with `tools/hotels/addrow.py`). Free cancellation, 2 adults + children aged 5 and 7, EUR.
3. **Flights** – Google Flights lists go into `flights.json`:
   - `tools/flights/gget.py` reads one result page with a single plain request (Google's first page of results);
   - `tools/flights/gfl.js` opens the page in a headless browser and presses "View more flights" (the complete list);
   - `tools/flights/snapshot.py` turns the saved pages into `flights.json`.
   Google limits automated searches. Both readers make one try per search, pause between searches and stop at once when
   Google answers "unusual traffic" – run them again later for the missing searches instead of pushing harder.
4. **Compare** – `python3 tools/trip/engine.py tools/data/<date>` prints, for every start date that has flight lists for
   both directions, the cheapest flights that fit the plan, the hotel total and the sum.
5. **Apply** – `python3 tools/trip/update.py tools/data/<date> <date> <cc> <new version>` writes the new
   `app/trip-data-<cc>.json`: flights and flight choices, hotel prices, budget, date table, notes. Optional files in the
   snapshot folder are applied on top: `alt_<cc>.json` (re-priced hotel alternatives) and `patch_<cc>.json` (texts written by
   hand, e.g. the last day when the return flight changes).
6. **Publish** – `python3 tools/trip/build.py cz:v9 hu:v4 …` writes the new version folders (page, data, photos) and
   refreshes the destination tabs of every page, the totals and links in the app and the root `index.html`.
   Older versions are never removed.
7. **Check** – `python3 tools/trip/golden.py` (the renderer still reproduces the pages of 9 Nov 2026 exactly) and, with
   `python3 -m http.server 8765` running in the repository root,
   `node tools/trip/verify.js http://127.0.0.1:8765 cz:v9 hu:v4 …` (pages and app open without errors, photos load,
   totals and default flights match the data).

## The rules the comparison uses

- Flights: total for 2 adults + 2 children, two one-way tickets, at most one stop, no departure before 04:00 when there is
  a connection, landing on the day of departure. Outbound: landing 16:00 or later (the plans are built on an evening
  arrival) and early enough to reach the first bed by about midnight.
- Bags: an estimate per direction – Wizz Air €200, other airlines €160.
- Hotels: live Booking.com total, free cancellation, air conditioning.
- The default flight in the app is the cheapest one that fits (flight + bags); the other options stay selectable.
