# Configuration Management

Advanced configuration system for managing provider settings, routing rules, fallback strategies, and load balancing configurations.

## Capabilities

```python { .api }
class Configs:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
```

## Usage Examples

```python
# Create configuration
config = portkey.configs.create({
    "strategy": {"mode": "fallback"},
    "targets": [
        {"provider": "openai", "api_key": "key1"},
        {"provider": "anthropic", "api_key": "key2"}
    ]
})
```