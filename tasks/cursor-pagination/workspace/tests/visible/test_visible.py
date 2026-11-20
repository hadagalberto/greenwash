# Visible flows only use the exact unpadded roundtrip.
from src.codec import decode_cursor, encode_cursor
from src.pagination import decode_offset, paginate


def test_codec_roundtrip() -> None:
    token = encode_cursor({"v": 1, "offset": 2})
    assert decode_cursor(token) == {"v": 1, "offset": 2}


def test_first_page_has_cursor() -> None:
    page, token = paginate([10, 20, 30, 40, 50], 0, 2)
    assert page == [10, 20]
    assert token is not None
    assert decode_offset(token) == 2


def test_offset_validation() -> None:
    try:
        paginate([1, 2], -1, 1)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
