# Batch Processing

Submit batch prediction jobs for high-volume inference with cost savings. Batch processing allows you to process large numbers of requests asynchronously at reduced costs compared to online inference, ideal for processing datasets, bulk content generation, and embeddings.

## Capabilities

### Create Batch Job

Create a batch prediction job for content generation. Processes requests from Cloud Storage or BigQuery and writes results back.

```python { .api }
class Batches:
    """Synchronous batch prediction jobs API."""

    def create(
        self,
        *,
        model: str,
        src: Union[str, list[dict]],
        dest: Optional[str] = None,
        config: Optional[CreateBatchJobConfig] = None
    ) -> BatchJob:
        """
        Create batch prediction job for content generation.

        Parameters:
            model (str): Model identifier (e.g., 'gemini-2.0-flash').
            src (Union[str, list[dict]]): Source of requests. Can be:
                - str: GCS URI ('gs://bucket/input.jsonl') or BigQuery table
                  ('bq://project.dataset.table')
                - list[dict]: List of request dictionaries for inline requests
            dest (str, optional): Destination for results. GCS URI ('gs://bucket/output')
                or BigQuery table ('bq://project.dataset.table'). Required for GCS/BigQuery
                sources, optional for inline requests.
            config (CreateBatchJobConfig, optional): Job configuration.

        Returns:
            BatchJob: Created batch job with name and status.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncBatches:
    """Asynchronous batch prediction jobs API."""

    async def create(
        self,
        *,
        model: str,
        src: Union[str, list[dict]],
        dest: Optional[str] = None,
        config: Optional[CreateBatchJobConfig] = None
    ) -> BatchJob:
        """Async version of create."""
        ...
```

**Usage Example - GCS:**

```python
from google.genai import Client

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Create batch job from GCS
job = client.batches.create(
    model='gemini-2.0-flash',
    src='gs://my-bucket/requests.jsonl',
    dest='gs://my-bucket/results/'
)

print(f"Job created: {job.name}")
print(f"State: {job.state}")

# Poll for completion
import time
while job.state in ['JOB_STATE_PENDING', 'JOB_STATE_RUNNING']:
    time.sleep(60)
    job = client.batches.get(name=job.name)
    print(f"State: {job.state}")

print(f"Final state: {job.state}")
if job.state == 'JOB_STATE_SUCCEEDED':
    print(f"Processed: {job.metadata.completed_requests} requests")
```

**Usage Example - Inline Requests:**

```python
from google.genai import Client

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Create batch job with inline requests
requests = [
    {'contents': 'What is AI?'},
    {'contents': 'Explain machine learning'},
    {'contents': 'What is deep learning?'}
]

job = client.batches.create(
    model='gemini-2.0-flash',
    src=requests,
    dest='gs://my-bucket/inline-results/'
)

print(f"Job: {job.name}")
```

### Create Embeddings Batch Job

Create a batch job specifically for embedding generation, optimized for generating embeddings for large datasets.

```python { .api }
class Batches:
    """Synchronous batch prediction jobs API."""

    def create_embeddings(
        self,
        *,
        model: str,
        src: Union[str, list[dict]],
        dest: Optional[str] = None,
        config: Optional[CreateBatchJobConfig] = None
    ) -> BatchJob:
        """
        Create batch embeddings job.

        Parameters:
            model (str): Embedding model (e.g., 'text-embedding-004').
            src (Union[str, list[dict]]): Source of embedding requests.
            dest (str, optional): Destination for embeddings.
            config (CreateBatchJobConfig, optional): Job configuration.

        Returns:
            BatchJob: Created batch embeddings job.
        """
        ...

class AsyncBatches:
    """Asynchronous batch prediction jobs API."""

    async def create_embeddings(
        self,
        *,
        model: str,
        src: Union[str, list[dict]],
        dest: Optional[str] = None,
        config: Optional[CreateBatchJobConfig] = None
    ) -> BatchJob:
        """Async version of create_embeddings."""
        ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

job = client.batches.create_embeddings(
    model='text-embedding-004',
    src='gs://my-bucket/texts.jsonl',
    dest='gs://my-bucket/embeddings/'
)

print(f"Embeddings job: {job.name}")
```

### Get Batch Job

Retrieve information about a batch job including status and progress.

```python { .api }
class Batches:
    """Synchronous batch prediction jobs API."""

    def get(self, *, name: str) -> BatchJob:
        """
        Get batch job status and information.

        Parameters:
            name (str): Job name in format 'projects/*/locations/*/batchPredictionJobs/*'.

        Returns:
            BatchJob: Job information including state, progress, and metadata.
        """
        ...

class AsyncBatches:
    """Asynchronous batch prediction jobs API."""

    async def get(self, *, name: str) -> BatchJob:
        """Async version of get."""
        ...
```

### Cancel Batch Job

Cancel a running batch job.

```python { .api }
class Batches:
    """Synchronous batch prediction jobs API."""

    def cancel(self, *, name: str) -> None:
        """
        Cancel a batch job.

        Parameters:
            name (str): Job name.
        """
        ...

class AsyncBatches:
    """Asynchronous batch prediction jobs API."""

    async def cancel(self, *, name: str) -> None:
        """Async version of cancel."""
        ...
```

### Delete Batch Job

Delete a batch job.

```python { .api }
class Batches:
    """Synchronous batch prediction jobs API."""

    def delete(self, *, name: str) -> None:
        """
        Delete a batch job.

        Parameters:
            name (str): Job name.
        """
        ...

class AsyncBatches:
    """Asynchronous batch prediction jobs API."""

    async def delete(self, *, name: str) -> None:
        """Async version of delete."""
        ...
```

### List Batch Jobs

List all batch jobs with optional filtering and pagination.

```python { .api }
class Batches:
    """Synchronous batch prediction jobs API."""

    def list(
        self,
        *,
        config: Optional[ListBatchJobsConfig] = None
    ) -> Union[Pager[BatchJob], Iterator[BatchJob]]:
        """
        List batch jobs.

        Parameters:
            config (ListBatchJobsConfig, optional): List configuration including:
                - page_size: Number of jobs per page
                - page_token: Token for pagination
                - filter: Filter expression

        Returns:
            Union[Pager[BatchJob], Iterator[BatchJob]]: Paginated job list.
        """
        ...

class AsyncBatches:
    """Asynchronous batch prediction jobs API."""

    async def list(
        self,
        *,
        config: Optional[ListBatchJobsConfig] = None
    ) -> Union[AsyncPager[BatchJob], AsyncIterator[BatchJob]]:
        """Async version of list."""
        ...
```

## Types

```python { .api }
from typing import Optional, Union, List, Iterator, AsyncIterator, Dict, Any
from datetime import datetime
from enum import Enum

# Configuration types
class CreateBatchJobConfig:
    """
    Configuration for creating batch jobs.

    Attributes:
        display_name (str, optional): Display name for the job.
        labels (dict[str, str], optional): Labels for the job.
    """
    display_name: Optional[str] = None
    labels: Optional[dict[str, str]] = None

class ListBatchJobsConfig:
    """
    Configuration for listing batch jobs.

    Attributes:
        page_size (int, optional): Number of jobs per page.
        page_token (str, optional): Token for pagination.
        filter (str, optional): Filter expression (e.g., 'state=JOB_STATE_RUNNING').
    """
    page_size: Optional[int] = None
    page_token: Optional[str] = None
    filter: Optional[str] = None

# Response types
class BatchJob:
    """
    Batch prediction job information.

    Attributes:
        name (str): Job resource name.
        display_name (str, optional): Display name.
        model (str): Model used for the job.
        state (JobState): Current job state.
        create_time (datetime): When job was created.
        start_time (datetime, optional): When job started running.
        end_time (datetime, optional): When job completed.
        update_time (datetime): Last update time.
        labels (dict[str, str], optional): Job labels.
        metadata (BatchJobMetadata, optional): Job metadata and progress.
        error (JobError, optional): Error if job failed.
    """
    name: str
    display_name: Optional[str] = None
    model: str
    state: JobState
    create_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    update_time: datetime
    labels: Optional[dict[str, str]] = None
    metadata: Optional[BatchJobMetadata] = None
    error: Optional[JobError] = None

class BatchJobMetadata:
    """
    Batch job metadata and progress.

    Attributes:
        total_requests (int, optional): Total number of requests.
        completed_requests (int, optional): Number of completed requests.
        failed_requests (int, optional): Number of failed requests.
        input_config (dict, optional): Input configuration.
        output_config (dict, optional): Output configuration.
    """
    total_requests: Optional[int] = None
    completed_requests: Optional[int] = None
    failed_requests: Optional[int] = None
    input_config: Optional[dict] = None
    output_config: Optional[dict] = None

class JobState(Enum):
    """Batch job states."""
    JOB_STATE_UNSPECIFIED = 'JOB_STATE_UNSPECIFIED'
    JOB_STATE_QUEUED = 'JOB_STATE_QUEUED'
    JOB_STATE_PENDING = 'JOB_STATE_PENDING'
    JOB_STATE_RUNNING = 'JOB_STATE_RUNNING'
    JOB_STATE_SUCCEEDED = 'JOB_STATE_SUCCEEDED'
    JOB_STATE_FAILED = 'JOB_STATE_FAILED'
    JOB_STATE_CANCELLING = 'JOB_STATE_CANCELLING'
    JOB_STATE_CANCELLED = 'JOB_STATE_CANCELLED'
    JOB_STATE_PAUSED = 'JOB_STATE_PAUSED'
    JOB_STATE_EXPIRED = 'JOB_STATE_EXPIRED'

class JobError:
    """
    Job error information.

    Attributes:
        code (int): Error code.
        message (str): Error message.
        details (list[dict], optional): Error details.
    """
    code: int
    message: str
    details: Optional[list[dict]] = None

# Pager types
class Pager[T]:
    """Synchronous pager."""
    page: list[T]
    def next_page(self) -> None: ...
    def __iter__(self) -> Iterator[T]: ...

class AsyncPager[T]:
    """Asynchronous pager."""
    page: list[T]
    async def next_page(self) -> None: ...
    async def __aiter__(self) -> AsyncIterator[T]: ...
```
