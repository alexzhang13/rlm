# Fine-Tuning

Model fine-tuning capabilities with job management, checkpoint handling, and training monitoring.

## Capabilities

```python { .api }
class FineTuning:
    jobs: Jobs
    checkpoints: Checkpoints

class Jobs:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def cancel(self, **kwargs): ...

class Checkpoints:
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
```

## Usage Examples

```python
# Create fine-tuning job
job = portkey.fine_tuning.jobs.create(
    training_file="file-123",
    model="gpt-3.5-turbo"
)

# Monitor job
job_status = portkey.fine_tuning.jobs.retrieve(job.id)
```