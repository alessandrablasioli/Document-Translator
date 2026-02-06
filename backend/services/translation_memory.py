"""
Translation memory for cost savings: cache (source_text, target_language) -> translated_text.
Reuses previous translations for identical segments (e.g. repeated headers, boilerplate).
"""
import hashlib
import logging
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger(__name__)


class TranslationMemory:
    """
    In-memory cache of source text + target language -> translated text.
    Uses LRU eviction when max_entries is reached.
    """

    def __init__(self, max_entries: int = 10_000):
        self.max_entries = max_entries
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _key(self, source_text: str, target_language: str) -> str:
        normalized = source_text.strip()
        h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{h}|{target_language}"

    def get(self, source_text: str, target_language: str) -> Optional[str]:
        k = self._key(source_text, target_language)
        if k in self._cache:
            self._hits += 1
            self._cache.move_to_end(k)  # LRU: mark as recently used
            logger.debug("Translation memory hit for %s", target_language)
            return self._cache[k]
        self._misses += 1
        return None

    def set(self, source_text: str, target_language: str, translated_text: str) -> None:
        k = self._key(source_text, target_language)
        if k in self._cache:
            self._cache.move_to_end(k)
        else:
            if len(self._cache) >= self.max_entries:
                self._cache.popitem(last=False)
            self._cache[k] = translated_text

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_entries": self.max_entries,
            "hit_rate": self._hits / total if total else 0,
        }
