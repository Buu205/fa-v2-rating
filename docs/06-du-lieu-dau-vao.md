# 6. Dữ liệu đầu vào

Tất cả các file nằm chung một thư mục. Mỗi file ở dạng `.csv` hoặc `.parquet`, đặt tên đúng như bảng dưới.

- Mỗi dòng ứng với một mã trong một quý.
- `report_date` là ngày cuối quý, ví dụ 2026-09-30.
- Số liệu ghi theo từng quý, không lũy kế từ đầu năm. Đơn vị là đồng.

**Ô trống nghĩa là thiếu số, không phải 0.** Bộ chấm không tự điền vào chỗ thiếu.

## Danh sách file

| File | Bắt buộc | Nội dung |
|---|---|---|
| `stocks` | có | Danh mục mã, xem bảng dưới |
| `company_quarterly` | có | Báo cáo quý của doanh nghiệp phi tài chính, xem phần riêng |
| `security_quarterly` | có | Báo cáo quý của công ty chứng khoán, xem phần riêng |
| `bank_quarterly` | có | Báo cáo quý của ngân hàng, cần có từ quý 1/2018, xem phần riêng |
| `market_cap_quarterly` | có | `ticker`, `report_date`, `cap_avg` (vốn hóa trung bình các phiên trong quý) |
| `corrections` | không | Số đã đối chiếu tay với BCTC gốc, xem bảng dưới. File mẫu: `examples/corrections.csv` |
| `market_cap_latest` | không | `ticker`, `market_cap`. Chỉ dùng để hiển thị trong file Excel |
| `liquidity_quarterly` | không | `ticker`, `report_date`, `gtgd_med20` (tỷ đồng). Chỉ dùng để hiển thị |
| `prices` | không | `ticker`, `date`, `close_adj`. Chỉ dùng để kiểm định (`--backtest`) |

Các cột của `stocks`:

| Cột | Nội dung |
|---|---|
| `ticker` | Mã |
| `exchange` | HOSE, HNX hoặc UPCOM |
| `entity_type` | COMPANY, SECURITY hoặc BANK |
| `icb_l1` | Ngành ICB cấp 1 |
| `icb_l2` | Ngành ICB cấp 2 |
| `sector_vi` | Tên ngành để hiển thị |

Các cột của `corrections`. Mỗi dòng là một con số đã kiểm tra với BCTC gốc, và được dùng thay cho số của nguồn.

| Cột | Nội dung |
|---|---|
| `entity` | Nhóm mã |
| `ticker` | Mã |
| `report_date` | Quý |
| `column` | Tên cột cần sửa |
| `value` | Giá trị đúng |
| `source` | Nguồn đối chiếu |

## Phi tài chính: `company_quarterly`

| Cột | Mã BSC |
|---|---|
| `net_revenue` | CIS_10 |
| `gross_profit` | CIS_20 |
| `selling_expense` | CIS_25 (số âm) |
| `admin_expense` | CIS_26 (số âm) |
| `finance_cost` | CIS_22 |
| `npatmi` | CIS_61 |
| `total_assets` | CBS_270 |
| `total_equity` | CBS_400 |
| `st_debt` | CBS_320 |
| `lt_debt` | CBS_338 |
| `cash` | CBS_110 |
| `st_investments` | CBS_120 |
| `retained_earnings` | CBS_421 |
| `charter_capital` | CBS_411 |

Hai cột dưới đây là cột tính ra. Nếu file không có, bộ chấm tự tính, và trong phép cộng này ô trống được tính là 0:

- `ebit` = `gross_profit` + `selling_expense` + `admin_expense`
- `total_debt` = `st_debt` + `lt_debt`

## Chứng khoán: `security_quarterly`

| Cột | Mã BSC |
|---|---|
| `total_assets` | SBS_270 (bằng SBS_440) |
| `total_equity` | SBS_400 |
| `parent_equity` | SBS_410 |
| `npat` | SIS_200 |
| `margin` (dư nợ cho vay) | SBS_114 |
| `inv_income` (lãi FVTPL) | SIS_1 |
| `htm_income` | SIS_2 |
| `afs_income` | SIS_4 |
| `cash` | SBS_111 |
| `htm` | SBS_113 |
| `retained_earnings` | SBS_417 |
| `charter_capital` | SBS_411_1A |

## Ngân hàng: `bank_quarterly`

| Cột | Mã BSC hoặc công thức |
|---|---|
| `total_assets` | BBS_100 |
| `total_equity` | BBS_501 (gồm cổ đông thiểu số) |
| `npatmi` | BIS_22A |
| `npatmi_ttm` | `npatmi` cộng 4 quý |
| `ppop` | BIS_14A − \|BIS_14\|, tức tổng thu nhập hoạt động trừ chi phí hoạt động |
| `npl_ratio` (%) | (BNOT_4_3 + BNOT_4_4 + BNOT_4_5) / BBS_161 × 100 |
| `group2_ratio` (%) | BNOT_4_2 / BNOT_4 × 100 |
| `llcr` (%) | \|BBS_169\| / (BNOT_4_3 + BNOT_4_4 + BNOT_4_5) × 100 |
| `roea_ttm` (%) | `npatmi` × 4 / vốn chủ công ty mẹ bình quân 2 quý × 100 |
| `avg_total_assets` | Tổng tài sản bình quân 2 quý |
