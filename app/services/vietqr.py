"""Tạo mã VietQR (chuẩn QR chuyển khoản nhanh NAPAS 247) có sẵn số tiền và nội dung.

Khi khách quét bằng app ngân hàng, app tự điền: ngân hàng nhận, số tài khoản,
SỐ TIỀN và NỘI DUNG chuyển khoản.

Cấu hình tài khoản nhận tiền đặt trong file .env:
    bank_bin=970436               # mã BIN 6 số của ngân hàng
    bank_account=0123456789       # số tài khoản nhận tiền
    bank_account_name=NGUYEN VAN A
    bank_name=Vietcombank         # chỉ để hiển thị
"""
import os
import re
import unicodedata


def _tlv(tag: str, value: str) -> str:
    """Một trường dữ liệu theo chuẩn EMVCo: <mã 2 ký tự><độ dài 2 chữ số><giá trị>."""
    if len(value) > 99:
        raise ValueError("Giá trị quá dài")
    return f"{tag}{len(value):02d}{value}"


def crc16_ccitt(data: str) -> str:
    """CRC-16/CCITT-FALSE (đa thức 0x1021, khởi tạo 0xFFFF), trả về 4 ký tự hex hoa."""
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def _bo_dau(text) -> str:
    """Bỏ dấu tiếng Việt và ký tự đặc biệt: 'Đơn hàng #12' -> 'Don hang 12'."""
    text = str(text).replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^0-9A-Za-z ]", "", text).strip()


def build_payload(bank_bin, account, amount, info):
    """Chuỗi nội dung của mã QR.

    bank_bin: mã BIN ngân hàng (6 chữ số); account: số tài khoản nhận;
    amount: số tiền VND (số nguyên dương); info: nội dung chuyển khoản.
    """
    bank_bin, account = str(bank_bin).strip(), str(account).strip()
    if not re.fullmatch(r"\d{6}", bank_bin):
        raise ValueError("Mã BIN ngân hàng phải gồm đúng 6 chữ số")
    if not re.fullmatch(r"[0-9A-Za-z]{1,19}", account):
        raise ValueError("Số tài khoản không hợp lệ (tối đa 19 ký tự chữ và số)")
    amount = int(amount)
    if amount <= 0:
        raise ValueError("Số tiền phải lớn hơn 0")
    info = _bo_dau(info)[:25]    # app ngân hàng chỉ nhận ASCII, tối đa 25 ký tự

    merchant = (
        _tlv("00", "A000000727")                                   # GUID NAPAS
        + _tlv("01", _tlv("00", bank_bin) + _tlv("01", account))   # ngân hàng + số tài khoản
        + _tlv("02", "QRIBFTTA")                                   # chuyển nhanh đến tài khoản
    )
    body = (
        _tlv("00", "01")                 # phiên bản
        + _tlv("01", "12")               # 12 = mã động (có số tiền)
        + _tlv("38", merchant)
        + _tlv("53", "704")              # VND
        + _tlv("54", str(amount))        # số tiền
        + _tlv("58", "VN")
        + _tlv("62", _tlv("08", info))   # nội dung chuyển khoản
        + "6304"                         # CRC tính trên toàn bộ chuỗi, gồm cả "6304"
    )
    return body + crc16_ccitt(body)


def _them_viewbox(svg: str) -> str:
    """Bổ sung viewBox cho SVG do segno tạo để hình co giãn theo khung chứa."""
    m = re.match(r"<svg\b[^>]*>", svg)
    if not m:
        return svg
    tag = m.group(0)
    w = re.search(r'\swidth="([\d.]+)"', tag)
    h = re.search(r'\sheight="([\d.]+)"', tag)
    extra = ""
    if w and h and "viewBox" not in tag:
        extra += f' viewBox="0 0 {w.group(1)} {h.group(1)}"'
    if "shape-rendering" not in tag:
        extra += ' shape-rendering="crispEdges"'
    if not extra:
        return svg
    return svg.replace(tag, tag[:-1] + extra + ">", 1)


def qr_svg(payload: str) -> str:
    """Vẽ mã QR thành thẻ <svg> (cần thư viện segno)."""
    import segno
    qr = segno.make(payload, error="m", micro=False)
    svg = qr.svg_inline(scale=1, border=2, dark="#000000", light="#ffffff")
    return _them_viewbox(svg)

def bank_config():
    """Đọc thông tin tài khoản nhận tiền từ .env; trả về None nếu chưa cấu hình."""
    bank_bin = (os.getenv("bank_bin") or "").strip()
    account = (os.getenv("bank_account") or "").strip()
    if not bank_bin or not account:
        return None
    return {
        "bin": bank_bin,
        "account": account,
        "account_name": (os.getenv("bank_account_name") or "").strip(),
        "bank_name": (os.getenv("bank_name") or "").strip(),
    }