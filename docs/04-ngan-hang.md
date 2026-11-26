# 4. Ngân hàng

Mã code: `fa_v2/bank.py`. Quy tắc: `rules.BANK`.

Ngành ngân hàng chỉ có khoảng 27 mã, quá ít để xếp theo phân vị. Vì vậy hai trụ Sức khỏe và Lợi nhuận chấm theo ngưỡng cố định, mỗi chỉ số được từ 1 đến 4 điểm.

## Tỷ trọng

| Trụ | Tỷ trọng |
|---|---|
| Quy mô | 50% |
| Sức khỏe | 28,6% (50% × 4/7) |
| Lợi nhuận | 21,4% (50% × 3/7) |

## Quy mô: thị phần chia tầng

| Chỉ số | Công thức |
|---|---|
| `sh_assets` | Tổng tài sản chia tổng của cả ngành trong quý |
| `sh_ppop` | Lợi nhuận trước dự phòng TTM chia tổng ngành; giá trị âm tính là 0 |
| `sh_equity` | Vốn chủ chia tổng ngành |

Mỗi chỉ số được chấm theo vị trí phân vị trong quý:

| Vị trí | Điểm |
|---|---|
| Nửa trên | 4 |
| Từ 25% đến 50% | 3 |
| Từ 10% đến 25% | 2 |
| 10% dưới cùng | 1 |

## Sức khỏe và Lợi nhuận: ngưỡng cố định

| Trụ | Chỉ số | Công thức | Ba ngưỡng |
|---|---|---|---|
| Sức khỏe | `npl4` | Tỷ lệ nợ xấu (nợ nhóm 3 đến 5 chia cho vay khách hàng), trung bình 4 quý, cần ít nhất 3 quý | dưới 1,9%, 2,5% và 3,5% |
| Sức khỏe | `g2_4` | Tỷ lệ nợ nhóm 2, trung bình 4 quý | dưới 1,5%, 2,2% và 3,5% |
| Sức khỏe | `llcr4` | Dự phòng chia nợ xấu, trung bình 4 quý | trên 42%, 51% và 67% |
| Lợi nhuận | `roe12` | ROE TTM trung bình 12 quý, cần ít nhất 8 quý | trên 4,0%, 7,8% và 13,4% |
| Lợi nhuận | `roe_min12` | ROE TTM thấp nhất trong 12 quý | trên −5,3%, 0,2% và 5,3% |
| Lợi nhuận | `ppop_ta` | Lợi nhuận trước dự phòng TTM chia tổng tài sản bình quân | trên 0,8%, 1,25% và 2,1% |

Điểm của một chỉ số bằng 1 cộng số ngưỡng mà nó qua được:

| Số ngưỡng qua được | Điểm |
|---|---|
| Cả ba | 4 |
| Hai | 3 |
| Một | 2 |
| Không ngưỡng nào | 1 |

Hai lưu ý về ngưỡng:

- **VPB và HDB** có mảng tài chính tiêu dùng, nên nợ xấu và nợ nhóm 2 dùng ngưỡng rộng hơn: 3,0%, 4,0% và 5,5%.
- **Tỷ lệ bằng 0 hoặc âm** trong nguồn được coi là thiếu số. Quy tắc này áp cho nợ xấu, nợ nhóm 2 và tỷ lệ bao phủ.

## Ngưỡng hạng

Ngưỡng gốc là 3,25, 2,75 và 2,25. Mô hình dùng các ngưỡng này sau khi hạ 15%:

| Hạng | Điểm tổng |
|---|---|
| A | từ 2,7625 |
| B | từ 2,3375 |
| C | từ 1,9125 |
| D | dưới 1,9125 |

## Luật riêng của ngân hàng

- **Lỗ 4 quý.** LNST công ty mẹ cộng 4 quý từ 0 trở xuống thì hạng theo điểm chuyển thành D.
- **Ổn định hạng.**
  - Hạ hạng có hiệu lực ngay.
  - Nâng hạng chỉ lên một bậc mỗi lần, và cần hai quý liền đạt điểm của hạng cao hơn.
  - Trong cả hai quý đó, `npl4` không được cao hơn cùng kỳ năm trước.
- **Quý không có điểm** vì thiếu chỉ số thì nhận NR, giống hai nhóm kia. Quý có điểm kế tiếp bắt đầu lại từ hạng theo điểm. Danh sách cuối quý ghi rõ chỉ số nào bị thiếu.
- **Loại (E).** Ngân hàng bị loại khi rơi vào một trong hai trường hợp:
  - vốn chủ từ 0 trở xuống;
  - LNST cộng 4 quý âm và lỗ hai quý liền. Hai quý chỉ tính là liền nhau khi cách nhau 85 đến 95 ngày.
- **Lịch sử.** Chuỗi hạng bắt đầu từ quý 4/2019, là quý đầu tiên có đủ 12 quý ROE phía trước. Dữ liệu đầu vào cần có từ quý 1/2018.
