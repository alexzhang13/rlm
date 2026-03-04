"""
LLM Call Caching for RLM.

Provides memoization for `llm_query` and `llm_query_batched` calls to avoid
redundant API requests when the same prompt is queried multiple times during
recursive RLM execution.

This addresses Issue #82: "Efficiency & Token Consumption: Proposal for
Benchmarking and Memoization in RLM"

Key Design Decisions:
1. Cache key is based on (prompt_hash, model) for exact matching
2. Thread-safe using threading.Lock for concurrent environments
3. LRU eviction when max_size is reached
4. Optional TTL for time-based expiration
5. Cache statistics for monitoring and debugging
6. Configurable at environment level (opt-in by default)

Example:
    cache = LLMCallCache(max_size=1000, ttl_seconds=3600)
    
    # First call - cache miss, makes API request
    result1 = cache.get_or_call("What is 2+2?", "gpt-4", lambda: api_call())
    
    # Second call - cache hit, returns cached result
    result2 = cache.get_or_call("What is 2+2?", "gpt-4", lambda: api_call())
    
    print(cache.stats)  # {'hits': 1, 'misses': 1, 'hit_rate': 0.5, ...}
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CacheEntry:
    """A single cached LLM response with metadata."""

    response: str
    timestamp: float
    prompt_preview: str  # First 100 chars for debugging
    model: str | None
    
    def is_expired(self, ttl_seconds: float | None) -> bool:
        """Check if this entry has expired based on TTL."""
        if ttl_seconds is None or ttl_seconds <= 0:
            return False
        return (time.time() - self.timestamp) > ttl_seconds


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    
    @property
    def total_requests(self) -> int:
        """Total number of cache lookups."""
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a fraction [0.0, 1.0]."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property
    def tokens_saved_estimate(self) -> int:
        """
        Rough estimate of tokens saved by cache hits.
        Assumes average prompt is ~500 tokens (conservative estimate).
        """
        return self.hits * 500
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 4),
            "tokens_saved_estimate": self.tokens_saved_estimate,
        }
    
    def reset(self) -> None:
        """Reset all statistics to zero."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.misses += 1


@dataclass
class LLMCallCache:
    """
    Thread-safe LRU cache for LLM call responses.
    
    Caches responses based on (prompt, model) pairs to avoid redundant API calls
    during recursive RLM execution. Uses LRU eviction when max_size is reached.
    
    Attributes:
        max_size: Maximum number of entries to cache (default: 1000).
        ttl_seconds: Time-to-live in seconds. None or 0 means no expiration.
        enabled: Whether caching is active. Can be toggled at runtime.
    
    Thread Safety:
        All public methods are thread-safe via internal locking.
    
    Example:
        >>> cache = LLMCallCache(max_size=100, ttl_seconds=3600)
        >>> 
        >>> def make_api_call():
        ...     return "API response"
        >>> 
        >>> # First call - miss
        >>> result = cache.get_or_call("prompt", "model", make_api_call)
        >>> 
        >>> # Second call - hit (no API call)
        >>> result = cache.get_or_call("prompt", "model", make_api_call)
        >>> 
        >>> print(cache.stats.hit_rate)  # 0.5
    """
    
    max_size: int = 1000
    ttl_seconds: float | None = None
    enabled: bool = True
    
    # Internal state (initialized in __post_init__)
    _cache: OrderedDict[str, CacheEntry] = field(default_factory=OrderedDict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _stats: CacheStats = field(default_factory=CacheStats, repr=False)
    
    def __post_init__(self) -> None:
        """Initialize internal state after dataclass initialization."""
        # Validate max_size
        if self.max_size < 1:
            raise ValueError("max_size must be >= 1")
        # Ensure we have fresh instances (dataclass default_factory quirk)
        if not isinstance(self._cache, OrderedDict):
            self._cache = OrderedDict()
        # threading.Lock() is a factory function, not a class, so we check for acquire method
        if not hasattr(self._lock, "acquire"):
            self._lock = threading.Lock()
        if not isinstance(self._stats, CacheStats):
            self._stats = CacheStats()
    
    @staticmethod
    def _hash_key(prompt: str, model: str | None) -> str:
        """
        Generate a cache key from prompt and model.
        
        Uses SHA-256 for consistent hashing. Model is normalized to handle None.
        
        Args:
            prompt: The full prompt string.
            model: The model name (or None for default).
        
        Returns:
            A hex digest string used as cache key.
        """
        # Normalize model to string
        model_str = model if model else "__default__"
        
        # Combine with length prefix to avoid collisions (e.g., model="a:", prompt="b")
        content = f"{len(model_str)}:{model_str}:{prompt}"
        
        # Use SHA-256 for good distribution and collision resistance
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def get(self, prompt: str, model: str | None = None) -> str | None:
        """
        Get a cached response if it exists and is not expired.
        
        Args:
            prompt: The prompt to look up.
            model: The model name (or None for default).
        
        Returns:
            The cached response string, or None if not found/expired.
        """
        if not self.enabled:
            return None
        
        key = self._hash_key(prompt, model)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
            
            # Check expiration
            if entry.is_expired(self.ttl_seconds):
                # Remove expired entry
                del self._cache[key]
                self._stats.expirations += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            return entry.response
    
    def set(self, prompt: str, model: str | None, response: str) -> None:
        """
        Cache a response for a prompt/model pair.
        
        Args:
            prompt: The prompt that was sent.
            model: The model name (or None for default).
            response: The response to cache.
        """
        if not self.enabled:
            return
        
        key = self._hash_key(prompt, model)
        
        with self._lock:
            # If key exists, update and move to end
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                # Evict oldest if at capacity
                while len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)
                    self._stats.evictions += 1
            
            # Store entry
            self._cache[key] = CacheEntry(
                response=response,
                timestamp=time.time(),
                prompt_preview=prompt[:100] if len(prompt) > 100 else prompt,
                model=model,
            )
    
    def get_or_call(
        self,
        prompt: str,
        model: str | None,
        call_fn: Callable[[], str],
    ) -> tuple[str, bool]:
        """
        Get cached response or execute the call function and cache the result.
        
        This is the primary method for cache integration. It performs the full
        cache-check -> call -> cache-store flow. Note: concurrent misses for the
        same key may result in multiple calls to call_fn.
        
        Args:
            prompt: The prompt to look up/cache.
            model: The model name (or None for default).
            call_fn: A zero-argument callable that makes the actual API call.
                     Only invoked on cache miss.
        
        Returns:
            A tuple of (response, was_cached) where was_cached indicates
            whether the response came from cache (True) or API call (False).
        """
        if not self.enabled:
            result = call_fn()
            return result, False
        
        # Try cache first
        cached = self.get(prompt, model)
        if cached is not None:
            with self._lock:
                self._stats.hits += 1
            return cached, True
        
        # Cache miss - make the call
        with self._lock:
            self._stats.misses += 1
        
        result = call_fn()
        
        # Store in cache
        self.set(prompt, model, result)
        
        return result, False
    
    def invalidate(self, prompt: str, model: str | None = None) -> bool:
        """
        Remove a specific entry from the cache.
        
        Args:
            prompt: The prompt to invalidate.
            model: The model name (or None for default).
        
        Returns:
            True if an entry was removed, False if not found.
        """
        key = self._hash_key(prompt, model)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> int:
        """
        Clear all cached entries.
        
        Returns:
            The number of entries that were cleared.
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    @property
    def stats(self) -> CacheStats:
        """Get cache statistics. Use record_hit()/record_miss() for thread-safe updates."""
        return self._stats
    
    def record_hit(self) -> None:
        """Thread-safe method to record a cache hit."""
        with self._lock:
            self._stats.hits += 1
    
    def record_miss(self) -> None:
        """Thread-safe method to record a cache miss."""
        with self._lock:
            self._stats.misses += 1
    
    @property
    def size(self) -> int:
        """Current number of cached entries."""
        with self._lock:
            return len(self._cache)
    
    def get_debug_info(self) -> dict[str, Any]:
        """
        Get detailed debug information about the cache.
        
        Returns:
            Dictionary with stats, configuration, and entry previews.
        """
        with self._lock:
            entries_preview = [
                {
                    "prompt_preview": entry.prompt_preview,
                    "model": entry.model,
                    "age_seconds": round(time.time() - entry.timestamp, 1),
                }
                for entry in list(self._cache.values())[-5:]  # Last 5 entries
            ]
        
        return {
            "enabled": self.enabled,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "current_size": self.size,
            "stats": self._stats.to_dict(),
            "recent_entries": entries_preview,
        }
    
    def __repr__(self) -> str:
        return (
            f"LLMCallCache(max_size={self.max_size}, "
            f"ttl_seconds={self.ttl_seconds}, "
            f"enabled={self.enabled}, "
            f"size={self.size}, "
            f"hit_rate={self._stats.hit_rate:.2%})"
        )


# =============================================================================
# Factory function for creating pre-configured caches
# =============================================================================

def create_cache(
    enabled: bool = True,
    max_size: int = 1000,
    ttl_seconds: float | None = None,
) -> LLMCallCache | None:
    """
    Factory function to create an LLMCallCache with common configurations.
    
    Args:
        enabled: Whether to create a cache at all. If False, returns None.
        max_size: Maximum number of entries.
        ttl_seconds: Time-to-live for entries. None means no expiration.
    
    Returns:
        An LLMCallCache instance, or None if enabled=False.
    
    Example:
        # Create a cache with 1-hour TTL
        cache = create_cache(max_size=500, ttl_seconds=3600)
        
        # Disable caching entirely
        cache = create_cache(enabled=False)  # Returns None
    """
    if not enabled:
        return None
    
    return LLMCallCache(
        max_size=max_size,
        ttl_seconds=ttl_seconds,
        enabled=True,
    )
