"""Check the grades against what the share price did afterwards.

A grade is usable 45 days after quarter end (the statement deadline). From that day, over the
next 126 sessions (about six months): the largest fall from a running peak (mdd), the return,
and the lowest price against the price on the grade date (low_ratio). A grade works when the
deep-fall rate rises from A to D and the price rarely falls through the loan value of the grade.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .rules import GRADES, LOAN, RANK

LAG_DAYS, WINDOW, MIN_SESSIONS = 45, 126, 60


def outcomes(grades: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """`prices`: ticker, date, close_adj (adjusted close)."""
    series = {t: g.set_index("date").close_adj.sort_index().dropna() for t, g in prices.groupby("ticker")}
    rows = []
    for t, rd in grades[["ticker", "report_date"]].drop_duplicates().itertuples(index=False):
        s = series.get(t)
        if s is None:
            continue
        fwd = s[s.index >= rd + pd.Timedelta(days=LAG_DAYS)].iloc[:WINDOW]
        if len(fwd) >= MIN_SESSIONS:
            rows.append((t, rd, (fwd / fwd.cummax() - 1).min(), fwd.iloc[-1] / fwd.iloc[0] - 1, fwd.min() / fwd.iloc[0]))
    out = pd.DataFrame(rows, columns=["ticker", "report_date", "mdd", "ret", "low_ratio"])
    return grades.merge(out, on=["ticker", "report_date"], how="left")


def evaluate(S: pd.DataFrame, col: str = "grade") -> dict:
    """Per grade: observations, share falling 30% or more (dd30), share whose low fell through the
    loan value (breach); overall: rank correlation of grade with the fall (IC) and grade churn."""
    d = S[S[col].isin(GRADES)].sort_values(["ticker", "report_date"])
    prev = d.groupby("ticker")[col].shift()
    o = d[d.mdd.notna()]
    ics = [q[col].map(RANK).corr(-q.mdd, method="spearman") for _, q in o.groupby("report_date") if len(q) >= 10]
    by = lambda f: {g: (round(float(f(o[o[col] == g])), 3) if (o[col] == g).any() else None) for g in GRADES}
    ex = S[(S[col] == "E") & S.mdd.notna()]
    return {"n": {g: int((o[col] == g).sum()) for g in GRADES},
            "dd30": by(lambda x: (x.mdd <= -0.3).mean()),
            "breach": by(lambda x: (x.low_ratio <= x[col].map(LOAN) / 100).mean()),
            "median_ret": by(lambda x: x.ret.median()),
            "excluded_dd30": round(float((ex.mdd <= -0.3).mean()), 3) if len(ex) else None,
            "ic": round(float(np.nanmean(ics)), 3) if ics else None,
            "churn_per_quarter": round(float((d[col] != prev)[prev.notna()].mean()), 3)}
