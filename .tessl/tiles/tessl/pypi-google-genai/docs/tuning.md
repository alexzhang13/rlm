# Model Fine-Tuning

Create and manage supervised fine-tuning jobs to customize models on your data (Vertex AI only). Fine-tuning allows you to adapt foundation models to your specific use case by training on your own datasets, improving model performance for domain-specific tasks.

## Capabilities

### Tune Model

Create a supervised fine-tuning job to customize a base model.

```python { .api }
class Tunings:
    """Synchronous tuning jobs API (Vertex AI only)."""

    def tune(
        self,
        *,
        base_model: str,
        training_dataset: TuningDataset,
        config: Optional[CreateTuningJobConfig] = None
    ) -> TuningJob:
        """
        Create a supervised fine-tuning job.

        Parameters:
            base_model (str): Base model to fine-tune (e.g., 'gemini-1.5-flash-002').
            training_dataset (TuningDataset): Training dataset specification including
                GCS URI or inline examples.
            config (CreateTuningJobConfig, optional): Tuning configuration including:
                - tuned_model_display_name: Display name for tuned model
                - epoch_count: Number of training epochs
                - learning_rate: Learning rate
                - adapter_size: Adapter size for efficient tuning
                - validation_dataset: Optional validation dataset

        Returns:
            TuningJob: Created tuning job with name and initial status.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncTunings:
    """Asynchronous tuning jobs API (Vertex AI only)."""

    async def tune(
        self,
        *,
        base_model: str,
        training_dataset: TuningDataset,
        config: Optional[CreateTuningJobConfig] = None
    ) -> TuningJob:
        """Async version of tune."""
        ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import (
    TuningDataset,
    CreateTuningJobConfig,
    HyperParameters,
    AdapterSize
)

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Define training dataset
training_dataset = TuningDataset(
    gcs_uri='gs://my-bucket/training_data.jsonl'
)

# Configure tuning
config = CreateTuningJobConfig(
    tuned_model_display_name='my-custom-model',
    epoch_count=5,
    learning_rate_multiplier=1.0,
    adapter_size=AdapterSize.ADAPTER_SIZE_SIXTEEN,
    validation_dataset=TuningDataset(
        gcs_uri='gs://my-bucket/validation_data.jsonl'
    )
)

# Start tuning
job = client.tunings.tune(
    base_model='gemini-1.5-flash-002',
    training_dataset=training_dataset,
    config=config
)

print(f"Tuning job created: {job.name}")
print(f"State: {job.state}")

# Poll for completion
import time
while job.state in ['JOB_STATE_PENDING', 'JOB_STATE_RUNNING']:
    time.sleep(60)
    job = client.tunings.get(name=job.name)
    print(f"State: {job.state}")

if job.state == 'JOB_STATE_SUCCEEDED':
    print(f"Tuned model: {job.tuned_model.model}")

    # Use tuned model
    response = client.models.generate_content(
        model=job.tuned_model.model,
        contents='Test the tuned model'
    )
    print(response.text)
```

### Get Tuning Job

Retrieve information about a tuning job including status and progress.

```python { .api }
class Tunings:
    """Synchronous tuning jobs API (Vertex AI only)."""

    def get(
        self,
        *,
        name: str,
        config: Optional[GetTuningJobConfig] = None
    ) -> TuningJob:
        """
        Get tuning job information.

        Parameters:
            name (str): Job name in format 'projects/*/locations/*/tuningJobs/*'.
            config (GetTuningJobConfig, optional): Get configuration.

        Returns:
            TuningJob: Job information including state, progress, and tuned model.

        Raises:
            ClientError: For client errors including 404 if job not found
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncTunings:
    """Asynchronous tuning jobs API (Vertex AI only)."""

    async def get(
        self,
        *,
        name: str,
        config: Optional[GetTuningJobConfig] = None
    ) -> TuningJob:
        """Async version of get."""
        ...
```

### Cancel Tuning Job

Cancel a running tuning job.

```python { .api }
class Tunings:
    """Synchronous tuning jobs API (Vertex AI only)."""

    def cancel(self, *, name: str) -> None:
        """
        Cancel a tuning job.

        Parameters:
            name (str): Job name in format 'projects/*/locations/*/tuningJobs/*'.

        Raises:
            ClientError: For client errors
            ServerError: For server errors
        """
        ...

class AsyncTunings:
    """Asynchronous tuning jobs API (Vertex AI only)."""

    async def cancel(self, *, name: str) -> None:
        """Async version of cancel."""
        ...
```

### List Tuning Jobs

List all tuning jobs with optional filtering and pagination.

```python { .api }
class Tunings:
    """Synchronous tuning jobs API (Vertex AI only)."""

    def list(
        self,
        *,
        config: Optional[ListTuningJobsConfig] = None
    ) -> Union[Pager[TuningJob], Iterator[TuningJob]]:
        """
        List tuning jobs.

        Parameters:
            config (ListTuningJobsConfig, optional): List configuration including:
                - page_size: Number of jobs per page
                - page_token: Token for pagination
                - filter: Filter expression

        Returns:
            Union[Pager[TuningJob], Iterator[TuningJob]]: Paginated job list.

        Raises:
            ClientError: For client errors
            ServerError: For server errors
        """
        ...

class AsyncTunings:
    """Asynchronous tuning jobs API (Vertex AI only)."""

    async def list(
        self,
        *,
        config: Optional[ListTuningJobsConfig] = None
    ) -> Union[AsyncPager[TuningJob], AsyncIterator[TuningJob]]:
        """Async version of list."""
        ...
```

**Usage Example:**

```python
from google.genai import Client

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# List all tuning jobs
for job in client.tunings.list():
    print(f"{job.name}: {job.state}")
    if job.tuned_model:
        print(f"  Tuned model: {job.tuned_model.model}")
```

## Types

```python { .api }
from typing import Optional, Union, List, Iterator, AsyncIterator, Dict
from datetime import datetime
from enum import Enum

# Configuration types
class CreateTuningJobConfig:
    """
    Configuration for creating tuning jobs.

    Attributes:
        tuned_model_display_name (str, optional): Display name for the tuned model.
        epoch_count (int, optional): Number of training epochs (1-100). Default: 5.
        learning_rate_multiplier (float, optional): Learning rate multiplier (0.001-10.0).
            Default: 1.0.
        adapter_size (AdapterSize, optional): Adapter size for efficient tuning.
            Default: ADAPTER_SIZE_ONE.
        validation_dataset (TuningDataset, optional): Validation dataset.
        labels (dict[str, str], optional): Job labels.
    """
    tuned_model_display_name: Optional[str] = None
    epoch_count: Optional[int] = None
    learning_rate_multiplier: Optional[float] = None
    adapter_size: Optional[AdapterSize] = None
    validation_dataset: Optional[TuningDataset] = None
    labels: Optional[dict[str, str]] = None

class GetTuningJobConfig:
    """Configuration for getting tuning job."""
    pass

class ListTuningJobsConfig:
    """
    Configuration for listing tuning jobs.

    Attributes:
        page_size (int, optional): Number of jobs per page.
        page_token (str, optional): Token for pagination.
        filter (str, optional): Filter expression.
    """
    page_size: Optional[int] = None
    page_token: Optional[str] = None
    filter: Optional[str] = None

class TuningDataset:
    """
    Training or validation dataset specification.

    Attributes:
        gcs_uri (str, optional): GCS URI to JSONL file (e.g., 'gs://bucket/data.jsonl').
            Each line should be a JSON object with 'contents' field.
    """
    gcs_uri: Optional[str] = None

# Response types
class TuningJob:
    """
    Tuning job information.

    Attributes:
        name (str): Job resource name.
        base_model (str): Base model being tuned.
        tuned_model (TunedModel, optional): Information about the tuned model.
        state (JobState): Current job state.
        create_time (datetime): When job was created.
        start_time (datetime, optional): When job started.
        end_time (datetime, optional): When job completed.
        update_time (datetime): Last update time.
        labels (dict[str, str], optional): Job labels.
        tuning_data_stats (TuningDataStats, optional): Training data statistics.
        error (JobError, optional): Error if job failed.
    """
    name: str
    base_model: str
    tuned_model: Optional[TunedModel] = None
    state: JobState
    create_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    update_time: datetime
    labels: Optional[dict[str, str]] = None
    tuning_data_stats: Optional[TuningDataStats] = None
    error: Optional[JobError] = None

class TunedModel:
    """
    Information about tuned model.

    Attributes:
        model (str): Model resource name for use in generation requests.
        endpoint (str, optional): Endpoint for the tuned model.
        display_name (str, optional): Display name.
    """
    model: str
    endpoint: Optional[str] = None
    display_name: Optional[str] = None

class TuningDataStats:
    """
    Statistics about tuning data.

    Attributes:
        training_dataset_size (int, optional): Number of training examples.
        validation_dataset_size (int, optional): Number of validation examples.
        total_tuning_character_count (int, optional): Total characters in training data.
        total_billable_character_count (int, optional): Billable characters.
    """
    training_dataset_size: Optional[int] = None
    validation_dataset_size: Optional[int] = None
    total_tuning_character_count: Optional[int] = None
    total_billable_character_count: Optional[int] = None

class JobState(Enum):
    """Tuning job states."""
    JOB_STATE_UNSPECIFIED = 'JOB_STATE_UNSPECIFIED'
    JOB_STATE_QUEUED = 'JOB_STATE_QUEUED'
    JOB_STATE_PENDING = 'JOB_STATE_PENDING'
    JOB_STATE_RUNNING = 'JOB_STATE_RUNNING'
    JOB_STATE_SUCCEEDED = 'JOB_STATE_SUCCEEDED'
    JOB_STATE_FAILED = 'JOB_STATE_FAILED'
    JOB_STATE_CANCELLING = 'JOB_STATE_CANCELLING'
    JOB_STATE_CANCELLED = 'JOB_STATE_CANCELLED'
    JOB_STATE_PAUSED = 'JOB_STATE_PAUSED'

class AdapterSize(Enum):
    """Adapter sizes for efficient tuning."""
    ADAPTER_SIZE_UNSPECIFIED = 'ADAPTER_SIZE_UNSPECIFIED'
    ADAPTER_SIZE_ONE = 'ADAPTER_SIZE_ONE'
    ADAPTER_SIZE_FOUR = 'ADAPTER_SIZE_FOUR'
    ADAPTER_SIZE_EIGHT = 'ADAPTER_SIZE_EIGHT'
    ADAPTER_SIZE_SIXTEEN = 'ADAPTER_SIZE_SIXTEEN'
    ADAPTER_SIZE_THIRTY_TWO = 'ADAPTER_SIZE_THIRTY_TWO'

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
