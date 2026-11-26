"""FA_V2 for banks: Scale 50%, Health 28.6%, Profit 21.4% (docs/04-ngan-hang.md)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data, scoring
from .rules import BANK, GRADES, RANK


INDICATORS = ("sh_assets", "sh_ppop", "sh_equity", "npl4", "g2_4", "llcr4", "roe12", "roe_min12", "ppop_ta")


def indicators(p: pd.DataFrame) -> pd.DataFrame:
    p = p.sort_values(["ticker", "report_date"]).reset_index(drop=True)
    for c in ("npl_ratio", "group2_ratio", "llcr"):
        p.loc[p[c] <= 0, c] = np.nan          # a zero ratio is a missing figure in this source
    roll = lambda s, n, m: s.groupby(p.ticker).transform(lambda x: x.rolling(n, min_periods=m).mean())
    share = lambda s: s / s.groupby(p.report_date).transform("sum")
    ppop = p.groupby("ticker").ppop.transform(lambda x: x.rolling(4, min_periods=4).sum())
    F = p[["ticker", "report_date", "exchange", "total_equity", "npatmi_ttm"]].copy()
    # Scale: share of the industry in the quarter
    F["sh_assets"] = share(p.total_assets)
    F["sh_equity"] = share(p.total_equity)
    F["sh_ppop"] = share(ppop.clip(lower=0))
    # Health: four-quarter averages (three needed)
    F["npl4"] = roll(p.npl_ratio, 4, 3)
    F["g2_4"] = roll(p.group2_ratio, 4, 3)
    F["llcr4"] = roll(p.llcr, 4, 3)
    F["npl4_yoy"] = F.npl4 - F.groupby("ticker").npl4.shift(4)
    # Profit
    F["roe12"] = roll(p.roea_ttm, 12, 8)
    F["roe_min12"] = p.roea_ttm.groupby(p.ticker).transform(lambda x: x.rolling(12, min_periods=8).min())
    F["ppop_ta"] = ppop / p.avg_total_assets * 100
    # two straight loss quarters, the earlier one being the quarter right before
    rd = p.report_date
    adjacent = (rd - rd.groupby(p.ticker).shift(1)).dt.days.between(85, 95)
    loss = p.npatmi < 0
    F["loss_2q"] = loss & adjacent & loss.groupby(p.ticker).shift(1, fill_value=False)
    F = F.replace([np.inf, -np.inf], np.nan)
    return F[F.report_date >= BANK["history_start"]].reset_index(drop=True)


def band(v, edges, higher_better: bool):
    """1-4 points on three fixed edges."""
    if pd.isna(v):
        return np.nan
    return 1 + sum((v > e) if higher_better else (v < e) for e in edges)


def score(D: pd.DataFrame) -> pd.DataFrame:
    B, cf = BANK["bands"], D.ticker.isin(BANK["consumer_finance"])
    tier = lambda col: (1 + sum((D.groupby("report_date")[col].rank(pct=True) > c).astype(float)
                                for c in BANK["scale_tiers"])).where(D[col].notna())
    pt = pd.DataFrame({c: tier(c) for c in BANK["scale"]}, index=D.index)
    pt["npl"] = [band(v, BANK["cf_bands"] if f else B["npl"], False) for v, f in zip(D.npl4, cf)]
    pt["g2"] = [band(v, BANK["cf_bands"] if f else B["g2"], False) for v, f in zip(D.g2_4, cf)]
    pt["llcr"] = D.llcr4.apply(band, args=(B["llcr"], True))
    pt["roe"] = D.roe12.apply(band, args=(B["roe"], True))
    pt["roe_min"] = D.roe_min12.apply(band, args=(B["roe_min"], True))
    pt["ppop_ta"] = D.ppop_ta.apply(band, args=(B["ppop_ta"], True))
    S = D[["ticker", "report_date", "exchange"]].copy()
    S["scale"] = pt[list(BANK["scale"])].mean(axis=1)
    S["health"] = pt[["npl", "g2", "llcr"]].mean(axis=1)
    S["profit"] = pt[["roe", "roe_min", "ppop_ta"]].mean(axis=1)
    S["score"] = sum(w * S[p] for p, w in BANK["weights"].items())
    S["grade_score"] = S.score.apply(lambda s: None if pd.isna(s) else next((g for c, g in BANK["cuts"] if s >= c), "D"))
    return S


def stabilise(D: pd.DataFrame, raw: pd.Series) -> pd.Series:
    """Downgrade at once. Upgrade one notch after two straight quarters above the current grade,
    each with NPL (4-quarter average) not above its level a year earlier. A quarter without a
    score is Not Rated, and the next scored quarter starts afresh, as for companies and brokers."""
    out = pd.Series(index=D.index, dtype=object)
    order = D.sort_values(["ticker", "report_date"]).index
    for _, idx in D.loc[order].groupby("ticker", sort=False).groups.items():
        cur, pend = None, 0
        for i in idx:
            g = raw[i]
            if g is None or pd.isna(g):
                out[i], cur, pend = None, None, 0
                continue
            if cur is None:
                cur = g
            elif RANK[g] > RANK[cur]:
                cur, pend = g, 0
            elif RANK[g] < RANK[cur]:
                ok = pd.notna(D.npl4_yoy[i]) and D.npl4_yoy[i] <= 0
                pend = pend + 1 if ok else 0
                if pend >= 2:
                    cur, pend = GRADES[RANK[cur] - 1], 0
            else:
                pend = 0
            out[i] = cur
    return out


def build(folder: Path) -> pd.DataFrame:
    D = indicators(data.panel(folder, "bank"))
    S = score(D)
    raw = S.grade_score.copy()
    raw[(D.npatmi_ttm <= 0) & raw.notna()] = "D"         # a loss over four quarters is High Risk
    S["grade_held"] = stabilise(D, raw)
    S["lasting_loss"] = (D.npatmi_ttm < 0) & D.loss_2q
    S["g2"] = D.total_equity <= 0
    S["g1"] = pd.NA            # banks have no two-loss-quarter notch; the loss rules above cover it
    excluded = S.g2 | S.lasting_loss
    S["grade"] = S.grade_held.where(~excluded, "E").fillna("NR")
    S["missing"] = scoring.missing(D, INDICATORS)
    return S.assign(group="bank")
