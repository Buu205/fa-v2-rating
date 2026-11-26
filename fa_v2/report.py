"""Final list of one quarter: every rated name of the three groups, as CSV and as an Excel file
with a sheet per group and a reading guide. A missing figure is a blank cell, never 0."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from . import data
from .rules import BANK, COMPANY, LOAN, SECURITY

GROUP_VN = {"company": "Phi tài chính", "bank": "Ngân hàng", "security": "Chứng khoán"}
GRADE_VN = {"A": "A", "B": "B", "C": "C", "D": "D", "E": "Loại", "NR": "Chưa chấm"}
FILL = {"A": "C6E5D3", "B": "DDECC8", "C": "FBE7B5", "D": "F6CDB9", "Loại": "D9D9D9", "Chưa chấm": "F2F2F2"}
num = lambda x: f"{x:.2f}".replace(".", ",")
CUTS = {GROUP_VN[g]: " / ".join(num(c) for c, _ in m["cuts"]) for g, m in (("company", COMPANY), ("bank", BANK), ("security", SECURITY))}
ORDER = {g: i for i, g in enumerate(["A", "B", "C", "D", "E", "NR"])}
quarter_vn = lambda d: f"quý {d.quarter}/{d.year}"


def note(r, quarter: str) -> str:
    t = lambda x: pd.notna(x) and bool(x)
    if r.grade == "NR":
        return f"Chưa chấm: thiếu dữ liệu gốc {quarter} cho chỉ số {r.missing}" if isinstance(r.missing, str) \
            else f"Thiếu ít nhất một chỉ số {quarter} nên không chấm"
    if r.grade == "E":
        why = [w for f, w in ((r.g2, "vốn chủ không dương hoặc lỗ lũy kế từ 50% vốn điều lệ"),
                              (r.lasting_loss, "lỗ 4 quý kèm lỗ hai quý liền")) if t(f)]
        return "Loại: " + "; ".join(why) if why else "Loại theo chốt chặn"
    if t(r.g1):
        return "Lỗ hai quý liền: hạ một bậc, tối đa C"
    if r.group == "company" and r.grade_held == "A" and r.grade == "B":
        return "Đủ điểm A nhưng EBIT chưa đủ bù chi phí tài chính: tối đa B"
    if r.group == "bank" and pd.notna(r.grade_score) and ORDER[r.grade_score] < ORDER[r.grade] <= 3:
        return "Đủ điểm hạng cao hơn, chờ hai quý đạt điều kiện nâng hạng (gồm nợ xấu không tăng so với năm trước)"
    if r.group != "bank" and pd.notna(r.grade_score) and r.grade_score != r.grade_held:
        return "Điểm sát ngưỡng: giữ hạng cũ theo quy tắc chống nhảy hạng"
    return ""


def final_list(grades: pd.DataFrame, folder: Path, quarter: pd.Timestamp | None = None) -> pd.DataFrame:
    g = grades.copy()
    quarter = quarter or g.report_date.max()
    prev = quarter - pd.offsets.QuarterEnd(1)
    now = g[g.report_date == quarter].copy()
    now["prev"] = now.ticker.map(g[g.report_date == prev].set_index("ticker").grade).fillna("NR")
    names = data.read(folder, "stocks").set_index("ticker")
    now["sector"] = now.ticker.map(names.sector_vi) if "sector_vi" in names else None
    cap = data.read(folder, "market_cap_latest", required=False)
    now["cap"] = now.ticker.map(cap.set_index("ticker").market_cap) / 1e9 if cap is not None else None
    liq = data.read(folder, "liquidity_quarterly", required=False)
    if liq is not None:
        liq = liq[liq.report_date == quarter].set_index("ticker").gtgd_med20
        now["liq"] = now.ticker.map(liq).where(lambda s: s > 0)   # no trade in the window is no figure
    else:
        now["liq"] = None
    now["loan"] = now.grade.map(LOAN) / 100                        # NR maps to blank, not 0
    now["note"] = [note(r, quarter_vn(quarter)) for r in now.itertuples()]
    now["group_vn"] = now.group.map(GROUP_VN)
    now["o"] = now.grade.map(ORDER)
    return now.sort_values("ticker").reset_index(drop=True)


COLS = [("STT", None, 6), ("Mã", "ticker", 8), ("Sàn", "exchange", 8), ("Nhóm", "group_vn", 14), ("Ngành", "sector", 32),
        ("Hạng", "grade", 11), ("Tỷ lệ vay theo hạng", "loan", 12), ("Điểm tổng (0-4)", "score", 10), ("Quy mô", "scale", 9),
        ("Sức khỏe", "health", 9), ("Lợi nhuận", "profit", 9), ("Hạng quý trước", "prev", 11),
        ("Vốn hóa (tỷ đồng)", "cap", 12), ("GTGD một phiên (tỷ đồng, trung vị 20 phiên)", "liq", 13), ("Ghi chú", "note", 58)]
HEAD, LINE, FONT = PatternFill("solid", fgColor="14323E"), Side(style="thin", color="D9DEE1"), "Arial"


def _head(ws, r, values):
    for i, v in enumerate(values, 1):
        c = ws.cell(r, i, v)
        c.font, c.fill = Font(name=FONT, bold=True, color="FFFFFF", size=10), HEAD
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _listing(ws, d, title):
    ws["A1"], ws["A1"].font = title, Font(name=FONT, bold=True, size=14)
    ws["A2"] = "Hạng theo mô hình, chưa xét thanh khoản, hạn mức và phê duyệt. Cách đọc ở trang cuối."
    ws["A2"].font = Font(name=FONT, italic=True, size=10, color="5A6770")
    _head(ws, 4, [c[0] for c in COLS])
    ws.row_dimensions[4].height = 44
    for n, r in enumerate(d.to_dict("records"), 1):
        for i, (_, key, _w) in enumerate(COLS, 1):
            v = n if key is None else r.get(key)
            v = GRADE_VN[v] if key in ("grade", "prev") else (None if not isinstance(v, str) and pd.isna(v) else v)
            c = ws.cell(n + 4, i, v)
            c.font, c.border = Font(name=FONT, size=10, bold=key in ("ticker", "grade")), Border(bottom=LINE)
            c.alignment = Alignment(horizontal="left" if key in ("ticker", "sector", "group_vn", "note") else
                                    "center" if key in (None, "exchange", "grade", "prev") else "right", vertical="center")
            if key in ("grade", "prev") and v:
                c.fill = PatternFill("solid", fgColor=FILL[v])
            c.number_format = {"loan": "0%", "cap": "#,##0", "liq": "#,##0.00"}.get(
                key, "0.00" if key in ("score", "scale", "health", "profit") else "General")
    for i, c in enumerate(COLS, 1):
        ws.column_dimensions[get_column_letter(i)].width = c[2]
    ws.freeze_panes, ws.sheet_view.showGridLines = "C5", False
    ws.auto_filter.ref = f"A4:{get_column_letter(len(COLS))}{len(d) + 4}"


def _summary(ws, d, title):
    ws["A1"], ws["A1"].font = title, Font(name=FONT, bold=True, size=14)
    shown = list(GRADE_VN.values())
    _head(ws, 3, ["Nhóm", *shown, "Tổng"])
    for i, grp in enumerate([*CUTS, "Tổng"]):
        x = d if grp == "Tổng" else d[d.group_vn == grp]
        ws.cell(4 + i, 1, grp)
        for j, s in enumerate(shown, 2):
            ws.cell(4 + i, j, int((x.grade.map(GRADE_VN) == s).sum()))
        ws.cell(4 + i, len(shown) + 2, len(x))
    ws.column_dimensions["A"].width = 18


def _guide(ws, quarter):
    w = lambda m, p: f"{m['weights'][p]:.1%}".replace(".", ",").replace(",0%", "%")
    lines = [("Cách đọc", True),
             (f"Kỳ chấm: báo cáo tài chính {quarter}, tính cộng 4 quý gần nhất. Phạm vi: mã HOSE và HNX gồm phi tài chính, ngân hàng và chứng khoán; không chấm bảo hiểm.", False),
             ("Hạng và tỷ lệ vay theo hạng: A 50%, B 40%, C 30%, D 20%, Loại 0%. Chưa chấm: thiếu dữ liệu, không có tỷ lệ.", False),
             ("Đây là hạng cơ bản theo mô hình. Tỷ lệ vay thực tế còn phụ thuộc thanh khoản, hạn mức và phê duyệt.", False),
             (f"Điểm tổng 0-4 = {w(COMPANY, 'scale')} Quy mô + {w(COMPANY, 'health')} Sức khỏe + {w(COMPANY, 'profit')} Lợi nhuận. "
              f"Riêng ngân hàng: Sức khỏe {w(BANK, 'health')} và Lợi nhuận {w(BANK, 'profit')}.", False),
             ("Ngưỡng điểm A / B / C:  " + ";  ".join(f"{k} {v}" for k, v in CUTS.items()), False),
             ("Hạng có thể khác ngưỡng điểm vì các chốt chặn và quy tắc chống nhảy hạng.", False), ("", False),
             ("Chốt chặn (phi tài chính và chứng khoán)", True),
             ("Loại: vốn chủ không dương; lỗ lũy kế từ 50% vốn điều lệ; hoặc lỗ 4 quý kèm lỗ hai quý liền.", False),
             ("Lỗ hai quý liền: hạ một bậc, tối đa C.", False),
             ("Trần trả lãi (chỉ phi tài chính): EBIT dưới 2 lần chi phí tài chính thì tối đa B; nhóm 10% vốn hóa lớn nhất dùng mốc 1 lần.", False),
             ("Chống nhảy hạng: điểm phải vượt ngưỡng ít nhất 0,20 thì mới đổi một bậc.", False),
             ("Ngân hàng: loại khi vốn chủ không dương, hoặc lỗ 4 quý kèm lỗ hai quý liền; lỗ 4 quý cộng lại thì hạng D. "
              "Hạ hạng áp ngay; nâng một bậc cần hai quý đạt điểm và nợ xấu không tăng so với năm trước.", False)]
    for i, (t, b) in enumerate(lines, 1):
        c = ws.cell(i, 1, t)
        c.font, c.alignment = Font(name=FONT, bold=b, size=12 if b else 10), Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 110


def write_excel(d: pd.DataFrame, out: Path, quarter: pd.Timestamp) -> None:
    q = quarter_vn(quarter)
    wb = Workbook()
    ws = wb.active
    ws.title = "Tất cả các mã"
    _listing(ws, d, f"Xếp hạng cơ bản FA_V2 cho vay ký quỹ, {q}")
    _summary(wb.create_sheet("Tổng hợp"), d, f"Số mã theo nhóm và hạng, {q}")
    for grp in CUTS:
        _listing(wb.create_sheet(grp), d[d.group_vn == grp].sort_values(["o", "score", "ticker"], ascending=[True, False, True]),
                 f"Xếp hạng cơ bản FA_V2: {grp.lower()}, {q}")
    _guide(wb.create_sheet("Cách đọc"), q)
    wb.save(out)
