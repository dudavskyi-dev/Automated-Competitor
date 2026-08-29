from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.models import CompanyContext, Competitor, MonitoringBrief, NewsItem


def make_company_context(**overrides: object) -> CompanyContext:
    data: dict[str, object] = {
        "source_url": "https://example.com",
        "company_name": "Acme",
        "domain": "B2B SaaS for project management",
        "target_audience": "small dev teams",
        "value_proposition": "faster sprint planning",
        "keywords": ["project management", "saas"],
    }
    data.update(overrides)
    return CompanyContext(**data)  # type: ignore[arg-type]


def make_competitor(**overrides: object) -> Competitor:
    data: dict[str, object] = {
        "name": "Acme Corp",
        "url": "https://acme.example.com",
        "reason": "similar target audience",
    }
    data.update(overrides)
    return Competitor(**data)  # type: ignore[arg-type]


def make_news_item(**overrides: object) -> NewsItem:
    data: dict[str, object] = {
        "title": "Acme raises Series B",
        "url": "https://news.example.com/acme-series-b",
        "source": "TechCrunch",
        "published_at": datetime(2026, 1, 1, tzinfo=UTC),
        "snippet": "Acme Corp announced a $20M Series B round.",
        "related_entity": "Acme Corp",
    }
    data.update(overrides)
    return NewsItem(**data)  # type: ignore[arg-type]


class TestCompanyContext:
    def test_happy_path(self) -> None:
        context = make_company_context()
        assert str(context.source_url) == "https://example.com/"
        assert context.keywords == ["project management", "saas"]

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            CompanyContext(
                domain="B2B SaaS",
                target_audience="small dev teams",
                value_proposition="faster sprint planning",
                keywords=["saas"],
            )  # type: ignore[call-arg]

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_company_context(source_url="not a url")

    def test_json_round_trip(self) -> None:
        context = make_company_context()
        restored = CompanyContext.model_validate_json(context.model_dump_json())
        assert restored == context


class TestCompetitor:
    def test_happy_path(self) -> None:
        competitor = make_competitor()
        assert competitor.name == "Acme Corp"

    def test_url_accepts_none(self) -> None:
        competitor = make_competitor(url=None)
        assert competitor.url is None

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            Competitor(url="https://acme.example.com", reason="similar audience")  # type: ignore[call-arg]

    def test_json_round_trip(self) -> None:
        competitor = make_competitor()
        restored = Competitor.model_validate_json(competitor.model_dump_json())
        assert restored == competitor


class TestNewsItem:
    def test_happy_path(self) -> None:
        item = make_news_item()
        assert item.source == "TechCrunch"

    def test_published_at_accepts_none(self) -> None:
        item = make_news_item(published_at=None)
        assert item.published_at is None

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_news_item(url="not a url")

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            NewsItem(
                title="Acme raises Series B",
                url="https://news.example.com/acme-series-b",
                published_at=None,
                snippet="Acme Corp announced a $20M Series B round.",
                related_entity="Acme Corp",
            )  # type: ignore[call-arg]

    def test_json_round_trip(self) -> None:
        item = make_news_item()
        restored = NewsItem.model_validate_json(item.model_dump_json())
        assert restored == item


class TestMonitoringBrief:
    def test_happy_path_composes_nested_models(self) -> None:
        brief = MonitoringBrief(
            company=make_company_context(),
            competitors=[make_competitor()],
            items=[make_news_item()],
            generated_at=datetime(2026, 1, 2, tzinfo=UTC),
            summary_markdown="# Weekly brief\n\nAcme raised a Series B.",
        )
        assert brief.company.domain == "B2B SaaS for project management"
        assert brief.competitors[0].name == "Acme Corp"
        assert brief.items[0].source == "TechCrunch"

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            MonitoringBrief(
                company=make_company_context(),
                competitors=[],
                items=[],
                summary_markdown="# Weekly brief",
            )  # type: ignore[call-arg]

    def test_json_round_trip_nests_correctly(self) -> None:
        brief = MonitoringBrief(
            company=make_company_context(),
            competitors=[make_competitor()],
            items=[make_news_item()],
            generated_at=datetime(2026, 1, 2, tzinfo=UTC),
            summary_markdown="# Weekly brief\n\nAcme raised a Series B.",
        )
        dumped = brief.model_dump()
        assert dumped["company"]["domain"] == "B2B SaaS for project management"
        assert dumped["competitors"][0]["name"] == "Acme Corp"
        assert dumped["items"][0]["related_entity"] == "Acme Corp"

        restored = MonitoringBrief.model_validate_json(brief.model_dump_json())
        assert restored == brief
