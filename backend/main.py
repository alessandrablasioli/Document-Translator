from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

from services.agent_translation_service import AgentTranslationService
from services.agents.agent_orchestrator import AgentOrchestrator  # Multi-agent orchestrator
from services.file_processor import FileProcessor
from services.app_state import (
    add_history,
    get_history as get_history_list,
    create_job,
    get_job,
    update_job,
)

# MCP server: same service as stdio MCP, so Cursor/IDE and HTTP clients share one backend
try:
    from mcp_server import DocumentTranslatorMCPServer
    _mcp_server = DocumentTranslatorMCPServer()
except Exception:
    _mcp_server = None

app = FastAPI(title="Document Translator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
agent_translation_service = AgentTranslationService()
file_processor = FileProcessor()
agent_orchestrator = AgentOrchestrator(file_processor)  # Multi-agent orchestrator with handoffs

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.md', '.txt', '.json', '.xml', '.docx', '.pptx']

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class TranslationRequest(BaseModel):
    target_language: str
    file_id: Optional[str] = None
    source_language: Optional[str] = None  # When omitted, backend auto-detects
    filename: Optional[str] = None  # Optional, for history display


class BatchTranslateRequest(BaseModel):
    file_ids: List[str]
    target_language: str
    source_language: Optional[str] = None
    filenames: Optional[List[str]] = None  # Optional, same order as file_ids


class TranslationStatus(BaseModel):
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    file_id: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Document Translator API", "version": "1.0.0"}


@app.post("/mcp")
async def mcp_json_rpc(body: dict):
    """
    MCP over HTTP: same tools as the stdio MCP server.
    Attach this backend so one running service serves both the web app and MCP.
    """
    if _mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not available")
    method = body.get("method")
    params = body.get("params") or {}
    req_id = body.get("id")
    result = await _mcp_server.handle_mcp_request({"method": method, "params": params})
    if "error" in result:
        return {"jsonrpc": "2.0", "id": req_id, "error": result["error"]}
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/metrics")
async def get_metrics():
    """Get translation metrics for observability"""
    try:
        from observability import metrics_collector, tracer
        
        service_metrics = agent_translation_service.get_metrics()
        observability_metrics = metrics_collector.get_metrics()
        recent_traces = tracer.get_recent_traces(limit=10)
        
        return {
            "status": "success",
            "service_metrics": service_metrics,
            "observability_metrics": observability_metrics,
            "recent_traces": recent_traces
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@app.get("/api/extract-text/{file_id}")
async def extract_text_for_search(file_id: str):
    """Extract text from uploaded file for chatbot search functionality"""
    try:
        # Find the uploaded file (could have any supported extension)
        file_path = None
        
        for ext in SUPPORTED_EXTENSIONS:
            potential_path = UPLOAD_DIR / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Extract text using file processor
        text_content, _ = file_processor.extract_text(file_path)
        
        return {"text": text_content, "file_id": file_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for translation (supports PDF, MD, TXT, JSON, XML, DOCX)"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Get file extension
        file_ext = Path(file.filename).suffix.lower()
        
        # Validate file type
        if file_ext not in SUPPORTED_EXTENSIONS:
            supported = ', '.join(SUPPORTED_EXTENSIONS)
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported types: {supported}"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate file size (max 50MB)
        if len(content) > 50 * 1024 * 1024:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_ext
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/api/translate")
async def translate_document(request: TranslationRequest):
    """Translate a document"""
    try:
        if not request.file_id:
            raise HTTPException(status_code=400, detail="file_id is required")
        
        # Find the uploaded file (could have any supported extension)
        file_path = None
        file_ext = None
        
        for ext in SUPPORTED_EXTENSIONS:
            potential_path = UPLOAD_DIR / f"{request.file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                file_ext = ext
                break
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Extract text using file processor (detects type and calls appropriate function)
        text_content, detected_ext = file_processor.extract_text(file_path)
        
        if not text_content:
            raise HTTPException(
                status_code=400, 
                detail=f"Could not extract text from {detected_ext} file"
            )
        
        # Translate using Multi-Agent Orchestrator (Extraction → Translation → Validation)
        # source_language optional: when omitted, orchestrator auto-detects
        orchestration_result = await agent_orchestrator.translate_document(
            file_path=file_path,
            target_language=request.target_language,
            source_language=request.source_language,
            file_type=detected_ext
        )
        
        if not orchestration_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Translation failed: {orchestration_result.get('error', 'Unknown error')}"
            )
        
        translated_text = orchestration_result["translated_text"]
        
        # Log agent workflow for observability
        logger.info(f"Agent workflow: {' → '.join(orchestration_result.get('agent_workflow', []))}")
        logger.info(f"Quality score: {orchestration_result.get('metadata', {}).get('quality_score', 0):.2f}")
        
        # Generate translated file (preserving original format when possible)
        output_file_id = str(uuid.uuid4())
        output_path = UPLOAD_DIR / f"{output_file_id}_translated{detected_ext}"
        file_processor.create_output_file(translated_text, detected_ext, output_path)
        
        response = {
            "file_id": output_file_id,
            "file_type": detected_ext,
            "status": "completed",
            "message": "Translation completed successfully"
        }
        if orchestration_result.get("detected_source_language"):
            response["detected_source_language"] = orchestration_result["detected_source_language"]
        add_history(
            original_file_id=request.file_id,
            translated_file_id=output_file_id,
            target_language=request.target_language,
            file_type=detected_ext,
            filename=request.filename,
            detected_source_language=orchestration_result.get("detected_source_language"),
        )
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e).lower()
        if "api key" in err_msg or "openai" in err_msg or ".env" in err_msg or "401" in err_msg or "invalid_api_key" in err_msg:
            raise HTTPException(status_code=500, detail="Contact the support")
        raise HTTPException(status_code=500, detail=f"Error translating document: {str(e)}")


@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    """Download translated file"""
    try:
        # Find the translated file (could have any supported extension)
        file_path = None
        file_ext = None
        
        for ext in SUPPORTED_EXTENSIONS:
            potential_path = UPLOAD_DIR / f"{file_id}_translated{ext}"
            if potential_path.exists():
                file_path = potential_path
                file_ext = ext
                break
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine media type based on extension
        media_types = {
            '.pdf': 'application/pdf',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        media_type = media_types.get(file_ext, 'application/octet-stream')
        
        return FileResponse(
            file_path,
            media_type=media_type,
            filename=f"translated_{file_id}{file_ext}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@app.post("/api/translate-batch")
async def translate_batch(request: BatchTranslateRequest):
    """Translate multiple documents to the same target language. Returns one result per file."""
    if not request.file_ids:
        raise HTTPException(status_code=400, detail="file_ids is required and must be non-empty")
    if len(request.file_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files per batch")
    filenames = request.filenames or [None] * len(request.file_ids)
    results = []
    for i, file_id in enumerate(request.file_ids):
        file_path = None
        file_ext = None
        for ext in SUPPORTED_EXTENSIONS:
            potential_path = UPLOAD_DIR / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                file_ext = ext
                break
        if not file_path or not file_path.exists():
            results.append({"original_file_id": file_id, "status": "failed", "error": "File not found"})
            continue
        try:
            text_content, detected_ext = file_processor.extract_text(file_path)
            if not text_content:
                results.append({"original_file_id": file_id, "status": "failed", "error": "Could not extract text"})
                continue
            orchestration_result = await agent_orchestrator.translate_document(
                file_path=file_path,
                target_language=request.target_language,
                source_language=request.source_language,
                file_type=detected_ext,
            )
            if not orchestration_result.get("success"):
                results.append({
                    "original_file_id": file_id,
                    "status": "failed",
                    "error": orchestration_result.get("error", "Translation failed"),
                })
                continue
            output_file_id = str(uuid.uuid4())
            output_path = UPLOAD_DIR / f"{output_file_id}_translated{detected_ext}"
            file_processor.create_output_file(
                orchestration_result["translated_text"], detected_ext, output_path
            )
            add_history(
                original_file_id=file_id,
                translated_file_id=output_file_id,
                target_language=request.target_language,
                file_type=detected_ext,
                filename=filenames[i] if i < len(filenames) else None,
                detected_source_language=orchestration_result.get("detected_source_language"),
            )
            results.append({
                "original_file_id": file_id,
                "translated_file_id": output_file_id,
                "file_type": detected_ext,
                "status": "completed",
                "detected_source_language": orchestration_result.get("detected_source_language"),
            })
        except Exception as e:
            logger.exception("Batch translate failed for %s", file_id)
            err_msg = str(e).lower()
            if "api key" in err_msg or "openai" in err_msg or ".env" in err_msg or "401" in err_msg or "invalid_api_key" in err_msg:
                results.append({"original_file_id": file_id, "status": "failed", "error": "Contact the support"})
            else:
                results.append({"original_file_id": file_id, "status": "failed", "error": str(e)})
    return {"results": results, "total": len(results)}


@app.get("/api/translated-text/{file_id}")
async def get_translated_text(file_id: str):
    """Get extracted text from a translated file (for side-by-side preview)."""
    file_path = None
    for ext in SUPPORTED_EXTENSIONS:
        potential_path = UPLOAD_DIR / f"{file_id}_translated{ext}"
        if potential_path.exists():
            file_path = potential_path
            break
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Translated file not found")
    text_content, _ = file_processor.extract_text(file_path)
    return {"text": text_content, "file_id": file_id}


@app.get("/api/preview")
async def get_preview(
    original_file_id: str = Query(..., description="Original uploaded file ID"),
    translated_file_id: str = Query(..., description="Translated file ID"),
):
    """Get original and translated text for side-by-side preview."""
    orig_path = None
    trans_path = None
    for ext in SUPPORTED_EXTENSIONS:
        if not orig_path:
            p = UPLOAD_DIR / f"{original_file_id}{ext}"
            if p.exists():
                orig_path = p
        if not trans_path:
            p = UPLOAD_DIR / f"{translated_file_id}_translated{ext}"
            if p.exists():
                trans_path = p
    if not orig_path or not orig_path.exists():
        raise HTTPException(status_code=404, detail="Original file not found")
    if not trans_path or not trans_path.exists():
        raise HTTPException(status_code=404, detail="Translated file not found")
    original_text, _ = file_processor.extract_text(orig_path)
    translated_text, _ = file_processor.extract_text(trans_path)
    return {
        "original_text": original_text,
        "translated_text": translated_text,
        "original_file_id": original_file_id,
        "translated_file_id": translated_file_id,
    }


@app.get("/api/history")
async def api_get_history(limit: int = Query(50, ge=1, le=100)):
    """Get translation history (newest first)."""
    entries = get_history_list(limit=limit)
    return {"history": entries, "count": len(entries)}


async def _run_translate_job_async(job_id: str, file_id: str, target_language: str, source_language: Optional[str]):
    """Run translation in background (async; SDK requires event loop)."""
    try:
        update_job(job_id, status="translating", progress=10, message="Extracting...")
        file_path = None
        file_ext = None
        for ext in SUPPORTED_EXTENSIONS:
            p = UPLOAD_DIR / f"{file_id}{ext}"
            if p.exists():
                file_path = p
                file_ext = ext
                break
        if not file_path or not file_path.exists():
            update_job(job_id, status="failed", progress=0, error="File not found")
            return
        update_job(job_id, progress=30, message="Translating...")
        orchestration_result = await agent_orchestrator.translate_document(
            file_path=file_path,
            target_language=target_language,
            source_language=source_language,
            file_type=file_ext or "unknown",
        )
        if not orchestration_result.get("success"):
            update_job(job_id, status="failed", progress=0, error=orchestration_result.get("error", "Translation failed"))
            return
        output_file_id = str(uuid.uuid4())
        output_path = UPLOAD_DIR / f"{output_file_id}_translated{file_ext}"
        file_processor.create_output_file(
            orchestration_result["translated_text"], file_ext, output_path
        )
        add_history(
            original_file_id=file_id,
            translated_file_id=output_file_id,
            target_language=target_language,
            file_type=file_ext or "",
            detected_source_language=orchestration_result.get("detected_source_language"),
        )
        update_job(
            job_id,
            status="completed",
            progress=100,
            message="Done",
            result={
                "file_id": output_file_id,
                "file_type": file_ext,
                "detected_source_language": orchestration_result.get("detected_source_language"),
            },
        )
    except Exception as e:
        logger.exception("Async translate job %s failed", job_id)
        update_job(job_id, status="failed", progress=0, error=str(e))


@app.post("/api/translate-async")
async def translate_async(request: TranslationRequest, background_tasks: BackgroundTasks):
    """Start translation in background; returns job_id. Poll GET /api/translate/status/{job_id} for progress."""
    if not request.file_id:
        raise HTTPException(status_code=400, detail="file_id is required")
    job_id = create_job()
    background_tasks.add_task(
        _run_translate_job_async,
        job_id,
        request.file_id,
        request.target_language,
        request.source_language,
    )
    return {"job_id": job_id, "status": "pending", "message": "Translation started"}


@app.get("/api/translate/status/{job_id}")
async def get_translate_status(job_id: str):
    """Get status of an async translation job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete("/api/cleanup/{file_id}")
async def cleanup_file(file_id: str):
    """Clean up uploaded and translated files"""
    try:
        # Clean up original file (any extension)
        for ext in SUPPORTED_EXTENSIONS:
            original_path = UPLOAD_DIR / f"{file_id}{ext}"
            if original_path.exists():
                os.remove(original_path)
        
        # Clean up translated file (any extension)
        for ext in SUPPORTED_EXTENSIONS:
            translated_path = UPLOAD_DIR / f"{file_id}_translated{ext}"
            if translated_path.exists():
                os.remove(translated_path)
        
        return {"message": "Files cleaned up successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up files: {str(e)}")

