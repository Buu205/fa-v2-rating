# 5. Chốt chặn và ổn định hạng

Phần này áp cho doanh nghiệp phi tài chính và công ty chứng khoán. Các bước chạy theo thứ tự dưới đây, trong hàm `scoring.rate`.

1. **Hạng theo điểm.** Đối chiếu điểm tổng với các ngưỡng để ra hạng.
2. **Băng giữ hạng 0,20 điểm.**
   - Hạng theo điểm chỉ lệch một bậc so với quý trước: mã giữ hạng cũ, trừ khi điểm vượt qua ngưỡng ít nhất 0,20.
   - Hạng lệch từ hai bậc trở lên: đổi hạng ngay.
3. **G1, lỗ hai quý liền.** LNST quý này và quý trước đều âm thì hạ một bậc, và hạng cao nhất có thể là C.
4. **Trần trả lãi.** Chỉ áp cho doanh nghiệp phi tài chính, xem [mục 2](02-phi-tai-chinh.md).
5. **Loại (E).** Hạng E đè lên mọi hạng khác, kể cả NR. Mã bị loại khi rơi vào một trong hai trường hợp:
   - **G2, vốn bị bào mòn:** vốn chủ từ 0 trở xuống, hoặc lỗ lũy kế từ 50% vốn điều lệ trở lên. Lỗ lũy kế là lợi nhuận chưa phân phối khi số này âm.
   - **Lỗ kéo dài:** LNST cộng 4 quý âm và đang bị G1.

Ngân hàng dùng luật riêng, mô tả ở [mục 4](04-ngan-hang.md). Ngân hàng không áp G1, luật lỗ lũy kế 50% và băng giữ hạng 0,20.

## Mã chưa chấm (NR) và cảnh báo thiếu dữ liệu

- Cả ba nhóm dùng chung một luật: thiếu một chỉ số thì trụ chứa nó để trống, và mã nhận NR.
- Cột `missing` ghi tên các chỉ số bị thiếu. Mỗi lần chạy, chương trình in danh sách mã NR kèm lý do, và cột Ghi chú trong file Excel cũng ghi lý do đó.
- Các lý do thường gặp:
  - nguồn không báo một dòng BCTC, ví dụ đầu tư ngắn hạn, khiến `netdebt_equity` bị thiếu;
  - mã chưa đủ số quý liền nhau;
  - mã chưa được phân ngành ICB;
  - ngành chỉ có một mã nên không xếp hạng trong ngành được.
- Khi đã đối chiếu tay với BCTC gốc, điền số đúng vào file `corrections` rồi chạy lại.

## Khác biệt với bản gốc

1. **Ngân hàng thiếu chỉ số thì nhận NR.**
   - Bản gốc giữ hạng cũ trong trường hợp này. Bản này đổi để thống nhất với hai nhóm kia.
   - Trên dữ liệu hiện tại, thay đổi này không làm đổi hạng nào. Có 6 dòng ngân hàng là NR, cả 6 đều do thiếu số liệu nợ xấu.
2. **Ngân hàng không còn cần lịch sử giá.**
   - Bản gốc chỉ chấm những quý có đủ 120 phiên giá trước đó. Bản này bỏ điều kiện ấy, vì hạng không dùng đến giá.
   - Hệ quả là có thêm 36 dòng ngân hàng trong các năm 2019 đến 2021.
   - Có 3 dòng năm 2020 và 2021 đổi hạng: BVB, NVB và VBB.
   - Từ năm 2022 trở đi, hạng khớp 100% với bản gốc.
