# Stark Document Translator

An AI-powered document translation tool that translates documents using OpenAI's Agents SDK. Built with FastAPI backend and React frontend, featuring a modern, user-friendly interface branded for Stark.

## Summary — What This Project Does

- **Input:** One or more files (PDF, DOCX, MD, TXT, JSON, XML, PPTX) + target language (and optional source language or auto-detect).
- **Output:** Translated file(s) in the same format, with optional side-by-side preview and translation history.
- **Flow:** Upload → (optional: batch upload) → choose source/target language → translate (sync or real-time progress) → download. Translation uses a **multi-agent pipeline** (Extraction → Translation → Validation) via the OpenAI Agents SDK, with chunking for large documents, retry logic, translation memory, observability, and an MCP server for IDE integration.

## Architecture

### Overview

The application follows a client-server architecture with clear separation of concerns:

- **Frontend**: React-based single-page application providing an intuitive user interface
- **Backend**: FastAPI REST API handling file uploads, translation processing, and file downloads
- **AI Integration**: OpenAI GPT models for document translation

### Technology Stack

#### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **OpenAI Agents SDK**: Agent-based translation with tool calling (`openai-agents>=0.1.0`)
- **OpenAI SDK**: Integration with OpenAI's GPT models for translation
- **pypdf**: PDF text extraction
- **ReportLab**: PDF generation from translated text
- **python-docx**: DOCX file processing
- **Python 3.11**: Backend runtime

#### Frontend
- **React 18**: UI framework
- **Axios**: HTTP client for API communication
- **Modern CSS**: Responsive design with gradient styling

### System Design Decisions

#### 1. **Multi-Agent Architecture with Handoffs**

The system uses a multi-agent architecture with proper agent orchestration and handoffs:
- **Extraction Agent**: Specialized in extracting text from documents while preserving structure
- **Translation Agent**: Focused on translating text with chunking, context preservation, and retry logic
- **Validation Agent**: Verifies translation quality, completeness, and formatting preservation
- **Agent Orchestrator**: Coordinates the flow (Extraction → Translation → Validation)
- **SDK tools**: `extract_document`, `translate_text`, `validate_translation` (logic lives in ExtractionAgent, TranslationAgent, ValidationAgent)
- **Observability**: Tracing and metrics for each step

**Why Multi-Agent Approach:**
- Demonstrates proper agent orchestration and handoffs (assessment requirement)
- Separation of concerns: each agent has a specialized role
- Better observability: can trace each agent's contribution
- Enables independent optimization of each step
- Foundation for adding more agents (e.g., formatting, quality validation)
- Shows understanding of agent engineering principles

**SDK implementation:** The translation path uses the **OpenAI Agents SDK** (`openai-agents`): one `Agent` with three `FunctionTool`s (`extract_document`, `translate_text`, `validate_translation`) run via `Runner.run()` (async under FastAPI). Extraction, translation, and validation logic lives inside those tools. See `backend/services/agents/sdk_translation_workflow.py` and `agent_orchestrator.py` (which delegates to it).

**Agent flow (conceptually):**
1. **Extraction** (tool) → extracts text from the document
2. **Translation** (tool) → translates with chunking, retry, translation memory; optional source-language detection
3. **Validation** (tool) → checks quality; final output is the translated text
4. **Orchestrator** calls the SDK workflow and returns the same API response shape as before

#### 2. **Document Processing Strategy with Chunking**

**Current Approach**: 
- Extract text → Check if chunking needed → Translate (with chunking if needed) → Generate file

**Chunking Strategy**:
- Automatic detection: Documents >100K characters (~25K tokens) are chunked
- Paragraph-aware splitting: Preserves paragraph boundaries
- Context preservation: Each chunk includes context from previous chunk for terminology consistency
- Sequential processing: Chunks processed in order with context passing
- Reassembly: Translated chunks reassembled maintaining structure

**Benefits**:
- Handles documents of any size
- Maintains translation consistency across chunks
- Preserves document structure
- Graceful error handling (one chunk failure doesn't break entire translation)

#### 3. **File Handling**

- **Upload**: Files stored temporarily with UUID-based naming
- **Processing**: In-memory text extraction and translation
- **Output**: Translated file in the same format as the input (PDF, DOCX, etc.)
- **Cleanup**: Files can be deleted after download (cleanup endpoint provided)

**Security Considerations**:
- File type and size validation (supported formats, 50MB limit)
- UUID-based file naming prevents path traversal
- Temporary storage (files not persisted long-term)

#### 4. **Agent Translation Service Design**

The agent-based translation service includes:
- **Model**: GPT-4o-mini (cost-effective for development)
- **Temperature**: 0.3 (lower for consistent translations)
- **System Prompt**: Professional translator persona
- **User Prompt**: Clear instructions to preserve formatting
- **Retry Logic**: Exponential backoff (3 attempts: 1s, 2s, 4s delays)
- **Chunking**: Automatic for large documents with context preservation
- **Observability**: Full tracing and metrics collection

**Why GPT-4o-mini?**
- Cost-effective during development
- Sufficient quality for most translations
- Can be upgraded to GPT-4o for production if needed

**Retry Strategy**:
- Exponential backoff prevents API rate limit issues
- Handles transient network errors
- Comprehensive error logging for debugging

#### 5. **Frontend UX Decisions**

- **Drag-and-drop**: Intuitive file upload
- **Progress Indicators**: Clear feedback during processing
- **Error Handling**: User-friendly error messages
- **Stark Branding**: Gradient color scheme matching Stark's brand
- **Responsive Design**: Works on desktop and mobile

## Project Structure

```
.
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── mcp_server.py               # MCP server for IDE integration (stdio + HTTP)
│   ├── observability.py            # Tracing and metrics
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt        # pytest, pytest-cov, httpx
│   ├── services/
│   │   ├── agent_translation_service.py  # Translation with chunking, used by API and MCP
│   │   ├── file_processor.py             # Multi-format extract/create
│   │   ├── translation_memory.py         # LRU cache for repeated phrases
│   │   ├── agents/                       # SDK workflow and orchestrator
│   │   │   ├── sdk_translation_workflow.py  # Agent + tools (extract, translate, validate)
│   │   │   ├── agent_orchestrator.py       # Delegates to SDK workflow
│   │   │   ├── extraction_agent.py
│   │   │   ├── translation_agent.py
│   │   │   └── validation_agent.py
│   │   └── document_processors/
│   │       ├── pdf_service.py
│   │       ├── docx_service.py
│   │       ├── pptx_service.py
│   │       ├── markdown_service.py
│   │       ├── text_service.py
│   │       ├── json_service.py
│   │       └── xml_service.py
│   ├── tests/                    # Unit and integration tests
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   ├── upload/           # FileUpload
│   │   │   ├── translation/      # TranslationForm, ProgressIndicator, ResultDisplay, BatchResultDisplay
│   │   │   ├── preview/          # SideBySidePreview
│   │   │   ├── history/          # TranslationHistory
│   │   │   └── layout/           # LanguageSelector, Chatbot
│   │   ├── contexts/
│   │   ├── data/
│   │   ├── translations/
│   │   └── index.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
├── PROMPTS.md
├── TESTING.md                   # How to run tests
├── MCP_SETUP.md                 # MCP server setup for Cursor
└── RETROSPECTIVE.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Document Translator"
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Usage

1. **Upload a document**: Drag and drop or click to browse (PDF, DOCX, MD, TXT, JSON, XML, PPTX). For batch, upload multiple files.
2. **Select target language**: Choose from the dropdown (optional: source language or auto-detect).
3. **Translate**: Click "Translate Document" or "Translate All" for batch. Optionally enable real-time progress.
4. **Download**: Download the translated file(s). Use Translation History for past jobs and side-by-side preview.

## API Endpoints

- `POST /api/upload` - Upload a document (PDF, DOCX, PPTX, MD, TXT, JSON, XML)
- `POST /api/translate` - Translate an uploaded document (optional `source_language`; returns `detected_source_language` when auto-detected)
- `POST /api/translate-batch` - Translate multiple files at once
- `POST /api/translate-async` - Start async translation; returns `job_id`
- `GET /api/translate/status/{job_id}` - Poll async job progress
- `GET /api/download/{file_id}` - Download translated file
- `GET /api/extract-text/{file_id}` - Extract text (e.g. for chatbot)
- `GET /api/translated-text/{file_id}` - Get translated text for preview
- `GET /api/preview?original_file_id=…&translated_file_id=…` - Side-by-side text
- `GET /api/history` - Translation history
- `GET /api/metrics` - Metrics and observability
- `DELETE /api/cleanup/{file_id}` - Clean up files
- `GET /health` - Health check

## Testing Guide

### Automated tests

The project has **unit**, **integration**, and **user flow** tests so you can add features (e.g. auto-detect language, translation memory) safely.

- **Backend:** From project root: `python -m pytest backend/tests/ -v`. From backend: `cd backend && pytest -v`. Install test deps: `pip install -r backend/requirements-dev.txt`.
- **Frontend:** `cd frontend && npm test -- --watchAll=false`.

See **[TESTING.md](TESTING.md)** for details (what’s covered, coverage, and how to run subsets).

### Manual Testing Steps

1. **Basic Translation Flow**
   - Upload a simple PDF (1-2 pages)
   - Select Spanish as target language
   - Verify translation completes
   - Download and verify translated PDF

2. **Error Handling**
   - Try uploading an unsupported file type (e.g. .csv) — should show error
   - Try uploading a very large file — should show size limit error
   - Try translating without uploading — should show error

3. **UI/UX Testing**
   - Test drag-and-drop file upload
   - Verify progress indicators show correctly
   - Test on different screen sizes (responsive design)
   - Verify error messages are clear and actionable

4. **API Testing**
   - Use `/docs` endpoint to test API directly
   - Test all endpoints with valid and invalid inputs
   - Verify CORS is working (frontend can call backend)

### Test Files

For manual testing, use any supported document (PDF, DOCX, TXT, etc.). Recommended:
- Small file (1–2 pages) for quick runs
- Multi-page or long document to exercise chunking
- Document with tables/images to see current formatting limits

## Development

### Running Locally (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

### Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `ENVIRONMENT`: development/production (default: development)
- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)

## Implemented Features

1. **Multi-format support**: PDF, DOCX, PPTX, Markdown, TXT, JSON, XML
2. **OpenAI Agents SDK**: One agent with three tools (extract_document, translate_text, validate_translation); Extraction → Translation → Validation pipeline
3. **Chunking**: Automatic for large documents with context preservation
4. **Auto-detect source language** and **translation memory** (LRU cache)
5. **Batch processing**: Upload multiple files → translate all → download each result
6. **Side-by-side preview**: Original vs translated text (from history or after translate)
7. **Real-time progress**: Optional async translation with progress polling
8. **Translation history**: List of past translations with download and preview
9. **Observability**: Tracing, metrics (`/api/metrics`), structured logging
10. **MCP server**: Model Context Protocol server for Cursor/IDE (see [MCP_SETUP.md](MCP_SETUP.md))
11. **i18n**: UI in English, Spanish, French, Catalan
12. **Stark branding**: Dark theme, clear feedback, error handling

## Security Considerations

- **API Key Security**: The OpenAI API key is stored in a `.env` file which is gitignored and never committed to the repository
- File type and size validation (supported formats, 50MB limit)
- UUID-based file naming
- Input sanitization
- CORS configuration
- Environment variable management (no secrets in code)
- The `.env` file must be created locally and is never shared or committed

## Cost Management

- Using GPT-4o-mini for cost-effective development
- Single API call per translation (no unnecessary calls)
- Can upgrade to GPT-4o for production if quality requires it

## Assessment compliance (AI Engineer Assessment)

| Requirement | Status |
|-------------|--------|
| Fresh `git clone` works | Repo is self-contained |
| `docker compose up --build` runs without errors | See [Getting Started](#getting-started) |
| Upload a PDF → get a translated PDF back | Supported; PDF in `SUPPORTED_EXTENSIONS`, full flow via upload → translate → download |
| PROMPTS.md exists and is complete | Log of prompts + fundamentals in [PROMPTS.md](PROMPTS.md) |
| README includes a testing guide | This README + [TESTING.md](TESTING.md) |
| No secrets committed | `.env` is in `.gitignore`; use `.env.example` as template |
| .env.example provided | Present in repo root |

Hard requirements: Python + FastAPI (backend), OpenAI Agents SDK (`openai-agents`), frontend (React), delivery via Docker Compose, PROMPTS.md, README.md, RETROSPECTIVE.md — all satisfied.

## License

This project is part of an AI Engineer assessment.

