"""Versioned price table and token-to-cost accounting.

The bundled table stores USD per 1,000,000 tokens and was transcribed from the
official OpenAI pricing documentation (see the ``source`` field in
``prices.json``). Prices change; users can point ``--price-table`` at their own
file with the same schema instead of editing the package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, cast

_SUPPORTED_VERSION = 1
_TOKENS_PER_UNIT = 1_000_000
_DEFAULT_TABLE = "prices.json"


class PriceTableError(ValueError):
    """Raised when a price table is malformed or uses an unsupported version."""


@dataclass(frozen=True)
class ModelPrice:
    """USD per 1M input and output tokens for one model."""

    input: float
    output: float


@dataclass(frozen=True)
class PriceTable:
    """A validated, versioned collection of model prices."""

    version: int
    source: str
    models: dict[str, ModelPrice]

    def price_for(self, model: str) -> ModelPrice | None:
        """Return the exact price entry for ``model`` or ``None`` when unknown."""
        return self.models.get(model)

    def cost_usd(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """Compute cost from usage counters. Unknown models cost ``0.0``."""
        price = self.price_for(model)
        if price is None:
            return 0.0
        return (
            tokens_in / _TOKENS_PER_UNIT * price.input
            + tokens_out / _TOKENS_PER_UNIT * price.output
        )


def _as_number(value: object, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PriceTableError(f"{location} must be a number")
    number = float(value)
    if number < 0:
        raise PriceTableError(f"{location} must not be negative")
    return number


def parse_price_table(raw: object) -> PriceTable:
    """Validate a parsed price-table document."""
    if not isinstance(raw, dict):
        raise PriceTableError("price table must be a JSON object")
    mapping = cast(dict[str, Any], raw)
    version = mapping.get("version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise PriceTableError("price table 'version' must be an integer")
    if version != _SUPPORTED_VERSION:
        raise PriceTableError(
            f"unsupported price table version {version}; expected {_SUPPORTED_VERSION}"
        )
    source = mapping.get("source", "")
    if not isinstance(source, str):
        raise PriceTableError("price table 'source' must be a string")
    models_raw = mapping.get("models")
    if not isinstance(models_raw, dict):
        raise PriceTableError("price table 'models' must be an object")
    models: dict[str, ModelPrice] = {}
    for name, entry in cast(dict[str, object], models_raw).items():
        if not name:
            raise PriceTableError("price table model names must not be empty")
        if not isinstance(entry, dict):
            raise PriceTableError(f"price entry for {name!r} must be an object")
        price_map = cast(dict[str, object], entry)
        models[name] = ModelPrice(
            input=_as_number(price_map.get("input"), f"{name}.input"),
            output=_as_number(price_map.get("output"), f"{name}.output"),
        )
    return PriceTable(version=version, source=source, models=models)


def load_price_table(path: Path | None = None) -> PriceTable:
    """Load a price table from ``path`` or from the packaged default file."""
    if path is None:
        text = resources.files("greenwash").joinpath(_DEFAULT_TABLE).read_text(encoding="utf-8")
        origin = f"package:{_DEFAULT_TABLE}"
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PriceTableError(f"cannot read price table {path}: {exc}") from exc
        origin = str(path)
    try:
        raw: object = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PriceTableError(f"invalid JSON in price table {origin}: {exc}") from exc
    return parse_price_table(raw)
