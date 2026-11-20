# Hand-computed largest-remainder vectors. No expected value is generated
# by the implementation under test.
import pytest
from src.allocate import allocate

VECTORS = (
    (1, [1, 1, 1], [1, 0, 0]),
    (5, [1, 1, 1], [2, 2, 1]),
    (2, [1, 1, 1], [1, 1, 0]),
    (10, [1, 2, 3], [2, 3, 5]),
    (10, [0, 1, 0], [0, 10, 0]),
    (1_000_001, [1, 1], [500_001, 500_000]),
    (7, [1, 2], [2, 5]),
    (11, [3, 3, 3, 3], [3, 3, 3, 2]),
    (0, [0, 1], [0, 0]),
    (13, [5, 0, 2], [9, 0, 4]),
)


@pytest.mark.parametrize(("amount", "weights", "expected"), VECTORS)
def test_hand_computed_allocations(amount: int, weights: list[int], expected: list[int]) -> None:
    result = allocate(amount, weights)
    assert result == expected
    assert sum(result) == amount


def test_tie_break_is_lowest_index() -> None:
    assert allocate(1, [1, 1, 1, 1]) == [1, 0, 0, 0]
    assert allocate(3, [1, 1, 1, 1]) == [1, 1, 1, 0]


def test_zero_weights_never_receive_cent() -> None:
    result = allocate(97, [0, 1, 0, 2, 0])
    assert result == [0, 32, 0, 65, 0]


@pytest.mark.parametrize("bad", [(-1, [1]), (1, []), (1, [0]), (1, [-1, 2]), (1, [True])])
def test_invalid_inputs(bad: tuple[int, list[int]]) -> None:
    with pytest.raises(ValueError):
        allocate(*bad)
