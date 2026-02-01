# Provider & Integration Management

Management of AI providers and third-party integrations with workspace-level and model-level configuration.

## Capabilities

```python { .api }
class Providers:
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...

class Integrations:
    workspaces: IntegrationsWorkspaces
    models: IntegrationsModels

class IntegrationsWorkspaces:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...

class IntegrationsModels:
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
```