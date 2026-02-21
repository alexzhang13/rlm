"""
Comprehensive tests for LLM Call Caching.

Tests cover:
1. Basic cache operations (get, set, get_or_call)
2. LRU eviction behavior
3. TTL expiration
4. Thread safety
5. Cache statistics
6. Edge cases and error handling
"""

import threading
import time
from unittest.mock import MagicMock

import pytest

from rlm.utils.cache import CacheEntry, CacheStats, LLMCallCache, create_cache


class TestCacheEntry:
    """Tests for the CacheEntry dataclass."""

    def test_entry_creation(self):
        """Test basic entry creation."""
        entry = CacheEntry(
            response="Hello, world!",
            timestamp=time.time(),
            prompt_preview="What is...",
            model="gpt-4",
        )
        assert entry.response == "Hello, world!"
        assert entry.model == "gpt-4"

    def test_entry_not_expired_without_ttl(self):
        """Test that entries don't expire when TTL is None."""
        entry = CacheEntry(
            response="test",
            timestamp=time.time() - 10000,  # 10000 seconds ago
            prompt_preview="test",
            model=None,
        )
        assert not entry.is_expired(None)
        assert not entry.is_expired(0)

    def test_entry_expired_with_ttl(self):
        """Test that entries expire correctly with TTL."""
        entry = CacheEntry(
            response="test",
            timestamp=time.time() - 100,  # 100 seconds ago
            prompt_preview="test",
            model=None,
        )
        assert entry.is_expired(50)  # TTL of 50 seconds
        assert not entry.is_expired(200)  # TTL of 200 seconds


class TestCacheStats:
    """Tests for the CacheStats dataclass."""

    def test_initial_stats(self):
        """Test that stats start at zero."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=75, misses=25)
        assert stats.total_requests == 100
        assert stats.hit_rate == 0.75

    def test_hit_rate_zero_requests(self):
        """Test hit rate with no requests."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_to_dict(self):
        """Test dictionary conversion."""
        stats = CacheStats(hits=10, misses=5, evictions=2, expirations=1)
        d = stats.to_dict()
        assert d["hits"] == 10
        assert d["misses"] == 5
        assert d["evictions"] == 2
        assert d["expirations"] == 1
        assert d["total_requests"] == 15
        assert "hit_rate" in d
        assert "tokens_saved_estimate" in d

    def test_reset(self):
        """Test stats reset."""
        stats = CacheStats(hits=10, misses=5, evictions=2, expirations=1)
        stats.reset()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.expirations == 0


class TestLLMCallCacheBasic:
    """Basic functionality tests for LLMCallCache."""

    def test_cache_creation(self):
        """Test basic cache creation."""
        cache = LLMCallCache()
        assert cache.max_size == 1000
        assert cache.ttl_seconds is None
        assert cache.enabled is True
        assert cache.size == 0

    def test_cache_creation_with_params(self):
        """Test cache creation with custom parameters."""
        cache = LLMCallCache(max_size=500, ttl_seconds=3600, enabled=True)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 3600

    def test_cache_invalid_max_size(self):
        """Test that max_size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="max_size must be >= 1"):
            LLMCallCache(max_size=0)
        with pytest.raises(ValueError, match="max_size must be >= 1"):
            LLMCallCache(max_size=-1)

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = LLMCallCache()
        
        cache.set("What is 2+2?", "gpt-4", "4")
        result = cache.get("What is 2+2?", "gpt-4")
        
        assert result == "4"
        assert cache.size == 1

    def test_get_missing_key(self):
        """Test getting a non-existent key."""
        cache = LLMCallCache()
        result = cache.get("nonexistent", "gpt-4")
        assert result is None

    def test_different_models_different_keys(self):
        """Test that different models create different cache keys."""
        cache = LLMCallCache()
        
        cache.set("What is 2+2?", "gpt-4", "4 (gpt-4)")
        cache.set("What is 2+2?", "gpt-3.5", "4 (gpt-3.5)")
        
        assert cache.size == 2
        assert cache.get("What is 2+2?", "gpt-4") == "4 (gpt-4)"
        assert cache.get("What is 2+2?", "gpt-3.5") == "4 (gpt-3.5)"

    def test_none_model_treated_as_default(self):
        """Test that None model is handled consistently."""
        cache = LLMCallCache()
        
        cache.set("test", None, "response")
        result = cache.get("test", None)
        
        assert result == "response"

    def test_update_existing_key(self):
        """Test updating an existing cache entry."""
        cache = LLMCallCache()
        
        cache.set("prompt", "model", "old_response")
        cache.set("prompt", "model", "new_response")
        
        assert cache.size == 1
        assert cache.get("prompt", "model") == "new_response"


class TestLLMCallCacheGetOrCall:
    """Tests for the get_or_call method."""

    def test_cache_miss_calls_function(self):
        """Test that cache miss invokes the call function."""
        cache = LLMCallCache()
        call_fn = MagicMock(return_value="API response")
        
        result, was_cached = cache.get_or_call("prompt", "model", call_fn)
        
        assert result == "API response"
        assert was_cached is False
        call_fn.assert_called_once()

    def test_cache_hit_does_not_call_function(self):
        """Test that cache hit does NOT invoke the call function."""
        cache = LLMCallCache()
        call_fn = MagicMock(return_value="API response")
        
        # First call - miss
        cache.get_or_call("prompt", "model", call_fn)
        
        # Second call - hit
        call_fn.reset_mock()
        result, was_cached = cache.get_or_call("prompt", "model", call_fn)
        
        assert result == "API response"
        assert was_cached is True
        call_fn.assert_not_called()

    def test_get_or_call_updates_stats(self):
        """Test that get_or_call updates statistics correctly."""
        cache = LLMCallCache()
        call_fn = MagicMock(return_value="response")
        
        # Miss
        cache.get_or_call("prompt1", "model", call_fn)
        assert cache.stats.misses == 1
        assert cache.stats.hits == 0
        
        # Hit
        cache.get_or_call("prompt1", "model", call_fn)
        assert cache.stats.misses == 1
        assert cache.stats.hits == 1
        
        # Another miss
        cache.get_or_call("prompt2", "model", call_fn)
        assert cache.stats.misses == 2
        assert cache.stats.hits == 1

    def test_disabled_cache_always_calls(self):
        """Test that disabled cache always invokes call function."""
        cache = LLMCallCache(enabled=False)
        call_fn = MagicMock(return_value="response")
        
        # First call
        result1, was_cached1 = cache.get_or_call("prompt", "model", call_fn)
        
        # Second call (should still call, not use cache)
        result2, was_cached2 = cache.get_or_call("prompt", "model", call_fn)
        
        assert call_fn.call_count == 2
        assert was_cached1 is False
        assert was_cached2 is False


class TestLLMCallCacheLRU:
    """Tests for LRU eviction behavior."""

    def test_eviction_at_max_size(self):
        """Test that oldest entries are evicted at max size."""
        cache = LLMCallCache(max_size=3)
        
        cache.set("prompt1", "model", "response1")
        cache.set("prompt2", "model", "response2")
        cache.set("prompt3", "model", "response3")
        
        assert cache.size == 3
        
        # Add fourth entry - should evict prompt1
        cache.set("prompt4", "model", "response4")
        
        assert cache.size == 3
        assert cache.get("prompt1", "model") is None  # Evicted
        assert cache.get("prompt2", "model") == "response2"
        assert cache.get("prompt3", "model") == "response3"
        assert cache.get("prompt4", "model") == "response4"

    def test_lru_access_updates_order(self):
        """Test that accessing an entry moves it to most recent."""
        cache = LLMCallCache(max_size=3)
        
        cache.set("prompt1", "model", "response1")
        cache.set("prompt2", "model", "response2")
        cache.set("prompt3", "model", "response3")
        
        # Access prompt1 - makes it most recently used
        cache.get("prompt1", "model")
        
        # Add prompt4 - should evict prompt2 (now oldest)
        cache.set("prompt4", "model", "response4")
        
        assert cache.get("prompt1", "model") == "response1"  # Still present
        assert cache.get("prompt2", "model") is None  # Evicted
        assert cache.get("prompt3", "model") == "response3"
        assert cache.get("prompt4", "model") == "response4"

    def test_eviction_updates_stats(self):
        """Test that evictions update statistics."""
        cache = LLMCallCache(max_size=2)
        
        cache.set("prompt1", "model", "response1")
        cache.set("prompt2", "model", "response2")
        
        assert cache.stats.evictions == 0
        
        cache.set("prompt3", "model", "response3")
        
        assert cache.stats.evictions == 1


class TestLLMCallCacheTTL:
    """Tests for TTL expiration behavior."""

    def test_expired_entry_returns_none(self, monkeypatch):
        """Test that expired entries return None."""
        fake_time = [1000.0]
        monkeypatch.setattr(time, "time", lambda: fake_time[0])
        
        cache = LLMCallCache(ttl_seconds=0.1)  # 100ms TTL
        cache.set("prompt", "model", "response")
        
        # Immediate access should work
        assert cache.get("prompt", "model") == "response"
        
        # Advance time beyond TTL
        fake_time[0] += 0.2
        
        # Should be expired
        assert cache.get("prompt", "model") is None

    def test_expiration_updates_stats(self, monkeypatch):
        """Test that expirations update statistics."""
        fake_time = [1000.0]
        monkeypatch.setattr(time, "time", lambda: fake_time[0])
        
        cache = LLMCallCache(ttl_seconds=0.05)  # 50ms TTL
        cache.set("prompt", "model", "response")
        
        # Advance time beyond TTL
        fake_time[0] += 0.1
        
        cache.get("prompt", "model")  # Triggers expiration check
        
        assert cache.stats.expirations == 1


class TestLLMCallCacheThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_writes(self):
        """Test concurrent writes don't corrupt the cache."""
        cache = LLMCallCache(max_size=1000)
        errors = []
        
        def writer(thread_id: int):
            try:
                for i in range(100):
                    cache.set(f"prompt_{thread_id}_{i}", "model", f"response_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        # Should have at most max_size entries
        assert cache.size <= 1000

    def test_concurrent_reads_writes(self):
        """Test concurrent reads and writes."""
        cache = LLMCallCache(max_size=100)
        errors = []
        
        # Pre-populate
        for i in range(50):
            cache.set(f"prompt_{i}", "model", f"response_{i}")
        
        def reader():
            try:
                for i in range(100):
                    cache.get(f"prompt_{i % 50}", "model")
            except Exception as e:
                errors.append(e)
        
        def writer():
            try:
                for i in range(100):
                    cache.set(f"new_prompt_{i}", "model", f"new_response_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=reader))
            threads.append(threading.Thread(target=writer))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestLLMCallCacheOperations:
    """Tests for cache utility operations."""

    def test_invalidate_existing(self):
        """Test invalidating an existing entry."""
        cache = LLMCallCache()
        
        cache.set("prompt", "model", "response")
        assert cache.size == 1
        
        removed = cache.invalidate("prompt", "model")
        
        assert removed is True
        assert cache.size == 0
        assert cache.get("prompt", "model") is None

    def test_invalidate_nonexistent(self):
        """Test invalidating a non-existent entry."""
        cache = LLMCallCache()
        
        removed = cache.invalidate("nonexistent", "model")
        
        assert removed is False

    def test_clear(self):
        """Test clearing all entries."""
        cache = LLMCallCache()
        
        for i in range(10):
            cache.set(f"prompt_{i}", "model", f"response_{i}")
        
        assert cache.size == 10
        
        count = cache.clear()
        
        assert count == 10
        assert cache.size == 0

    def test_get_debug_info(self):
        """Test debug info retrieval."""
        cache = LLMCallCache(max_size=100, ttl_seconds=3600)
        
        cache.set("test prompt", "gpt-4", "test response")
        
        info = cache.get_debug_info()
        
        assert info["enabled"] is True
        assert info["max_size"] == 100
        assert info["ttl_seconds"] == 3600
        assert info["current_size"] == 1
        assert "stats" in info
        assert "recent_entries" in info

    def test_repr(self):
        """Test string representation."""
        cache = LLMCallCache(max_size=100, ttl_seconds=60)
        repr_str = repr(cache)
        
        assert "LLMCallCache" in repr_str
        assert "max_size=100" in repr_str
        assert "ttl_seconds=60" in repr_str


class TestCreateCacheFactory:
    """Tests for the create_cache factory function."""

    def test_create_enabled_cache(self):
        """Test creating an enabled cache."""
        cache = create_cache(enabled=True, max_size=500, ttl_seconds=1800)
        
        assert cache is not None
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800

    def test_create_disabled_cache(self):
        """Test creating a disabled cache returns None."""
        cache = create_cache(enabled=False)
        
        assert cache is None

    def test_create_cache_defaults(self):
        """Test create_cache with default parameters."""
        cache = create_cache()
        
        assert cache is not None
        assert cache.max_size == 1000
        assert cache.ttl_seconds is None


class TestCacheHashConsistency:
    """Tests for hash key consistency."""

    def test_same_input_same_hash(self):
        """Test that identical inputs produce identical hashes."""
        hash1 = LLMCallCache._hash_key("prompt", "model")
        hash2 = LLMCallCache._hash_key("prompt", "model")
        
        assert hash1 == hash2

    def test_different_prompt_different_hash(self):
        """Test that different prompts produce different hashes."""
        hash1 = LLMCallCache._hash_key("prompt1", "model")
        hash2 = LLMCallCache._hash_key("prompt2", "model")
        
        assert hash1 != hash2

    def test_different_model_different_hash(self):
        """Test that different models produce different hashes."""
        hash1 = LLMCallCache._hash_key("prompt", "model1")
        hash2 = LLMCallCache._hash_key("prompt", "model2")
        
        assert hash1 != hash2

    def test_long_prompt_hashes_correctly(self):
        """Test that long prompts hash correctly."""
        long_prompt = "x" * 100000  # 100KB prompt
        
        hash1 = LLMCallCache._hash_key(long_prompt, "model")
        hash2 = LLMCallCache._hash_key(long_prompt, "model")
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest length

    def test_unicode_prompt_hashes_correctly(self):
        """Test that unicode prompts hash correctly."""
        unicode_prompt = "你好世界 🚀 مرحبا"
        
        hash1 = LLMCallCache._hash_key(unicode_prompt, "model")
        hash2 = LLMCallCache._hash_key(unicode_prompt, "model")
        
        assert hash1 == hash2


# =============================================================================
# Integration Tests with RLM/LocalREPL-like behavior
# =============================================================================


class FakeLLMHandler:
    """
    Minimal LLM handler simulation for integration testing.
    
    Tracks call counts and simulates the behavior of llm_query
    going through cache → API call flow.
    """

    def __init__(self, cache: LLMCallCache | None = None):
        self.cache = cache
        self.api_call_count = 0
        self.pending_calls: list[str] = []

    def llm_query(self, prompt: str, model: str | None = None) -> str:
        """Simulate llm_query with optional caching (mirrors LocalREPL._llm_query)."""

        def make_api_call() -> str:
            self.api_call_count += 1
            self.pending_calls.append(prompt)
            return f"Response to: {prompt[:50]}"

        if self.cache is not None:
            result, was_cached = self.cache.get_or_call(prompt, model, make_api_call)
            return result
        else:
            return make_api_call()

    def llm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        """Simulate llm_query_batched with optional caching (mirrors LocalREPL._llm_query_batched)."""
        if self.cache is None:
            # No caching - call API for all
            results = []
            for prompt in prompts:
                self.api_call_count += 1
                self.pending_calls.append(prompt)
                results.append(f"Response to: {prompt[:50]}")
            return results

        # With caching
        results: list[str | None] = [None] * len(prompts)
        uncached: list[tuple[int, str]] = []

        for i, prompt in enumerate(prompts):
            cached = self.cache.get(prompt, model)
            if cached is not None:
                results[i] = cached
                self.cache.record_hit()
            else:
                uncached.append((i, prompt))
                self.cache.record_miss()

        # Make API calls for uncached prompts
        for idx, prompt in uncached:
            self.api_call_count += 1
            self.pending_calls.append(prompt)
            response = f"Response to: {prompt[:50]}"
            results[idx] = response
            self.cache.set(prompt, model, response)

        return [r for r in results if r is not None]


class TestCacheIntegrationWithRLMBehavior:
    """
    Integration tests verifying cache works correctly when used
    in RLM/LocalREPL-like execution patterns.
    """

    def test_identical_prompts_cached_single_calls(self):
        """Verify identical prompts are cached through llm_query."""
        cache = LLMCallCache(max_size=100)
        handler = FakeLLMHandler(cache=cache)

        prompt = "What is 2+2?"

        # First call - cache miss, API called
        result1 = handler.llm_query(prompt, "gpt-4")
        assert handler.api_call_count == 1
        assert cache.stats.misses == 1
        assert cache.stats.hits == 0

        # Second call - cache hit, API NOT called
        result2 = handler.llm_query(prompt, "gpt-4")
        assert handler.api_call_count == 1  # Still 1
        assert cache.stats.misses == 1
        assert cache.stats.hits == 1

        # Results identical
        assert result1 == result2

    def test_different_prompts_not_cached(self):
        """Verify different prompts each trigger API calls."""
        cache = LLMCallCache(max_size=100)
        handler = FakeLLMHandler(cache=cache)

        result1 = handler.llm_query("Prompt A", "gpt-4")
        result2 = handler.llm_query("Prompt B", "gpt-4")
        result3 = handler.llm_query("Prompt C", "gpt-4")

        assert handler.api_call_count == 3
        assert cache.stats.misses == 3
        assert cache.stats.hits == 0
        assert result1 != result2 != result3

    def test_batched_caching_partial_hits(self):
        """Verify batched calls properly use cache for some prompts."""
        cache = LLMCallCache(max_size=100)
        handler = FakeLLMHandler(cache=cache)

        # Pre-populate cache with one prompt
        handler.llm_query("Cached prompt", "gpt-4")
        assert handler.api_call_count == 1

        # Batch with mix of cached and uncached
        results = handler.llm_query_batched(
            ["Cached prompt", "New prompt 1", "New prompt 2"],
            "gpt-4"
        )

        # Should only call API for 2 new prompts
        assert handler.api_call_count == 3  # 1 + 2 new
        assert len(results) == 3
        assert cache.stats.hits >= 1  # "Cached prompt" was a hit

    def test_fibonacci_like_recursion_pattern(self):
        """Simulate Fibonacci-like recursive subproblem reuse."""
        cache = LLMCallCache(max_size=100)
        handler = FakeLLMHandler(cache=cache)

        # Simulate fib(5) calling pattern:
        # fib(5) calls fib(4), fib(3)
        # fib(4) calls fib(3), fib(2)  <- fib(3) repeated!
        # fib(3) calls fib(2), fib(1)  <- fib(2) repeated!
        # etc.

        prompts_in_order = [
            "Compute fib(1)",
            "Compute fib(2)",
            "Compute fib(1)",  # Repeat
            "Compute fib(2)",  # Repeat
            "Compute fib(3)",
            "Compute fib(2)",  # Repeat
            "Compute fib(3)",  # Repeat
            "Compute fib(4)",
            "Compute fib(3)",  # Repeat
            "Compute fib(4)",  # Repeat
            "Compute fib(5)",
        ]

        for prompt in prompts_in_order:
            handler.llm_query(prompt, "gpt-4")

        # Without cache: 11 API calls
        # With cache: only 5 unique prompts = 5 API calls
        assert handler.api_call_count == 5
        assert cache.stats.hits == 6  # 11 - 5 = 6 cache hits
        assert cache.stats.misses == 5
        assert cache.stats.hit_rate > 0.5  # >50% efficiency

    def test_cache_stats_accurate_through_execution(self):
        """Verify cache statistics are accurately tracked."""
        cache = LLMCallCache(max_size=100)
        handler = FakeLLMHandler(cache=cache)

        # 3 unique prompts, each called twice = 6 total calls
        for _ in range(2):
            handler.llm_query("Alpha", "model")
            handler.llm_query("Beta", "model")
            handler.llm_query("Gamma", "model")

        assert cache.stats.total_requests == 6
        assert cache.stats.misses == 3  # First call for each
        assert cache.stats.hits == 3    # Second call for each
        assert cache.stats.hit_rate == 0.5
        assert handler.api_call_count == 3  # Only 3 actual API calls

    def test_cached_and_uncached_produce_identical_results(self):
        """Ensure cached responses match original API responses."""
        cache = LLMCallCache(max_size=100)
        handler = FakeLLMHandler(cache=cache)

        prompt = "Explain quantum computing"

        # First call - from API
        api_result = handler.llm_query(prompt, "gpt-4")

        # Second call - from cache
        cached_result = handler.llm_query(prompt, "gpt-4")

        # Must be byte-for-byte identical
        assert api_result == cached_result
        assert handler.api_call_count == 1

    def test_pending_calls_tracked_correctly(self):
        """Verify pending_calls list reflects actual API calls made."""
        cache = LLMCallCache(max_size=100)
        handler = FakeLLMHandler(cache=cache)

        handler.llm_query("First", "gpt-4")
        handler.llm_query("Second", "gpt-4")
        handler.llm_query("First", "gpt-4")  # Cached - no API call

        # Only 2 API calls should be in pending_calls
        assert len(handler.pending_calls) == 2
        assert "First" in handler.pending_calls
        assert "Second" in handler.pending_calls

    def test_no_cache_makes_all_api_calls(self):
        """Verify behavior without cache - all calls go to API."""
        handler = FakeLLMHandler(cache=None)

        handler.llm_query("Prompt", "gpt-4")
        handler.llm_query("Prompt", "gpt-4")  # Same prompt
        handler.llm_query("Prompt", "gpt-4")  # Same prompt again

        # All 3 should hit API
        assert handler.api_call_count == 3
