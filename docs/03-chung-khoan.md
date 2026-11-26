# 3. Công ty chứng khoán

Mã nguồn: `fa_v2/security.py`. Quy tắc: `rules.SECURITY`.

## Trụ, chỉ số và tỷ trọng

| Trụ (tỷ trọng) | Chỉ số | Công thức | Tốt khi |
|---|---|---|---|
| Quy mô (50%) | `assets_avg4` | Tổng tài sản, trung bình 4 quý | cao |
| | `equity_avg4` | Vốn chủ, trung bình 4 quý | cao |
| | `margin_avg4` | Dư nợ cho vay ký quỹ, trung bình 4 quý | cao |
| Sức khỏe (30%) | `loan_equity` | Dư nợ cho vay chia vốn chủ, trung bình 4 quý | cao |
| | `fvtpl_share` | Lãi FVTPL TTM chia tổng lãi FVTPL, HTM và AFS TTM | thấp |
| | `liquid` | Tiền cộng HTM, chia tổng tài sản, tại cuối quý | cao |
| Lợi nhuận (20%) | `roe_min4` | ROE quý thấp nhất trong 4 quý; ROE quý năm hóa bằng LNST × 4 chia vốn chủ | cao |
| | `roe` | LNST TTM chia vốn chủ trung bình 2 quý | cao |

## Quy ước tính

- **Vốn chủ** lấy vốn chủ công ty mẹ. Nguồn để trống thì dùng tổng vốn chủ.
- **Lợi nhuận** lấy LNST toàn công ty, không lấy phần của công ty mẹ. Nguồn đôi khi ghi toàn bộ lợi nhuận vào dòng cổ đông thiểu số và để trống phần công ty mẹ, trong khi công ty chứng khoán gần như không có cổ đông thiểu số.
- **`loan_equity` cao là tốt.** Chỉ số này đo mức công ty sống bằng mảng cho vay, mảng ổn định hơn tự doanh.
- **`fvtpl_share`:**
  - Lãi HTM hoặc lãi AFS để trống được tính là 0, vì công ty không có danh mục đó.
  - Dòng lãi FVTPL bắt buộc phải có số.
  - Chỉ tính khi tổng lãi đầu tư dương.
- **`liquid`:**
  - Không có số dư HTM và cũng không có lãi HTM: số dư HTM tính là 0.
  - Không có số dư HTM nhưng có lãi HTM: để trống.

## Ngưỡng hạng

| Hạng | Điểm tổng |
|---|---|
| A | từ 2,31 |
| B | từ 1,50 |
| C | từ 0,90 |
| D | dưới 0,90 |

## Cách chấm điểm

- Điểm từng chỉ số tính theo phân vị, giống [mục 2](02-phi-tai-chinh.md).
- Phân vị lấy trên toàn bộ công ty chứng khoán HOSE và HNX trong cùng quý.
- Nhóm này không áp trần trả lãi.
