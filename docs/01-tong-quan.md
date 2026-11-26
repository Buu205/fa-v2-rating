# 1. Tổng quan FA_V2

FA_V2 chấm hạng cơ bản cho cổ phiếu được cho vay ký quỹ trên HOSE và HNX. Hạng dựa hoàn toàn vào báo cáo tài chính quý. Nó không dùng giá, thanh khoản hay dữ liệu cho vay nội bộ. Bộ chấm phủ ba nhóm: doanh nghiệp phi tài chính, công ty chứng khoán và ngân hàng. Bảo hiểm và UPCoM nằm ngoài phạm vi.

## Thang hạng

| Hạng | Tên | Tỷ lệ vay theo hạng |
|---|---|---|
| A | Safe | 50% |
| B | Caution | 40% |
| C | Reduce | 30% |
| D | High Risk | 20% |
| E | Excluded (Loại) | 0% |
| NR | Not Rated (Chưa chấm) | không có tỷ lệ |

- **NR** nghĩa là thiếu ít nhất một chỉ số trong quý, nên mô hình không chấm. Ô tỷ lệ để trống chứ không ghi 0.
- **E** là luật vốn và lỗ kéo dài, xem [mục 5](05-chot-chan-va-on-dinh.md). Luật này đè lên mọi hạng, kể cả NR.

## Ba trụ và tỷ trọng

| Nhóm | Quy mô | Sức khỏe | Lợi nhuận | Ngưỡng A / B / C | Chi tiết |
|---|---|---|---|---|---|
| Phi tài chính | 50% | 30% | 20% | 1,883 / 1,650 / 0,950 | [02](02-phi-tai-chinh.md) |
| Chứng khoán | 50% | 30% | 20% | 2,31 / 1,50 / 0,90 | [03](03-chung-khoan.md) |
| Ngân hàng | 50% | 28,6% | 21,4% | 2,7625 / 2,3375 / 1,9125 | [04](04-ngan-hang.md) |

- Mỗi chỉ số cho từ 0 đến 4 điểm, trong đó 4 là tốt nhất.
- Điểm trụ là trung bình các chỉ số trong trụ, mỗi chỉ số nặng như nhau. Thiếu một chỉ số thì trụ để trống và mã thành NR.
- Điểm tổng bằng tổng có trọng số của ba trụ, nằm trên thang 0 đến 4.
- Hạng theo ngưỡng như sau:
  - từ ngưỡng A trở lên là A;
  - từ ngưỡng B đến dưới ngưỡng A là B;
  - từ ngưỡng C đến dưới ngưỡng B là C;
  - dưới ngưỡng C là D.

Quy mô nặng nhất (50%) là chủ đích. Mất vốn khi cho vay ký quỹ thường đến từ mã nhỏ, doanh thu thất thường, rơi sâu khi thị trường xấu. Doanh nghiệp lớn có nhiều người mua hơn khi phải bán giải chấp.

## Thứ tự tính mỗi quý

Quy tắc của cả ba nhóm nằm trong `fa_v2/rules.py`.

1. **Chỉ số.** Tính chỉ số từ báo cáo quý: cộng 4 quý (TTM) hoặc trung bình 2 đến 4 quý. Một khung cuộn không được bắc qua quý bị thiếu.
2. **Điểm chỉ số.**
   - Phi tài chính và chứng khoán: lấy phân vị trong quý, rồi chấm 4 điểm từ phân vị 90, 3 điểm từ 70, 2 điểm từ 40, 1 điểm từ 20, còn lại 0.
   - Ngân hàng: Quy mô theo tầng thị phần, Sức khỏe và Lợi nhuận theo ngưỡng cố định.
3. **Hạng theo điểm.** Điểm trụ, điểm tổng, rồi đối chiếu ngưỡng để ra hạng.
4. **Ổn định.**
   - Phi tài chính và chứng khoán: băng giữ hạng 0,20 điểm.
   - Ngân hàng: hạ áp ngay; nâng hạng cần hai quý đạt điểm và nợ xấu không tăng so với cùng kỳ năm trước.
5. **Chốt chặn.**
   - G1, lỗ hai quý liền, chỉ áp cho phi tài chính và chứng khoán.
   - Trần trả lãi, chỉ áp cho phi tài chính.
   - Ngân hàng lỗ 4 quý cộng lại thì hạng D.
6. **Loại (E).** Vốn chủ không dương; lỗ lũy kế từ 50% vốn điều lệ (không áp cho ngân hàng); hoặc lỗ 4 quý cộng lại kèm lỗ hai quý liền.

## Tần suất chạy

- Chạy lại mỗi khi có báo cáo quý mới.
- Hạng có hiệu lực từ ngày thứ 45 sau khi quý kết thúc, là hạn nộp báo cáo.
- Luật Loại có thể quét hằng ngày ngay khi từng báo cáo ra, không cần chờ đủ cả thị trường.

## Bộ chấm này không làm gì

- Không xét thanh khoản, hạn mức theo mã, hạn mức theo ngành hay phê duyệt. Các phần này thuộc bộ phận cho vay.
- Không dùng giá. Giá chỉ dùng để kiểm định hạng sau khi chấm, xem [mục 7](07-kiem-dinh.md).
