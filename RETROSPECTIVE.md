# Retrospective: Document Translator Project

## If I Had to Start Over, What Would I Do Differently?

Right now the app uses the OpenAI Agents SDK: one agent with three tools (extract, translate, validate) and `Runner.run()`. We chunk big docs, retry with backoff, have translation memory, tracing/metrics, an MCP server for Cursor, multi-format support, batch jobs, side-by-side preview, and tests. Here’s what I’d do differently if I was starting from scratch.

---

### 1. Architecture — use the SDK from day one

We ended up with the SDK (one agent, three tools, async under FastAPI), but I built custom orchestration first and refactored later. That cost time and gave us the whole run_sync vs event loop headache. If I started again I’d pick the SDK and a clear tool design from the first version. Maybe even separate agents with handoffs (extract → translate → validate) if the SDK makes that easy. Steeper learning curve at the start, but way less rework.

---

### 2. Chunking — have it from version one

We do have paragraph-aware chunking now, with context between chunks and sequential processing. I’d still introduce chunking from the beginning and experiment with parallel chunks where it’s safe. Real docs often blow past context limits; chunking from the start would have made large files and error recovery (e.g. one chunk fails, others still work) much simpler.

---

### 3. Format preservation — still the weak spot

We extract text, translate it, and generate a simple PDF. Tables, images, and styles don’t survive. I’d invest earlier in better PDF parsing (pdfplumber, pymupdf), keep formatting metadata, store structure as JSON, and rebuild the PDF so it looks like the original. More work, but that’s what people actually expect from a “translated document.”

---

### 4. Testing — TDD would’ve helped

We have pytest on the backend and Jest on the frontend now, plus manual testing. I’d write tests first next time: unit tests for extraction, translation, PDF generation, integration tests for the API, and a few E2E flows. Would’ve caught bugs earlier and made refactors (like the SDK switch) less scary.

---

### 5. Observability — we’re in good shape, could go further

We have tracing, `/api/metrics`, and structured logging in `observability.py`; the SDK sends traces too. If I started over I’d still add JSON logging and OpenTelemetry-style tracing from the beginning, and maybe a small dashboard for translation time, success rate, token usage. Debugging agents without that is painful.

---

### 6. Error handling — already decent

We retry with exponential backoff and show clear messages in the API and UI (e.g. “Contact support” for auth issues). I’d add partial success: if some chunks fail, return what we got instead of failing the whole job. More code, but the system would feel more reliable.

---

### 7. Configuration — less hardcoding

Model choice is still mostly hardcoded. I’d make model, chunk size, and retry policy configurable (env or config file) from the start so we can tune cost vs quality and try different prompts without code changes.

---

### 8. Frontend — state and feedback

Everything’s in React useState. For a next version I’d use Context or similar for the heavier flows, add skeleton loaders and maybe WebSockets for live progress so long translations don’t feel stuck. Error boundaries would help too.

---

### 9. Documentation — write it as you go

README and prompt docs were written at the end. I’d jot down decisions and API behaviour as I build, add a few ADRs, and comment the tricky bits. Would’ve saved me time when I came back to refactor.

---

### 10. MCP — we have it; I’d design for it earlier

We have an MCP server and MCP_SETUP.md; you can translate from Cursor. If I started over I’d design the REST API with MCP in mind from the beginning (same semantics, same error shapes) and add the MCP server in the first iteration. Would’ve kept the API cleaner and avoided duplicate concepts.

---

## Takeaways

- Start with the right abstraction: SDK and MCP from day one would’ve avoided a lot of refactoring.
- Chunking, observability, and tests from the start pay off.
- We have tests now; TDD would’ve caught more earlier.
- Tracing and metrics are in place—keep them central.
- Format preservation is still the main gap; progress and error handling are in good shape.

## What I’d keep

FastAPI + React, Docker Compose, the SDK-based translation path (agent + tools + Runner), chunking, retries, translation memory, observability, the MCP server, multi-format and batch support, side-by-side preview, gpt-4o-mini for cost, and the current project layout and test setup.

## Final thoughts

The app meets the assessment: SDK-driven translation, multi-step flow, MCP, chunking, observability, tests. If I started over I’d adopt the SDK and MCP from the beginning and invest earlier in format preservation and TDD so the same feature set would be easier to maintain and extend.
