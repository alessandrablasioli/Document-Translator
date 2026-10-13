# Document Translator – Testing Guide

This project includes **unit tests**, **integration tests**, and **user flow tests** so you can safely add features (e.g. auto-detect language and translation memory) with confidence.

## Backend (Python / FastAPI)

### Setup

From the project root, with the virtual environment activated:

```bash
pip install -r backend/requirements-dev.txt
```

Or install test deps into your existing venv:

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### Run all backend tests

From the **project root**:

```bash
python -m pytest backend/tests/ -v
```

From the **backend** directory:

```bash
cd backend
pytest -v
```

### What’s covered

| Layer | Location | Description |
|-------|----------|-------------|
| **Unit** | `backend/tests/unit/` | `FileProcessor` (extract/create, file types), `AgentTranslationService` (chunking, metrics, no-API-key), MCP server (tools list, initialize) |
| **Integration** | `backend/tests/integration/test_api.py` | API endpoints: health, root, upload, translate (mocked), download, extract-text, cleanup, **translate-batch**, **translated-text**, **preview**, **history**, **translate-async**, **translate/status/{job_id}** |
| **User flow** | `backend/tests/integration/test_user_flow_api.py` | Full flow: upload → translate (mocked) → download → cleanup |

Backend integration tests also cover: batch translate (success, empty file_ids, mixed success/failed), translated-text and preview (success, 404), history (list, after translate), translate-async (job_id, status polling, 404 for unknown job_id), preview (missing params, 404 for unknown files).

Translation is **mocked** in integration and user-flow tests (no real OpenAI calls). Unit tests for the translation service use an empty API key so only chunking/metrics and error handling are exercised.

### Coverage (optional)

```bash
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

---

## Frontend (React)

### Prerequisites

You need **Node.js** (and **npm**) installed and on your PATH. If you see `npm non riconosciuto` / "npm is not recognized":

- Install Node.js from [nodejs.org](https://nodejs.org/) (LTS), or
- If you use **nvm-windows**, run `nvm use <version>` in the same terminal before running tests.

Then install dependencies once:

```bash
cd frontend
npm install
```

### Run frontend tests

From the **frontend** directory:

```bash
cd frontend
npm test -- --watchAll=false
```

To run a subset:

```bash
npm test -- --watchAll=false --testPathPattern="TranslationForm|App"
```

### What’s covered

| Type | Files | Description |
|------|--------|-------------|
| **Unit** | `src/components/translation/TranslationForm.test.js` | Language select, submit, reset, **isBatch (Translate All)** |
| **Unit** | `src/components/upload/FileUpload.test.js` | Supported/unsupported file types, callback, **multiple files → onFilesUpload** |
| **Unit** | `src/components/layout/LanguageSelector.test.js` | Dropdown, change UI language |
| **Unit** | `src/components/translation/ResultDisplay.test.js` | Download and “translate another” buttons |
| **Unit** | `src/components/preview/SideBySidePreview.test.js` | Fetch preview, show original/translated, error state |
| **Unit** | `src/components/history/TranslationHistory.test.js` | Fetch history, list, preview button, empty/error |
| **Unit** | `src/components/translation/BatchResultDisplay.test.js` | Batch results table, filenames, download, reset |
| **User flow** | `src/App.test.js` | Upload (mocked) → translate (mocked) → result; reset; **batch: multiple files → Translate All → batch results** |

Components that use `useLanguage()` are rendered via `src/test-utils.js` with `LanguageProvider` so translations work in tests.

---

## Summary

- **Unit tests**: Services and components in isolation (and MCP tools/list, initialize).
- **Integration tests**: API endpoints with a temporary upload dir and mocked translation.
- **User flow tests**: Backend = full upload/translate/download/cleanup via API; frontend = upload → translate → result and reset with mocked `fetch`.

### New features and how to test them

- **Batch processing**: Select multiple files in the upload area → list appears → choose target language → “Translate All” → batch results table with download per file. API: `POST /api/translate-batch` with `file_ids`, `filenames`, `target_language`.
- **Side-by-side preview**: Open “Translation History” → click “Preview” on an entry → original and translated text shown side by side. API: `GET /api/preview?original_file_id=…&translated_file_id=…`.
- **Real-time progress**: Check “Use real-time progress” before translating → progress and messages update via polling. API: `POST /api/translate-async` → poll `GET /api/translate/status/{job_id}`.
- **Translation history**: “Translation History” button → list of past translations with download and preview. API: `GET /api/history?limit=…`.

When you add new features (e.g. auto-detect source language or more translation memory options), run these tests and add new ones for the new behavior so they stay green.
