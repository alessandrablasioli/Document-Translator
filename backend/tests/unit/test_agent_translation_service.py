"""
Unit tests for AgentTranslationService: chunking, metrics, no real API calls.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from services.agent_translation_service import AgentTranslationService


@pytest.fixture
def service_no_api():
    """Service with no API key so translate will fail fast; use for chunking/metrics only."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
        return AgentTranslationService()


class TestChunking:
    def test_should_chunk_false_for_short_text(self, service_no_api):
        short = "Hello world. " * 100  # well under 100k chars
        assert service_no_api._should_chunk(short) is False

    def test_should_chunk_true_for_very_long_text(self, service_no_api):
        long_text = "x" * (100 * 1024)  # 100k chars
        assert service_no_api._should_chunk(long_text) is True

    def test_chunk_text_returns_single_element_when_no_chunking(self, service_no_api):
        text = "One paragraph."
        chunks = service_no_api._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_preserves_paragraphs_when_possible(self, service_no_api):
        # Create text that exceeds chunk size with clear paragraph breaks
        base = "Paragraph content here. "
        paragraphs = [base * 100] * 300  # many paragraphs
        text = "\n\n".join(paragraphs)
        chunks = service_no_api._chunk_text(text)
        assert len(chunks) >= 2
        # Each chunk should be non-empty and not exceed max_chunk_size by much
        for c in chunks:
            assert len(c) > 0
            assert len(c) <= service_no_api.max_chunk_size + 1000  # allow some slack


class TestMetrics:
    def test_get_metrics_returns_dict_with_keys(self, service_no_api):
        m = service_no_api.get_metrics()
        assert "total_translations" in m
        assert "total_chunks" in m
        assert "total_retries" in m
        assert "total_errors" in m
        assert m["total_translations"] >= 0

    def test_metrics_are_copy(self, service_no_api):
        m1 = service_no_api.get_metrics()
        m2 = service_no_api.get_metrics()
        m1["total_translations"] = 999
        assert service_no_api.get_metrics()["total_translations"] != 999


class TestTranslateRequiresApiKey:
    def test_translate_raises_without_api_key(self, service_no_api):
        with pytest.raises(Exception) as exc_info:
            service_no_api.translate("Hello", "Spanish")
        msg = str(exc_info.value).lower()
        assert "openai_api_key" in msg or "configured" in msg or "translation failed" in msg
