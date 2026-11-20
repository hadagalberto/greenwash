"""Render docs/sample-report.png from the committed fixture results.

The image is a faithful, downscaled illustration of the generated HTML
leaderboard; every number and status is read from tests/fixtures/report-a, so
the README screenshot can never drift from the golden report data. Dev-only:
Pillow is only needed to regenerate the image, never to run greenwash.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from greenwash.report import load_report  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "report-a"
OUTPUT = ROOT / "docs" / "sample-report.png"

BG = "#0b1020"
PANEL = "#141b31"
PANEL_2 = "#1b2440"
LINE = "#2c3757"
INK = "#e8ecf7"
MUTED = "#9aa7c4"
GOOD = "#52d39b"
BAD = "#ff7181"
WARN = "#ffc861"

WIDTH, HEIGHT = 1200, 940


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default(size=size)


def _text(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    value: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    *,
    anchor: str | None = None,
) -> None:
    draw.text(position, value, font=font, fill=fill, anchor=anchor)


def _rate(value: object) -> str:
    return f"{float(value):.1%}"


def main() -> None:
    data = load_report(FIXTURE)
    overall = data.summary["overall"]
    assert isinstance(overall, dict)
    by_agent = data.summary["by_agent_model"]
    assert isinstance(by_agent, dict)

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    title_font = _font(34, bold=True)
    h2_font = _font(21, bold=True)
    label_font = _font(15)
    value_font = _font(29, bold=True)
    body_font = _font(16)
    small_font = _font(13)

    _text(draw, (36, 28), "greenwash report", title_font, INK)
    _text(
        draw,
        (36, 76),
        f"{len(data.summary['tasks']) if isinstance(data.summary.get('tasks'), list) else 0}"
        f" tasks · {len(data.records)} attempts · offline static report",
        label_font,
        MUTED,
    )
    draw.line((36, 112, WIDTH - 36, 112), fill=LINE, width=1)

    cards = (
        ("Hidden pass rate", _rate(overall["hidden_pass_rate"]), "95% CI [0.0%, 66.7%]", GOOD),
        (
            "Partial hidden score",
            _rate(overall["partial_hidden_score"]),
            "mean hidden test score",
            INK,
        ),
        ("Greenwash rate", _rate(overall["greenwash_rate"]), "claimed DONE, hidden fail", WARN),
        (
            "Visible pass rate",
            _rate(overall["visible_pass_rate"]),
            "as delivered by the agent",
            BAD,
        ),
    )
    card_width, gap = 272, 14
    for index, (label, value, note, color) in enumerate(cards):
        x = 36 + index * (card_width + gap)
        draw.rounded_rectangle((x, 134, x + card_width, 252), radius=10, fill=PANEL, outline=LINE)
        _text(draw, (x + 16, 148), label, label_font, MUTED)
        _text(draw, (x + 16, 172), value, value_font, color)
        _text(draw, (x + 16, 218), note, small_font, MUTED)

    _text(draw, (36, 276), "Leaderboard", h2_font, INK)
    draw.rounded_rectangle((36, 310, WIDTH - 36, 520), radius=10, fill=PANEL, outline=LINE)
    draw.rectangle((36, 310, WIDTH - 36, 346), fill=PANEL_2)
    columns = (
        (52, "Agent / model"),
        (650, "Hidden"),
        (800, "Partial"),
        (940, "Greenwash"),
        (1090, "pass@1"),
    )
    for x, label in columns:
        _text(draw, (x, 318), label, small_font, MUTED)
    for row_index, name in enumerate(sorted(by_agent)):
        metrics = by_agent[name]
        assert isinstance(metrics, dict)
        pass_at_1 = metrics["pass_at_k"]
        assert isinstance(pass_at_1, dict)
        y = 358 + row_index * 52
        if row_index % 2:
            draw.rectangle((37, y - 6, WIDTH - 37, y + 42), fill=PANEL_2)
        _text(draw, (52, y), name, body_font, INK)
        _text(draw, (650, y), _rate(metrics["hidden_pass_rate"]), body_font, INK)
        _text(draw, (800, y), _rate(metrics["partial_hidden_score"]), body_font, INK)
        _text(draw, (940, y), _rate(metrics["greenwash_rate"]), body_font, WARN)
        _text(draw, (1090, y), _rate(pass_at_1["1"]), body_font, INK)

    _text(draw, (36, 542), "Per-task matrix", h2_font, INK)
    tasks: dict[str, list[object]] = {}
    for row in data.records:
        task_id = row["task_id"]
        assert isinstance(task_id, str)
        tasks.setdefault(task_id, []).append(row)
    for index, task_id in enumerate(sorted(tasks)):
        y = 596 + index * 72
        _text(draw, (52, y), task_id, body_font, INK)
        for cell_index, record in enumerate(tasks[task_id]):
            passed = record["hidden_pass"] is True
            greenwash = record["greenwash"] is True
            x = 420 + cell_index * 170
            color = GOOD if passed else BAD
            draw.rounded_rectangle((x, y - 8, x + 148, y + 34), radius=8, fill=PANEL, outline=color)
            _text(
                draw,
                (x + 14, y - 2),
                f"R{cell_index + 1} {'PASS' if passed else 'FAIL'}",
                body_font,
                color,
            )
            if greenwash:
                _text(draw, (x + 14, y + 18), "greenwash", small_font, WARN)

    draw.line((36, HEIGHT - 70, WIDTH - 36, HEIGHT - 70), fill=LINE, width=1)
    _text(
        draw,
        (36, HEIGHT - 52),
        "Generated from results.jsonl + summary.json · no CDN, no network, opens offline",
        small_font,
        MUTED,
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", optimize=True)
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
