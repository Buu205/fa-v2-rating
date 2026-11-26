# 2. Doanh nghiệp phi tài chính

Mã nguồn: `fa_v2/company.py`. Quy tắc: `rules.COMPANY`.

## Trụ, chỉ số và tỷ trọng

| Trụ (tỷ trọng) | Chỉ số | Công thức | Tốt khi |
|---|---|---|---|
| Quy mô (50%) | `revenue_ttm` | Doanh thu thuần cộng 4 quý | cao |
| | `revenue_steady` | Doanh thu TTM thấp nhất chia cao nhất trong 8 quý gần nhất (cần ít nhất 4 giá trị TTM dương) | cao, xếp hạng trong ngành |
| | `assets_avg4` | Tổng tài sản, trung bình 4 quý | cao |
| Sức khỏe (30%) | `fincost_cover` | EBIT TTM chia \|chi phí tài chính\| TTM | cao |
| | `netdebt_equity` | (Vay ngắn hạn + vay dài hạn − tiền − đầu tư ngắn hạn) chia vốn chủ | thấp |
| | `loss_quarters8` | Số quý có LNST công ty mẹ ≤ 0 trong 8 quý gần nhất (cần 4 quý có số) | thấp, chấm điểm cố định |
| Lợi nhuận (20%) | `roa` | LNST công ty mẹ TTM chia tổng tài sản trung bình 2 quý | cao |
| | `ebit_margin` | EBIT TTM chia doanh thu TTM | cao |

Trong cùng một trụ, các chỉ số nặng như nhau.

## Quy ước tính

- **Cửa sổ cuộn.** Phép cộng 4 quý và các phép trung bình chỉ chạy trên một chuỗi quý liền nhau. Thiếu một quý thì chuỗi bắt đầu lại từ quý sau đó.
- **EBIT** bằng lãi gộp cộng chi phí bán hàng và chi phí quản lý. Theo quy ước dấu của BSC, hai khoản chi phí này mang dấu âm.
- **`fincost_cover`** có ba trường hợp đặc biệt:
  - Không có chi phí tài chính và EBIT dương: ghi 1.000.000, mức tốt nhất.
  - Không có chi phí tài chính và EBIT âm: ghi 0.
  - Thiếu EBIT hoặc thiếu chi phí tài chính: để trống.
- **`netdebt_equity`** chỉ tính khi vốn chủ dương. Doanh nghiệp có tiền ròng nhận giá trị âm, nên được xếp tốt hơn.
- **`roa`** chỉ tính khi tài sản trung bình dương. **`ebit_margin`** chỉ tính khi doanh thu TTM dương.

## Cách chấm điểm

1. **Phân vị.** Tính phân vị theo hàm `PERCENTRANK.INC` của Excel rồi nhân 100. Phân vị lấy trong từng quý, trên toàn bộ mã HOSE và HNX.
2. **Đổi phân vị ra điểm.**

   | Phân vị | Điểm |
   |---|---|
   | Từ 90 | 4 |
   | Từ 70 | 3 |
   | Từ 40 | 2 |
   | Từ 20 | 1 |
   | Dưới 20 | 0 |

   Chỉ số "thấp là tốt" được lật phân vị (100 trừ phân vị) trước khi chấm.
3. **`revenue_steady` xếp hạng trong ngành.**
   - Ngành là ICB cấp 2. Ngành cấp 2 có dưới 10 mã trong quý thì gộp lên ICB cấp 1.
   - Lý do: doanh thu bất động sản ghi nhận theo bàn giao, nên thất thường vì cách hạch toán chứ không vì rủi ro.
4. **`loss_quarters8` chấm điểm cố định**, vì phần lớn các mã cùng có giá trị 0.

   | Số quý lỗ trong 8 quý | Điểm |
   |---|---|
   | 0 | 2 |
   | 1 | 1 |
   | Từ 2 trở lên | 0 |

## Ngưỡng hạng

| Hạng | Điểm tổng |
|---|---|
| A | từ 1,883 (113/60) |
| B | từ 1,650 (99/60) |
| C | từ 0,950 (57/60) |
| D | dưới 0,950 |

Các ngưỡng được đặt dựa trên mức giảm giá trong quá khứ. Mỗi ngưỡng thấp hơn nửa bước (1/60) so với điểm thấp nhất từng đạt hạng đó.

## Trần trả lãi

Mã đạt hạng A bị hạ xuống B khi EBIT không đủ bù chi phí tài chính. Mức đòi hỏi tùy theo quy mô:

| Nhóm mã | Hạ xuống B khi |
|---|---|
| 10% vốn hóa lớn nhất trong quý | `fincost_cover` dưới 1 |
| Các mã còn lại | `fincost_cover` dưới 2 |

Vốn hóa của một quý là vốn hóa trung bình các phiên trong quý (cột `cap_avg`). Thứ hạng vốn hóa tính trên mọi mã có chỉ số trong quý đó.

Các chốt chặn chung và luật Loại xem ở [mục 5](05-chot-chan-va-on-dinh.md).
