# Data

`world_space/derived/` contains tables computed by `python -m worldspace` from the
**General Catalog of Artificial Space Objects** (GCAT), release 1.8.9, data update 2026 Nov 19:

> McDowell, J., 2020: General Catalog of Artificial Space Objects, https://planet4589.org/space/gcat

GCAT is © 2020-2026 Jonathan McDowell and released under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0). These tables are adapted from it (orbital launches
selected, organisations and catalogue objects joined, counts and masses aggregated, groups and
masses re-derived as described in the main README) and are shared under the same CC BY 4.0 licence.

| file | content |
|---|---|
| `orbital_launches.csv` | one row per orbital launch attempt: GCAT tag, date, vehicle, agency, country code, our operator group, launch-service code, outcome, GCAT OrbPay, cargo mass, payload and Starlink counts |
| `falcon_booster_flights.csv` | one row per Falcon first-stage flight: core serial, its flight number, days since its previous flight |
| `by_year.csv`, `successes_by_year.csv` | attempts and successes per year and operator group |
| `mass_by_year.csv`, `starlink_mass_by_year.csv` | cargo tonnes in orbit per year (successful launches) |
| `china_by_year.csv` | Chinese attempts: state / commercial arms of state groups / private start-ups |
| `payloads_by_year.csv` | payloads (and Starlinks) placed in orbit per year |
| `crosscheck_wikipedia.csv` | GCAT vs Wikipedia "<year> in spaceflight" by-country totals |
| `facts.json` | every headline number quoted in the README |

The raw GCAT files are downloaded into `world_space/raw/` (ignored by git).
