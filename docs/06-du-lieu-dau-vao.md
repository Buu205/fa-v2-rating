# 6. Dữ liệu đầu vào

## Cách nhanh nhất: đọc thẳng file xuất của BSC

Repo đã có sẵn trong thư mục `data/` các file không lấy được từ BSC: danh mục mã, vốn hóa quý, vốn hóa mới nhất, thanh khoản quý và các số đã sửa tay. Phần còn thiếu chỉ là báo cáo tài chính quý. Bạn đặt 20 file CSV xuất từ BSC vào một thư mục, rồi chạy:

```bash
python -m fa_v2 --bsc <thư mục 20 file BSC> --data data --out output
```

Chương trình dựng ba file `company_quarterly`, `security_quarterly` và `bank_quarterly` trong `data/`, rồi chấm hạng. Mã nằm trong `fa_v2/bsc.py`. Chương trình đọc 7 file: `{COMPANY,SECURITY,BANK}_{BALANCE_SHEET,INCOME}.csv` và `BANK_NOTE.csv`.

Các luật khi đọc:

- Chỉ lấy dòng có `FREQ_CODE` là `Q`.
- **Mã viết sai thì bỏ**, ví dụ mã viết thường, có khoảng trắng thừa, hoặc là một ngày tháng. Mã chỉ thừa khoảng trắng được giữ lại khi quý đó không có dòng nào mang mã viết đúng. Mỗi lần chạy, chương trình in danh sách mã bị bỏ.
- **Cùng một mã và một quý xuất hiện hai lần trong một file thì lấy dòng sau**, vì BSC ghi bản nộp lại xuống cuối file.
- **Dòng chi phí bỏ trống được tính là 0** khi báo cáo kết quả kinh doanh của quý đó đã có. Luật này áp cho chi phí tài chính, chi phí bán hàng và chi phí quản lý, vì báo cáo đã nộp mà không ghi một khoản chi phí nghĩa là doanh nghiệp không có khoản đó. Lợi nhuận gộp bỏ trống thì vẫn để trống.
- Mọi ô trống khác giữ nguyên là trống.

**Lỗi đã biết trong file BSC.** Một số ô trong file BSC sai so với BCTC đã công bố. Các số đúng nằm trong `data/corrections.csv` và được dùng thay cho số của BSC. Ví dụ:

- NHH quý 3/2024: file ghi số lũy kế 9 tháng thay cho số của riêng quý đó;
- VPS quý 1/2025: lợi nhuận gộp ghi 1.468 tỷ, trong khi doanh thu chỉ 5 tỷ.

Khi phát hiện thêm lỗi, thêm một dòng vào file này kèm nguồn đối chiếu.

**Độ khớp với hệ thống gốc.** Đo trên dữ liệu tới quý 3/2026:

- Quý 3/2026 khớp 100%, 692 trên 692 mã.
- Toàn bộ lịch sử từ năm 2020 khớp 99,65%, tức 72 dòng lệch trên 20.696 dòng.
- Các dòng lệch thuộc những quý mà hệ thống gốc đã sửa số sau khi nhập, hoặc lấy thêm từ nguồn khác. Riêng nhóm chứng khoán, hệ thống gốc có thêm khoảng 300 dòng quý từ năm 2018 đến 2023 mà file BSC không có.

## Đặc tả từng file

Tất cả các file nằm chung một thư mục. Mỗi file ở dạng `.csv` hoặc `.parquet`, đặt tên đúng như bảng dưới.

- Mỗi dòng ứng với một mã trong một quý.
- `report_date` là ngày cuối quý, ví dụ 2026-09-30.
- Số liệu ghi theo từng quý, không lũy kế từ đầu năm. Đơn vị là đồng.

**Ô trống nghĩa là thiếu số, không phải 0.** Bộ chấm không tự điền vào chỗ thiếu.

### Danh sách file

| File | Bắt buộc | Nội dung |
|---|---|---|
| `stocks` | có | Danh mục mã, xem bảng dưới |
| `company_quarterly` | có | Báo cáo quý của doanh nghiệp phi tài chính, xem phần riêng |
| `security_quarterly` | có | Báo cáo quý của công ty chứng khoán, xem phần riêng |
| `bank_quarterly` | có | Báo cáo quý của ngân hàng, cần có từ quý 1/2018, xem phần riêng |
| `market_cap_quarterly` | có | `ticker`, `report_date`, `cap_avg` (vốn hóa trung bình các phiên trong quý) |
| `corrections` | không | Số đã đối chiếu tay với BCTC gốc, xem bảng dưới. Repo có sẵn `data/corrections.csv` |
| `market_cap_latest` | không | `ticker`, `market_cap`. Chỉ dùng để hiển thị trong file Excel |
| `liquidity_quarterly` | không | `ticker`, `report_date`, `gtgd_med20` (tỷ đồng). Chỉ dùng để hiển thị |
| `prices` | không | `ticker`, `date`, `close_adj`. Chỉ dùng để kiểm định (`--backtest`). Repo không kèm file này vì quá lớn |

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

### Phi tài chính: `company_quarterly`

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

Khi đọc từ file BSC, ba dòng chi phí tài chính, bán hàng và quản lý được tính là 0 nếu bỏ trống trên báo cáo đã nộp, như đã nêu ở trên.

Hai cột dưới đây là cột tính ra. Nếu file không có, bộ chấm tự tính, và trong phép cộng này ô trống được tính là 0:

- `ebit` = `gross_profit` + `selling_expense` + `admin_expense`
- `total_debt` = `st_debt` + `lt_debt`

### Chứng khoán: `security_quarterly`

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

### Ngân hàng: `bank_quarterly`

| Cột | Mã BSC hoặc công thức |
|---|---|
| `total_assets` | BBS_100 |
| `total_equity` | BBS_501 (gồm cổ đông thiểu số). Khi BBS_501 trống hoặc bằng 0 thì dùng BBS_500 |
| `npatmi` | BIS_22A |
| `npatmi_ttm` | `npatmi` cộng 4 quý |
| `ppop` | BIS_14A − \|BIS_14\|, tức tổng thu nhập hoạt động trừ chi phí hoạt động |
| `npl_ratio` (%) | (BNOT_4_3 + BNOT_4_4 + BNOT_4_5) / BBS_161 × 100 |
| `group2_ratio` (%) | BNOT_4_2 / BNOT_4 × 100 |
| `llcr` (%) | \|BBS_169\| / (BNOT_4_3 + BNOT_4_4 + BNOT_4_5) × 100 |
| `roea_ttm` (%) | `npatmi` × 4 / vốn chủ công ty mẹ bình quân 2 quý × 100. Vốn chủ công ty mẹ = `total_equity` − BBS_700; không có dòng BBS_700 thì coi như không có cổ đông thiểu số |
| `avg_total_assets` | Tổng tài sản bình quân 2 quý |
