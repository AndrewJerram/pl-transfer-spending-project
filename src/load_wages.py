"""
Combines the per-season wage bill CSVs in data/raw/wages/ (manually compiled -
see data/raw/wages/SOURCES.md for where each season's figures came from) into
one table. Unlike results and transfers, this data can't be auto-downloaded -
see SOURCES.md for the two main sources (Guardian, Swiss Ramble) and which
seasons still need filling in.

Usage:
    python src/load_wages.py
"""
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "wages"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Same target names as CLUB_NAME_MAP's values in load_transfers.py - kept
# here as a validation set so a typo'd club name in a wages CSV gets caught
# immediately rather than silently failing to join later.
VALID_TEAM_NAMES = {
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Burnley", "Cardiff", "Chelsea", "Crystal Palace", "Everton", "Fulham",
    "Huddersfield", "Hull", "Leeds", "Leicester", "Liverpool", "Man City",
    "Man United", "Middlesbrough", "Newcastle", "Norwich", "Nott'm Forest",
    "Sheffield United", "Southampton", "Stoke", "Sunderland", "Swansea",
    "Tottenham", "Watford", "West Brom", "West Ham", "Wigan", "Wolves",
    "Blackburn", "Blackpool", "Bolton", "Birmingham", "QPR", "Reading",
    "Luton", "Ipswich",
}


def load_all_seasons() -> pd.DataFrame:
    frames = []
    cols = ["Season", "Team", "wage_bill_gbp_m", "source_url"]
    for path in sorted(RAW_DIR.glob("*.csv")):
        df = pd.read_csv(path).dropna(how="all")
        df["wage_bill_gbp_m"] = pd.to_numeric(df["wage_bill_gbp_m"], errors="coerce")
        bad = df[df[["Season", "Team", "wage_bill_gbp_m"]].isna().any(axis=1)]
        if len(bad):
            print(f"WARNING: {path.name} has {len(bad)} row(s) with a missing or non-numeric value, skipped:")
            print(bad.to_string())
            df = df.drop(bad.index)
        frames.append(df.reindex(columns=cols))
    if not frames:
        raise FileNotFoundError(f"No wage files found in {RAW_DIR}")
    combined = pd.concat(frames, ignore_index=True)

    unknown = set(combined["Team"].unique()) - VALID_TEAM_NAMES
    if unknown:
        print(f"WARNING: unrecognised team names in data/raw/wages/: {sorted(unknown)}")
    return combined


def main():
    wages = load_all_seasons()
    wages.to_csv(OUT_DIR / "wages_by_club_season.csv", index=False)
    seasons_covered = sorted(wages["Season"].unique())
    print(f"Wrote {len(wages):,} club-seasons -> data/processed/wages_by_club_season.csv")
    print(f"Seasons covered so far: {', '.join(seasons_covered)}")
    print("See data/raw/wages/SOURCES.md for which seasons still need compiling.")


if __name__ == "__main__":
    main()
