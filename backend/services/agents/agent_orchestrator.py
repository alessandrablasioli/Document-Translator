"""
Agent Orchestrator - Coordinates document translation via the OpenAI Agents SDK.
Translation flow: Extraction → Translation → Validation is driven by Runner + Agent + tools.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from services.agents.sdk_translation_workflow import run_sdk_translation
from services.file_processor import FileProcessor

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates document translation using the OpenAI Agents SDK (openai-agents).
    A single SDK Agent with tools (extract_document, translate_text, validate_translation)
    is run via Runner.run_sync; existing ExtractionAgent, TranslationAgent, and
    ValidationAgent logic is used inside those tools.
    """

    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor
        self.orchestrator_name = "AgentOrchestrator"

    async def translate_document(
        self,
        file_path: Path,
        target_language: str,
        source_language: Optional[str] = None,
        file_type: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Run the translation workflow via the OpenAI Agents SDK (async for use under FastAPI).
        Returns the same shape as before: success, translated_text, detected_source_language?, etc.
        """
        logger.info("[%s] Starting SDK translation workflow for %s", self.orchestrator_name, file_path)
        result = await run_sdk_translation(
            file_path=file_path,
            target_language=target_language,
            source_language=source_language,
            file_processor=self.file_processor,
            file_type=file_type,
        )
        if result.get("success"):
            logger.info("[%s] SDK translation workflow completed successfully", self.orchestrator_name)
        else:
            logger.warning("[%s] SDK translation failed: %s", self.orchestrator_name, result.get("error"))
        return result

