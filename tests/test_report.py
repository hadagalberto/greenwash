"""Golden-file and structure tests for the offline HTML leaderboard."""

from __future__ import annotations

import json
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path

import pytest

from greenwash.report import ReportData, ReportError, load_report, render_html, write_report

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FIXTURE_A = FIXTURES / "report-a"


class _Structure(HTMLParser):
    """Collect the structural markers the report contract promises."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.tables: set[str] = set()
        self.sort_headers: list[str] = []
        self.task_rows: list[str] = []
        self.classes: set[str] = set()
        self.external_refs: list[str] = []
        self.script_sources: list[str] = []
        self.link_tags: int = 0
        self.inline_scripts: int = 0
        self._script_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script":
            self.inline_scripts += 1
            if values.get("src"):
                self.script_sources.append(str(values["src"]))
            self._script_depth += 1
        if tag == "link":
            self.link_tags += 1
        for key in ("href", "src"):
            value = values.get(key)
            if value and ("://" in value or value.startswith("//")):
                self.external_refs.append(value)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        if tag == "table" and values.get("id"):
            self.tables.add(str(values["id"]))
        if tag == "th" and values.get("data-sort"):
            self.sort_headers.append(str(values["data-sort"]))
        if tag == "tr" and values.get("data-task"):
            self.task_rows.append(str(values["data-task"]))
        if values.get("class"):
            self.classes.update(str(values["class"]).split())

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._script_depth = max(0, self._script_depth - 1)


def _structure(html: str) -> _Structure:
    parser = _Structure()
    parser.feed(html)
    return parser


def _data() -> ReportData:
    return load_report(FIXTURE_A)


def test_render_matches_golden_file_exactly() -> None:
    golden = (FIXTURES / "golden" / "report.html").read_text(encoding="utf-8")
    assert render_html(_data()) == golden


def test_write_report_uses_lf_and_matches_golden(tmp_path: Path) -> None:
    target = write_report(FIXTURE_A, tmp_path / "nested" / "report.html")
    raw = target.read_bytes()
    assert b"\r\n" not in raw
    assert raw.decode("utf-8") == (FIXTURES / "golden" / "report.html").read_text(encoding="utf-8")


def test_html_has_sortable_leaderboard_matrix_and_drilldowns() -> None:
    html = render_html(_data())
    structure = _structure(html)
    assert {"leaderboard-table", "matrix-table"}.issubset(structure.tables)
    assert structure.sort_headers == ["string"] + ["number"] * 9
    assert structure.task_rows == ["base64url", "crc32-check", "semver-compare"]
    assert {f"attempt-{index:03d}" for index in range(1, 7)}.issubset(structure.ids)
    assert {"card", "sortable", "matrix", "cell", "attempt", "tamper-hunk", "stdout"}.issubset(
        structure.classes
    )
    assert "Aggregated metrics" in html
    assert "Greenwash rate" in html
    assert "50.0%" in html
    assert "95% CI [16.7%, 83.3%]" in html
    assert "pass@1" in html and "pass@2" in html
    assert "tamper:expected_literal_changed" in html
    assert "tamper:skip_marker" in html


def test_html_contains_spec_diff_tamper_hunks_and_test_output() -> None:
    html = render_html(_data())
    assert "base64url alphabet (RFC 4648 section 5)" in html
    assert "diff --git a/tests/visible/test_semver.test.ts" in html
    assert "expected value -1 rewritten to 0" in html
    assert "test() changed to test.skip()" in html
    assert "assert.equal(compareSemver(&#39;1.0.0&#39;, &#39;2.0.0&#39;), -1);" in html
    assert "Visible tests (originals restored)" in html
    assert "Hidden tests" in html
    assert "fixture output: 4 passed, 0 failed" in html
    assert "No test-tampering findings for this attempt." in html


def test_html_has_no_external_runtime_dependencies() -> None:
    structure = _structure(render_html(_data()))
    assert structure.external_refs == []
    assert structure.script_sources == []
    assert structure.link_tags == 0
    assert structure.inline_scripts == 1
    assert "network unplugged" in render_html(_data())


def test_untrusted_record_fields_are_escaped() -> None:
    data = _data()
    first = dict(data.records[0])
    payload = "<script>alert('xss')</script>"
    first["task_id"] = payload
    first["spec"] = payload
    first["diff"] = payload
    data = replace(data, records=(first, *data.records[1:]))
    html = render_html(data)
    assert payload not in html
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in html
    assert _structure(html).inline_scripts == 1


def test_load_report_rejects_missing_and_malformed_files(tmp_path: Path) -> None:
    with pytest.raises(ReportError, match="missing result file"):
        load_report(tmp_path)
    summary = (FIXTURE_A / "summary.json").read_text(encoding="utf-8")
    (tmp_path / "summary.json").write_text(summary, encoding="utf-8")
    (tmp_path / "results.jsonl").write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(ReportError, match="invalid JSON"):
        load_report(tmp_path)
    (tmp_path / "results.jsonl").write_text("[]\n", encoding="utf-8")
    with pytest.raises(ReportError, match="expected a JSON object"):
        load_report(tmp_path)
    (tmp_path / "summary.json").write_text("[]", encoding="utf-8")
    (tmp_path / "results.jsonl").write_text('{"task_id": "a"}\n', encoding="utf-8")
    with pytest.raises(ReportError, match="must contain a JSON object"):
        load_report(tmp_path)
    (tmp_path / "summary.json").write_text('{"overall": {}}', encoding="utf-8")
    with pytest.raises(ReportError, match="object named 'by_agent_model'"):
        load_report(tmp_path)


def test_known_invalid_record_field_types_are_rejected(tmp_path: Path) -> None:
    summary = json.loads((FIXTURE_A / "summary.json").read_text(encoding="utf-8"))
    (tmp_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    row = json.loads((FIXTURE_A / "results.jsonl").read_text(encoding="utf-8").splitlines()[0])
    row["agent"] = 42
    (tmp_path / "results.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ReportError, match="'agent' must be a string"):
        load_report(tmp_path)
