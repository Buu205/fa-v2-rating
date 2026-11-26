"""FA_V2 for non-financial companies: Scale 50%, Health 30%, Profit 20% (docs/02-phi-tai-chinh.md)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data, scoring
from .rules import COMPANY


def indicators(p: pd.DataFrame) -> pd.DataFrame:
    p = scoring.consecutive_quarters(p)
    key = [p.ticker, p._run]
    tsum = lambda s: scoring.ttm(s, key)
    roll = lambda s, n: scoring.rolling_mean(s, key, n)
    F = p[["ticker", "report_date", "exchange", "icb_l1", "icb_l2"]].copy()
    # industry: ICB level 2, merged into level 1 when the quarter has fewer than the minimum peers
    n2 = F.groupby(["report_date", "icb_l2"]).ticker.transform("count")
    F["industry"] = F.icb_l2.where(n2 >= COMPANY["min_industry_peers"], F.icb_l1)

    npatmi_ttm = tsum(p.npatmi)
    F["revenue_ttm"] = tsum(p.net_revenue)
    ebit_ttm = tsum(p.ebit)
    # Scale
    F["assets_avg4"] = roll(p.total_assets, 4)
    # revenue steadiness: lowest over highest trailing-year revenue in the last eight quarters,
    # needs four trailing-year values (seven quarters of statements)
    rt = F.revenue_ttm.where(F.revenue_ttm > 0)
    lo = rt.groupby(key).transform(lambda x: x.rolling(8, min_periods=4).min())
    hi = rt.groupby(key).transform(lambda x: x.rolling(8, min_periods=4).max())
    F["revenue_steady"] = lo / hi
    # Health
    # cover on total finance cost: no cost with a positive EBIT is the best cover, an operating loss is 0
    fin_ttm = tsum(p.finance_cost.abs())
    F["fincost_cover"] = (ebit_ttm / fin_ttm.where(fin_ttm > 0)).where(
        fin_ttm > 0, np.where(ebit_ttm > 0, 1e6, 0.0)).where(ebit_ttm.notna() & fin_ttm.notna())
    # borrowings less cash and short-term investments, over equity; net cash is negative and ranks by size
    F["netdebt_equity"] = (p.total_debt - p.cash - p.st_investments) / p.total_equity.where(p.total_equity > 0)
    # quarters without a positive parent profit among the last eight reported (four needed)
    F["loss_quarters8"] = (p.npatmi <= 0).astype(float).where(p.npatmi.notna()).groupby(key).transform(
        lambda x: x.rolling(8, min_periods=4).sum())
    # Profit
    ta2 = roll(p.total_assets, 2)
    F["roa"] = (npatmi_ttm / ta2).where(ta2 > 0)
    F["ebit_margin"] = (ebit_ttm / F.revenue_ttm).where(F.revenue_ttm > 0)
    # guards
    loss = p.npatmi < 0
    F["g1_two_loss"] = loss & loss.groupby(key).shift(1, fill_value=False)
    F["g2_capital"] = scoring.capital_impaired(p.total_equity, p.retained_earnings, p.charter_capital)
    F["lasting_loss"] = (npatmi_ttm < 0) & F.g1_two_loss
    F["cap_avg"] = p.cap_avg
    return F.replace([np.inf, -np.inf], np.nan)


def build(folder: Path) -> pd.DataFrame:
    p = data.panel(folder, "company")
    cap = data.read(folder, "market_cap_quarterly")
    p = p.merge(cap[["ticker", "report_date", "cap_avg"]], on=["ticker", "report_date"], how="left")
    F = indicators(p)
    cap_pct = F.cap_avg.groupby(F.report_date).rank(pct=True)
    return scoring.rate(F, COMPANY, cap_pct).assign(group="company")
