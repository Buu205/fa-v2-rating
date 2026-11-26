"""The BSC export reader: row selection, ticker clean-up and the filed-statement zero rule."""
import pandas as pd

from fa_v2 import bsc

HEAD = "REPORT_DATE,REPORTED_DATE,FREQ_CODE,SECURITY_CODE,AUDITED,MONTH_IN_PERIOD"


def write(folder, name, codes, rows):
    lines = [HEAD + "," + ",".join(codes)] + [",".join(map(str, r)) for r in rows]
    (folder / name).write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")


def test_company_reader(tmp_path):
    inc = ["CIS_10", "CIS_20", "CIS_22", "CIS_25", "CIS_26", "CIS_61"]
    write(tmp_path, "COMPANY_INCOME.csv", inc, [
        ("2026-09-30", "", "Q", "AAA", "N", 3, 100, 20, "", -5, -3, 9),     # blank finance cost
        ("2026-09-30", "", "Q", "AAA", "Y", 3, 110, 22, "", -5, -3, 10),    # refiling, wins
        ("2026-09-30", "", "Y", "AAA", "N", 12, 400, 80, -1, -20, -12, 40),  # annual, ignored
        ("2026-09-30", "", "Q", "bbb", "N", 0, 1, 1, 1, 1, 1, 1),           # lower case, dropped
        ("2026-09-30", "", "Q", " CCC", "N", 3, 50, "", "", "", "", 2),      # trimmed, kept
    ])
    bs = ["CBS_110", "CBS_120", "CBS_270", "CBS_320", "CBS_338", "CBS_400", "CBS_411", "CBS_421"]
    write(tmp_path, "COMPANY_BALANCE_SHEET.csv", bs, [
        ("2026-09-30", "", "Q", "AAA", "N", 3, 1, 2, 30, 4, 5, 12, 10, 2),
    ])
    c = bsc.company(tmp_path).set_index("ticker")
    assert sorted(c.index) == ["AAA", "CCC"]
    assert c.loc["AAA", "net_revenue"] == 110
    assert c.loc["AAA", "finance_cost"] == 0
    assert c.loc["CCC", "selling_expense"] == 0
    assert pd.isna(c.loc["CCC", "gross_profit"])
    assert pd.isna(c.loc["CCC", "total_assets"])


def test_bank_ratios(tmp_path):
    write(tmp_path, "BANK_INCOME.csv", ["BIS_14A", "BIS_14", "BIS_22A"], [
        (d, "", "Q", "BBB", "N", 3, 10, -4, 3) for d in ("2026-03-31", "2026-06-30", "2026-09-30", "2026-12-31")
    ])
    write(tmp_path, "BANK_BALANCE_SHEET.csv", ["BBS_100", "BBS_161", "BBS_169", "BBS_500", "BBS_501", "BBS_700"], [
        (d, "", "Q", "BBB", "N", 3, 1000, 500, -12, 90, 100, 10) for d in ("2026-03-31", "2026-06-30", "2026-09-30", "2026-12-31")
    ])
    write(tmp_path, "BANK_NOTE.csv", ["BNOT_4", "BNOT_4_2", "BNOT_4_3", "BNOT_4_4", "BNOT_4_5"], [
        (d, "", "Q", "BBB", "N", 3, 500, 10, 4, 3, 3) for d in ("2026-03-31", "2026-06-30", "2026-09-30", "2026-12-31")
    ])
    b = bsc.bank(tmp_path).iloc[-1]
    assert b.ppop == 6
    assert b.npatmi_ttm == 12
    assert b.npl_ratio == 2.0
    assert b.group2_ratio == 2.0
    assert b.llcr == 120.0
    assert b.roea_ttm == 3 * 4 / 90 * 100
