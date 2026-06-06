import uuid
import pytest
from services.analytics_service import AnalyticsService
from unittest.mock import MagicMock


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def mock_db_for_analytics(mock_db):
    # Setup mock returns for the analytics queries if needed
    # It's better to test integration-style with a real SQLite in-memory DB or fully mock it.
    # Since we are fully mocking DB here based on AGENTS.md, we will mock the query chains.
    return mock_db


def test_get_basic_metrics_empty(mock_db_for_analytics):
    tenant_id = uuid.uuid4()

    # Mocking the scalar() calls for empty DB
    mock_query = mock_db_for_analytics.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.scalar.return_value = 0
    mock_filter.filter.return_value.scalar.return_value = 0

    # Mocking the first() calls for empty DB
    mock_query.first.return_value = None
    # Mocking the group_by().order_by().first() for empty DB
    mock_filter.group_by.return_value.order_by.return_value.first.return_value = None

    svc = AnalyticsService(mock_db_for_analytics, tenant_id)
    metrics = svc.get_basic_metrics()

    assert metrics["total_conversations"] == 0
    assert metrics["messages_today"] == 0
    assert metrics["total_messages"] == 0
    assert metrics["active_conversations_24h"] == 0
    assert metrics["avg_messages_per_conversation"] == 0.0
    assert metrics["peak_activity_hour"] == "N/A"
    assert metrics["avg_response_time_ms"] == 0.0
    assert metrics["fast_responses_percentage"] == 0.0
    assert metrics["conversation_duration_sec"]["min"] == 0.0
    assert metrics["conversation_duration_sec"]["max"] == 0.0
    assert metrics["conversation_duration_sec"]["avg"] == 0.0
