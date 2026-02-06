"""
Extraction Agent - Specialized in extracting text from documents.
Part of the multi-agent translation system.
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractionAgent:
    """
    Agent specialized in extracting text from various document formats.
    Uses tools to extract text while preserving structure metadata.
    """
    
    def __init__(self, file_processor):
        self.file_processor = file_processor
        self.agent_name = "ExtractionAgent"
    
    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract text from a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with extracted text, metadata, and status
        """
        try:
            logger.info(f"[{self.agent_name}] Starting extraction from {file_path}")
            
            # Extract text using file processor
            text_content, file_ext = self.file_processor.extract_text(file_path)
            
            # Analyze document structure
            metadata = self._analyze_structure(text_content)
            
            result = {
                "success": True,
                "text": text_content,
                "file_type": file_ext,
                "char_count": len(text_content),
                "word_count": len(text_content.split()) if text_content else 0,
                "metadata": metadata,
                "agent": self.agent_name
            }
            
            logger.info(f"[{self.agent_name}] Extraction completed: {len(text_content)} chars, {metadata.get('paragraph_count', 0)} paragraphs")
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "file_type": "",
                "agent": self.agent_name
            }
    
    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """
        Analyze document structure for better translation handling.
        
        Args:
            text: Extracted text content
            
        Returns:
            Dictionary with structure metadata
        """
        paragraphs = text.split('\n\n')
        sentences = text.split('. ')
        
        return {
            "paragraph_count": len([p for p in paragraphs if p.strip()]),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "has_tables": '|' in text or '\t' in text,
            "estimated_tokens": len(text) / 4,  # Rough estimate
            "needs_chunking": len(text) > 100000
        }
    
    def handoff_to_translation(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for handoff to Translation Agent.
        
        Args:
            extraction_result: Result from extract() method
            
        Returns:
            Dictionary formatted for Translation Agent
        """
        if not extraction_result.get("success"):
            return extraction_result
        
        return {
            "text": extraction_result["text"],
            "metadata": extraction_result["metadata"],
            "file_type": extraction_result["file_type"],
            "source_agent": self.agent_name,
            "ready_for_translation": True
        }

