"""Build the three quarterly input tables straight from the BSC export (the 20 CSV files
`{ENTITY}_{BALANCE_SHEET,INCOME,NOTE,...}.csv`, one column per metric code).

Rows: FREQ_CODE 'Q' only. A ticker code that is not a clean upper-case code is dropped, unless
it is the only filing for that quarter, in which case it is trimmed. When a file holds the same
ticker and quarter twice, the later row wins (BSC appends refilings). Blank cells stay blank,
except the expense lines in ZERO_IF_FILED.
Codes and formulas are listed in docs/06-du-lieu-dau-vao.md.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)
CLEAN = re.compile(r"[A-Z0-9]+")
KEY = ["ticker", "report_date"]

# column -> (file, code)
COMPANY = {
    "net_revenue": ("INCOME", "CIS_10"), "gross_profit": ("INCOME", "CIS_20"),
    "finance_cost": ("INCOME", "CIS_22"), "selling_expense": ("INCOME", "CIS_25"),
    "admin_expense": ("INCOME", "CIS_26"), "npatmi": ("INCOME", "CIS_61"),
    "cash": ("BALANCE_SHEET", "CBS_110"), "st_investments": ("BALANCE_SHEET", "CBS_120"),
    "total_assets": ("BALANCE_SHEET", "CBS_270"), "st_debt": ("BALANCE_SHEET", "CBS_320"),
    "lt_debt": ("BALANCE_SHEET", "CBS_338"), "total_equity": ("BALANCE_SHEET", "CBS_400"),
    "charter_capital": ("BALANCE_SHEET", "CBS_411"), "retained_earnings": ("BALANCE_SHEET", "CBS_421"),
}
SECURITY = {
    "inv_income": ("INCOME", "SIS_1"), "htm_income": ("INCOME", "SIS_2"), "afs_income": ("INCOME", "SIS_4"),
    "npat": ("INCOME", "SIS_200"),
    "cash": ("BALANCE_SHEET", "SBS_111"), "htm": ("BALANCE_SHEET", "SBS_113"),
    "margin": ("BALANCE_SHEET", "SBS_114"), "total_assets": ("BALANCE_SHEET", "SBS_270"),
    "total_equity": ("BALANCE_SHEET", "SBS_400"), "parent_equity": ("BALANCE_SHEET", "SBS_410"),
    "charter_capital": ("BALANCE_SHEET", "SBS_411_1A"), "retained_earnings": ("BALANCE_SHEET", "SBS_417"),
}
BANK = {
    "toi": ("INCOME", "BIS_14A"), "opex": ("INCOME", "BIS_14"), "npatmi": ("INCOME", "BIS_22A"),
    "total_assets": ("BALANCE_SHEET", "BBS_100"), "customer_loan": ("BALANCE_SHEET", "BBS_161"),
    "loan_provision": ("BALANCE_SHEET", "BBS_169"), "equity_and_funds": ("BALANCE_SHEET", "BBS_500"),
    "total_equity": ("BALANCE_SHEET", "BBS_501"), "minority_interest": ("BALANCE_SHEET", "BBS_700"),
    "loans_by_group": ("NOTE", "BNOT_4"), "group2": ("NOTE", "BNOT_4_2"),
    "group3": ("NOTE", "BNOT_4_3"), "group4": ("NOTE", "BNOT_4_4"), "group5": ("NOTE", "BNOT_4_5"),
}


def _clean_codes(df: pd.DataFrame, name: str) -> pd.DataFrame:
    code = df.SECURITY_CODE.astype(str)
    exact = code.str.fullmatch(CLEAN)
    stripped = code.str.strip()
    slot = stripped + "|" + df.REPORT_DATE.astype(str)
    rescued = ~exact & stripped.str.fullmatch(CLEAN) & ~slot.isin(set(slot[exact]))
    bad = ~exact & ~rescued
    if bad.any():
        log.warning("%s: dropped %d row(s) with a malformed ticker code %s", name, bad.sum(),
                    sorted(repr(c) for c in code[bad].unique())[:20])
    df = df[~bad].copy()
    df["SECURITY_CODE"] = df.SECURITY_CODE.astype(str).str.strip()
    return df


def _read(folder: Path, entity: str, kind: str, codes: list[str]) -> pd.DataFrame:
    path = Path(folder) / f"{entity}_{kind}.csv"
    head = pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns
    use = ["REPORT_DATE", "FREQ_CODE", "SECURITY_CODE"] + [c for c in codes if c in head]
    lost = sorted(set(codes) - set(head))
    if lost:
        log.warning("%s: codes not in the file, left blank: %s", path.name, lost)
    df = pd.read_csv(path, usecols=use, dtype={"SECURITY_CODE": str, "FREQ_CODE": str},
                     encoding="utf-8-sig", low_memory=False)
    df = df[df.FREQ_CODE.astype(str).str.strip() == "Q"]
    df = _clean_codes(df, path.name)
    df = df.drop_duplicates(["SECURITY_CODE", "REPORT_DATE"], keep="last")
    df = df.rename(columns={"SECURITY_CODE": "ticker", "REPORT_DATE": "report_date"}).drop(columns="FREQ_CODE")
    df["report_date"] = pd.to_datetime(df.report_date)
    for c in lost:
        df[c] = np.nan
    return df


def _load(folder: Path, entity: str, spec: dict) -> pd.DataFrame:
    out = None
    for kind in sorted({k for k, _ in spec.values()}):
        cols = {code: name for name, (k, code) in spec.items() if k == kind}
        part = _read(folder, entity, kind, list(cols)).rename(columns=cols)
        out = part if out is None else out.merge(part, on=KEY, how="outer")
    return out.sort_values(KEY).reset_index(drop=True)


# An expense line left blank on an income statement that was filed means the company had none
# of it, so it counts as zero. Gross profit is never filled: a quarter without it stays blank.
ZERO_IF_FILED = ("finance_cost", "selling_expense", "admin_expense")


def company(folder: Path) -> pd.DataFrame:
    c = _load(folder, "COMPANY", COMPANY)
    filed = c[["net_revenue", "gross_profit", "npatmi"]].notna().any(axis=1)
    for col in ZERO_IF_FILED:
        c.loc[filed, col] = c.loc[filed, col].fillna(0)
    return c


def security(folder: Path) -> pd.DataFrame:
    return _load(folder, "SECURITY", SECURITY)


def bank(folder: Path) -> pd.DataFrame:
    b = _load(folder, "BANK", BANK)
    g = b.groupby("ticker")
    eq = b.total_equity.where(b.total_equity.notna() & (b.total_equity != 0), b.equity_and_funds)
    b["total_equity"] = eq
    parent = eq - b.minority_interest.fillna(0)            # no minority line means none
    b["ppop"] = b.toi.fillna(0) - b.opex.fillna(0).abs()
    b["npatmi_ttm"] = g.npatmi.transform(lambda x: x.rolling(4, min_periods=4).sum())
    npl = b.group3.fillna(0) + b.group4.fillna(0) + b.group5.fillna(0)
    ratio = lambda num, den: (num / den.where(den != 0) * 100)
    b["npl_ratio"] = ratio(npl, b.customer_loan.fillna(0))
    b["group2_ratio"] = ratio(b.group2.fillna(0), b.loans_by_group.fillna(0))
    b["llcr"] = ratio(b.loan_provision.fillna(0).abs(), npl)
    avg2 = lambda s: s.groupby(b.ticker).transform(lambda x: x.rolling(2, min_periods=1).mean())
    b["avg_total_assets"] = avg2(b.total_assets)
    b["roea_ttm"] = ratio(b.npatmi * 4, avg2(parent))
    return b


def write_inputs(bsc_folder: Path, out: Path) -> None:
    """Write company_quarterly, security_quarterly and bank_quarterly (parquet) into `out`."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in (("company", company), ("security", security), ("bank", bank)):
        df = fn(bsc_folder)
        df.to_parquet(out / f"{name}_quarterly.parquet", index=False)
        log.info("%s_quarterly: %d rows, %s to %s", name, len(df), df.report_date.min().date(), df.report_date.max().date())
