# Vector Stores

Vector database operations for retrieval-augmented generation (RAG) applications with file management and batch processing.

## Capabilities

### Vector Store Management

```python { .api }
class VectorStores:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
    files: VectorFiles
    file_batches: VectorFileBatches

class VectorFiles:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def delete(self, **kwargs): ...

class VectorFileBatches:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def cancel(self, **kwargs): ...
```

## Usage Examples

```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Create vector store
vector_store = portkey.beta.vector_stores.create(
    name="Knowledge Base"
)

# Add files to vector store
portkey.beta.vector_stores.files.create(
    vector_store_id=vector_store.id,
    file_id="file-123"
)

# Create file batch
batch = portkey.beta.vector_stores.file_batches.create(
    vector_store_id=vector_store.id,
    file_ids=["file-123", "file-456"]
)
```