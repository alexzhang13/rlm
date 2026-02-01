# Pagination Reference

Auto-paginating iterators for list operations with manual control options. The SDK provides three pagination types: ID-based, token-based, and cursor-based.

## Pagination Classes

### Synchronous Pagination

```python { .api }
class SyncPage(Generic[T]):
    """
    Synchronous ID-based pagination.

    Provides:
        - Automatic iteration over all items
        - Manual page control
        - Page metadata access

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over all items across all pages automatically.

        Yields:
            Individual items from current and subsequent pages
        """
        ...

    def __getitem__(self, index: int) -> T:
        """
        Get item by index in current page.

        Parameters:
            index: Item index in current page

        Returns:
            Item at index

        Raises:
            IndexError: If index out of range
        """
        ...

    def has_next_page(self) -> bool:
        """
        Check if another page exists.

        Returns:
            True if next page available
        """
        ...

    def next_page_info(self) -> dict[str, Any]:
        """
        Get information needed to fetch next page.

        Returns:
            Dictionary with pagination parameters (after_id, limit, etc.)
        """
        ...

    def get_next_page(self) -> SyncPage[T]:
        """
        Fetch next page.

        Returns:
            New SyncPage for next page

        Raises:
            ValueError: If no next page exists
        """
        ...

class SyncTokenPage(Generic[T]):
    """
    Synchronous token-based pagination.

    Similar to SyncPage but uses continuation tokens instead of IDs.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items automatically."""
        ...

    def has_next_page(self) -> bool:
        """Check if next page exists."""
        ...

    def next_page_info(self) -> dict[str, Any]:
        """Get next page token."""
        ...

    def get_next_page(self) -> SyncTokenPage[T]:
        """Fetch next page."""
        ...

class SyncPageCursor(Generic[T]):
    """
    Synchronous cursor-based pagination.

    Uses cursors for pagination instead of IDs or tokens.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items automatically."""
        ...

    def has_next_page(self) -> bool:
        """Check if next page exists."""
        ...

    def next_page_info(self) -> dict[str, Any]:
        """Get next page cursor."""
        ...

    def get_next_page(self) -> SyncPageCursor[T]:
        """Fetch next page."""
        ...
```

### Asynchronous Pagination

```python { .api }
class AsyncPage(Generic[T]):
    """
    Asynchronous ID-based pagination.

    Provides:
        - Async automatic iteration over all items
        - Async manual page control
        - Page metadata access

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __aiter__(self) -> AsyncIterator[T]:
        """
        Async iterate over all items across all pages.

        Yields:
            Individual items from current and subsequent pages
        """
        ...

    def __getitem__(self, index: int) -> T:
        """Get item by index in current page."""
        ...

    async def has_next_page(self) -> bool:
        """Check if another page exists."""
        ...

    async def next_page_info(self) -> dict[str, Any]:
        """Get information needed to fetch next page."""
        ...

    async def get_next_page(self) -> AsyncPage[T]:
        """Fetch next page."""
        ...

class AsyncTokenPage(Generic[T]):
    """
    Asynchronous token-based pagination.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __aiter__(self) -> AsyncIterator[T]: ...
    async def has_next_page(self) -> bool: ...
    async def next_page_info(self) -> dict[str, Any]: ...
    async def get_next_page(self) -> AsyncTokenPage[T]: ...

class AsyncPageCursor(Generic[T]):
    """
    Asynchronous cursor-based pagination.

    Attributes:
        data: Items in current page
    """
    data: list[T]

    def __aiter__(self) -> AsyncIterator[T]: ...
    async def has_next_page(self) -> bool: ...
    async def next_page_info(self) -> dict[str, Any]: ...
    async def get_next_page(self) -> AsyncPageCursor[T]: ...
```

## Usage Examples

### Auto-Pagination (Simple)

```python
from anthropic import Anthropic

client = Anthropic()

# Automatically iterate over all batches
for batch in client.messages.batches.list():
    print(f"Batch {batch.id}: {batch.processing_status}")
```

### Auto-Pagination with Limit

```python
# Get first 100 batches total (auto-fetching pages)
count = 0
for batch in client.messages.batches.list(limit=20):
    print(batch.id)
    count += 1
    if count >= 100:
        break
```

### Manual Pagination

```python
# Get first page
page = client.messages.batches.list(limit=10)

# Process first page
for batch in page.data:
    print(f"Batch: {batch.id}")

# Check if more pages
if page.has_next_page():
    print("More pages available")

    # Get next page info
    next_info = page.next_page_info()
    print(f"Next page params: {next_info}")

    # Fetch next page
    next_page = page.get_next_page()
    for batch in next_page.data:
        print(f"Next page batch: {batch.id}")
```

### Iterate All Pages Manually

```python
page = client.messages.batches.list(limit=10)

while True:
    # Process current page
    for batch in page.data:
        print(batch.id)

    # Check for next page
    if not page.has_next_page():
        break

    # Fetch next page
    page = page.get_next_page()
```

### Pagination with Before/After

```python
# Get batches after specific ID
page = client.messages.batches.list(
    after_id="batch_abc123",
    limit=20
)

for batch in page:
    print(batch.id)

# Get batches before specific ID
page = client.messages.batches.list(
    before_id="batch_xyz789",
    limit=20
)

for batch in page:
    print(batch.id)
```

### Access Current Page Data

```python
page = client.messages.batches.list(limit=5)

# Get items in current page
items = page.data
print(f"Current page has {len(items)} items")

# Access by index
first_item = page[0]
print(f"First item: {first_item.id}")
```

### Async Auto-Pagination

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    # Automatically iterate over all batches
    async for batch in client.messages.batches.list():
        print(f"Batch {batch.id}: {batch.processing_status}")

asyncio.run(main())
```

### Async Manual Pagination

```python
async def paginate_manually():
    client = AsyncAnthropic()

    # Get first page
    page = await client.messages.batches.list(limit=10)

    # Process first page
    for batch in page.data:
        print(batch.id)

    # Check and fetch next page
    if await page.has_next_page():
        next_page = await page.get_next_page()
        for batch in next_page.data:
            print(batch.id)

asyncio.run(paginate_manually())
```

### Async Iterate All Pages

```python
async def iterate_all_pages():
    client = AsyncAnthropic()

    page = await client.messages.batches.list(limit=10)

    while True:
        for batch in page.data:
            print(batch.id)

        if not await page.has_next_page():
            break

        page = await page.get_next_page()

asyncio.run(iterate_all_pages())
```

### Pagination with Processing

```python
# Collect all batches with filtering
completed_batches = []

for batch in client.messages.batches.list():
    if batch.processing_status == "ended":
        completed_batches.append(batch)

print(f"Found {len(completed_batches)} completed batches")
```

### Limit Total Items

```python
# Get exactly 50 items total
items = []
for batch in client.messages.batches.list(limit=20):
    items.append(batch)
    if len(items) >= 50:
        break

print(f"Collected {len(items)} items")
```

### Paginate with Error Handling

```python
from anthropic import APIError

try:
    for batch in client.messages.batches.list():
        print(batch.id)
except APIError as e:
    print(f"Pagination error: {e}")
```

### Concurrent Page Fetching

```python
import asyncio

async def fetch_multiple_pages():
    client = AsyncAnthropic()

    # Fetch first page
    page1 = await client.messages.batches.list(limit=10)

    # Fetch multiple subsequent pages concurrently
    if await page1.has_next_page():
        next_info = await page1.next_page_info()

        pages = await asyncio.gather(
            page1.get_next_page(),
            client.messages.batches.list(**next_info, limit=10),
        )

        for page in pages:
            for batch in page.data:
                print(batch.id)

asyncio.run(fetch_multiple_pages())
```

### List Models with Pagination

```python
# Auto-paginate through all models
for model in client.models.list():
    print(f"{model.id}: {model.display_name}")
```

### Count Items with Pagination

```python
# Count total items
total = 0
for batch in client.messages.batches.list():
    total += 1

print(f"Total batches: {total}")
```

### Pagination Performance

```python
import time

start = time.time()

# Efficient pagination with larger page size
count = 0
for batch in client.messages.batches.list(limit=100):
    count += 1

elapsed = time.time() - start
print(f"Processed {count} items in {elapsed:.2f} seconds")
```

### Page Metadata

```python
page = client.messages.batches.list(limit=10)

print(f"Items in page: {len(page.data)}")
print(f"Has next: {page.has_next_page()}")

if page.has_next_page():
    next_info = page.next_page_info()
    print(f"Next page info: {next_info}")
```

### Reverse Pagination

```python
# Get most recent items first (default)
for batch in client.messages.batches.list(limit=10):
    print(f"Recent: {batch.id} - {batch.created_at}")

# Get older items using before_id
oldest_on_page = None
for batch in page.data:
    oldest_on_page = batch.id

if oldest_on_page:
    older_page = client.messages.batches.list(before_id=oldest_on_page, limit=10)
    for batch in older_page:
        print(f"Older: {batch.id}")
```

### Collect All Items

```python
# Collect all items into list
all_batches = []
for batch in client.messages.batches.list():
    all_batches.append(batch)

print(f"Total batches: {len(all_batches)}")
```

### Batch Processing Pages

```python
def process_batch(batches):
    """Process a batch of items."""
    for batch in batches:
        print(f"Processing {batch.id}")

page = client.messages.batches.list(limit=50)
while True:
    process_batch(page.data)

    if not page.has_next_page():
        break

    page = page.get_next_page()
```

### Custom Page Size

```python
# Use small pages for frequent updates
for batch in client.messages.batches.list(limit=5):
    print(batch.id)

# Use large pages for bulk processing
for batch in client.messages.batches.list(limit=100):
    print(batch.id)
```

## JSONL Stream Decoders

For batch results that return JSONL streams:

```python { .api }
from typing import Generic, TypeVar, Iterator, AsyncIterator

T = TypeVar('T')

class JSONLDecoder(Generic[T]):
    """
    Synchronous JSONL stream decoder.

    Decodes newline-delimited JSON objects from streaming responses,
    commonly used for batch result streaming.

    Yields:
        Decoded objects of type T, one per JSONL line
    """

    def __iter__(self) -> Iterator[T]:
        """Iterate over decoded JSONL objects."""
        ...

class AsyncJSONLDecoder(Generic[T]):
    """
    Asynchronous JSONL stream decoder.

    Async version for decoding JSONL streams.

    Yields:
        Decoded objects of type T, one per JSONL line
    """

    def __aiter__(self) -> AsyncIterator[T]:
        """Async iterate over decoded JSONL objects."""
        ...
```

### JSONL Decoder Usage

```python
# Stream batch results (returns JSONL decoder)
results = client.messages.batches.results("batch_abc123")

# Iterate over individual results
for result in results:
    if result.result.type == "succeeded":
        print(f"Message: {result.result.message.content[0].text}")
    elif result.result.type == "errored":
        print(f"Error: {result.result.error.message}")
```

### Async JSONL Decoding

```python
import asyncio

async def process_batch_results():
    client = AsyncAnthropic()

    # Get async JSONL decoder
    results = await client.messages.batches.results("batch_abc123")

    # Async iterate
    async for result in results:
        print(f"Custom ID: {result.custom_id}")
        # Process result

asyncio.run(process_batch_results())
```

## See Also

- [Messages API](../api/messages.md) - Message pagination
- [Batches API](../api/batches.md) - Batch pagination and JSONL results
- [Models API](../api/models.md) - Model pagination
- [Type System](./types.md) - Pagination type definitions
