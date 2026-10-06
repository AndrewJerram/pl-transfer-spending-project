# Wage bill sources, season by season

No single free bulk dataset exists for this, so each season is sourced from
whichever credible outlet compiled it from actual club accounts that year.
Two recurring sources cover almost the whole 2010-11 to present range between
them:

**The Guardian's annual Premier League finances review** (by David Conn,
published every spring, usually titled something like "Premier League clubs'
wages revealed" or "Premier League finances"). Sourced directly from each
club's annual accounts, gives a full club-by-club breakdown. Best source for
**2010-11 through roughly 2015-16** - search "guardian premier league
finances wages [season] david conn" to find each year's piece.

**Swiss Ramble** (Twitter/X: @SwissRamble, and swissramble.substack.com).
A football finance analyst who's published detailed club-by-club wage
breakdowns, also sourced from club accounts, from roughly **2016-17
onward**, usually as an annual Twitter thread (sometimes mirrored in full by
sites like PlanetFootball, which is where the 2018-19 season below came
from - easier to read than reconstructing a tweet thread). Search "swiss
ramble premier league wages [season]" or check the Twitter/X account's
pinned threads and the Substack archive directly.

For seasons neither source conveniently covers, Deloitte's Annual Review of
Football Finance (published every June, covering the prior season) has
league-wide wage totals and ratios but not always a clean free per-club
breakdown - still worth checking as a cross-check on any figure that looks
off.

## Status by season

| Season  | Status | Source |
|---------|--------|--------|
| 2010-11 | not done | Guardian, search "premier league finances 2010-11" |
| 2011-12 | not done | Guardian - partial figures found for Man City (£202m) and Chelsea (£173m) during initial research, full table not yet pulled |
| 2012-13 | not done | Guardian - partial figures found for Man City (£233m), Man United (£181m), Chelsea (£173m), Arsenal (£154m), Liverpool (£131m), full table not yet pulled |
| 2013-14 | not done | Guardian |
| 2014-15 | not done | Guardian |
| 2015-16 | not done | Guardian or Swiss Ramble - transition year, check both |
| 2016-17 | not done | Swiss Ramble |
| 2017-18 | not done | Swiss Ramble |
| **2018-19** | **done** | Swiss Ramble via PlanetFootball - see `2018-19.csv` |
| 2019-20 | not done | Swiss Ramble via PlanetFootball - a similar article exists, full table not yet pulled |
| 2020-21 | not done | Swiss Ramble |
| 2021-22 | not done | Swiss Ramble - partial figures found for Man United (£384m), Liverpool (£366m), Man City (£354m), Chelsea (£340m), Brentford (£68m) during initial research |
| 2022-23 | not done | Swiss Ramble |
| 2023-24 | not done | Swiss Ramble, Alliance Fund/Capology also compiled this season |
| 2024-25 | not done | Swiss Ramble |
| 2025-26 | likely unavailable | season in progress - club accounts for a season aren't published until months after it ends, so this one may need to stay blank until well after the season finishes |

## File format

One CSV per season, named `<season>.csv` e.g. `2018-19.csv`, columns:
`Season,Team,wage_bill_gbp_m,source_url`. Use the same club names as
`CLUB_NAME_MAP` in `src/load_transfers.py` (i.e. "Man United" not
"Manchester United", "Nott'm Forest" not "Nottingham Forest") so it joins
cleanly - `src/load_wages.py` will warn about any name it doesn't recognise.
