# Does Spending Buy Success?
Premier League wage bills, transfer spend, and league performance, 2010-11 to present.

## Research questions
1. **Primary:** How strongly does wage bill correlate with final league position,
   and does that relationship hold across the whole table or only at the extremes
   (top-six vs. rest)?
2. How strongly does wage bill correlate with points compared to net transfer spend?
   (Treated as a secondary, caveated question - wage bill and transfer spend are
   likely collinear, so "which matters more" is a harder claim to make cleanly.)
3. Supporting: how much does spending efficiency (points per £m of wage bill) vary
   between clubs?
4. Future work (not in v1): has the strength of the spend-performance relationship
   changed over time as broadcast revenue has grown? Flagged as risky with ~15
   seasons of data - would need a proper structural-break test, not just eyeballing
   a trend line.

## Data sources
- **Results / points / goals:** [football-data.co.uk](https://www.football-data.co.uk/englandm.php)
  - `src/fetch_results.py` downloads one CSV per season into `data/raw/results/`.
  - `data/raw/results/1011_E0.csv` in this repo is a small **sample** (a handful of
    matches) just to keep the schema pinned down for development - run
    `fetch_results.py` on a machine with normal internet access to pull full seasons.
- **Transfer spend:** per-season CSVs of every Premier League transfer (player,
  fee, in/out) from [eordo/transfermarkt-data](https://github.com/eordo/transfermarkt-data),
  itself built on the [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets)
  project. `data/raw/transfers/` has the 2010-2025 season files already copied in,
  and `src/load_transfers.py` turns them into gross spend / gross income / net
  spend per club per season, in euros. Live scraping wasn't necessary here since
  this pre-built dataset already covers exactly what's needed - it's re-run
  weekly upstream if you want to refresh the raw files later.
- **Wage bills:** no clean free bulk source exists, so this is compiled season by
  season from two recurring journalism sources that source figures from actual
  club accounts: the Guardian's annual Premier League finances review (David Conn,
  best for 2010-11 through roughly 2015-16) and Swiss Ramble (swissramble.substack.com,
  best for 2016-17 onward). See `data/raw/wages/SOURCES.md` for a season-by-season
  status table and where to find each one. 2018-19 is done as a worked example;
  the rest still need compiling by hand.

## Project layout
```
data/
  raw/results/        one CSV per season from football-data.co.uk (sample only - see note above)
  raw/transfers/       one CSV per season, 2010-2025, from eordo/transfermarkt-data
  raw/wages/           (empty - hand-compiled wage bill data goes here)
  processed/          cleaned, combined datasets ready for analysis
src/
  fetch_results.py       downloads season results CSVs
  load_results.py        combines seasons, derives final league tables
  load_transfers.py      combines transfer CSVs into spend/income/net per club-season
  load_wages.py          combines hand-compiled wage CSVs (see data/raw/wages/SOURCES.md)
  build_analysis_table.py joins standings + spend + wages into one analysis-ready table
notebooks/               exploratory analysis (to be added)
```

## Setup
```
pip install -r requirements.txt
python src/fetch_results.py         # needs real internet access - see note above
python src/load_results.py
python src/load_transfers.py
python src/load_wages.py          # optional until data/raw/wages/ has more seasons filled in
python src/build_analysis_table.py
```

## Status
- [x] Results data pipeline (fetch + combine + derive standings)
- [x] Transfer spend data pipeline (gross spend / income / net per club-season)
- [x] Wage bill pipeline built, one season (2018-19) compiled as a worked example
- [x] Join spend + wages onto standings -> data/processed/analysis_table.csv
- [ ] Compile remaining 15 seasons of wage data (see data/raw/wages/SOURCES.md)
- [ ] Inflation-adjust spend and wages to real terms
- [ ] EDA: scatter plots, correlation by table tier
- [ ] Linear regression baseline + random forest comparison
- [ ] Robustness checks (exclude relegated clubs, check for outlier-driven results)
- [ ] Write-up

## Notes / caveats to keep in the final write-up
- Wage bill and transfer spend are likely collinear - check correlation between
  them before making any claim about which one "matters more."
- Watch for one big-spending underperformer driving the whole correlation - check
  robustness with and without outliers.
- Scope is 2010-11 onward because reliable wage bill data gets hard to source
  before then.
