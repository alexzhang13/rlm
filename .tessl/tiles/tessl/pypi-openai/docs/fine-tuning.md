# Fine-tuning

Create and manage fine-tuning jobs to customize models on your own data. Fine-tune base models to improve performance on specific tasks, add domain knowledge, or adjust model behavior.

## Capabilities

### Create Fine-tuning Job

Start a fine-tuning job to train a custom model.

```python { .api }
def create(
    self,
    *,
    model: str,
    training_file: str,
    hyperparameters: dict | Omit = omit,
    method: dict | Omit = omit,
    integrations: list[dict] | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    seed: int | Omit = omit,
    suffix: str | Omit = omit,
    validation_file: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FineTuningJob:
    """
    Create a fine-tuning job to train a custom model.

    Args:
        model: Base model to fine-tune. Supported models:
            - "gpt-4o-2024-08-06"
            - "gpt-4o-mini-2024-07-18"
            - "gpt-3.5-turbo"
            - "babbage-002", "davinci-002"

        training_file: ID of uploaded training file (JSONL format).
            Each line: {"messages": [...], "response": ...}

        hyperparameters: Training hyperparameters. Options:
            - n_epochs: Number of training epochs (auto or 1-50)
            - batch_size: Batch size (auto or specific value)
            - learning_rate_multiplier: Learning rate multiplier (auto or 0.02-2)

        method: Fine-tuning method configuration. Options:
            - {"type": "supervised"}: Standard supervised fine-tuning
            - {"type": "dpo"}: Direct Preference Optimization
            - {"type": "reinforcement"}: Reinforcement learning

        integrations: External tool integrations. Options:
            - Weights & Biases: [{"type": "wandb", "wandb": {"project": "..."}}]

        metadata: Key-value pairs for storing additional information (max 16 pairs).
            Keys max 64 chars, values max 512 chars.

        seed: Random seed for reproducibility.

        suffix: Custom suffix for fine-tuned model name (max 18 chars).
            Final model name: ft:{base_model}:{suffix}:{job_id}

        validation_file: ID of validation file for evaluation during training.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FineTuningJob: Created job with status "created" or "validating_files".

    Raises:
        BadRequestError: Invalid parameters or file format
        NotFoundError: Training file not found
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Upload training data first
with open("training_data.jsonl", "rb") as f:
    training_file = client.files.create(file=f, purpose="fine-tune")

# Create fine-tuning job
job = client.fine_tuning.jobs.create(
    model="gpt-3.5-turbo",
    training_file=training_file.id
)

print(f"Job ID: {job.id}")
print(f"Status: {job.status}")

# With hyperparameters
job = client.fine_tuning.jobs.create(
    model="gpt-3.5-turbo",
    training_file=training_file.id,
    hyperparameters={
        "n_epochs": 3,
        "batch_size": 4,
        "learning_rate_multiplier": 0.1
    }
)

# With validation file
with open("validation_data.jsonl", "rb") as f:
    validation_file = client.files.create(file=f, purpose="fine-tune")

job = client.fine_tuning.jobs.create(
    model="gpt-3.5-turbo",
    training_file=training_file.id,
    validation_file=validation_file.id,
    suffix="my-custom-model"
)

# With Weights & Biases integration
job = client.fine_tuning.jobs.create(
    model="gpt-3.5-turbo",
    training_file=training_file.id,
    integrations=[{
        "type": "wandb",
        "wandb": {
            "project": "my-fine-tuning",
            "name": "experiment-1"
        }
    }]
)

# Using DPO method
job = client.fine_tuning.jobs.create(
    model="gpt-3.5-turbo",
    training_file=training_file.id,
    method={"type": "dpo"}
)
```

### Retrieve Fine-tuning Job

Get status and details of a fine-tuning job.

```python { .api }
def retrieve(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FineTuningJob:
    """
    Retrieve fine-tuning job details.

    Args:
        fine_tuning_job_id: The ID of the fine-tuning job.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FineTuningJob: Job details including current status.

    Raises:
        NotFoundError: Job not found
    """
```

Usage example:

```python
# Check job status
job = client.fine_tuning.jobs.retrieve("ftjob-abc123")

print(f"Status: {job.status}")
print(f"Model: {job.fine_tuned_model}")
print(f"Trained tokens: {job.trained_tokens}")

if job.status == "succeeded":
    print(f"Fine-tuned model ready: {job.fine_tuned_model}")
elif job.status == "failed":
    print(f"Error: {job.error}")
```

### List Fine-tuning Jobs

List fine-tuning jobs with optional filtering and pagination.

```python { .api }
def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[FineTuningJob]:
    """
    List fine-tuning jobs with pagination.

    Args:
        after: Cursor for pagination. Return jobs after this job ID.
        limit: Number of jobs to retrieve (max 100). Default 20.
        metadata: Optional metadata filter. To filter, use the syntax `metadata[k]=v`.
            Alternatively, set `metadata=null` to indicate no metadata.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[FineTuningJob]: Paginated list of jobs.
    """
```

Usage example:

```python
# List all jobs
jobs = client.fine_tuning.jobs.list()

for job in jobs:
    print(f"{job.id}: {job.status}")

# Pagination
page1 = client.fine_tuning.jobs.list(limit=10)
page2 = client.fine_tuning.jobs.list(limit=10, after=page1.data[-1].id)

# Filter by status
succeeded_jobs = [
    job for job in client.fine_tuning.jobs.list()
    if job.status == "succeeded"
]
```

### Cancel Fine-tuning Job

Cancel an in-progress fine-tuning job.

```python { .api }
def cancel(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FineTuningJob:
    """
    Cancel a running fine-tuning job.

    Args:
        fine_tuning_job_id: The ID of the job to cancel.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FineTuningJob: Job with status "cancelled".

    Raises:
        NotFoundError: Job not found
        BadRequestError: Job not in cancellable state
    """
```

Usage example:

```python
# Cancel job
job = client.fine_tuning.jobs.cancel("ftjob-abc123")

print(f"Status: {job.status}")  # "cancelled"
```

### Pause Fine-tuning Job

Temporarily pause a running fine-tuning job to save costs.

```python { .api }
def pause(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FineTuningJob:
    """
    Pause a running fine-tuning job.

    Args:
        fine_tuning_job_id: The ID of the job to pause.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FineTuningJob: Job with status "paused".

    Raises:
        NotFoundError: Job not found
        BadRequestError: Job not in pauseable state
    """
```

### Resume Fine-tuning Job

Resume a previously paused fine-tuning job.

```python { .api }
def resume(
    self,
    fine_tuning_job_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> FineTuningJob:
    """
    Resume a paused fine-tuning job.

    Args:
        fine_tuning_job_id: The ID of the job to resume.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        FineTuningJob: Job with status "running".

    Raises:
        NotFoundError: Job not found
        BadRequestError: Job not in resumeable state
    """
```

Usage example:

```python
# Pause job to save costs
job = client.fine_tuning.jobs.pause("ftjob-abc123")
print(f"Status: {job.status}")  # "paused"

# Resume later
job = client.fine_tuning.jobs.resume("ftjob-abc123")
print(f"Status: {job.status}")  # "running"
```

### List Job Events

Stream events and training metrics from a fine-tuning job.

```python { .api }
def list_events(
    self,
    fine_tuning_job_id: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[FineTuningJobEvent]:
    """
    List events for a fine-tuning job (training logs, metrics).

    Args:
        fine_tuning_job_id: The job ID.
        after: Return events after this event ID.
        limit: Number of events to retrieve (max 100). Default 20.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[FineTuningJobEvent]: Job events and logs.
    """
```

Usage example:

```python
# Get training events
events = client.fine_tuning.jobs.list_events("ftjob-abc123")

for event in events:
    print(f"[{event.created_at}] {event.message}")
    if event.data:
        print(f"  Metrics: {event.data}")

# Monitor training progress
import time

job_id = "ftjob-abc123"
while True:
    job = client.fine_tuning.jobs.retrieve(job_id)

    if job.status in ["succeeded", "failed", "cancelled"]:
        break

    events = client.fine_tuning.jobs.list_events(job_id, limit=5)
    for event in events:
        print(event.message)

    time.sleep(10)
```

### List Checkpoints

List checkpoints saved during fine-tuning.

```python { .api }
def list(
    self,
    fine_tuning_job_id: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[FineTuningJobCheckpoint]:
    """
    List checkpoints for a fine-tuning job.

    Args:
        fine_tuning_job_id: The job ID.
        after: Return checkpoints after this checkpoint ID.
        limit: Number of checkpoints to retrieve. Default 10.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[FineTuningJobCheckpoint]: Job checkpoints.
    """
```

Usage example:

```python
# List checkpoints
checkpoints = client.fine_tuning.jobs.checkpoints.list("ftjob-abc123")

for checkpoint in checkpoints:
    print(f"Step {checkpoint.step_number}: {checkpoint.metrics}")
    print(f"  Model: {checkpoint.fine_tuned_model_checkpoint}")
```

### Checkpoint Permissions

Manage access permissions for fine-tuning checkpoints to enable sharing.

```python { .api }
# Accessed via: client.fine_tuning.checkpoints.permissions
def create(
    self,
    fine_tuned_model_checkpoint: str,
    *,
    project_ids: list[str],
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncPage[PermissionCreateResponse]:
    """
    Grant access permission to a checkpoint.

    NOTE: Calling this endpoint requires an admin API key.
    This enables organization owners to share fine-tuned models with other projects
    in their organization.

    Args:
        fine_tuned_model_checkpoint: The checkpoint model ID (e.g., "ftckpt-xyz789").
        project_ids: The project identifiers to grant access to (list of strings).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncPage[PermissionCreateResponse]: Paginated list of created permissions.
    """

def retrieve(
    self,
    fine_tuned_model_checkpoint: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["ascending", "descending"] | Omit = omit,
    project_id: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> PermissionRetrieveResponse:
    """
    List all permissions for a checkpoint.

    NOTE: This endpoint requires an admin API key.
    Organization owners can use this endpoint to view all permissions for a
    fine-tuned model checkpoint.

    Args:
        fine_tuned_model_checkpoint: The checkpoint model ID.
        after: Identifier for the last permission ID from the previous pagination request.
        limit: Number of permissions to retrieve.
        order: The order in which to retrieve permissions ("ascending" or "descending").
        project_id: The ID of the project to get permissions for (filter).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        PermissionRetrieveResponse: Permissions list response.
    """

def delete(
    self,
    permission_id: str,
    *,
    fine_tuned_model_checkpoint: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> PermissionDeleteResponse:
    """
    Revoke a checkpoint permission.

    NOTE: This endpoint requires an admin API key.
    Organization owners can use this endpoint to delete a permission for a
    fine-tuned model checkpoint.

    Args:
        permission_id: The ID of the permission to delete (positional parameter).
        fine_tuned_model_checkpoint: The checkpoint model ID (keyword-only parameter).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        PermissionDeleteResponse: Deletion confirmation.
    """
```

Usage example:

```python
# Grant checkpoint access to other projects
permissions = client.fine_tuning.checkpoints.permissions.create(
    fine_tuned_model_checkpoint="ftckpt-xyz789",
    project_ids=["proj-456", "proj-789"]
)

print(f"Created {len(permissions.data)} permissions")
for perm in permissions:
    print(f"  Permission ID: {perm.id}")

# Retrieve all permissions for a checkpoint
all_perms = client.fine_tuning.checkpoints.permissions.retrieve(
    fine_tuned_model_checkpoint="ftckpt-xyz789"
)

print(f"Total permissions: {len(all_perms.data)}")
for perm in all_perms.data:
    print(f"  {perm.id}: Project {perm.project_id}")

# Filter permissions by project
project_perms = client.fine_tuning.checkpoints.permissions.retrieve(
    fine_tuned_model_checkpoint="ftckpt-xyz789",
    project_id="proj-456"
)

# Revoke a permission
deleted = client.fine_tuning.checkpoints.permissions.delete(
    permission_id="perm-abc123",
    fine_tuned_model_checkpoint="ftckpt-xyz789"
)

print(f"Deleted: {deleted.deleted}")  # True
```

### Alpha Graders

Run graders to evaluate fine-tuning results (alpha feature).

```python { .api }
# Accessed via: client.fine_tuning.alpha.graders
def run(
    self,
    *,
    grader: dict,
    model_sample: str,
    item: object | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> GraderRunResponse:
    """
    Run a grader on a model sample.

    Args:
        grader: The grader used for the fine-tuning job (structured Grader object).
        model_sample: The model sample to be evaluated. This value will be used to
            populate the `sample` namespace. See the guide for more details.
            The `output_json` variable will be populated if the model sample is
            a valid JSON string.
        item: The dataset item provided to the grader. This will be used to
            populate the `item` namespace. See the guide for more details.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        GraderRunResponse: Grading results with scores and analysis.
    """

def validate(
    self,
    *,
    grader: dict,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> GraderValidateResponse:
    """
    Validate a grader configuration before running.

    Args:
        grader: Grader configuration to validate (structured Grader object).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ValidationResult: Validation status and any errors.
    """
```

Usage example:

```python
# Validate grader configuration
validation = client.fine_tuning.alpha.graders.validate(
    grader_config={
        "type": "model_grader",
        "criteria": "accuracy",
        "model": "gpt-4"
    }
)

if validation.valid:
    # Run grader on evaluation data
    result = client.fine_tuning.alpha.graders.run(
        grader_config={
            "type": "model_grader",
            "criteria": "accuracy"
        },
        evaluation_data=[
            {
                "input": "What is 2+2?",
                "expected": "4",
                "actual": "4"
            }
        ],
        model="ft:gpt-3.5-turbo:my-org:custom_suffix:id"
    )

    print(f"Score: {result.score}")
    print(f"Analysis: {result.analysis}")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class FineTuningJob(BaseModel):
    """Fine-tuning job."""
    id: str
    created_at: int
    error: dict | None
    fine_tuned_model: str | None
    finished_at: int | None
    hyperparameters: dict
    model: str
    object: Literal["fine_tuning.job"]
    organization_id: str
    result_files: list[str]
    seed: int
    status: Literal[
        "validating_files", "queued", "running",
        "succeeded", "failed", "cancelled"
    ]
    trained_tokens: int | None
    training_file: str
    validation_file: str | None
    integrations: list[dict] | None
    user_provided_suffix: str | None

class FineTuningJobEvent(BaseModel):
    """Job event/log entry."""
    id: str
    created_at: int
    level: Literal["info", "warn", "error"]
    message: str
    object: Literal["fine_tuning.job.event"]
    data: dict | None
    type: str

class FineTuningJobCheckpoint(BaseModel):
    """Training checkpoint."""
    id: str
    created_at: int
    fine_tuned_model_checkpoint: str
    fine_tuning_job_id: str
    metrics: dict
    object: Literal["fine_tuning.job.checkpoint"]
    step_number: int

# Pagination
class SyncCursorPage[T](BaseModel):
    data: list[T]
    object: str
    has_more: bool
    def __iter__(self) -> Iterator[T]: ...
```

## Training Data Format

Training data must be JSONL (JSON Lines) format:

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is 2+2?"}, {"role": "assistant", "content": "4"}]}
{"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is the capital of France?"}, {"role": "assistant", "content": "Paris"}]}
```

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Validate training data before upload
def validate_jsonl(file_path: str) -> bool:
    import json

    with open(file_path) as f:
        for i, line in enumerate(f):
            try:
                data = json.loads(line)
                assert "messages" in data
            except Exception as e:
                print(f"Line {i}: {e}")
                return False
    return True

# 2. Monitor job progress
def wait_for_job(job_id: str):
    import time

    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)

        if job.status == "succeeded":
            return job.fine_tuned_model
        elif job.status in ["failed", "cancelled"]:
            raise Exception(f"Job {job.status}: {job.error}")

        print(f"Status: {job.status}")
        time.sleep(30)

# 3. Use validation file for monitoring
with open("train.jsonl", "rb") as train_f, \
     open("val.jsonl", "rb") as val_f:

    train_file = client.files.create(file=train_f, purpose="fine-tune")
    val_file = client.files.create(file=val_f, purpose="fine-tune")

    job = client.fine_tuning.jobs.create(
        model="gpt-3.5-turbo",
        training_file=train_file.id,
        validation_file=val_file.id
    )

# 4. Clean up after completion
fine_tuned_model = wait_for_job(job.id)

# Use the model
response = client.chat.completions.create(
    model=fine_tuned_model,
    messages=[{"role": "user", "content": "Test"}]
)

# Later, delete if no longer needed
client.models.delete(fine_tuned_model)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_fine_tune():
    client = AsyncOpenAI()

    job = await client.fine_tuning.jobs.create(
        model="gpt-3.5-turbo",
        training_file="file-abc123"
    )

    return job.id

job_id = asyncio.run(create_fine_tune())
```
