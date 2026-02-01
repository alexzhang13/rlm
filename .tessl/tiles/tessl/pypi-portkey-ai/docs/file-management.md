# File Management

File upload, management, and processing capabilities including support for assistants, fine-tuning, and batch operations.

## Capabilities

### File Operations

```python { .api }
class MainFiles:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def delete(self, **kwargs): ...

class Uploads:
    def create(self, **kwargs): ...
    parts: Parts

class Parts:
    def create(self, **kwargs): ...
```

## Usage Examples

```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Upload file
file_response = portkey.files.create(
    file=open("document.pdf", "rb"),
    purpose="assistants"
)

# List files
files = portkey.files.list()

# Delete file
portkey.files.delete(file_response.id)
```