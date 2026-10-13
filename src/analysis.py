"""
Analysis of Premier League wage bills / transfer spend vs league performance.

Reads data/processed/analysis_table.csv (built by build_analysis_table.py),
prints a results report, saves it to data/processed/analysis_results.txt and
saves figures to figures/.

Design choices worth knowing about:
  * Wage bills and transfer spend are converted to SHARES of each season's
    league-wide total. That removes currency (GBP vs EUR) and inflation, so
    seasons are comparable without needing exchange-rate or CPI data.
  * "Top six vs the rest" is defined by WAGE RANK within the season, not by
    league finish. Splitting on finishing position would split on the outcome
    we're trying to explain, which mechanically weakens correlations inside
    each group (range restriction) and would make the result meaningless.
  * Club-seasons aren't independent (the same club appears many times), so
    regression standard errors are clustered by club.
  * Seasons without a wage bill (2025-26) are dropped.

Usage:
    python src/analysis.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

report = []


def say(text=""):
    print(text)
    report.append(str(text))


def heading(text):
    say("\n" + "=" * 70)
    say(text)
    say("=" * 70)


def load_and_engineer() -> pd.DataFrame:
    df = pd.read_csv(PROC / "analysis_table.csv")
    n_raw = len(df)
    df = df.dropna(subset=["wage_bill_gbp_m", "net_spend_eur", "gross_spend_eur"]).copy()
    say(f"Loaded {n_raw} club-seasons; {len(df)} have wage and transfer data.")
    say(f"Seasons used: {df['Season'].min()} to {df['Season'].max()} "
        f"({df['Season'].nunique()} seasons, {df['Team'].nunique()} clubs)")

    g = df.groupby("Season")
    df["wage_share_pct"] = 100 * df["wage_bill_gbp_m"] / g["wage_bill_gbp_m"].transform("sum")
    df["gross_spend_share_pct"] = 100 * df["gross_spend_eur"] / g["gross_spend_eur"].transform("sum")
    # net spend scaled by the season's total gross spend: keeps the sign (sellers go negative)
    df["net_spend_index"] = 100 * df["net_spend_eur"] / g["gross_spend_eur"].transform("sum")
    df["log_wage_share"] = np.log(df["wage_share_pct"])
    df["wage_rank"] = g["wage_bill_gbp_m"].rank(ascending=False, method="first")
    df["tier"] = np.select(
        [df["wage_rank"] <= 6, df["wage_rank"] <= 14],
        ["Top 6 by wages", "Middle (wage rank 7-14)"],
        default="Bottom (wage rank 15-20)",
    )
    df["team_id"] = df["Team"].astype("category").cat.codes
    return df


def spearman(x, y):
    rho, p = stats.spearmanr(x, y)
    return rho, p


def section_headline(df):
    heading("1. HEADLINE: does wage share relate to league performance?")
    r, p = stats.pearsonr(df["wage_share_pct"], df["Pts"])
    rho, rp = spearman(df["wage_share_pct"], df["Pts"])
    say(f"Wage share vs points   : Pearson r = {r:.3f} (R2 = {r*r:.3f}),  Spearman rho = {rho:.3f}  (n = {len(df)})")
    rho2, _ = spearman(df["wage_share_pct"], df["Position"])
    say(f"Wage share vs position : Spearman rho = {rho2:.3f}  (negative = higher wages, better finish)")
    say("Pooled across seasons; club-seasons are not independent, so p-values here are")
    say("optimistic. Use the clustered regression in section 4 for inference.")


def section_per_season(df):
    heading("2. PER-SEASON CHECK: wage rank vs points, one season at a time")
    rows = []
    for s, sdf in df.groupby("Season"):
        rho, _ = spearman(sdf["wage_bill_gbp_m"], sdf["Pts"])
        rows.append({"Season": s, "spearman_rho": rho, "n_clubs": len(sdf)})
    per = pd.DataFrame(rows)
    say(per.round(3).to_string(index=False))
    say(f"\nMean rho {per['spearman_rho'].mean():.3f}, range {per['spearman_rho'].min():.3f} "
        f"to {per['spearman_rho'].max():.3f}")
    low = per.nsmallest(2, "spearman_rho")
    say("Weakest seasons: " + ", ".join(f"{r.Season} ({r.spearman_rho:.2f})" for r in low.itertuples()))
    say("A season far weaker than the rest is either genuinely unusual (e.g. 2015-16)")
    say("or a sign of a data-entry error in that season's wage file - check it first.")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(per["Season"], per["spearman_rho"], color="#c8102e")
    ax.axhline(per["spearman_rho"].mean(), color="black", ls="--", lw=1, label="mean")
    ax.set_ylabel("Spearman rho (wage bill vs points)")
    ax.set_title("How strongly did wages predict points, season by season?")
    ax.set_ylim(0, 1)
    plt.setp(ax.get_xticklabels(), rotation=60, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "per_season_correlation.png", dpi=150)
    plt.close(fig)
    return per


def section_tiers(df):
    heading("3. PRIMARY QUESTION: does the relationship hold across the whole table?")
    say("Tiers are defined by wage rank within each season (not by finishing position).\n")
    rows = []
    for tier, tdf in df.groupby("tier"):
        rho, p = spearman(tdf["wage_share_pct"], tdf["Pts"])
        rows.append({
            "tier": tier, "n": len(tdf), "mean_pts": tdf["Pts"].mean(),
            "sd_pts": tdf["Pts"].std(), "spearman_rho": rho, "p_value": p,
        })
    say(pd.DataFrame(rows).round(3).to_string(index=False))
    say("\nRead 'sd_pts' alongside rho: a tier with little spread in points will show a")
    say("weak correlation partly for that reason alone. Interpret with caution.")


def section_regression(df):
    heading("4. REGRESSION (standard errors clustered by club)")
    groups = df["team_id"]
    m_lin = smf.ols("Pts ~ wage_share_pct", df).fit(cov_type="cluster", cov_kwds={"groups": groups})
    m_log = smf.ols("Pts ~ log_wage_share", df).fit(cov_type="cluster", cov_kwds={"groups": groups})
    for name, m, var in [("Linear  ", m_lin, "wage_share_pct"), ("Log-wage", m_log, "log_wage_share")]:
        lo, hi = m.conf_int().loc[var]
        say(f"{name}: Pts ~ {var}: coef = {m.params[var]:.2f} (95% CI {lo:.2f} to {hi:.2f}), R2 = {m.rsquared:.3f}")
    say("\nLinear: each extra percentage point of the league's total wage bill goes with")
    say(f"about {m_lin.params['wage_share_pct']:.1f} extra points. Log version captures diminishing returns:")
    say("a doubling of wage share goes with the coefficient x ln(2) extra points "
        f"(~{m_log.params['log_wage_share'] * np.log(2):.1f}).")
    best = m_log if m_log.rsquared > m_lin.rsquared else m_lin
    best_name = "log" if best is m_log else "linear"
    say(f"Better fit by R2: {best_name}.")

    heading("4b. COLLINEARITY: wage share vs transfer spend")
    r = df[["wage_share_pct", "gross_spend_share_pct"]].corr().iloc[0, 1]
    say(f"Correlation between wage share and gross transfer-spend share: {r:.3f}")
    X = df[["wage_share_pct", "gross_spend_share_pct"]].assign(const=1.0)
    vifs = {c: variance_inflation_factor(X.values, i) for i, c in enumerate(X.columns) if c != "const"}
    say("VIF: " + ", ".join(f"{k} = {v:.2f}" for k, v in vifs.items()) + "  (above ~5 means unstable coefficients)")
    m_both = smf.ols("Pts ~ wage_share_pct + gross_spend_share_pct", df).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    for var in ["wage_share_pct", "gross_spend_share_pct"]:
        lo, hi = m_both.conf_int().loc[var]
        say(f"Both together: {var}: coef = {m_both.params[var]:.2f} (95% CI {lo:.2f} to {hi:.2f})")
    say(f"R2 wages only {m_lin.rsquared:.3f} -> wages + transfers {m_both.rsquared:.3f}")
    say("If R2 barely moves and the transfer CI spans zero, transfer spend adds little once")
    say("wages are known. Transfer fees are a one-off outlay; wages are the ongoing cost.")
    return best, best_name


def section_residuals(df, best, best_name):
    heading("5. OVER- AND UNDER-PERFORMERS (residuals from the best model)")
    df["resid"] = best.resid
    cols = ["Season", "Team", "Pts", "Position", "wage_share_pct", "resid"]
    say("Most points ABOVE what wage share predicts:")
    say(df.nlargest(8, "resid")[cols].round(2).to_string(index=False))
    say("\nMost points BELOW what wage share predicts:")
    say(df.nsmallest(8, "resid")[cols].round(2).to_string(index=False))
    say("\nSanity check: well-known overachievers (e.g. Leicester 2015-16) should appear in the")
    say("first list. If famous cases are missing, something upstream may be wrong.")

    liv = df[df["Team"] == "Liverpool"].sort_values("Season")
    if len(liv):
        say("\nLiverpool across seasons (residual > 0 means outperformed their wage share):")
        say(liv[["Season", "Position", "Pts", "wage_share_pct", "resid"]].round(2).to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 6))
    pick = pd.concat([df.nlargest(8, "resid"), df.nsmallest(8, "resid")]).sort_values("resid")
    labels = pick["Team"] + " " + pick["Season"]
    ax.barh(labels, pick["resid"], color=np.where(pick["resid"] > 0, "#2a9d8f", "#c8102e"))
    ax.axvline(0, color="black", lw=1)
    ax.set_xlabel("Points above / below prediction from wage share")
    ax.set_title("Biggest over- and under-performers relative to wage share")
    fig.tight_layout()
    fig.savefig(FIG / "residual_outliers.png", dpi=150)
    plt.close(fig)


def section_robustness(df, best, best_name):
    heading("6. ROBUSTNESS")
    formula = "Pts ~ log_wage_share" if best_name == "log" else "Pts ~ wage_share_pct"
    var = formula.split("~")[1].strip()
    base = smf.ols(formula, df).fit()
    say(f"Baseline ({best_name}): coef = {base.params[var]:.2f}, R2 = {base.rsquared:.3f}")

    trimmed = df.loc[df["resid"].abs().sort_values().index[:-10]]
    t = smf.ols(formula, trimmed).fit()
    say(f"Dropping the 10 largest outliers: coef = {t.params[var]:.2f}, R2 = {t.rsquared:.3f}")

    rest = df[df["wage_rank"] > 6]
    r = smf.ols(formula, rest).fit()
    say(f"Only clubs ranked 7-20 by wages:  coef = {r.params[var]:.2f}, R2 = {r.rsquared:.3f}"
        "  <- does money still matter outside the top six?")

    slopes = []
    for s in df["Season"].unique():
        m = smf.ols(formula, df[df["Season"] != s]).fit()
        slopes.append(m.params[var])
    say(f"Leave-one-season-out coefficient range: {min(slopes):.2f} to {max(slopes):.2f}"
        "  <- narrow means no single season drives the result")

    early = df[df["Season"] <= "2015-16"]
    late = df[df["Season"] > "2015-16"]
    say(f"R2 by era: 2010-11 to 2015-16 = {smf.ols(formula, early).fit().rsquared:.3f}, "
        f"2016-17 onward = {smf.ols(formula, late).fit().rsquared:.3f}")
    say("This split coincides with the change of wage data source (Guardian -> Swiss Ramble),")
    say("so a difference here could be real OR a definitional discontinuity between sources.")


def section_prediction(df):
    heading("7. PREDICTIVE COMPARISON: simple vs complex model (held-out seasons)")
    feats = ["wage_share_pct", "gross_spend_share_pct", "net_spend_index"]
    X, y, groups = df[feats], df["Pts"], df["Season"]
    cv = GroupKFold(n_splits=min(5, groups.nunique()))
    models = {
        "Baseline (predict mean)": (DummyRegressor(), feats),
        "Linear, wage share only": (LinearRegression(), ["wage_share_pct"]),
        "Linear, all 3 features": (LinearRegression(), feats),
        "Random forest, all 3": (RandomForestRegressor(
            n_estimators=300, min_samples_leaf=5, random_state=0), feats),
    }
    for name, (model, cols) in models.items():
        pred = cross_val_predict(model, df[cols], y, groups=groups, cv=cv)
        rmse = np.sqrt(np.mean((y - pred) ** 2))
        say(f"{name:28s}: out-of-sample R2 = {r2_score(y, pred):6.3f}, RMSE = {rmse:.1f} pts")
    say("\nFolds hold out whole seasons, so a model can't learn from the season it is tested on.")
    say("If the random forest doesn't clearly beat the linear model, prefer the linear one:")
    say("it is simpler and you can explain it.")
    rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=0).fit(X, y)
    imp = pd.Series(rf.feature_importances_, index=feats).sort_values(ascending=False)
    say("\nRandom forest feature importance (shared between correlated features, read loosely):")
    say(imp.round(3).to_string())


def figure_scatter(df, best, best_name):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = {"Top 6 by wages": "#c8102e", "Middle (wage rank 7-14)": "#f4a261",
              "Bottom (wage rank 15-20)": "#2a9d8f"}
    for tier, tdf in df.groupby("tier"):
        ax.scatter(tdf["wage_share_pct"], tdf["Pts"], s=22, alpha=0.7, label=tier, color=colors[tier])
    xs = np.linspace(df["wage_share_pct"].min(), df["wage_share_pct"].max(), 200)
    pred = best.params["Intercept"] + best.params[
        "log_wage_share" if best_name == "log" else "wage_share_pct"
    ] * (np.log(xs) if best_name == "log" else xs)
    ax.plot(xs, pred, color="black", lw=1.5, label=f"Fit ({best_name})")
    for _, r in pd.concat([df.nlargest(4, "resid"), df.nsmallest(4, "resid")]).iterrows():
        ax.annotate(f"{r['Team']} {r['Season']}", (r["wage_share_pct"], r["Pts"]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("Share of league-wide wage bill that season (%)")
    ax.set_ylabel("League points")
    ax.set_title("Wage share vs points, Premier League 2010-11 to 2024-25")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "wage_share_vs_points.png", dpi=150)
    plt.close(fig)


def main():
    df = load_and_engineer()
    section_headline(df)
    section_per_season(df)
    section_tiers(df)
    best, best_name = section_regression(df)
    section_residuals(df, best, best_name)
    section_robustness(df, best, best_name)
    section_prediction(df)
    figure_scatter(df, best, best_name)

    heading("CAVEATS TO CARRY INTO THE WRITE-UP")
    say("* Association, not causation. Success also drives wages (bonuses, Champions League")
    say("  revenue, contract renewals), so wage share partly reflects results, not just buys them.")
    say("* Wage data comes from two sources with possibly different definitions of 'wages'.")
    say("* Transfer fees ignore wages, loans, free transfers and add-ons.")
    say("* ~15 seasons x 20 clubs, with repeat clubs: effective sample size is smaller than n.")

    (PROC / "analysis_results.txt").write_text("\n".join(report), encoding="utf-8")
    print(f"\nSaved report to {PROC / 'analysis_results.txt'} and figures to {FIG}")


if __name__ == "__main__":
    main()
