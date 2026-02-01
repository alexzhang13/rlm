# Evaluations

Create and manage evaluations to test model performance with custom testing criteria and data sources. The Evals API enables systematic evaluation of different models and parameters against consistent benchmarks.

## Capabilities

### Create Evaluation

Create an evaluation structure with testing criteria and data source configuration.

```python { .api }
def create(
    self,
    *,
    data_source_config: dict,
    testing_criteria: Iterable[dict],
    metadata: dict[str, str] | None | Omit = omit,
    name: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Eval:
    """
    Create an evaluation for testing model performance.

    Args:
        data_source_config: Configuration for the data source used in eval runs.
            Dictates the schema of data used in the evaluation.
            Example: {
                "type": "file",
                "file_id": "file-abc123",
                "schema": {
                    "input": {"type": "string"},
                    "expected_output": {"type": "string"}
                }
            }

        testing_criteria: List of graders for all eval runs. Graders can reference
            variables in the data source using double curly braces notation like
            {{item.variable_name}}. To reference model output, use {{sample.output_text}}.
            Example: [
                {
                    "type": "exact_match",
                    "expected": "{{item.expected_output}}",
                    "actual": "{{sample.output_text}}"
                },
                {
                    "type": "contains",
                    "substring": "{{item.keyword}}",
                    "text": "{{sample.output_text}}"
                }
            ]

        metadata: Up to 16 key-value pairs for storing additional information.
            Keys max 64 characters, values max 512 characters.

        name: Name of the evaluation for identification.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Eval: Created evaluation object with ID for running evaluations.

    Notes:
        - After creating an evaluation, run it on different models/parameters
        - See https://platform.openai.com/docs/guides/evals for grader types
        - Supported graders: exact_match, contains, llm_judge, custom_code
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Create evaluation with testing criteria
eval = client.evals.create(
    name="Customer Support Eval",
    data_source_config={
        "type": "file",
        "file_id": "file-abc123",
        "schema": {
            "customer_query": {"type": "string"},
            "expected_tone": {"type": "string"},
            "expected_answer": {"type": "string"}
        }
    },
    testing_criteria=[
        {
            "type": "exact_match",
            "name": "Answer Correctness",
            "expected": "{{item.expected_answer}}",
            "actual": "{{sample.output_text}}"
        },
        {
            "type": "llm_judge",
            "name": "Tone Check",
            "prompt": "Does the response match the tone: {{item.expected_tone}}?",
            "text": "{{sample.output_text}}"
        }
    ],
    metadata={
        "team": "customer-success",
        "version": "v1"
    }
)

print(f"Created evaluation: {eval.id}")
```

### Retrieve Evaluation

Get an evaluation by ID.

```python { .api }
def retrieve(
    self,
    eval_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Eval:
    """
    Retrieve an evaluation by its ID.

    Args:
        eval_id: ID of the evaluation to retrieve.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Eval: Evaluation object with full configuration and metadata.
    """
```

### Update Evaluation

Update evaluation properties like name or metadata.

```python { .api }
def update(
    self,
    eval_id: str,
    *,
    metadata: dict[str, str] | None | Omit = omit,
    name: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Eval:
    """
    Update certain properties of an evaluation.

    Args:
        eval_id: ID of the evaluation to update.

        metadata: New metadata key-value pairs. Replaces existing metadata.
            Up to 16 pairs, keys max 64 chars, values max 512 chars.

        name: New name for the evaluation.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Eval: Updated evaluation object.

    Notes:
        - Only name and metadata can be updated
        - Cannot modify data_source_config or testing_criteria after creation
    """
```

### List Evaluations

List all evaluations for the current project.

```python { .api }
def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    order_by: Literal["created_at", "updated_at"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Eval]:
    """
    List evaluations for a project.

    Args:
        after: Cursor for pagination. ID of last eval from previous request.

        limit: Number of evaluations to retrieve. Default varies by API.

        order: Sort order by timestamp.
            - "asc": Ascending (oldest first)
            - "desc": Descending (newest first, default)

        order_by: Field to order by.
            - "created_at": Creation time (default)
            - "updated_at": Last modification time

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[Eval]: Paginated list of evaluations.
            Supports iteration: for eval in client.evals.list(): ...
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# List all evaluations
for eval in client.evals.list():
    print(f"{eval.name}: {eval.id}")

# List with pagination
page = client.evals.list(limit=10)
for eval in page:
    print(eval.name)

# Get next page
if page.has_more:
    next_page = client.evals.list(
        limit=10,
        after=page.data[-1].id
    )

# List by last updated
for eval in client.evals.list(order_by="updated_at", order="desc"):
    print(f"{eval.name} - Updated: {eval.updated_at}")
```

### Delete Evaluation

Delete an evaluation.

```python { .api }
def delete(
    self,
    eval_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> EvalDeleteResponse:
    """
    Delete an evaluation.

    Args:
        eval_id: ID of the evaluation to delete.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        EvalDeleteResponse: Confirmation of deletion with ID and status.

    Notes:
        - Deletion is permanent
        - Associated eval runs are also deleted
    """
```

### Evaluation Runs

Run an evaluation against a model configuration.

```python { .api }
# Access via client.evals.runs

def create(
    self,
    eval_id: str,
    *,
    data_source: dict,
    metadata: dict[str, str] | None | Omit = omit,
    name: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RunCreateResponse:
    """
    Create a run of the evaluation with specified data source and configuration.

    Args:
        eval_id: ID of the evaluation to run.

        data_source: Details about the run's data source. Can be either:
            - File content: {"type": "file_content", "content": [...]}
            - File ID: {"type": "file_id", "file_id": "file-xxx"}
            The data source will be validated against the schema specified in the evaluation config.

        metadata: Set of 16 key-value pairs that can be attached to an object.
            Keys have a maximum length of 64 characters.
            Values have a maximum length of 512 characters.

        name: The name of the run.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        RunCreateResponse: Created run object. Use retrieve() to check status and results.
    """

def retrieve(
    self,
    eval_id: str,
    run_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> EvalRun:
    """
    Retrieve a specific evaluation run.

    Args:
        eval_id: ID of the evaluation.
        run_id: ID of the run.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        EvalRun: Run object with status, results, and scores.
    """

def cancel(
    self,
    run_id: str,
    *,
    eval_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RunCancelResponse:
    """
    Cancel an ongoing evaluation run.

    Args:
        run_id: ID of the run to cancel.
        eval_id: ID of the evaluation.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        RunCancelResponse: Confirmation of run cancellation.
    """

def delete(
    self,
    run_id: str,
    *,
    eval_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RunDeleteResponse:
    """
    Permanently delete an evaluation run.

    Args:
        run_id: ID of the run to delete.
        eval_id: ID of the evaluation.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        RunDeleteResponse: Confirmation of run deletion.
    """

def list(
    self,
    eval_id: str,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    status: Literal["queued", "in_progress", "completed", "canceled", "failed"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[RunListResponse]:
    """
    List all runs for an evaluation.

    Args:
        eval_id: ID of the evaluation.
        after: Cursor for pagination.
        limit: Number of runs to retrieve.
        order: Sort order ("asc" or "desc").
        status: Filter by run status ("queued", "in_progress", "completed", "canceled", or "failed").

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[RunListResponse]: Paginated list of runs.
    """
```

### Evaluation Run Output Items

Inspect individual output items from an evaluation run.

```python { .api }
# Access via client.evals.runs.output_items

def retrieve(
    self,
    output_item_id: str,
    *,
    eval_id: str,
    run_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> OutputItemRetrieveResponse:
    """
    Get an evaluation run output item by ID.

    Args:
        output_item_id: ID of the output item to retrieve.

        eval_id: ID of the evaluation.

        run_id: ID of the evaluation run.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        OutputItemRetrieveResponse: Individual output item with test results
            and grader scores for a specific data point in the evaluation.
    """

def list(
    self,
    run_id: str,
    *,
    eval_id: str,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    status: Literal["fail", "pass"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[OutputItemListResponse]:
    """
    Get a list of output items for an evaluation run.

    Args:
        run_id: ID of the evaluation run.

        eval_id: ID of the evaluation.

        after: Cursor for pagination. ID of last output item from previous request.

        limit: Number of output items to retrieve.

        order: Sort order by timestamp.
            - "asc": Ascending (oldest first)
            - "desc": Descending (newest first, default)

        status: Filter output items by status.
            - "fail": Only failed output items
            - "pass": Only passed output items
            Omit to retrieve all output items.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[OutputItemListResponse]: Paginated list of output items.
            Each output item contains the model output and grader results for
            a single test case in the evaluation run.
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# List all output items for a run
for output_item in client.evals.runs.output_items.list(
    eval_id="eval-abc123",
    run_id="run-def456"
):
    print(f"Item {output_item.id}: {output_item.status}")
    if output_item.status == "fail":
        print(f"  Failed on: {output_item.grader_results}")

# Filter only failed items
failed_items = client.evals.runs.output_items.list(
    eval_id="eval-abc123",
    run_id="run-def456",
    status="fail"
)

for item in failed_items:
    print(f"Failed item: {item.id}")
    # Retrieve detailed information
    detail = client.evals.runs.output_items.retrieve(
        eval_id="eval-abc123",
        run_id="run-def456",
        output_item_id=item.id
    )
    print(f"  Model output: {detail.model_output}")
    print(f"  Expected: {detail.expected}")

# Paginate through all output items
page = client.evals.runs.output_items.list(
    eval_id="eval-abc123",
    run_id="run-def456",
    limit=10,
    order="asc"
)

for item in page:
    print(f"{item.id}: {item.status}")
```

Complete workflow example:

```python
from openai import OpenAI
import time

client = OpenAI()

# 1. Create evaluation
eval = client.evals.create(
    name="Model Comparison",
    data_source_config={
        "type": "file",
        "file_id": "file-abc123"
    },
    testing_criteria=[
        {
            "type": "exact_match",
            "expected": "{{item.expected}}",
            "actual": "{{sample.output_text}}"
        }
    ]
)

# 2. Run evaluation with different models
run_gpt4 = client.evals.runs.create(
    eval_id=eval.id,
    model="gpt-4",
    temperature=0.7,
    metadata={"variant": "gpt-4"}
)

run_gpt35 = client.evals.runs.create(
    eval_id=eval.id,
    model="gpt-3.5-turbo",
    temperature=0.7,
    metadata={"variant": "gpt-3.5"}
)

# 3. Wait for completion and check results
def wait_for_run(eval_id: str, run_id: str):
    while True:
        run = client.evals.runs.retrieve(eval_id=eval_id, run_id=run_id)
        if run.status in ["completed", "failed", "cancelled"]:
            return run
        time.sleep(2)

gpt4_results = wait_for_run(eval.id, run_gpt4.id)
gpt35_results = wait_for_run(eval.id, run_gpt35.id)

print(f"GPT-4 Score: {gpt4_results.score}")
print(f"GPT-3.5 Score: {gpt35_results.score}")

# 4. Compare results
for run in client.evals.runs.list(eval_id=eval.id):
    print(f"{run.model}: {run.score} ({run.status})")

# 5. Update evaluation name
client.evals.update(
    eval_id=eval.id,
    name="Model Comparison - Updated",
    metadata={"status": "active"}
)

# 6. Clean up
client.evals.delete(eval_id=eval.id)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def run_eval():
    client = AsyncOpenAI()

    # Create evaluation
    eval = await client.evals.create(
        name="Async Eval",
        data_source_config={"type": "file", "file_id": "file-abc"},
        testing_criteria=[{"type": "exact_match", "expected": "{{item.expected}}", "actual": "{{sample.output_text}}"}]
    )

    # Run evaluation
    run = await client.evals.runs.create(
        eval_id=eval.id,
        model="gpt-4"
    )

    # Check results
    result = await client.evals.runs.retrieve(
        eval_id=eval.id,
        run_id=run.id
    )

    return result.score

score = asyncio.run(run_eval())
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Eval(BaseModel):
    """Evaluation object."""
    id: str
    created_at: int
    updated_at: int
    name: str | None
    object: Literal["eval"]
    data_source_config: dict
    testing_criteria: list[dict]
    metadata: dict[str, str] | None

class EvalRun(BaseModel):
    """Evaluation run object."""
    id: str
    eval_id: str
    created_at: int
    model: str
    status: Literal["queued", "in_progress", "completed", "failed", "cancelled"]
    score: float | None  # Present when status="completed"
    results: list[dict] | None  # Detailed results per test case
    metadata: dict[str, str] | None

class EvalDeleteResponse(BaseModel):
    """Response from delete operation."""
    id: str
    deleted: bool
    object: Literal["eval.deleted"]

class OutputItemRetrieveResponse(BaseModel):
    """Individual evaluation run output item."""
    id: str
    eval_id: str
    run_id: str
    status: Literal["fail", "pass"]
    model_output: str | dict  # Model's generated output
    expected: str | dict | None  # Expected output if defined
    grader_results: list[dict]  # Results from each grader
    created_at: int

class OutputItemListResponse(BaseModel):
    """Evaluation run output item in list responses."""
    id: str
    eval_id: str
    run_id: str
    status: Literal["fail", "pass"]
    created_at: int

class SyncCursorPage[T]:
    """Cursor-based pagination."""
    data: list[T]
    has_more: bool
    def __iter__(self) -> Iterator[T]: ...

class Omit:
    """Sentinel value for omitted parameters."""
```

## Access Pattern

```python
# Synchronous
from openai import OpenAI
client = OpenAI()
client.evals.create(...)
client.evals.retrieve(...)
client.evals.update(...)
client.evals.list(...)
client.evals.delete(...)
client.evals.runs.create(...)
client.evals.runs.retrieve(...)
client.evals.runs.list(...)
client.evals.runs.output_items.retrieve(...)
client.evals.runs.output_items.list(...)

# Asynchronous
from openai import AsyncOpenAI
client = AsyncOpenAI()
await client.evals.create(...)
await client.evals.retrieve(...)
await client.evals.update(...)
await client.evals.list(...)
await client.evals.delete(...)
await client.evals.runs.create(...)
await client.evals.runs.retrieve(...)
await client.evals.runs.list(...)
await client.evals.runs.output_items.retrieve(...)
await client.evals.runs.output_items.list(...)
```
