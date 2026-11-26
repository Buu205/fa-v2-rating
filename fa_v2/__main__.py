"""python -m fa_v2 --data <folder> [--bsc <BSC csv folder>] [--quarter 2026-09-30] [--out output] [--backtest]"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from . import backtest, bsc, data, rate_all, report


def main() -> None:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description="FA_V2 margin grades")
    ap.add_argument("--data", type=Path, required=True, help="folder with the input files (docs/06-du-lieu-dau-vao.md)")
    ap.add_argument("--bsc", type=Path, help="folder with the 20 BSC export CSVs; rebuilds the three *_quarterly files in --data first")
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--quarter", help="quarter end for the final list, e.g. 2026-09-30 (default: latest)")
    ap.add_argument("--backtest", action="store_true", help="also check grades against prices (needs prices file)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.bsc:
        bsc.write_inputs(a.bsc, a.data)
    g = rate_all(a.data)
    g.to_csv(a.out / "grades_history.csv", index=False)
    q = pd.Timestamp(a.quarter) if a.quarter else g.report_date.max()
    d = report.final_list(g, a.data, q)
    d.drop(columns=["o"]).to_csv(a.out / f"final_list_{q:%Y-%m-%d}.csv", index=False)
    report.write_excel(d, a.out / f"xep-hang-fa-v2-{q.year}-Q{q.quarter}.xlsx", q)
    print(pd.crosstab(d.group_vn, d.grade, margins=True, margins_name="Tổng"))
    nr = d[d.grade == "NR"]
    if len(nr):
        print(f"\nCảnh báo: {len(nr)} mã chưa chấm vì thiếu dữ liệu gốc (chi tiết ở cột Ghi chú):")
        for r in nr.itertuples():
            print(f"  {r.group_vn:14} {r.ticker:6} thiếu: {r.missing or 'không rõ'}")
    if a.backtest:
        S = backtest.outcomes(g, data.read(a.data, "prices"))
        res = {grp: backtest.evaluate(S[S.group == grp]) for grp in ("company", "security", "bank")}
        json.dump(res, open(a.out / "backtest.json", "w"), indent=1, ensure_ascii=False)
        for grp, r in res.items():
            print(grp, "dd30", r["dd30"], "breach", r["breach"], "ic", r["ic"], "churn", r["churn_per_quarter"])


if __name__ == "__main__":
    main()
