"""FA_V2 for securities companies (brokers): Scale 50%, Health 30%, Profit 20% (docs/03-chung-khoan.md)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data, scoring
from .rules import SECURITY


def indicators(p: pd.DataFrame) -> pd.DataFrame:
    p = scoring.consecutive_quarters(p)
    key = [p.ticker, p._run]
    tsum = lambda s: scoring.ttm(s, key)
    roll = lambda s, n: scoring.rolling_mean(s, key, n)
    F = p[["ticker", "report_date", "exchange"]].copy()
    equity = p.parent_equity.fillna(p.total_equity)
    # total net profit, not the parent's share: the source sometimes books the whole profit on the
    # minority line and leaves the parent's share blank; brokers carry almost no minority
    npat = p.npat
    npat_ttm = tsum(npat)
    # Scale
    F["assets_avg4"] = roll(p.total_assets, 4)
    F["equity_avg4"] = roll(equity, 4)
    F["margin_avg4"] = roll(p.margin, 4)
    # Health
    F["loan_equity"] = roll((p.margin / equity).where(equity > 0), 4)
    # FVTPL share of investment gains, TTM. A broker without an HTM or AFS book has no such line,
    # so a blank HTM or AFS income reads as none; the FVTPL line itself must be reported.
    fv, htm, afs = tsum(p.inv_income), tsum(p.htm_income.fillna(0)), tsum(p.afs_income.fillna(0))
    gain = fv + htm + afs
    F["fvtpl_share"] = (fv / gain).where(gain > 0)
    # cash and HTM deposits over total assets, quarter end. No HTM balance and no HTM income means
    # no such book (0); a blank balance next to reported HTM income stays blank.
    htm_bal = p.htm.where(p.htm.notna(), np.where(p.htm_income.fillna(0) == 0, 0.0, np.nan))
    F["liquid"] = (p.cash + htm_bal) / p.total_assets.where(p.total_assets > 0)
    # Profit
    eq2 = roll(equity, 2)
    F["roe"] = (npat_ttm / eq2).where(eq2 > 0)
    roe_q = (npat * 4 / equity).where(equity > 0)
    F["roe_min4"] = roe_q.groupby(key).transform(lambda x: x.rolling(4, min_periods=4).min())
    # guards
    loss = npat < 0
    F["g1_two_loss"] = loss & loss.groupby(key).shift(1, fill_value=False)
    F["g2_capital"] = scoring.capital_impaired(equity, p.retained_earnings, p.charter_capital)
    F["lasting_loss"] = (npat_ttm < 0) & F.g1_two_loss
    return F.replace([np.inf, -np.inf], np.nan)


def build(folder: Path) -> pd.DataFrame:
    return scoring.rate(indicators(data.panel(folder, "security")), SECURITY).assign(group="security")
