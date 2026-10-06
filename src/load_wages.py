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
    for path in sorted(RAW_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(
            f"No wage files found in {RAW_DIR} - see SOURCES.md to start "
            "compiling them."
        )
    combined = pd.concat(frames, ignore_index=True)

    unknown = set(combined["Team"].unique()) - VALID_TEAM_NAMES
    if unknown:
        print(
            f"WARNING: these team names in data/raw/wages/ aren't in the "
            f"standard name set and won't join cleanly: {sorted(unknown)}"
        )
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
