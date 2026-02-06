"""
User flow test: full translation flow via API (upload → translate → download) without real OpenAI.
Verifies the happy path that users experience when using the app.
"""
import pytest
from unittest.mock import AsyncMock, patch

import main as main_module


@pytest.fixture
def mock_orchestrator():
    return {
        "success": True,
        "translated_text": "Bonjour le monde",
        "original_text": "Hello world",
        "file_type": ".txt",
        "agent_workflow": ["ExtractionAgent", "TranslationAgent", "ValidationAgent"],
        "metadata": {"quality_score": 0.95},
    }


def test_full_user_flow_upload_translate_download(client, upload_dir, mock_orchestrator):
    """
    User flow: upload a .txt file → choose target language → translate → download translated file.
    Asserts each step succeeds and the downloaded content matches the mocked translation.
    """
    # 1. Upload
    files = {"file": ("document.txt", b"Hello world\nThis is a test.", "text/plain")}
    upload_res = client.post("/api/upload", files=files)
    assert upload_res.status_code == 200, upload_res.text
    upload_data = upload_res.json()
    file_id = upload_data["file_id"]
    assert file_id
    assert (upload_dir / f"{file_id}.txt").exists()

    # 2. Translate (orchestrator mocked)
    with patch.object(main_module.agent_orchestrator, "translate_document", new_callable=AsyncMock, return_value=mock_orchestrator):
        translate_res = client.post(
            "/api/translate",
            json={"file_id": file_id, "target_language": "French"},
        )
    assert translate_res.status_code == 200, translate_res.text
    translate_data = translate_res.json()
    assert translate_data["status"] == "completed"
    translated_file_id = translate_data["file_id"]
    assert translated_file_id
    assert (upload_dir / f"{translated_file_id}_translated.txt").exists()

    # 3. Download
    download_res = client.get(f"/api/download/{translated_file_id}")
    assert download_res.status_code == 200
    content = download_res.content.decode("utf-8")
    assert "Bonjour le monde" in content

    # 4. Optional: extract text from original (chatbot/search path)
    extract_res = client.get(f"/api/extract-text/{file_id}")
    assert extract_res.status_code == 200
    assert "Hello world" in extract_res.json()["text"]

    # 5. Cleanup
    cleanup_res = client.delete(f"/api/cleanup/{file_id}")
    assert cleanup_res.status_code == 200
    assert not (upload_dir / f"{file_id}.txt").exists()
