
from types import SimpleNamespace

from agent.citation_validator import (
    is_valid_http_url,
    validate_source_urls,
    validate_report_source_ids,
)


def test_valid_http_urls():
    assert is_valid_http_url("https://example.com/article")
    assert is_valid_http_url("http://example.com")


def test_invalid_urls():
    assert not is_valid_http_url("")
    assert not is_valid_http_url("javascript:alert(1)")
    assert not is_valid_http_url("not-a-url")


def test_source_validation_rejects_invalid_and_duplicate_urls():
    sources = [
        SimpleNamespace(title="A", url="https://example.com/a"),
        SimpleNamespace(title="A duplicate", url="https://example.com/a"),
        SimpleNamespace(title="Invalid", url="not-a-url"),
    ]

    valid, issues = validate_source_urls(sources)

    assert len(valid) == 1
    assert len(issues) == 2


def test_report_rejects_unknown_source_ids():
    report = SimpleNamespace(
        sections=[
            SimpleNamespace(source_ids=["S1", "S99"])
        ],
        recommendations=[
            SimpleNamespace(source_ids=["S2"])
        ],
    )

    issues = validate_report_source_ids(
        report,
        {"S1": {}, "S2": {}},
    )

    assert len(issues) == 1
    assert issues[0]["source_id"] == "S99"
