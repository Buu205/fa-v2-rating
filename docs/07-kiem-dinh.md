# 7. Kiểm định

Lệnh chạy: `python -m fa_v2 --data <thư mục> --backtest`. Mã kiểm định nằm trong `fa_v2/backtest.py`.

## Cách đo

**Cửa sổ quan sát.** Hạng có hiệu lực từ ngày thứ 45 sau khi kết thúc quý. Từ ngày đó, lấy 126 phiên tiếp theo, tức khoảng 6 tháng. Quan sát nào có ít hơn 60 phiên thì bỏ qua.

**Ba con số đo trong cửa sổ:**

- **mdd**: mức giảm sâu nhất so với đỉnh gần nhất trước đó.
- **ret**: lợi suất cả cửa sổ.
- **low_ratio**: giá thấp nhất chia cho giá ngày đầu.

**Bốn chỉ tiêu tổng hợp:**

- **dd30**: tỷ lệ quan sát có mức giảm từ 30% trở lên.
- **breach**: tỷ lệ quan sát có giá thấp nhất rơi xuống dưới tỷ lệ cho vay của hạng. Tỷ lệ cho vay là A 50%, B 40%, C 30%, D 20% giá.
- **IC**: tương quan Spearman giữa hạng và mức giảm, tính riêng từng quý rồi lấy trung bình.
- **Đổi hạng mỗi quý**: tỷ lệ mã có hạng khác quý trước.

## Kết quả trên mã HOSE và HNX, dữ liệu tới quý 3/2026

| Chỉ tiêu | Phi tài chính | Chứng khoán | Ngân hàng |
|---|---|---|---|
| dd30, hạng A | 27,6% | 26,3% | 17,9% |
| dd30, hạng B | 32,9% | 44,8% | 21,2% |
| dd30, hạng C | 38,2% | 57,1% | 43,6% |
| dd30, hạng D | 61,0% | 57,1% | 29,3% |
| breach, hạng A | 2,7% | 6,9% | 0% |
| breach, hạng B | 1,5% | 2,4% | 0% |
| breach, hạng C | 0,9% | 0,6% | 0% |
| breach, hạng D | 0,1% | 0% | 0% |
| IC | 0,25 | 0,31 | 0,29 |
| Đổi hạng mỗi quý | 9,5% | 6,0% | 4,1% |

## Đọc kết quả

**Phi tài chính.**

- Tỷ lệ giảm sâu tăng dần đều từ hạng A đến hạng D.
- Kết quả vẫn đứng vững trên 5 quý kiểm tra ngoài mẫu: IC đạt 0,23, dd30 tăng từ 20,8% ở hạng A lên 52,5% ở hạng D.
- Trong các mã bị loại, 54% có mức giảm sâu.

**Chứng khoán.**

- Thứ tự giữa các hạng đúng khi tính trên toàn bộ dữ liệu.
- Ngoài mẫu thì yếu: IC chỉ đạt 0,05 ± 0,07.
- Đây là nhóm nhỏ và biến động theo chu kỳ thị trường.

**Ngân hàng.**

- Thứ tự A đến D không giữ được khi thị trường sập: hạng D giảm sâu ít hơn hạng C.
- Phần lớn ngân hàng xếp hạng A, khoảng 18 trên 25 mã mỗi quý.

**Breach.** Chỉ tiêu này không tăng dần theo hạng, vì tỷ lệ cho vay khác nhau giữa các hạng. Hạng A được vay 50% giá, nên giá chỉ cần giảm 50% là đã chạm mức vay. Muốn so độ rủi ro giữa các hạng thì xem dd30.
