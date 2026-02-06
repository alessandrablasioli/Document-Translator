"""
In-memory app state for translation history and async jobs.
MVP: in-memory only; can be replaced with DB/Redis later.
"""
import uuid
import time
from typing import List, Dict, Any, Optional

# Translation history: list of { id, original_file_id, translated_file_id, filename?, target_language, detected_source?, timestamp }
translation_history: List[Dict[str, Any]] = []
HISTORY_MAX_ENTRIES = 100

# Async translation jobs: job_id -> { status, progress, message, result?, error? }
translation_jobs: Dict[str, Dict[str, Any]] = {}
JOB_EXPIRE_SECONDS = 3600


def add_history(
    original_file_id: str,
    translated_file_id: str,
    target_language: str,
    file_type: str,
    filename: Optional[str] = None,
    detected_source_language: Optional[str] = None,
) -> str:
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "original_file_id": original_file_id,
        "translated_file_id": translated_file_id,
        "target_language": target_language,
        "file_type": file_type,
        "filename": filename,
        "detected_source_language": detected_source_language,
        "timestamp": time.time(),
    }
    translation_history.insert(0, entry)
    while len(translation_history) > HISTORY_MAX_ENTRIES:
        translation_history.pop()
    return entry_id


def get_history(limit: int = 50) -> List[Dict[str, Any]]:
    return translation_history[:limit]


def create_job() -> str:
    job_id = str(uuid.uuid4())
    translation_jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "",
        "result": None,
        "error": None,
    }
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return translation_jobs.get(job_id)


def update_job(job_id: str, **kwargs) -> None:
    if job_id in translation_jobs:
        translation_jobs[job_id].update(kwargs)
