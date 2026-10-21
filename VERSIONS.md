# Versions

Nothing is deleted: every version stays in the repository and on GitHub Pages, and each page has a version dropdown.

| Version | Date | Language | Folder | What it is |
|---|---|---|---|---|
| v6 (awaiting approval) | 21 Oct 2026 | Hebrew + English | `v6/` | Air conditioning is a must: Doky Apartments and Encore Boutique Residence (no A/C) are swapped for Jedeme Lipno (Lipno, 18–22 Aug) and The Nova Apart Hotel (Prague, 22–26 Aug), both with A/C; Holiday Inn Prague Airport confirmed. Same dates (Tue 17 – Thu 26 Aug 2027). Data: `v6/trip-research-v6.json`. |
| v5 (approved, in the app) | 17 Oct 2026 | Hebrew + English | `v5/` | v4 moved two days later (Tue 17 – Thu 26 Aug 2027), the cheapest start date of 15–22 Aug; hotels €167.67 cheaper. Includes the start-date comparison. Data: `v5/trip-research-v5.json`. Approved 17 Oct 2026; the app uses it. |
| v4 | 17 Oct 2026 | Hebrew + English | `v4/` | Start outside Prague: night 1 at Holiday Inn Prague Airport, car Days 2–6 to Hluboká and Lipno (4 nights), then 4 nights in the Prague apartment without a car. All free cancellation. Data: `v4/trip-research-v4.json`. Approved 17 Oct 2026, replaced by v5. |
| v3 | 15 Oct 2026 | Hebrew + English | `v3/` | No car in Prague (rental car Day 5–10 only), Prague apartment Encore Boutique Residence, all hotels on free-cancellation rates. Data: `v3/trip-research-v3.json`. |
| v2 | 15 Oct 2026 | Hebrew + English | `v2/` | Evening outbound flight (QS 1285), no border crossings, 2 hotels (Prague 4 + Lipno 5 nights), more kids' attractions, shorter days. Data: `v2/trip-research-v2.json`. |
| v1 | 15 Oct 2026 | English | `phase1/` | Original Phase 1 research: 3 hotels (Bohemian Switzerland, Lipno, Prague), morning flight, Bastei day in Germany. Data: `phase1/trip-research.json`. |

## Other destinations (same rules: cheapest dates and flights, max 3 hotels with free cancellation, kids' attractions)

| Destination | Version | Date | Folder | What it is |
|---|---|---|---|---|
| Hungary | v2 (awaiting approval) | 21 Oct 2026 | `hu/v2/` | Same plan, all three hotels confirmed air-conditioned; alternatives list only air-conditioned options. Data: `hu/v2/trip-research-hu-v2.json`. |
| Hungary | v1 (in the app) | 18 Oct 2026 | `hu/v1/` | Mon 16 – Wed 25 Aug 2027: airport night, Lake Balaton (Balatonfüred) 4 nights, Budapest apartment 4 nights. Data: `hu/v1/trip-research-hu-v1.json`. |
| Poland | v3 (awaiting approval) | 21 Oct 2026 | `pl/v3/` | Same plan and dates, all three hotels confirmed air-conditioned; Hampton re-priced (+€49, total about €5,048). Data: `pl/v3/trip-research-pl-v3.json`. |
| Poland | v2 (in the app) | 19 Oct 2026 | `pl/v2/` | Same plan one day later, Wed 18 – Fri 27 Aug 2027: the v1 return flight rose €111 on 19 Oct, so this start became cheapest (−€108), with easier flight times. Data: `pl/v2/trip-research-pl-v2.json`. |
| Poland | v1 | 18 Oct 2026 | `pl/v1/` | Tue 17 – Thu 26 Aug 2027: Kraków airport night, Białka Tatrzańska (Tatras) 4 nights, Kraków apartment 4 nights, Energylandia day. Data: `pl/v1/trip-research-pl-v1.json`. |

| Romania | v2 (awaiting approval) | 21 Oct 2026 | `ro/v2/` | Hello Mountains (no A/C) replaced by the 4-star Hotel Carpathia, Sinaia (A/C, spa with indoor pool, breakfast); same dates; total about €4,025 (+€568). Data: `ro/v2/trip-research-ro-v2.json`. |
| Romania | v1 (in the app) | 21 Oct 2026 | `ro/v1/` | Sat 14 – Mon 23 Aug 2027, max 2 hotels (no airport night): Sinaia / Prahova valley 5 nights (Peleș, Brașov, Bran, Dino Parc, Libearty bears), Bucharest apartment 4 nights, car Days 1–6. Cheapest flights (Wizz Air out, TAROM back). Data: `ro/v1/trip-research-ro-v1.json`. |

**Rule from 21 Oct 2026: every hotel in every trip must have air conditioning (a must).** The v6 / v2 / v3 / v2 pages above implement it; the app still shows the previous approved versions until you approve.

| Slovenia | v1 (awaiting approval) | 21 Oct 2026 | `si/v1/` | Sun 15 – Tue 24 Aug 2027, 2 air-conditioned apartments: Lake Bled 5 nights, Ljubljana 4 nights, car Days 1–6; daytime arrival (SWISS) chosen over the €51 cheaper 21:50 Lufthansa landing, because car-rental desks at LJU are closed then. About €4,872. Data: `si/v1/trip-research-si-v1.json`. |
| Georgia | v1 (awaiting approval) | 21 Oct 2026 | `ge/v1/` | Tue 17 – Thu 26 Aug 2027: Tbilisi night 1, Borjomi 4 nights, Tbilisi 4 nights (all air-conditioned), car Days 2–6; Israir out, Aegean back (04:35 departure). About €4,144. Israel's NSC level-3 travel warning (March 2026, per press) – check before booking. Data: `ge/v1/trip-research-ge-v1.json`. |

Every plan page has destination tabs at the top (Czechia · Hungary · Poland · Romania · Slovenia · Georgia).

Pages: https://yanik1983.github.io/Trip-to-Cheque-republic/ opens the latest Czech version.

## Trip app (Phase 2)

`app/` – mobile web app built only from the approved data: Czechia v5 (`app/trip-data.json`), Hungary v1 (`app/trip-data-hu.json`), Poland v2 (`app/trip-data-pl.json`), Romania v1 (`app/trip-data-ro.json`); choose the country at the top (link straight to one with `?d=cz`, `?d=hu`, `?d=pl` or `?d=ro`): overview, map with all routes, day-by-day view, flights, hotels, car and budget, in Hebrew and English.
Open on the phone: https://yanik1983.github.io/Trip-to-Cheque-republic/app/
