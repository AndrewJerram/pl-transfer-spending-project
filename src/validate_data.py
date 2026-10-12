"""
Sanity checks on data/processed/analysis_table.csv. Run after
build_analysis_table.py. Catches problems the joins can't: duplicate rows,
incomplete seasons, missing wage/transfer data, and hand-typo outliers in
the manually compiled wage bills.

Usage:
    python src/validate_data.py
"""
import pandas as pd
from pathlib import Path

PROC_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
problems = 0


def flag(msg):
    global problems
    problems += 1
    print(f"PROBLEM: {msg}")


def main():
    df = pd.read_csv(PROC_DIR / "analysis_table.csv")
    seasons = sorted(df["Season"].unique())
    latest = seasons[-1]  # may be in progress, so some checks skip it
    print(f"{len(df)} club-seasons across {len(seasons)} seasons ({seasons[0]} to {latest})\n")

    # 1. Duplicate club-seasons
    dupes = df[df.duplicated(["Season", "Team"], keep=False)]
    if len(dupes):
        flag(f"duplicate Season/Team rows:\n{dupes[['Season','Team']].to_string(index=False)}")

    # 2. Every season should have 20 clubs, and finished seasons 38 games each
    for s in seasons:
        sdf = df[df["Season"] == s]
        if len(sdf) != 20:
            flag(f"{s} has {len(sdf)} clubs in standings, expected 20")
        if s != latest:
            bad = sdf[sdf["Pld"] != 38]
            if len(bad):
                flag(f"{s}: clubs without 38 games played: {list(bad['Team'])}")
        if sdf["W"].sum() != sdf["L"].sum():
            flag(f"{s}: total wins ({sdf['W'].sum()}) != total losses ({sdf['L'].sum()})")

    # 3. Transfer coverage
    miss = df[df["net_spend_eur"].isna()]
    if len(miss):
        flag(f"{len(miss)} club-seasons missing transfer data, e.g.\n{miss[['Season','Team']].head(10).to_string(index=False)}")

    # 4. Wage coverage per season (latest season may legitimately be empty)
    if "wage_bill_gbp_m" not in df.columns:
        flag("no wage_bill_gbp_m column - run load_wages.py then build_analysis_table.py")
    else:
        for s in seasons:
            n = df[(df["Season"] == s)]["wage_bill_gbp_m"].notna().sum()
            if n < 20 and s != latest:
                flag(f"{s}: only {n}/20 clubs have a wage bill")
        # 5. Typo hunting: wage bill vs the same club's neighbouring seasons
        w = df.dropna(subset=["wage_bill_gbp_m"]).sort_values(["Team", "Season"]).copy()
        w["prev"] = w.groupby("Team")["wage_bill_gbp_m"].shift(1)
        w["ratio"] = w["wage_bill_gbp_m"] / w["prev"]
        odd = w[(w["ratio"] > 1.8) | (w["ratio"] < 0.55)]
        if len(odd):
            print("\nCHECK BY HAND (wage bill moved >80% up or >45% down vs the club's previous "
                  "season in the data - could be real, e.g. promotion or a takeover, or a typo):")
            print(odd[["Season", "Team", "prev", "wage_bill_gbp_m"]].to_string(index=False))
        # 6. League-wide total per season, to compare against published totals
        print("\nTotal wage bill per season (£m) - compare against published league totals:")
        print(df.groupby("Season")["wage_bill_gbp_m"].sum().round(0).to_string())

    print(f"\n{problems} hard problem(s) found.")


if __name__ == "__main__":
    main()