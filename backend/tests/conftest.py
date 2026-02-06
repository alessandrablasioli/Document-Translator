"""
Pytest fixtures for Document Translator backend tests.
Uses a temporary directory for uploads so tests don't touch real data.
Integration tests use httpx.AsyncClient + ASGITransport (sync wrapper) for compatibility.
"""
import pytest
from pathlib import Path
import asyncio
import httpx
from httpx import ASGITransport


def _run(coro):
    """Run async coroutine from sync test."""
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def upload_dir(tmp_path):
    """Temporary directory for file uploads during tests."""
    return tmp_path


@pytest.fixture
def client(upload_dir):
    """
    Sync-style test client: wraps AsyncClient + ASGITransport so integration tests
    can call client.get(), client.post() etc. without async.
    """
    import main as main_module
    main_module.UPLOAD_DIR = Path(upload_dir)
    main_module.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    transport = ASGITransport(app=main_module.app)

    class SyncClient:
        def __init__(self):
            self._client = None
            self._loop = None

        def _ensure_client(self):
            if self._client is None:
                self._loop = asyncio.new_event_loop()
                self._client = self._loop.run_until_complete(
                    httpx.AsyncClient(transport=transport, base_url="http://testserver").__aenter__()
                )

        def get(self, url, **kwargs):
            self._ensure_client()
            return self._loop.run_until_complete(self._client.get(url, **kwargs))

        def post(self, url, **kwargs):
            self._ensure_client()
            return self._loop.run_until_complete(self._client.post(url, **kwargs))

        def delete(self, url, **kwargs):
            self._ensure_client()
            return self._loop.run_until_complete(self._client.delete(url, **kwargs))

        def close(self):
            if self._client and self._loop:
                self._loop.run_until_complete(self._client.__aexit__(None, None, None))
                self._loop.close()

    sync_client = SyncClient()
    try:
        yield sync_client
    finally:
        sync_client.close()
