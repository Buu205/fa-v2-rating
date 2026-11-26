"""Read the input files (CSV or Parquet, same stem) from one data folder.

Files, columns and source metric codes are listed in docs/06-du-lieu-dau-vao.md. A blank cell is a
missing figure and stays blank; nothing here fills a gap with 0 or carries a value forward.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .rules import EXCHANGES


def read(folder: Path, stem: str, required: bool = True) -> pd.DataFrame | None:
    for ext, reader in ((".parquet", pd.read_parquet), (".csv", pd.read_csv)):
        p = Path(folder) / f"{stem}{ext}"
        if p.exists():
            df = reader(p)
            for c in ("report_date", "date"):
                if c in df:
                    df[c] = pd.to_datetime(df[c])
            return df
    if required:
        raise FileNotFoundError(f"{stem}.parquet or {stem}.csv not found in {folder}")
    return None


def stocks(folder: Path, entity: str) -> pd.DataFrame:
    """Listed names of one entity type on HOSE or HNX."""
    s = read(folder, "stocks")
    return s[(s.entity_type.str.upper() == entity.upper()) & s.exchange.isin(EXCHANGES)]


def corrections(folder: Path, entity: str, panel: pd.DataFrame) -> pd.DataFrame:
    """Apply figures checked one by one against the published statement (corrections file),
    overriding what the source holds for that cell."""
    fix = read(folder, "corrections", required=False)
    if fix is None:
        return panel
    fix = fix[fix.entity.str.lower() == entity]
    panel = panel.set_index(["ticker", "report_date"])
    for r in fix.itertuples():
        key = (r.ticker, pd.Timestamp(r.report_date))
        if key in panel.index and r.column in panel.columns:
            panel.loc[key, r.column] = float(r.value)
    return panel.reset_index()


def derive_company(p: pd.DataFrame) -> pd.DataFrame:
    """Lines the BSC wide table derives, built from their parts when the file lacks them
    (same formulas as the source: a blank part counts as nothing)."""
    p = p.copy()
    if "ebit" not in p:
        p["ebit"] = p.gross_profit.fillna(0) + p.selling_expense.fillna(0) + p.admin_expense.fillna(0)
    if "total_debt" not in p:
        p["total_debt"] = p.st_debt.fillna(0) + p.lt_debt.fillna(0)
    return p


def panel(folder: Path, entity: str) -> pd.DataFrame:
    p = read(folder, f"{entity}_quarterly")
    names = stocks(folder, entity)
    keep = ["ticker", "exchange"] + (["icb_l1", "icb_l2"] if entity == "company" else [])
    p = p.merge(names[keep], on="ticker", how="inner")
    p = corrections(folder, entity, p)
    return derive_company(p) if entity == "company" else p
