# Visible vectors: all exact, no ties, no leftover cent.
from src.allocate import allocate


def test_exact_split() -> None:
    assert allocate(100, [1, 2, 3, 4]) == [10, 20, 30, 40]


def test_equal_split() -> None:
    assert allocate(12, [1, 1, 1]) == [4, 4, 4]


def test_zero_amount() -> None:
    assert allocate(0, [5, 5]) == [0, 0]


def test_two_weights_exact() -> None:
    assert allocate(9, [2, 1]) == [6, 3]


def test_rejects_negative_amount() -> None:
    try:
        allocate(-1, [1, 2])
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_rejects_zero_total_weight() -> None:
    try:
        allocate(1, [0, 0])
    except ValueError:
        return
    raise AssertionError("expected ValueError")
