"""
Document translation workflow using the OpenAI Agents SDK (openai-agents).
Uses Agent + FunctionTools + Runner; preserves existing extraction, translation, and validation logic.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents import Agent, Runner, RunContextWrapper, function_tool, ToolsToFinalOutputResult
from agents.tool import FunctionToolResult

from services.agents.extraction_agent import ExtractionAgent
from services.agents.translation_agent import TranslationAgent
from services.agents.validation_agent import ValidationAgent
from services.file_processor import FileProcessor

logger = logging.getLogger(__name__)

@dataclass
class TranslationContext:
    """Context passed to the SDK agent run; holds services and mutable workflow state."""

    file_path: str
    target_language: str
    source_language: Optional[str]
    file_processor: FileProcessor
    extraction_agent: ExtractionAgent
    translation_agent: TranslationAgent
    validation_agent: ValidationAgent
    # Mutable state filled by tools for final response
    detected_source_language: Optional[str] = None
    extraction_result: Optional[Dict[str, Any]] = None
    translation_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    stored_translated_text: Optional[str] = field(default=None, repr=False)


# --- SDK tools (used by the agent) ---


@function_tool
def extract_document(
    ctx: RunContextWrapper[TranslationContext],
    file_path: str,
) -> Dict[str, Any]:
    """Extract text and metadata from a document file. Call this first with the document path."""
    context = ctx.context
    if not isinstance(context, TranslationContext):
        return {"success": False, "error": "Missing translation context", "text": "", "file_type": ""}
    try:
        result = context.extraction_agent.extract(Path(file_path))
        context.extraction_result = result
        return result
    except Exception as e:
        logger.exception("Extract document failed: %s", e)
        return {"success": False, "error": str(e), "text": "", "file_type": ""}


@function_tool
def translate_text(
    ctx: RunContextWrapper[TranslationContext],
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
) -> Dict[str, Any]:
    """Translate the given text to the target language. Call this after extract_document with the extracted text."""
    context = ctx.context
    if not isinstance(context, TranslationContext):
        return {"success": False, "error": "Missing translation context", "translated_text": ""}
    # Auto-detect source language when not provided
    if not source_language or (isinstance(source_language, str) and source_language.strip() == ""):
        detected = context.translation_agent.detect_language(text)
        if detected:
            source_language = detected
            context.detected_source_language = detected
    metadata = context.extraction_result.get("metadata", {}) if context.extraction_result else {}
    result = context.translation_agent.translate(
        text=text,
        target_language=target_language,
        source_language=source_language,
        metadata=metadata,
    )
    if result.get("success") and result.get("translated_text"):
        context.stored_translated_text = result["translated_text"]
    context.translation_result = result
    return result


@function_tool
def validate_translation(
    ctx: RunContextWrapper[TranslationContext],
    original_text: str,
    translated_text: str,
    target_language: str,
) -> Dict[str, Any]:
    """Validate translation quality. Call this after translate_text with the original and translated text."""
    context = ctx.context
    if not isinstance(context, TranslationContext):
        return {"validated": False, "quality_score": 0.0, "issues": ["Missing context"]}
    result = context.validation_agent.validate(
        original_text=original_text,
        translated_text=translated_text,
        target_language=target_language,
    )
    context.validation_result = result
    return result


def _tools_to_final_output(context_wrapper: Any, tool_results: List[FunctionToolResult]) -> ToolsToFinalOutputResult:
    """Use translated text as final output when validation ran, or when translation ran (so we can stop)."""
    # Prefer stopping after validation so we have quality score in context
    for r in tool_results:
        if r.tool.name == "validate_translation":
            ctx = getattr(context_wrapper, "context", None)
            if ctx and getattr(ctx, "stored_translated_text", None):
                return ToolsToFinalOutputResult(is_final_output=True, final_output=ctx.stored_translated_text)
            # Fallback: use last tool output if no stored text
            if tool_results:
                prev = [x for x in tool_results if x.tool.name == "translate_text"]
                if prev and isinstance(prev[-1].output, dict):
                    return ToolsToFinalOutputResult(
                        is_final_output=True,
                        final_output=prev[-1].output.get("translated_text") or "",
                    )
    # Stop after translation if we have translated text (don't require validation)
    for r in tool_results:
        if r.tool.name == "translate_text" and isinstance(r.output, dict):
            out = r.output.get("translated_text")
            if out:
                return ToolsToFinalOutputResult(is_final_output=True, final_output=out)
    return ToolsToFinalOutputResult(is_final_output=False, final_output=None)


# --- Agent and runner ---

TRANSLATION_AGENT_INSTRUCTIONS = """You are a document translation coordinator. When the user asks you to translate a document:

1. Call extract_document with the file path they give to get the document text.
2. Call translate_text with the extracted text, target language, and optionally source language (use empty or omit if unknown).
3. Call validate_translation with the original text, the translated text, and the target language.

Always call these three tools in order. Use the exact file path, target language, and source language from the user message."""


def build_translation_agent(
    model: str = "gpt-4o-mini",
) -> Agent[TranslationContext]:
    """Build the SDK Agent used for document translation."""
    tools = [extract_document, translate_text, validate_translation]
    return Agent[TranslationContext](
        name="DocumentTranslator",
        instructions=TRANSLATION_AGENT_INSTRUCTIONS,
        tools=tools,
        model=model,
        tool_use_behavior=_tools_to_final_output,
        output_type=str,
    )


async def run_sdk_translation(
    file_path: Path,
    target_language: str,
    source_language: Optional[str],
    file_processor: FileProcessor,
    file_type: str = "unknown",
    max_turns: int = 20,
) -> Dict[str, Any]:
    """
    Run the OpenAI Agents SDK translation workflow (async; use from FastAPI/async code).
    Returns the same shape as the legacy orchestrator.
    """
    extraction_agent = ExtractionAgent(file_processor)
    translation_agent = TranslationAgent()
    validation_agent = ValidationAgent()

    context = TranslationContext(
        file_path=str(file_path),
        target_language=target_language,
        source_language=source_language or None,
        file_processor=file_processor,
        extraction_agent=extraction_agent,
        translation_agent=translation_agent,
        validation_agent=validation_agent,
    )

    user_input = (
        f"Translate the document at path: {file_path} to language: {target_language}."
        + (f" Source language: {source_language}." if source_language else " Source language: auto-detect.")
    )

    agent = build_translation_agent()

    try:
        result = await Runner.run(
            agent,
            user_input,
            context=context,
            max_turns=max_turns,
        )
    except Exception as e:
        logger.exception("SDK translation run failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "stage": "orchestration",
            "agent_workflow": ["DocumentTranslator (SDK)"],
        }

    final_text = result.final_output if isinstance(result.final_output, str) else ""
    if not final_text and context.stored_translated_text:
        final_text = context.stored_translated_text

    # Check for extraction failure (e.g. wrong path)
    if context.extraction_result and not context.extraction_result.get("success"):
        return {
            "success": False,
            "error": context.extraction_result.get("error", "Extraction failed"),
            "stage": "extraction",
            "agent_workflow": ["DocumentTranslator (SDK)"],
        }

    validation_result = context.validation_result or {}
    extraction_result = context.extraction_result or {}
    translation_result = context.translation_result or {}

    response: Dict[str, Any] = {
        "success": True,
        "translated_text": final_text,
        "original_text": extraction_result.get("text", ""),
        "file_type": extraction_result.get("file_type", file_type),
        "agent_workflow": ["ExtractionAgent", "TranslationAgent", "ValidationAgent"],
        "validation": validation_result,
        "metadata": {
            "chunked": translation_result.get("chunked", False),
            "chunk_count": translation_result.get("chunk_count", 1),
            "quality_score": validation_result.get("quality_score", 0.0),
            "duration": translation_result.get("duration", 0.0),
        },
    }
    if context.detected_source_language is not None:
        response["detected_source_language"] = context.detected_source_language

    return response
