"""Tests for the versioned price table and cost accounting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from greenwash.pricing import (
    ModelPrice,
    PriceTableError,
    load_price_table,
    parse_price_table,
)


def test_bundled_price_table_is_versioned_and_uses_official_prices() -> None:
    table = load_price_table()
    assert table.version == 1
    assert "platform.openai.com/docs/pricing" in table.source
    mini = table.price_for("gpt-4o-mini")
    assert mini == ModelPrice(input=0.15, output=0.6)
    # Known vector: 1M input tokens + 0.5M output tokens at gpt-4o-mini rates.
    assert table.cost_usd("gpt-4o-mini", 1_000_000, 500_000) == pytest.approx(0.15 + 0.30)
    assert table.cost_usd("unknown-model", 1_000_000, 1_000_000) == 0.0


def test_custom_price_table_from_path(tmp_path: Path) -> None:
    path = tmp_path / "prices.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "source": "unit test",
                "models": {"unit-model": {"input": 1.0, "output": 2.0}},
            }
        ),
        encoding="utf-8",
    )
    table = load_price_table(path)
    assert table.cost_usd("unit-model", 1_000_000, 1_000_000) == pytest.approx(3.0)
    assert table.price_for("gpt-4o-mini") is None


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ('{"version": 2, "models": {}}', "unsupported price table version"),
        ('{"models": {}}', "version.*must be an integer"),
        ('{"version": 1}', "models.*must be an object"),
        ('{"version": 1, "models": {"x": 3}}', "price entry.*must be an object"),
        ('{"version": 1, "models": {"x": {"input": 1}}}', "x.output.*must be a number"),
        ('{"version": 1, "models": {"x": {"input": -1, "output": 0}}}', "must not be negative"),
        ('{"version": 1, "models": {"x": {"input": true, "output": 0}}}', "must be a number"),
        ("[]", "must be a JSON object"),
        ("not json", "invalid JSON"),
    ],
)
def test_rejects_invalid_price_tables(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(PriceTableError, match=message):
        load_price_table(path)


def test_missing_price_table_file(tmp_path: Path) -> None:
    with pytest.raises(PriceTableError, match="cannot read price table"):
        load_price_table(tmp_path / "absent.json")


def test_unsupported_source_type_and_empty_model_name() -> None:
    with pytest.raises(PriceTableError, match="source.*must be a string"):
        parse_price_table({"version": 1, "source": 3, "models": {}})
    with pytest.raises(PriceTableError, match="model names must not be empty"):
        parse_price_table({"version": 1, "models": {"": {"input": 0, "output": 0}}})
