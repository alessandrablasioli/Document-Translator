"""
Translation Agent - Specialized in translating text.
Part of the multi-agent translation system.
Supports auto-detect source language and translation memory for cost savings.
"""
import os
import logging
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add parent directory for observability and translation_memory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from observability import tracer, metrics_collector
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
from services.translation_memory import TranslationMemory

logger = logging.getLogger(__name__)
load_dotenv()

# Sample size for language detection (keep API cost low)
DETECT_LANGUAGE_SAMPLE_CHARS = 2000

# Valid natural (human) languages for detection - reject programming/technical answers like "SQL"
VALID_NATURAL_LANGUAGES = {
    "english", "spanish", "french", "german", "italian", "portuguese", "russian", "chinese",
    "japanese", "korean", "arabic", "dutch", "swedish", "norwegian", "danish", "polish",
    "turkish", "hindi", "greek", "catalan", "vietnamese", "thai", "indonesian", "malay",
}
# Reject these: programming languages or technical terms wrongly returned as "language"
INVALID_LANGUAGE_ANSWERS = {
    "sql", "python", "javascript", "java", "code", "programming", "technical",
    "mixed", "unknown", "n/a", "none", "multiple",
}


class TranslationAgent:
    """
    Agent specialized in translating text to target languages.
    Handles chunking, context preservation, retry logic, translation memory, and language detection.
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Translation will fail at runtime.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        
        self.agent_name = "TranslationAgent"
        self.model = "gpt-4o-mini"
        self.max_retries = 3
        self.retry_delay = 1.0
        self.max_chunk_size = 100000  # ~25K tokens
        self.translation_memory = TranslationMemory(max_entries=10_000)
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the natural (human) language of the given text using OpenAI.
        Returns language name in English (e.g. "Spanish", "French"), or None if unclear or not a natural language.
        Rejects programming-language answers (e.g. SQL, Python) so we only show real source languages.
        """
        if not self.client or not text or not text.strip():
            return None
        sample = text.strip()[:DETECT_LANGUAGE_SAMPLE_CHARS]
        prompt = f"""What natural human language is the following text mainly written in? Reply with ONLY one language name in English (e.g. English, Spanish, French, German, Chinese). Do NOT reply with programming languages (e.g. SQL, Python), technical terms, or "mixed". Only the main natural language.

Text:
{sample}

Language:"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=30,
            )
            raw = (response.choices[0].message.content or "").strip()
            if not raw:
                return None
            lang_lower = raw.lower().strip()
            if lang_lower in INVALID_LANGUAGE_ANSWERS:
                logger.info(f"[{self.agent_name}] Rejected non-natural language: {raw}")
                return None
            if lang_lower in VALID_NATURAL_LANGUAGES:
                result = raw[0].upper() + raw[1:].lower() if len(raw) > 1 else raw
                logger.info(f"[{self.agent_name}] Detected source language: {result}")
                return result
            # Allow other plausible single-word language names (e.g. "Italian")
            if " " not in lang_lower and len(lang_lower) < 25:
                result = raw[0].upper() + raw[1:].lower() if len(raw) > 1 else raw
                logger.info(f"[{self.agent_name}] Detected source language: {result}")
                return result
            logger.info(f"[{self.agent_name}] Rejected ambiguous language answer: {raw}")
            return None
        except Exception as e:
            logger.warning(f"[{self.agent_name}] Language detection failed: {e}")
        return None

    def translate(self, text: str, target_language: str, source_language: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language
            source_language: Optional source language (auto-detected if not provided)
            metadata: Optional metadata from extraction agent
            
        Returns:
            Dictionary with translated text and status
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not initialized",
                "translated_text": "",
                "agent": self.agent_name
            }
        
        start_time = time.time()
        trace_id = None
        
        if OBSERVABILITY_AVAILABLE:
            trace_id = tracer.start_trace(
                "translation_agent",
                {
                    "text_length": len(text),
                    "target_language": target_language,
                    "source_language": source_language,
                    "agent": self.agent_name
                }
            )
        
        logger.info(f"[{self.agent_name}] Starting translation to {target_language}")
        
        try:
            # Check if chunking is needed
            needs_chunking = metadata and metadata.get("needs_chunking", False) or len(text) > self.max_chunk_size
            
            if needs_chunking:
                result = self._translate_with_chunking(text, target_language, source_language, trace_id)
            else:
                result = self._translate_single(text, target_language, source_language, trace_id)
            
            duration = time.time() - start_time
            result["duration"] = duration
            result["agent"] = self.agent_name
            
            if OBSERVABILITY_AVAILABLE and trace_id:
                tracer.end_trace(trace_id, "completed", {
                    "original_length": len(text),
                    "translated_length": len(result.get("translated_text", "")),
                    "duration": duration
                })
            
            logger.info(f"[{self.agent_name}] Translation completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Translation failed: {e}")
            if OBSERVABILITY_AVAILABLE and trace_id:
                tracer.end_trace(trace_id, "failed", {"error": str(e)})
            
            return {
                "success": False,
                "error": str(e),
                "translated_text": "",
                "agent": self.agent_name
            }
    
    def _translate_single(self, text: str, target_language: str, source_language: Optional[str],
                         trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Translate text in a single API call"""
        translated_text = self._translate_with_retry(text, target_language, source_language)
        
        return {
            "success": True,
            "translated_text": translated_text,
            "chunked": False,
            "chunk_count": 1
        }
    
    def _translate_with_chunking(self, text: str, target_language: str, source_language: Optional[str],
                                 trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Translate text with chunking for large documents"""
        chunks = self._chunk_text(text)
        translated_chunks = []
        previous_context = None
        
        logger.info(f"[{self.agent_name}] Translating {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks, 1):
            if OBSERVABILITY_AVAILABLE and trace_id:
                tracer.add_event(trace_id, "chunk_translation", {
                    "chunk_number": i,
                    "total_chunks": len(chunks)
                })
            
            translated_chunk = self._translate_with_retry(
                chunk,
                target_language,
                source_language,
                context=previous_context
            )
            
            translated_chunks.append(translated_chunk)
            
            # Use summary of current chunk as context for next
            if i < len(chunks):
                previous_context = translated_chunk[:500]
        
        translated_text = "\n\n".join(translated_chunks)
        
        return {
            "success": True,
            "translated_text": translated_text,
            "chunked": True,
            "chunk_count": len(chunks)
        }
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks preserving paragraph boundaries"""
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _translate_with_retry(self, text: str, target_language: str, source_language: Optional[str] = None,
                              context: Optional[str] = None) -> str:
        """Translate with retry logic, translation memory lookup, and exponential backoff."""
        cached = self.translation_memory.get(text, target_language)
        if cached is not None:
            return cached

        source_lang_text = f" from {source_language}" if source_language else ""
        context_text = f"\n\nContext from previous section: {context}" if context else ""
        
        prompt = f"""Translate the following text{source_lang_text} to {target_language}. 
Preserve the formatting, structure, and meaning of the original text. 
Maintain paragraph breaks and line structure exactly as in the original.
{context_text}

Text to translate:
{text}

Translated text:"""
        
        system_prompt = f"""You are a professional translator. Translate the provided text to {target_language} while preserving all formatting, structure, and meaning.
Maintain consistency with previous translations if context is provided."""
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                )
                
                translated = response.choices[0].message.content.strip()
                self.translation_memory.set(text, target_language, translated)
                return translated
                
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Retry {attempt}/{self.max_retries}: {e}")
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                else:
                    raise Exception(f"Translation failed after {self.max_retries} attempts: {str(e)}")
        
        raise Exception("Translation failed: Max retries exceeded")
    
    def handoff_to_validation(self, translation_result: Dict[str, Any], original_text: str,
                              target_language: str) -> Dict[str, Any]:
        """
        Prepare data for handoff to Validation Agent.
        
        Args:
            translation_result: Result from translate() method
            original_text: Original text for comparison
            target_language: Target language
            
        Returns:
            Dictionary formatted for Validation Agent
        """
        if not translation_result.get("success"):
            return translation_result
        
        return {
            "original_text": original_text,
            "translated_text": translation_result["translated_text"],
            "target_language": target_language,
            "source_agent": self.agent_name,
            "ready_for_validation": True,
            "metadata": {
                "chunked": translation_result.get("chunked", False),
                "chunk_count": translation_result.get("chunk_count", 1)
            }
        }

