# Versions

Nothing is deleted: every version stays in the repository and on GitHub Pages, and each page has a version dropdown.

| Version | Date | Language | Folder | What it is |
|---|---|---|---|---|
| v5 (latest, approved) | 17 Oct 2026 | Hebrew + English | `v5/` | v4 moved two days later (Tue 17 – Thu 26 Aug 2027), the cheapest start date of 15–22 Aug; hotels €167.67 cheaper. Includes the start-date comparison. Data: `v5/trip-research-v5.json`. Approved 17 Oct 2026; the app uses it. |
| v4 | 17 Oct 2026 | Hebrew + English | `v4/` | Start outside Prague: night 1 at Holiday Inn Prague Airport, car Days 2–6 to Hluboká and Lipno (4 nights), then 4 nights in the Prague apartment without a car. All free cancellation. Data: `v4/trip-research-v4.json`. Approved 17 Oct 2026, replaced by v5. |
| v3 | 15 Oct 2026 | Hebrew + English | `v3/` | No car in Prague (rental car Day 5–10 only), Prague apartment Encore Boutique Residence, all hotels on free-cancellation rates. Data: `v3/trip-research-v3.json`. |
| v2 | 15 Oct 2026 | Hebrew + English | `v2/` | Evening outbound flight (QS 1285), no border crossings, 2 hotels (Prague 4 + Lipno 5 nights), more kids' attractions, shorter days. Data: `v2/trip-research-v2.json`. |
| v1 | 15 Oct 2026 | English | `phase1/` | Original Phase 1 research: 3 hotels (Bohemian Switzerland, Lipno, Prague), morning flight, Bastei day in Germany. Data: `phase1/trip-research.json`. |

## Other destinations (same rules: cheapest dates and flights, max 3 hotels with free cancellation, kids' attractions)

| Destination | Version | Date | Folder | What it is |
|---|---|---|---|---|
| Hungary | v1 (in the app) | 18 Oct 2026 | `hu/v1/` | Mon 16 – Wed 25 Aug 2027: airport night, Lake Balaton (Balatonfüred) 4 nights, Budapest apartment 4 nights. Data: `hu/v1/trip-research-hu-v1.json`. |
| Poland | v1 (in the app) | 18 Oct 2026 | `pl/v1/` | Tue 17 – Thu 26 Aug 2027: Kraków airport night, Białka Tatrzańska (Tatras) 4 nights, Kraków apartment 4 nights, Energylandia day. Data: `pl/v1/trip-research-pl-v1.json`. |

Every plan page has destination tabs at the top (Czechia · Hungary · Poland).

Pages: https://yanik1983.github.io/Trip-to-Cheque-republic/ opens the latest Czech version.

## Trip app (Phase 2)

`app/` – mobile web app built only from the approved data: Czechia v5 (`app/trip-data.json`), Hungary v1 (`app/trip-data-hu.json`), Poland v1 (`app/trip-data-pl.json`); choose the country at the top (link straight to one with `?d=cz`, `?d=hu` or `?d=pl`): overview, map with all routes, day-by-day view, flights, hotels, car and budget, in Hebrew and English.
Open on the phone: https://yanik1983.github.io/Trip-to-Cheque-republic/app/
