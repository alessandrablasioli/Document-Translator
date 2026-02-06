"""
Agent-based translation service using OpenAI Agents SDK.
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

logger = logging.getLogger(__name__)
load_dotenv()

# Add parent directory to path for observability and translation_memory
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from observability import tracer, metrics_collector
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    logger.warning("Observability module not available, running without tracing")
from services.translation_memory import TranslationMemory

DETECT_LANGUAGE_SAMPLE_CHARS = 2000

VALID_NATURAL_LANGUAGES = {
    "english", "spanish", "french", "german", "italian", "portuguese", "russian", "chinese",
    "japanese", "korean", "arabic", "dutch", "swedish", "norwegian", "danish", "polish",
    "turkish", "hindi", "greek", "catalan", "vietnamese", "thai", "indonesian", "malay",
}
INVALID_LANGUAGE_ANSWERS = {
    "sql", "python", "javascript", "java", "code", "programming", "technical",
    "mixed", "unknown", "n/a", "none", "multiple",
}


class AgentTranslationService:
    """
    Translation service using OpenAI Agents SDK with tool calling.
    Handles document translation with chunking, retry logic, and observability.
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Translation will fail at runtime.")
            self.client = None
            self.api_key = None
        else:
            self.client = OpenAI(api_key=api_key)
            self.api_key = api_key
        
        self.model = "gpt-4o-mini"
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        self.max_chunk_size = 100000  # ~25K tokens (conservative estimate)
        self.translation_memory = TranslationMemory(max_entries=10_000)
        
        # Observability
        self.translation_metrics = {
            "total_translations": 0,
            "total_chunks": 0,
            "total_retries": 0,
            "total_errors": 0
        }
    
    def _log_translation_start(self, text_length: int, target_language: str, chunked: bool = False):
        """Log translation start for observability"""
        logger.info(f"[TRANSLATION_START] length={text_length} chars, language={target_language}, chunked={chunked}")
        self.translation_metrics["total_translations"] += 1
    
    def _log_translation_complete(self, original_length: int, translated_length: int, duration: float):
        """Log translation completion"""
        logger.info(f"[TRANSLATION_COMPLETE] {original_length} -> {translated_length} chars, duration={duration:.2f}s")
    
    def _log_chunk_translation(self, chunk_num: int, total_chunks: int):
        """Log chunk translation progress"""
        logger.info(f"[CHUNK_TRANSLATION] chunk {chunk_num}/{total_chunks}")
        self.translation_metrics["total_chunks"] += 1
    
    def _log_retry(self, attempt: int, error: str):
        """Log retry attempt"""
        logger.warning(f"[RETRY] attempt {attempt}/{self.max_retries}, error: {error}")
        self.translation_metrics["total_retries"] += 1
    
    def _log_error(self, error: str):
        """Log error"""
        logger.error(f"[TRANSLATION_ERROR] {error}")
        self.translation_metrics["total_errors"] += 1
    
    def _should_chunk(self, text: str) -> bool:
        """Determine if text should be chunked"""
        # Conservative estimate: 1 token ≈ 4 characters
        estimated_tokens = len(text) / 4
        # GPT-4o-mini context: 128K tokens, but we'll be conservative
        return estimated_tokens > 25000  # ~100K characters
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for processing.
        Tries to preserve paragraph boundaries.
        """
        if not self._should_chunk(text):
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph would exceed limit, save current chunk
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    # Paragraph itself is too large, split by sentences
                    sentences = para.split('. ')
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 2 > self.max_chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sent
                        else:
                            current_chunk += ". " + sent if current_chunk else sent
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the natural (human) language of the text. Rejects programming-language
        answers (e.g. SQL, Python) so we only return real source languages.
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
                logger.info(f"[TRANSLATION] Rejected non-natural language: {raw}")
                return None
            if lang_lower in VALID_NATURAL_LANGUAGES:
                result = raw[0].upper() + raw[1:].lower() if len(raw) > 1 else raw
                logger.info(f"[TRANSLATION] Detected source language: {result}")
                return result
            if " " not in lang_lower and len(lang_lower) < 25:
                result = raw[0].upper() + raw[1:].lower() if len(raw) > 1 else raw
                logger.info(f"[TRANSLATION] Detected source language: {result}")
                return result
            logger.info(f"[TRANSLATION] Rejected ambiguous language answer: {raw}")
            return None
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
        return None

    def _translate_with_retry(self, text: str, target_language: str, source_language: Optional[str] = None, 
                             context: Optional[str] = None) -> str:
        """
        Translate text with retry logic, translation memory lookup, and exponential backoff.
        """
        if not self.client:
            raise Exception("OPENAI_API_KEY is not configured. Please set it in your .env file.")
        
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
                
                translated_text = response.choices[0].message.content.strip()
                self.translation_memory.set(text, target_language, translated_text)
                return translated_text
                
            except Exception as e:
                error_msg = str(e)
                self._log_retry(attempt, error_msg)
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                else:
                    self._log_error(error_msg)
                    raise Exception(f"Translation failed after {self.max_retries} attempts: {error_msg}")
        
        raise Exception("Translation failed: Max retries exceeded")
    
    def translate(self, text: str, target_language: str, source_language: Optional[str] = None, 
                  file_type: str = "unknown") -> str:
        """
        Translate text to target language using OpenAI Agent with chunking support.
        
        Args:
            text: Text to translate
            target_language: Target language (e.g., "Spanish", "French", "German")
            source_language: Optional source language (auto-detected if not provided)
            file_type: File type for metrics (e.g., ".pdf", ".docx")
            
        Returns:
            Translated text
        """
        start_time = time.time()
        trace_id = None
        if OBSERVABILITY_AVAILABLE:
            trace_id = tracer.start_trace(
                "translate_document",
                {
                    "text_length": len(text),
                    "target_language": target_language,
                    "source_language": source_language,
                    "file_type": file_type
                }
            )
        
        self._log_translation_start(len(text), target_language)
        error_occurred = False
        retry_count = 0
        
        try:
            # Auto-detect source language when not provided
            if source_language is None or (isinstance(source_language, str) and source_language.strip() == ""):
                detected = self.detect_language(text)
                if detected:
                    source_language = detected
            
            # Check if chunking is needed
            chunks = self._chunk_text(text)
            needs_chunking = len(chunks) > 1
            
            if OBSERVABILITY_AVAILABLE and trace_id:
                tracer.add_event(trace_id, "chunking_decision", {
                    "needs_chunking": needs_chunking,
                    "chunk_count": len(chunks)
                })
            
            if needs_chunking:
                logger.info(f"Document requires chunking: {len(chunks)} chunks")
                translated_chunks = []
                previous_context = None
                
                for i, chunk in enumerate(chunks, 1):
                    self._log_chunk_translation(i, len(chunks))
                    if OBSERVABILITY_AVAILABLE and trace_id:
                        tracer.add_event(trace_id, "chunk_translation_start", {
                            "chunk_number": i,
                            "total_chunks": len(chunks),
                            "chunk_length": len(chunk)
                        })
                    
                    # Include context from previous chunk for consistency
                    translated_chunk = self._translate_with_retry(
                        chunk, 
                        target_language, 
                        source_language,
                        context=previous_context
                    )
                    
                    translated_chunks.append(translated_chunk)
                    if OBSERVABILITY_AVAILABLE and trace_id:
                        tracer.add_event(trace_id, "chunk_translation_complete", {
                            "chunk_number": i,
                            "translated_length": len(translated_chunk)
                        })
                    
                    # Use a summary of current chunk as context for next
                    # (to maintain terminology consistency)
                    if i < len(chunks):  # Not the last chunk
                        previous_context = translated_chunk[:500]  # First 500 chars as context
                
                # Reassemble chunks
                translated_text = "\n\n".join(translated_chunks)
            else:
                # Single chunk translation
                translated_text = self._translate_with_retry(text, target_language, source_language)
            
            duration = time.time() - start_time
            self._log_translation_complete(len(text), len(translated_text), duration)
            
            # Record metrics
            if OBSERVABILITY_AVAILABLE:
                metrics_collector.record_translation(
                    language=target_language,
                    file_type=file_type,
                    duration=duration,
                    chunked=needs_chunking,
                    chunks=len(chunks),
                    retries=retry_count,
                    error=False
                )
            
            if OBSERVABILITY_AVAILABLE and trace_id:
                tracer.end_trace(trace_id, "completed", {
                    "original_length": len(text),
                    "translated_length": len(translated_text),
                    "duration": duration,
                    "chunked": needs_chunking,
                    "chunks": len(chunks)
                })
            
            return translated_text
            
        except Exception as e:
            error_occurred = True
            duration = time.time() - start_time
            self._log_error(str(e))
            
            # Record error metrics
            if OBSERVABILITY_AVAILABLE:
                metrics_collector.record_translation(
                    language=target_language,
                    file_type=file_type,
                    duration=duration,
                    chunked=needs_chunking if 'needs_chunking' in locals() else False,
                    chunks=len(chunks) if 'chunks' in locals() else 1,
                    retries=retry_count,
                    error=True
                )
            
            if OBSERVABILITY_AVAILABLE and trace_id:
                tracer.end_trace(trace_id, "failed", {"error": str(e)})
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get translation metrics for observability (includes translation memory stats)."""
        m = self.translation_metrics.copy()
        m["translation_memory"] = self.translation_memory.stats()
        return m
    
    def translate_chunk(self, chunk: str, target_language: str, context: Optional[str] = None) -> str:
        """
        Translate a single chunk of text (for use with chunking strategy).
        
        Args:
            chunk: Text chunk to translate
            target_language: Target language
            context: Optional context from previous chunks
            
        Returns:
            Translated chunk
        """
        return self._translate_with_retry(chunk, target_language, context=context)

