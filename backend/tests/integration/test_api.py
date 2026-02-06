"""
Integration tests for FastAPI endpoints: health, root, upload, translate (mocked), download, cleanup, extract-text.
"""
import uuid
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Import after conftest sets up path
import main as main_module


@pytest.fixture
def mock_orchestrator():
    """Fake orchestration result so we don't call OpenAI."""
    return {
        "success": True,
        "translated_text": "Hola mundo",
        "original_text": "Hello world",
        "file_type": ".txt",
        "agent_workflow": ["ExtractionAgent", "TranslationAgent", "ValidationAgent"],
        "metadata": {"quality_score": 0.95},
    }


@pytest.fixture
def mock_translated_file(upload_dir):
    """Create a translated file in upload_dir and return (file_id, path)."""
    file_id = str(uuid.uuid4())
    path = upload_dir / f"{file_id}_translated.txt"
    path.write_text("Hola mundo", encoding="utf-8")
    return file_id, path


class TestHealthAndRoot:
    def test_root_returns_message_and_version(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert "version" in data

    def test_health_returns_healthy(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "healthy"}


class TestUpload:
    def test_upload_txt_returns_file_id(self, client, upload_dir):
        files = {"file": ("sample.txt", b"Hello world", "text/plain")}
        r = client.post("/api/upload", files=files)
        assert r.status_code == 200
        data = r.json()
        assert "file_id" in data
        assert data["filename"] == "sample.txt"
        assert data["file_type"] == ".txt"
        assert (upload_dir / f"{data['file_id']}.txt").exists()

    def test_upload_rejects_unsupported_type(self, client):
        files = {"file": ("file.csv", b"a,b,c", "text/csv")}
        r = client.post("/api/upload", files=files)
        assert r.status_code == 400
        assert "Unsupported" in r.json().get("detail", "")

    def test_upload_requires_filename(self, client):
        r = client.post("/api/upload", files={"file": ("", b"content", "text/plain")})
        # 400 from app or 422 from FastAPI validation
        assert r.status_code in (400, 422)


class TestTranslate:
    def test_translate_returns_file_id_when_mocked(self, client, upload_dir, mock_orchestrator):
        # Upload a file first
        files = {"file": ("doc.txt", b"Hello world", "text/plain")}
        up = client.post("/api/upload", files=files)
        assert up.status_code == 200
        file_id = up.json()["file_id"]

        with patch.object(main_module.agent_orchestrator, "translate_document", new_callable=AsyncMock, return_value=mock_orchestrator):
            r = client.post(
                "/api/translate",
                json={"file_id": file_id, "target_language": "Spanish"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "completed"
        assert "file_id" in data
        # Translated file should exist
        out_id = data["file_id"]
        assert (upload_dir / f"{out_id}_translated.txt").exists()

    def test_translate_400_without_file_id(self, client):
        r = client.post("/api/translate", json={"target_language": "Spanish"})
        assert r.status_code == 400

    def test_translate_404_for_unknown_file_id(self, client, mock_orchestrator):
        with patch.object(main_module.agent_orchestrator, "translate_document", new_callable=AsyncMock, return_value=mock_orchestrator):
            r = client.post(
                "/api/translate",
                json={"file_id": "00000000-0000-0000-0000-000000000000", "target_language": "Spanish"},
            )
        assert r.status_code == 404


class TestDownload:
    def test_download_returns_file(self, client, upload_dir, mock_translated_file):
        file_id, _ = mock_translated_file
        r = client.get(f"/api/download/{file_id}")
        assert r.status_code == 200
        assert "translated_" in r.headers.get("content-disposition", "")
        assert r.content.decode("utf-8") == "Hola mundo"

    def test_download_404_for_unknown_id(self, client):
        r = client.get("/api/download/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404

class TestExtractText:
    def test_extract_text_returns_text(self, client, upload_dir):
        files = {"file": ("doc.txt", b"Secret content here", "text/plain")}
        up = client.post("/api/upload", files=files)
        file_id = up.json()["file_id"]
        r = client.get(f"/api/extract-text/{file_id}")
        assert r.status_code == 200
        assert r.json()["text"] == "Secret content here"
        assert r.json()["file_id"] == file_id

    def test_extract_text_404_for_unknown_file_id(self, client):
        r = client.get("/api/extract-text/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404


class TestCleanup:
    def test_cleanup_removes_files(self, client, upload_dir):
        files = {"file": ("doc.txt", b"Content", "text/plain")}
        up = client.post("/api/upload", files=files)
        file_id = up.json()["file_id"]
        path = upload_dir / f"{file_id}.txt"
        assert path.exists()
        r = client.delete(f"/api/cleanup/{file_id}")
        assert r.status_code == 200
        assert not path.exists()


class TestBatchTranslate:
    def test_batch_returns_one_result_per_file_when_mocked(self, client, upload_dir, mock_orchestrator):
        up1 = client.post("/api/upload", files={"file": ("a.txt", b"Hello", "text/plain")})
        up2 = client.post("/api/upload", files={"file": ("b.txt", b"World", "text/plain")})
        id1, id2 = up1.json()["file_id"], up2.json()["file_id"]
        with patch.object(main_module.agent_orchestrator, "translate_document", new_callable=AsyncMock, return_value=mock_orchestrator):
            r = client.post(
                "/api/translate-batch",
                json={"file_ids": [id1, id2], "target_language": "Spanish"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        for item in data["results"]:
            assert item["status"] == "completed"
            assert "translated_file_id" in item

    def test_batch_400_empty_file_ids(self, client):
        r = client.post("/api/translate-batch", json={"file_ids": [], "target_language": "Spanish"})
        assert r.status_code == 400

    def test_batch_mixes_success_and_failed_for_unknown_file(self, client, upload_dir, mock_orchestrator):
        up = client.post("/api/upload", files={"file": ("a.txt", b"Hello", "text/plain")})
        id1 = up.json()["file_id"]
        unknown_id = "00000000-0000-0000-0000-000000000000"
        with patch.object(main_module.agent_orchestrator, "translate_document", new_callable=AsyncMock, return_value=mock_orchestrator):
            r = client.post(
                "/api/translate-batch",
                json={"file_ids": [id1, unknown_id], "target_language": "Spanish"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        completed = [x for x in data["results"] if x["status"] == "completed"]
        failed = [x for x in data["results"] if x["status"] == "failed"]
        assert len(completed) == 1
        assert len(failed) == 1
        assert failed[0]["original_file_id"] == unknown_id
        assert "error" in failed[0]


class TestTranslatedText:
    def test_translated_text_returns_text(self, client, upload_dir, mock_translated_file):
        file_id, _ = mock_translated_file
        r = client.get(f"/api/translated-text/{file_id}")
        assert r.status_code == 200
        assert r.json()["text"] == "Hola mundo"

    def test_translated_text_404_unknown(self, client):
        r = client.get("/api/translated-text/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404


class TestPreview:
    def test_preview_returns_both_texts(self, client, upload_dir, mock_orchestrator, mock_translated_file):
        files = {"file": ("doc.txt", b"Hello world", "text/plain")}
        up = client.post("/api/upload", files=files)
        orig_id = up.json()["file_id"]
        with patch.object(main_module.agent_orchestrator, "translate_document", new_callable=AsyncMock, return_value=mock_orchestrator):
            tr = client.post("/api/translate", json={"file_id": orig_id, "target_language": "Spanish"})
        trans_id = tr.json()["file_id"]
        r = client.get(f"/api/preview?original_file_id={orig_id}&translated_file_id={trans_id}")
        assert r.status_code == 200
        data = r.json()
        assert "original_text" in data
        assert "translated_text" in data
        assert "Hello world" in data["original_text"]
        assert "Hola mundo" in data["translated_text"]

    def test_preview_400_missing_params(self, client):
        r = client.get("/api/preview")
        assert r.status_code == 422  # FastAPI validation

    def test_preview_404_unknown_file(self, client):
        r = client.get(
            "/api/preview?original_file_id=00000000-0000-0000-0000-000000000000&translated_file_id=00000000-0000-0000-0000-000000000001"
        )
        assert r.status_code == 404


class TestHistory:
    def test_history_returns_list(self, client):
        r = client.get("/api/history")
        assert r.status_code == 200
        data = r.json()
        assert "history" in data
        assert "count" in data
        assert isinstance(data["history"], list)

    def test_history_after_translate_contains_entry(self, client, upload_dir, mock_orchestrator):
        up = client.post("/api/upload", files={"file": ("doc.txt", b"Hi", "text/plain")})
        file_id = up.json()["file_id"]
        with patch.object(main_module.agent_orchestrator, "translate_document", new_callable=AsyncMock, return_value=mock_orchestrator):
            client.post("/api/translate", json={"file_id": file_id, "target_language": "French"})
        r = client.get("/api/history?limit=10")
        assert r.status_code == 200
        assert len(r.json()["history"]) >= 1
        assert r.json()["history"][0]["original_file_id"] == file_id
        assert "translated_file_id" in r.json()["history"][0]


class TestTranslateAsync:
    def test_translate_async_returns_job_id(self, client, upload_dir):
        up = client.post("/api/upload", files={"file": ("doc.txt", b"Hi", "text/plain")})
        file_id = up.json()["file_id"]
        r = client.post(
            "/api/translate-async",
            json={"file_id": file_id, "target_language": "Spanish"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_translate_status_returns_job(self, client, upload_dir):
        up = client.post("/api/upload", files={"file": ("doc.txt", b"Hi", "text/plain")})
        file_id = up.json()["file_id"]
        create = client.post(
            "/api/translate-async",
            json={"file_id": file_id, "target_language": "Spanish"},
        )
        job_id = create.json()["job_id"]
        r = client.get(f"/api/translate/status/{job_id}")
        assert r.status_code == 200
        assert "status" in r.json()

    def test_translate_status_404_unknown_job_id(self, client):
        r = client.get("/api/translate/status/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404
