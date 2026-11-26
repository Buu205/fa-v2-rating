# FA_V2: xếp hạng cơ bản cho vay ký quỹ

Bộ chấm hạng A, B, C, D, E (Loại) và NR (Chưa chấm) cho cổ phiếu trên HOSE và HNX, dựa trên báo cáo tài chính quý. Bộ chấm phủ ba nhóm: doanh nghiệp phi tài chính, công ty chứng khoán và ngân hàng.

## Cài đặt và chạy

```bash
pip install -r requirements.txt
python -m fa_v2 --data <thư mục dữ liệu> --out output
python -m fa_v2 --data <thư mục dữ liệu> --quarter 2026-09-30 --backtest
pytest -q
```

Lệnh chạy ghi ra thư mục `output/` bốn file:

- `grades_history.csv`: hạng của mọi quý, cả ba nhóm;
- `final_list_<quý>.csv`: danh sách của một quý;
- `xep-hang-fa-v2-<năm>-Q<quý>.xlsx`: bản Excel gồm một trang tổng, một trang cho mỗi nhóm và một trang hướng dẫn cách đọc;
- `backtest.json`: kết quả kiểm định, chỉ có khi chạy với `--backtest`.

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `fa_v2/rules.py` | **Mọi quy tắc**: tỷ trọng, chỉ số, ngưỡng, chốt chặn. Muốn đổi quy tắc thì chỉ sửa ở file này |
| `fa_v2/scoring.py` | Điểm theo phân vị, hạng, băng giữ hạng, các chốt chặn |
| `fa_v2/company.py`, `security.py`, `bank.py` | Chỉ số và hạng của từng nhóm |
| `fa_v2/data.py` | Đọc dữ liệu đầu vào và áp các số đã sửa tay |
| `fa_v2/report.py` | Danh sách cuối quý, xuất CSV và Excel |
| `fa_v2/backtest.py` | Kiểm định hạng với diễn biến giá sau đó |
| `docs/` | Tài liệu công thức bằng tiếng Việt, đọc theo thứ tự 01 đến 07 |
| `tests/` | Kiểm thử quy tắc, kèm phép so với bộ hạng tham chiếu nếu có |

## Tài liệu

1. [Tổng quan](docs/01-tong-quan.md)
2. [Phi tài chính](docs/02-phi-tai-chinh.md)
3. [Chứng khoán](docs/03-chung-khoan.md)
4. [Ngân hàng](docs/04-ngan-hang.md)
5. [Chốt chặn và ổn định hạng](docs/05-chot-chan-va-on-dinh.md)
6. [Dữ liệu đầu vào và mã BSC](docs/06-du-lieu-dau-vao.md)
7. [Kiểm định](docs/07-kiem-dinh.md)

## So với bộ hạng tham chiếu

Đặt hai biến môi trường rồi chạy kiểm thử:

- `FA_V2_DATA`: đường dẫn tới thư mục dữ liệu;
- `FA_V2_REFERENCE`: đường dẫn tới file CSV tham chiếu, gồm các cột `ticker`, `report_date`, `group`, `grade`.

Sau đó chạy `pytest -q`. Kiểm thử sẽ báo mọi dòng có hạng khác với file tham chiếu.

Repo không chứa dữ liệu. Bên dùng cần tự chuẩn bị dữ liệu theo đặc tả ở mục 6 của tài liệu.
