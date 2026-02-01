# Evaluation & Testing

AI evaluation framework with automated grading, test execution, and performance measurement capabilities.

## Capabilities

```python { .api }
class Evals:
    runs: EvalsRuns

class EvalsRuns:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...

class Alpha:
    graders: Graders

class Graders:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
```