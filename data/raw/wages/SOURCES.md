# Wage bill sources, season by season

No single free bulk dataset exists for this, so each season is sourced from
whichever credible outlet compiled it from actual club accounts that year.
Two recurring sources cover almost the whole 2010-11 to present range between
them:


## Status by season

| Season  | Status | Source |
|---------|--------|--------|
| 2010-11 | not done | Guardian |
| 2011-12 | not done | Guardian |
| 2012-13 | not done | Guardian |
| 2013-14 | not done | Guardian |
| 2014-15 | not done | Guardian |
| 2015-16 | not done | Guardian or Swiss Ramble |
| 2016-17 | not done | Swiss Ramble |
| 2017-18 | not done | Swiss Ramble |
| 2018-19 | **done** | Swiss Ramble via PlanetFootball |
| 2019-20 | **done** | Swiss Ramble via PlanetFootball |
| 2020-21 | **done** | Swiss Ramble |
| 2021-22 | **done** | Swiss Ramble |
| 2022-23 | **done** | Swiss Ramble |
| 2023-24 | **done** | Swiss Ramble |
| 2024-25 | **done** | Deloitte  |
| 2025-26 | likely unavailable | season in progress - club accounts for a season aren't published until months after it ends, so this one may need to stay blank until well after the season finishes |

## File format

One CSV per season, named `<season>.csv` e.g. `2018-19.csv`, columns:
`Season,Team,wage_bill_gbp_m,source_url`. Use the same club names as
`CLUB_NAME_MAP` in `src/load_transfers.py` (i.e. "Man United" not
"Manchester United", "Nott'm Forest" not "Nottingham Forest") so it joins
cleanly - `src/load_wages.py` will warn about any name it doesn't recognise.
