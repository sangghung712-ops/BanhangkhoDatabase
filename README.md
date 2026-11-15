# Cửa hàng bán lẻ (Retail) — ứng dụng web Flask + MySQL

Ứng dụng web bán hàng gồm hai vai trò: **khách hàng** (xem sản phẩm, đặt hàng, thanh toán, theo dõi đơn) và **quản trị viên** (quản lý sản phẩm, đơn hàng, xác nhận thanh toán, xem báo cáo). Phần nghiệp vụ quan trọng (kiểm tra tồn kho, trừ kho, tính tổng tiền, chuyển trạng thái đơn) được đặt ở cơ sở dữ liệu bằng **trigger** và **stored procedure**.

![Sơ đồ ERD](ẢNH%20ERD.png)

## Mục lục

- [Tính năng](#tính-năng)
- [Công nghệ](#công-nghệ)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cơ sở dữ liệu](#cơ-sở-dữ-liệu)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [Cấu hình `.env`](#cấu-hình-env)
- [Cách sử dụng](#cách-sử-dụng)
- [Luồng trạng thái đơn hàng](#luồng-trạng-thái-đơn-hàng)
- [Thanh toán chuyển khoản bằng mã QR](#thanh-toán-chuyển-khoản-bằng-mã-qr)
- [Ảnh sản phẩm](#ảnh-sản-phẩm)
- [Hạn chế đã biết](#hạn-chế-đã-biết)
- [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)

## Tính năng

**Khách hàng**

- Đăng ký tài khoản (bắt buộc họ tên, email, số điện thoại 10 số bắt đầu bằng 0), đăng nhập, đăng xuất.
- Xem sản phẩm đang kinh doanh, tìm kiếm theo tên, lọc theo danh mục, xem ảnh và tồn kho.
- Giỏ hàng (lưu theo phiên đăng nhập), kiểm tra không cho thêm vượt tồn kho.
- Đặt hàng: nhập địa chỉ giao (tự điền từ hồ sơ), chọn **tiền mặt khi nhận hàng** hoặc **chuyển khoản qua mã QR**.
- Trang "Đơn hàng của tôi": xem danh sách và chi tiết, **hủy** đơn khi còn chờ xác nhận, bấm **Đã nhận hàng** khi đơn đang giao để hoàn thành.

**Quản trị viên**

- Tổng quan: số sản phẩm, khách hàng, đơn hàng, đơn chờ xác nhận, doanh thu đã thu, sản phẩm sắp hết hàng.
- Quản lý sản phẩm: thêm, sửa, tải ảnh, nhập thêm hoặc đặt lại tồn kho, ngừng bán hoặc bán lại.
- Quản lý đơn hàng: xem mọi đơn, lọc theo trạng thái, chuyển trạng thái đúng luồng, xem chi tiết.
- **Xác nhận đã nhận tiền** cho đơn chuyển khoản.
- Báo cáo (xem `My_Retail_Report.sql`).

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ, web | Python 3.10+, Flask, Jinja2 |
| Cơ sở dữ liệu | MySQL **8.0.16 trở lên** (cần cho ràng buộc `CHECK` và `REGEXP_LIKE`) |
| Kết nối DB | `mysql-connector-python` |
| Cấu hình | `python-dotenv` (đọc file `.env`) |
| Mã QR | `segno` (vẽ mã VietQR) |
| Giao diện | HTML, CSS thuần (không dùng framework CSS) |

Danh sách thư viện và phiên bản nằm trong `requirements.txt`.

## Cấu trúc thư mục

```
banhang_app/
├── main.py                   # điểm chạy ứng dụng
├── requirements.txt
├── .env                      # cấu hình riêng từng máy (KHÔNG đưa lên git)
├── My_Retail_Table.sql       # tạo bảng
├── My_Retail_Trigger.sql     # trigger kiểm tra và trừ tồn kho, cộng tổng tiền
├── My_Retail_Procedures.sql  # stored procedure
├── My_Retail_TestCase.sql    # test mẫu dữ liệu
├── My_Retail_Report.sql      # procedure/view cho báo cáo
├── My_Retail_Insertdata.sql  # dữ liệu mẫu (tùy chọn)
└── app/
    ├── __init__.py           # create_app(), đăng ký blueprint, SECRET_KEY
    ├── db.py                 # kết nối MySQL
    ├── labels.py             # nhãn tiếng Việt, dịch thông báo lỗi từ DB
    ├── models/               # lớp dữ liệu: User, Customer, Product, Order, OrderItem, enum
    ├── repositories/         # truy vấn MySQL (product, customer, order)
    ├── services/             # đăng nhập/phân quyền, tải ảnh sản phẩm, tạo mã VietQR
    ├── routes/               # auth_routes, customer_routes, admin_routes
    ├── templates/            # giao diện HTML (Jinja2)
    └── static/
        ├── css/              # base, auth, shop, admin, payment
        └── uploads/products/ # ảnh sản phẩm tải lên (tự tạo, không đưa lên git)
```

Luồng xử lý một yêu cầu: `routes → (services) → repositories → MySQL`, kết quả trả về dưới dạng đối tượng trong `models` rồi đưa vào template.

## Cơ sở dữ liệu

Cơ sở dữ liệu tên **`Retail`**, gồm 5 bảng:

| Bảng | Nội dung |
|---|---|
| `users` | tài khoản (`user_name`, `user_password`, `user_role` mặc định `Customer`) |
| `customers` | hồ sơ khách hàng, quan hệ 1–1 với `users` (họ tên, email, số điện thoại, địa chỉ) |
| `products` | sản phẩm (giá, danh mục, tồn kho, trạng thái `Active`/`Inactive`) |
| `orders` | đơn hàng (trạng thái, địa chỉ giao, tổng tiền, cách và trạng thái thanh toán) |
| `order_items` | dòng sản phẩm trong đơn (`UNIQUE (order_id, product_id)`) |

**Trigger**

- `trg_order_items_bi_check_stock` (trước khi thêm dòng): kiểm tra đơn tồn tại và đang `Pending`, sản phẩm tồn tại và đang kinh doanh, đủ hàng trong kho.
- `trg_order_items_ai_deduct_stock` (sau khi thêm dòng): trừ tồn kho và cộng `số lượng × giá hiện tại` vào `total_amount` của đơn.
- `trg_order_items_bd_block_delete` (trước khi xóa dòng) và `trg_order_items_bu_block_update` (trước khi sửa dòng): không cho xóa hoặc sửa sản phẩm trong đơn khi đơn không còn `Pending`.

**Stored procedure chính**

`dang_ky_khach_hang`, `them_san_pham`, `cap_nhat_san_pham`, `cap_nhat_ton_kho`, `ngung_kinh_doanh_san_pham`, `kinh_doanh_lai_san_pham`, `cap_nhat_trang_thai_don_hang` và các procedure báo cáo trong `My_Retail_Report.sql`.

**Tạo đơn từ giỏ hàng** được xử lý trong code Python (`order_repo.create_from_cart`) bên trong **một transaction**: tạo đơn rồi thêm từng sản phẩm, trigger lo kiểm tra và trừ kho. Lỗi ở bất kỳ bước nào thì hoàn tác toàn bộ, không để lại đơn rỗng.

## Cài đặt và chạy

### 1. Lấy mã nguồn và cài thư viện

```bash
git clone <địa-chỉ-repo>
cd banhang_app

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Dựng cơ sở dữ liệu

Cài MySQL 8.0.16 trở lên và chạy các file SQL **theo đúng thứ tự** (trong MySQL Workbench hoặc bằng `mysql`):

1. `My_Retail_Table.sql`
2. `My_Retail_Trigger.sql`
3. `My_Retail_Procedures.sql`
4. `My_Retail_Report.sql`
5. `My_Retail_Insertdata.sql` (tùy chọn, dữ liệu mẫu)
6.  `My_Retail_TestCase.sql`

```bash
mysql -u root -p < My_Retail_Table.sql
mysql -u root -p Retail < My_Retail_Trigger.sql
# ... tiếp tục với các file còn lại
```

> **Cẩn thận:** `My_Retail_Table.sql` có lệnh `DROP TABLE`, chạy lại sẽ **xóa sạch dữ liệu**. Khi cập nhật code về, chỉ chạy lại các file Trigger, Procedures, View, Report (đều dùng `DROP ... IF EXISTS` rồi tạo lại nên an toàn).

### 3. Tạo file `.env`

Xem phần [Cấu hình `.env`](#cấu-hình-env).

### 4. Chạy ứng dụng

```bash
python main.py
```

Mở trình duyệt tại <http://127.0.0.1:5000>. Lệnh trên chạy chế độ debug, chỉ dùng khi phát triển.

## Cấu hình `.env`

Tạo file `.env` ở thư mục gốc (cạnh `main.py`). Mỗi người tự tạo trên máy mình, file này đã nằm trong `.gitignore`.

```
# Kết nối MySQL
db_host=127.0.0.1
db_port=3306
db_user=root
db_password=
db_name=Retail

# Khóa mã hóa phiên đăng nhập của Flask
SECRET_KEY=

# Tài khoản quản trị (lưu ngoài database)
admin_username=admin
admin_salt=
admin_hash=

# Tài khoản nhận tiền cho thanh toán chuyển khoản (tùy chọn)
bank_bin=
bank_account=
bank_account_name=
bank_name=
```

**Tạo `SECRET_KEY`:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Tạo mật khẩu admin** (băm PBKDF2-HMAC-SHA256, 200.000 vòng). Chạy lệnh, gõ mật khẩu (không hiện ký tự), rồi chép hai dòng in ra vào `.env`. Hai giá trị phải lấy từ cùng một lần chạy:

```bash
python -c "
import os, hashlib, getpass
mk = getpass.getpass('Mật khẩu admin: ')
salt = os.urandom(16)
print('admin_salt=' + salt.hex())
print('admin_hash=' + hashlib.pbkdf2_hmac('sha256', mk.encode(), salt, 200_000).hex())
"
```

> Sửa `.env` xong phải **tắt hẳn và chạy lại** ứng dụng, vì `.env` chỉ được đọc lúc khởi động.

## Cách sử dụng

**Tài khoản**

- **Admin:** đăng nhập bằng `admin_username` và mật khẩu bạn đã tạo hash ở trên. Chỉ có một tài khoản admin, lưu trong `.env`, không nằm trong database.
- **Khách hàng:** bấm **Tạo tài khoản** ở trang đăng nhập. Tài khoản mới có vai trò `Customer`.

**Các trang chính**

| Đường dẫn | Mô tả |
|---|---|
| `/login`, `/register` | đăng nhập, đăng ký |
| `/shop` | danh sách sản phẩm |
| `/cart`, `/checkout` | giỏ hàng, đặt hàng |
| `/orders`, `/orders/<mã>` | đơn hàng của tôi, chi tiết |
| `/orders/<mã>/pay` | trang mã QR thanh toán chuyển khoản |
| `/admin/` | tổng quan quản trị |
| `/admin/products` | quản lý sản phẩm |
| `/admin/orders` | quản lý đơn hàng |

## Luồng trạng thái đơn hàng

```
Pending ──▶ Confirmed ──▶ Shipping ──▶ Completed
   │            │
   └────────────┴──▶ Cancelled
```

| Chuyển trạng thái | Ai làm | Ghi chú |
|---|---|---|
| Pending → Confirmed | Admin | |
| Confirmed → Shipping | Admin | ghi ngày giao |
| Shipping → Completed | Khách (**Đã nhận hàng**) hoặc admin | đơn **tiền mặt** tự chuyển sang `Paid` và ghi ngày thanh toán; đơn **chuyển khoản** phải đã `Paid` mới hoàn thành được |
| Pending / Confirmed → Cancelled | Khách (chỉ khi `Pending`) hoặc admin | hoàn lại tồn kho; đơn đã `Paid` chuyển sang `Refunded` |

Quy tắc chuyển trạng thái nằm trong procedure `cap_nhat_trang_thai_don_hang` và được phản ánh trong `app/models/enums.py` để giao diện chỉ hiện các nút hợp lệ.

## Thanh toán chuyển khoản bằng mã QR

Khi khách chọn **chuyển khoản**, ứng dụng tạo mã **VietQR** (chuẩn QR chuyển khoản nhanh NAPAS 247). Khách quét bằng app ngân hàng thì số tiền, người nhận và nội dung được điền sẵn. Nội dung chuyển khoản là **`DH` + mã đơn** (ví dụ `DH12`).

1. Điền `bank_bin`, `bank_account`, `bank_account_name`, `bank_name` trong `.env`.
2. Khách chuyển khoản theo mã QR.
3. Admin kiểm tra tiền về trong app ngân hàng, đối chiếu theo nội dung, rồi bấm **Đã nhận tiền** ở trang đơn hàng. Đơn chuyển sang `Paid`.

`bank_bin` là mã 6 số của **ngân hàng nơi mở tài khoản nhận tiền**, ví dụ:

| Ngân hàng | BIN | Ngân hàng | BIN |
|---|---|---|---|
| Vietcombank | 970436 | Techcombank | 970407 |
| VietinBank | 970415 | ACB | 970416 |
| BIDV | 970418 | MB Bank | 970422 |

(Kiểm tra lại BIN với ngân hàng của bạn.) `bank_account` là **số tài khoản thanh toán** (không phải số thẻ 16 chữ số). Nếu app ngân hàng báo "tài khoản hưởng không hợp lệ" thì thường là sai BIN hoặc sai số tài khoản.

Việc xác nhận tiền là **thủ công**, hệ thống không tự biết tiền đã về.

## Ảnh sản phẩm

Admin tải ảnh khi thêm hoặc sửa sản phẩm (PNG, JPG, GIF hoặc WEBP, tối đa 2 MB). Hệ thống kiểm tra bằng nội dung thật của file, không nhận SVG.

Ảnh được lưu theo mã sản phẩm: `app/static/uploads/products/<mã>.<đuôi>`, **không cần thêm cột nào vào database**. Vì ảnh gắn theo mã sản phẩm, khi **xóa dữ liệu và dựng lại database** (mã tự tăng bắt đầu lại từ 1) hãy xóa luôn thư mục `app/static/uploads/products/` để ảnh cũ không bị gắn nhầm. Thư mục này không đưa lên git, mỗi máy tự có ảnh riêng.

## Hạn chế đã biết

Dự án phục vụ học tập và trình diễn, chưa sẵn sàng triển khai thật:

- **Mật khẩu khách hàng lưu dạng văn bản thuần** trong bảng `users` (theo thiết kế ban đầu). Khi triển khai thật cần băm (ví dụ `werkzeug.security` hoặc `bcrypt`).
- **Chỉ có một tài khoản admin**, cấu hình cố định trong `.env`.
- Ứng dụng chạy bằng máy chủ phát triển của Flask (`debug=True`).

## Tác giả
- Lê Sang Hùng
  
- Nguyễn Hoài Nhân
