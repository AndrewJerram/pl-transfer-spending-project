"""
Joins data/processed/standings_by_season.csv (from load_results.py) with
data/processed/spend_by_club_season.csv (from load_transfers.py) and, where
available, data/processed/wages_by_club_season.csv (from load_wages.py) into
one analysis-ready table: one row per club-season, with final position,
points, transfer spend/income/net, and wage bill where it's been compiled.

Run load_results.py and load_transfers.py first (and load_wages.py if you've
started filling in wage data - it's fine if that file doesn't exist yet, the
wage columns will just be empty for every row until it does).

Usage:
    python src/build_analysis_table.py
"""
import pandas as pd
from pathlib import Path

PROC_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def main():
    standings = pd.read_csv(PROC_DIR / "standings_by_season.csv")
    spend = pd.read_csv(PROC_DIR / "spend_by_club_season.csv")

    merged = standings.merge(
        spend[["Season", "Team", "gross_spend_eur", "gross_income_eur", "net_spend_eur"]],
        on=["Season", "Team"],
        how="left",
    )

    missing_spend = merged[merged["net_spend_eur"].isna()]
    if len(missing_spend):
        print(
            f"WARNING: {len(missing_spend)} club-seasons in standings have no matching "
            "transfer data (check CLUB_NAME_MAP in load_transfers.py, or these "
            "are promoted clubs whose season isn't in the transfer files):"
        )
        print(missing_spend[["Season", "Team"]].to_string(index=False))

    wages_path = PROC_DIR / "wages_by_club_season.csv"
    if wages_path.exists():
        wages = pd.read_csv(wages_path)
        merged = merged.merge(
            wages[["Season", "Team", "wage_bill_gbp_m"]],
            on=["Season", "Team"],
            how="left",
        )
        have_wages = merged["wage_bill_gbp_m"].notna().sum()
        print(
            f"\nWage data: {have_wages:,} of {len(merged):,} club-seasons have a "
            "wage bill filled in (see data/raw/wages/SOURCES.md for what's left)."
        )
    else:
        print(
            "\nNo wages_by_club_season.csv found - run src/load_wages.py once "
            "you've compiled at least one season's wage data (see "
            "data/raw/wages/SOURCES.md). Proceeding without a wage column."
        )

    merged.to_csv(PROC_DIR / "analysis_table.csv", index=False)
    print(f"\nWrote {len(merged):,} rows -> data/processed/analysis_table.csv")


if __name__ == "__main__":
    main()
