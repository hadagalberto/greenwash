# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: ## Contract - `amount_cents` is a non-negative `int` (not `bool`).
#     -> test_bool_amount_and_zero_total_raise, test_hand_computed_allocations,
#       test_invalid_inputs
# R2: - `weights` is a non-empty sequence of non-negative `int` values ...
#     -> test_bool_amount_and_zero_total_raise, test_tuple_weights_are_accepted,
#       test_zero_weights_never_receive_cent
# R3: - `sum(weights)` must be positive.
#     -> test_result_shape_and_exact_sum, test_tuple_weights_are_accepted,
#       test_zero_weights_never_receive_cent
# R4: ## Examples ``` allocate(100, [1, 2, 3, 4]) == [10, 20, 30, 40] ...
#     -> test_tie_break_is_lowest_index, test_spec_example_allocations,
#       test_bool_amount_and_zero_total_raise
#
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


def test_spec_example_allocations() -> None:
    # All four expectations are listed verbatim in the spec.md examples.
    assert allocate(100, [1, 2, 3, 4]) == [10, 20, 30, 40]
    assert allocate(12, [1, 1, 1]) == [4, 4, 4]
    assert allocate(0, [5, 5]) == [0, 0]
    assert allocate(10, [0, 1, 0]) == [0, 10, 0]


def test_result_shape_and_exact_sum() -> None:
    # spec.md: result has len(weights) non-negative ints summing to the amount.
    result = allocate(997, [3, 5, 7, 11])
    assert len(result) == 4
    assert sum(result) == 997
    assert all(isinstance(value, int) and value >= 0 for value in result)


def test_bool_amount_and_zero_total_raise() -> None:
    # spec.md: amount_cents is a non-negative int, not bool; total > 0 required.
    with pytest.raises(ValueError):
        allocate(True, [1])
    with pytest.raises(ValueError):
        allocate(1, [0, 0])


def test_tuple_weights_are_accepted() -> None:
    # spec.md: weights is a non-empty *sequence*, so a tuple is valid input.
    assert allocate(1, (1, 2)) == [0, 1]
    assert allocate(10, (1, 1)) == [5, 5]
