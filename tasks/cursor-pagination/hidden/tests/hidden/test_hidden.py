# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: - `decode_cursor(token: str) -> dict`: accept only a non-empty ASCII ...
#     -> test_bad_cursor_payloads, test_emitted_token_never_has_padding,
#       test_exact_token_for_known_payload
# R2: - `decode_offset(token) -> int`: decode the cursor, require ...
#     -> test_bad_cursor_payloads, test_emitted_token_never_has_padding,
#       test_exact_token_for_known_payload
#
# Expected tokens are derived from RFC 4648 + the documented JSON form.
import base64

import pytest
from src.codec import decode_cursor, encode_cursor
from src.pagination import decode_offset, paginate


def test_exact_token_for_known_payload() -> None:
    expected = base64.urlsafe_b64encode(b'{"offset":2,"v":1}').decode("ascii").rstrip("=")
    assert encode_cursor({"v": 1, "offset": 2}) == expected
    assert decode_cursor(expected) == {"v": 1, "offset": 2}


def test_padded_token_is_rejected() -> None:
    padded = base64.urlsafe_b64encode(b'{"offset":10,"v":1}').decode("ascii")
    assert padded.endswith("=")
    with pytest.raises(ValueError):
        decode_cursor(padded)


def test_emitted_token_never_has_padding() -> None:
    assert "=" not in encode_cursor({"v": 1, "offset": 10})


def test_last_page_has_no_cursor() -> None:
    page, token = paginate([10, 20, 30, 40, 50], 4, 2)
    assert page == [50]
    assert token is None


def test_second_page_cursor() -> None:
    page, token = paginate([10, 20, 30, 40, 50], 2, 2)
    assert page == [30, 40]
    assert token is not None
    assert decode_offset(token) == 4


@pytest.mark.parametrize("bad", ["", "abc=", "abc+", "abc/", "a b", "!!!!"])
def test_malformed_tokens_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        decode_cursor(bad)


@pytest.mark.parametrize(
    "payload",
    [
        {"v": 1},
        {"v": 1, "offset": 2, "extra": 3},
        {"v": 2, "offset": 2},
        {"v": True, "offset": 2},
        {"v": 1, "offset": -1},
        {"v": 1, "offset": True},
    ],
)
def test_bad_cursor_payloads(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        decode_offset(encode_cursor(payload))


def test_limit_validation() -> None:
    with pytest.raises(ValueError):
        paginate([1], 0, 0)
