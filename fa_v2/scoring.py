"""Scoring steps shared by companies and brokers: percentile points, pillar scores, grade from
score, guards, the cover ceiling and the hold band against grade flicker."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .rules import FIXED_POINTS, G2_ACCUMULATED_LOSS, GRADES, HOLD_MARGIN, PCT_EDGES, RANK


def consecutive_quarters(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by name and quarter and number each unbroken run of quarters (`_run`), so a rolling
    window never spans a missing quarter."""
    df = df.sort_values(["ticker", "report_date"]).reset_index(drop=True)
    q = pd.PeriodIndex(df.report_date, freq="Q")
    step = pd.Series(q.year * 4 + q.quarter, index=df.index)
    gap = step.groupby(df.ticker).diff().fillna(1) != 1
    df["_run"] = gap.groupby(df.ticker).cumsum()
    return df


def percentrank_inc(s: pd.Series) -> pd.Series:
    """Excel PERCENTRANK.INC x 100: share of the other names strictly below."""
    v = s.dropna()
    if len(v) < 2:
        return pd.Series(np.nan, index=s.index)
    below = v.rank(method="min") - 1
    return (below / (len(v) - 1) * 100).reindex(s.index)


def edge_points(pct: pd.Series, edges=PCT_EDGES) -> pd.Series:
    return sum((pct >= e).astype(float) for e in edges).where(pct.notna())


def indicator_points(F: pd.DataFrame, col: str, higher_better: bool, group: pd.Series | None = None) -> pd.Series:
    """0-4 points from the percentile inside the quarter (and inside `group` when given)."""
    if col in FIXED_POINTS:
        return sum((F[col] <= m).astype(float) for m in FIXED_POINTS[col]).where(F[col].notna())
    v = F[col] if higher_better else -F[col]
    keys = [F.report_date] if group is None else [F.report_date, group]
    return edge_points(v.groupby(keys).transform(percentrank_inc))


def pillar_scores(F: pd.DataFrame, model: dict) -> pd.DataFrame:
    """Mean points per pillar (blank when any indicator is blank) and the weighted score."""
    out = pd.DataFrame(index=F.index)
    for pillar, cols in model["pillars"].items():
        pts = pd.concat([indicator_points(F, c, hb, F.industry if c in model["industry_ranked"] else None).rename(c)
                         for c, hb in cols], axis=1)
        out[pillar] = pts.mean(axis=1).where(pts.notna().all(axis=1))
    out["score"] = sum(w * out[p] for p, w in model["weights"].items())
    return out


def grade_of(score: pd.Series, cuts) -> pd.Series:
    return score.apply(lambda s: "NR" if pd.isna(s) else next((g for c, g in cuts if s >= c), "D"))


def worse(a: str, b: str) -> str:
    return a if RANK[a] >= RANK[b] else b


def guard_g1(grade: pd.Series, two_loss_quarters: pd.Series) -> pd.Series:
    """G1: two straight loss quarters move the grade one notch down and no better than C."""
    out = grade.copy()
    hit = out.isin(GRADES) & two_loss_quarters.fillna(False).astype(bool)
    out[hit] = [worse(GRADES[min(RANK[g] + 1, 3)], "C") for g in out[hit]]
    return out


def capital_impaired(equity: pd.Series, retained_earnings: pd.Series, charter_capital: pd.Series) -> pd.Series:
    """G2: equity not positive, or accumulated loss from half of charter capital."""
    acc_loss = (-retained_earnings).clip(lower=0)
    return (equity <= 0) | (acc_loss >= G2_ACCUMULATED_LOSS * charter_capital.where(charter_capital > 0))


def exclude(grade: pd.Series, *flags: pd.Series) -> pd.Series:
    """Excluded (E, 0%) overrides every grade, Not Rated included: the rules read reported figures."""
    out = grade.copy()
    hit = pd.Series(False, index=grade.index)
    for f in flags:
        hit |= f.astype("boolean").fillna(False).astype(bool)
    out[hit] = "E"
    return out


def cover_ceiling(grade: pd.Series, cover: pd.Series, cap_pct: pd.Series, marks=(1.0, 2.0), spared=0.90) -> pd.Series:
    """EBIT under twice the finance cost holds A at B; the top 10% by cap only under once."""
    out = grade.copy()
    weak = (cover < marks[0]) | ((cover < marks[1]) & (cap_pct < spared))
    out[(out == "A") & weak] = "B"
    return out


def hold_band(df: pd.DataFrame, grade: pd.Series, score: pd.Series, cuts, margin: float = HOLD_MARGIN) -> pd.Series:
    """A one-notch move set by the score keeps the previous grade until the score clears the cutoff
    by `margin`. Two-notch moves, NR and E act at once."""
    cut = {RANK[g]: c for c, g in cuts}
    out = pd.Series(index=df.index, dtype=object)
    order = df.sort_values(["ticker", "report_date"]).index
    for _, idx in df.loc[order].groupby("ticker", sort=False).groups.items():
        cur = None
        for i in idx:
            g = grade[i]
            if g not in GRADES:
                out[i], cur = g, None
                continue
            if (cur is not None and g != cur and abs(RANK[g] - RANK[cur]) == 1
                    and abs(score[i] - cut[min(RANK[g], RANK[cur])]) < margin):
                g = cur
            out[i] = cur = g
    return out


def ttm(s: pd.Series, key) -> pd.Series:
    """Sum of the last four quarters inside an unbroken run, blank until four exist."""
    return s.groupby(key).transform(lambda x: x.rolling(4, min_periods=4).sum())


def rolling_mean(s: pd.Series, key, n: int, min_periods: int | None = None) -> pd.Series:
    return s.groupby(key).transform(lambda x: x.rolling(n, min_periods=min_periods or n).mean())


def rate(F: pd.DataFrame, model: dict, cap_pct: pd.Series | None = None) -> pd.DataFrame:
    """Score, grade, guards and exclusions for a company or broker indicator frame."""
    S = F[["ticker", "report_date", "exchange"]].join(pillar_scores(F, model))
    S["grade_score"] = grade_of(S.score, model["cuts"])
    S["grade_held"] = hold_band(S, S.grade_score, S.score, model["cuts"])
    g = guard_g1(S.grade_held, F.g1_two_loss)
    if cap_pct is not None:
        g = cover_ceiling(g, F.fincost_cover, cap_pct, model["cover_ceiling"], model["ceiling_spared_cap_pct"])
    S["grade"] = exclude(g, F.g2_capital, F.lasting_loss)
    S["g1"], S["g2"], S["lasting_loss"] = F.g1_two_loss, F.g2_capital, F.lasting_loss
    S["missing"] = missing(F, [c for ind in model["pillars"].values() for c, _ in ind])
    # an indicator ranked inside the industry cannot be scored without an industry, or when the
    # industry has a single name in the quarter
    for c in model["industry_ranked"]:
        lone = F.industry.notna() & (F.groupby(["report_date", "industry"])[c].transform("count") < 2)
        why = pd.Series(None, index=F.index, dtype=object)
        why[F.industry.isna()] = "ngành ICB (chưa phân ngành)"
        why[lone & F[c].notna()] = f"{c} (ngành chỉ có một mã)"
        S["missing"] = S.missing.where(why.isna(), S.missing.fillna("").str.cat(why.fillna(""), sep=", ").str.strip(", "))
    return S


def missing(F: pd.DataFrame, cols) -> pd.Series:
    """Indicators left blank in the row, comma-separated; blank when none is missing.
    A blank indicator means a source figure it needs was not reported (or not for enough quarters)."""
    blank = F[list(cols)].isna()
    return blank.apply(lambda r: ", ".join(c for c in cols if r[c]), axis=1).replace("", None)
