# Async Patterns Reference

## Basic Async/Await

```python
import asyncio

async def fetch_data(url: str) -> dict:
    await asyncio.sleep(1)  # Simulate I/O
    return {"url": url, "data": "..."}

async def main() -> None:
    result = await fetch_data("https://api.example.com")
    print(result)

asyncio.run(main())
```

## Concurrent Operations with gather

```python
async def fetch_all(urls: list[str]) -> list[dict]:
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)

# With error handling
results = await asyncio.gather(*tasks, return_exceptions=True)
for result in results:
    if isinstance(result, Exception):
        print(f"Error: {result}")
```

## Task Groups (Python 3.11+)

```python
async def process_batch(items: list[str]) -> list[str]:
    results: list[str] = []

    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(process_item(item))

    return results
```

## Semaphore for Rate Limiting

```python
sem = asyncio.Semaphore(5)  # Max 5 concurrent

async def rate_limited_call(prompt: str) -> str:
    async with sem:
        return await api_call(prompt)

# Use with batched operations
async def batch_calls(prompts: list[str]) -> list[str]:
    tasks = [rate_limited_call(p) for p in prompts]
    return await asyncio.gather(*tasks)
```

## Async Context Managers

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def managed_connection(url: str) -> AsyncIterator[Connection]:
    conn = await connect(url)
    try:
        yield conn
    finally:
        await conn.close()
```

## Mixing Sync and Async

```python
# Run blocking I/O in thread pool
async def read_large_file(path: str) -> str:
    return await asyncio.to_thread(Path(path).read_text)

# Bridge sync code calling async
def sync_wrapper() -> str:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(async_function())
    finally:
        loop.close()
```

## Async Generators

```python
from collections.abc import AsyncIterator

async def stream_results(query: str) -> AsyncIterator[dict]:
    offset = 0
    while True:
        batch = await fetch_batch(query, offset)
        if not batch:
            break
        for item in batch:
            yield item
        offset += len(batch)

# Consume
async for result in stream_results("SELECT *"):
    process(result)
```

## Timeouts

```python
async def fetch_with_timeout(url: str, timeout: float = 5.0) -> dict:
    async with asyncio.timeout(timeout):
        return await fetch_data(url)
```

## Background Tasks

```python
class TaskManager:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    def spawn(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
```
