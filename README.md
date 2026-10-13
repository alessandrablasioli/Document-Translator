# Document Translator

Web app that translates documents with OpenAI. You upload a file, choose the languages, and download a translated file in the same format.

The interface is a React app. The API is FastAPI. Translation runs through the OpenAI Agents SDK: one agent calls three tools in order — extract the text, translate it, then check the result.

## What you can do

- Upload one file or several at once (PDF, DOCX, PPTX, Markdown, TXT, JSON, XML, up to 50 MB each).
- Pick a source language or let the app detect it, then pick a target language.
- Follow progress while a translation runs, then download the result.
- Preview original and translated text side by side.
- Reopen past translations from the history list.
- Ask the in-app helper how the page works, or search for a word inside the uploaded document.
- Switch the interface between English, Spanish, French, and Catalan.

Sample files for every supported format are in `test-files/`.

## How a translation runs

1. **Extract.** The file is read and turned into text. Paragraphs are kept so the structure is not flattened into one block.
2. **Translate.** Short documents go out in one request. Longer ones (over about 100,000 characters) are split on paragraph boundaries. Each chunk carries a bit of the previous chunk so terms stay consistent. Repeated phrases can be served from an in-memory cache. Failed calls are retried with backoff.
3. **Validate.** A check looks at whether the translation is complete and whether the formatting cues survived.
4. **Write the file.** The translated text is saved in the original format and offered for download.

The model used for translation is GPT-4o-mini, with a low temperature so wording stays stable. The OpenAI key is read from the environment and is never stored in the repo.

Tables, colours, and custom fonts are simplified in the output. The translated file keeps the text and the format type, not a pixel-perfect copy of the layout.

## Stack

- **Frontend:** React 18
- **Backend:** Python 3.11, FastAPI
- **Translation:** OpenAI Agents SDK (`openai-agents`) and the OpenAI API
- **Documents:** pypdf, ReportLab, python-docx, python-pptx

## Run it

You need Docker and an OpenAI API key.

```bash
cp .env.example .env
```

Put your key in `.env` as `OPENAI_API_KEY`, then:

```bash
docker compose up --build
```

- App: http://localhost:3000
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs

### Without Docker

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend, in another terminal:

```bash
cd frontend
npm install
npm start
```

Optional environment variables:

- `ENVIRONMENT` — `development` or `production` (default `development`)
- `REACT_APP_API_URL` — backend URL for the frontend (default `http://localhost:8000`)

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/upload` | Store a document and return a file id |
| POST | `/api/translate` | Translate one uploaded file |
| POST | `/api/translate-batch` | Translate several files |
| POST | `/api/translate-async` | Start a translation and return a job id |
| GET | `/api/translate/status/{job_id}` | Poll progress for an async job |
| GET | `/api/download/{file_id}` | Download a translated file |
| GET | `/api/preview` | Original and translated text for one pair of ids |
| GET | `/api/history` | Recent translations |
| GET | `/api/extract-text/{file_id}` | Plain text of an uploaded file |
| GET | `/api/translated-text/{file_id}` | Plain text of a translation |
| GET | `/api/metrics` | Request traces and counters |
| DELETE | `/api/cleanup/{file_id}` | Remove stored files for an id |
| GET | `/health` | Health check |
| POST | `/mcp` | Same translation tools over MCP (HTTP) |

## Project layout

```
backend/
  main.py                         FastAPI app
  mcp_server.py                   MCP server (stdio and HTTP)
  observability.py                Tracing and metrics
  services/
    agent_translation_service.py  Chunking, retries, cache
    file_processor.py             Read and write every format
    translation_memory.py         Cache of repeated phrases
    agents/                       Agent, tools, and orchestrator
    document_processors/          PDF, DOCX, PPTX, MD, TXT, JSON, XML
  tests/                          Unit and API tests
frontend/
  src/
    components/                   Upload, translation, preview, history, chat
    translations/                 Interface copy (en, es, fr, ca)
    data/knowledgeBase.json       Answers for the helper chat
test-files/                       Sample documents, one per format
docker-compose.yml
```

## Tests

Backend (from the repo root, with test dependencies installed):

```bash
pip install -r backend/requirements-dev.txt
python -m pytest backend/tests/ -v
```

Frontend:

```bash
cd frontend
npm test -- --watchAll=false
```

Translation calls are mocked, so the tests do not spend API credit. Details of what each suite covers are in [TESTING.md](TESTING.md).

## Use it from an editor

The same translation service is exposed as an MCP server, over stdio or at `POST /mcp` on the running API. Setup for Cursor is in [MCP_SETUP.md](MCP_SETUP.md).
