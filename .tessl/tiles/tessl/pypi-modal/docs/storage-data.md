# Storage & Data

Modal provides comprehensive storage solutions for persisting data across function calls, including volumes, network file systems, key-value stores, queues, and cloud bucket mounts. These storage primitives enable building stateful applications while maintaining the benefits of serverless architecture.

## Capabilities

### Volume - Persistent Networked File System

Persistent networked file system storage that provides POSIX-like file operations and can be mounted to multiple functions simultaneously.

```python { .api }
class Volume:
    @classmethod
    def from_name(cls, label: str, *, environment_name: Optional[str] = None) -> "Volume":
        """Load a Volume by its unique name"""
    
    @classmethod
    def persist(cls, label: str, *, environment_name: Optional[str] = None) -> "Volume":
        """Create a persistent Volume with given name"""
    
    @classmethod
    def ephemeral(cls, **kwargs) -> "Volume":
        """Create an ephemeral Volume that's deleted when not in use"""
    
    def listdir(self, path: str) -> list[FileEntry]:
        """List files and directories at path"""
    
    def iterdir(self, path: str) -> AsyncIterator[FileEntry]:
        """Async iterator over files and directories at path"""
    
    def put_file(
        self, 
        local_file: Union[str, Path, BinaryIO], 
        remote_path: str,
        *, 
        progress: Optional[bool] = None
    ) -> None:
        """Upload a local file to the volume"""
    
    def put_directory(
        self,
        local_path: Union[str, Path],
        remote_path: str,
        *,
        pattern: Optional[str] = None,
        progress: Optional[bool] = None
    ) -> None:
        """Upload a local directory to the volume"""
    
    def get_file(self, remote_path: str, local_file: Union[str, Path, BinaryIO]) -> None:
        """Download a file from the volume to local storage"""
    
    def remove_file(self, path: str, *, recursive: bool = False) -> None:
        """Remove a file or directory from the volume"""
    
    def exists(self, path: str) -> bool:
        """Check if a path exists in the volume"""
    
    def reload(self) -> None:
        """Reload the volume to get latest state"""

class FileEntry:
    """Represents a file or directory entry in a volume"""
    path: str
    type: FileEntryType  # FILE, DIRECTORY, SYMLINK, etc.
    mtime: int          # Modified time as Unix timestamp
    size: int           # Size in bytes

class FileEntryType:
    """Type of file entry"""
    FILE: int
    DIRECTORY: int
    SYMLINK: int
    FIFO: int
    SOCKET: int
```

#### Usage Examples

```python
import modal

app = modal.App()

# Create a persistent volume
volume = modal.Volume.persist("my-data-volume")

@app.function(volumes={"/data": volume})
def process_data():
    # Files are accessible at /data mount point
    with open("/data/input.txt", "r") as f:
        content = f.read()
    
    # Process data and save results
    with open("/data/output.txt", "w") as f:
        f.write(f"Processed: {content}")

# Upload files to volume from local machine
@app.local_entrypoint()
def upload_data():
    volume.put_file("local_data.txt", "/input.txt")
    volume.put_directory("./datasets", "/datasets")
    
    # List volume contents
    for entry in volume.listdir("/"):
        print(f"{entry.path}: {entry.type.name}, {entry.size} bytes")
```

### NetworkFileSystem - Shared Networked Storage

Shared networked file system that allows multiple functions to read and write files concurrently with better performance for frequent access patterns.

```python { .api }
class NetworkFileSystem:
    @classmethod
    def from_name(cls, label: str, *, environment_name: Optional[str] = None) -> "NetworkFileSystem":
        """Load a NetworkFileSystem by its unique name"""
    
    @classmethod
    def persist(cls, label: str, *, environment_name: Optional[str] = None) -> "NetworkFileSystem":
        """Create a persistent NetworkFileSystem with given name"""
    
    @classmethod
    def ephemeral(cls, **kwargs) -> "NetworkFileSystem":
        """Create an ephemeral NetworkFileSystem"""
```

#### Usage Examples

```python
import modal

app = modal.App()
nfs = modal.NetworkFileSystem.persist("shared-cache")

@app.function(network_file_systems={"/cache": nfs})
def worker_function(task_id: str):
    cache_file = f"/cache/task_{task_id}.json"
    
    # Check if cached result exists
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    
    # Process and cache result
    result = expensive_computation(task_id)
    with open(cache_file, "w") as f:
        json.dump(result, f)
    
    return result
```

### Dict - Persistent Key-Value Store

Distributed key-value store for sharing data between functions with automatic serialization and deserialization.

```python { .api }
class Dict:
    @classmethod
    def from_name(cls, label: str, *, environment_name: Optional[str] = None) -> "Dict":
        """Load a Dict by its unique name"""
    
    @classmethod
    def persist(cls, label: str, *, environment_name: Optional[str] = None) -> "Dict":
        """Create a persistent Dict with given name"""
    
    @classmethod
    def ephemeral(cls, **kwargs) -> "Dict":
        """Create an ephemeral Dict"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key, returns default if key doesn't exist"""
    
    def __getitem__(self, key: str) -> Any:
        """Get value by key using dict[key] syntax"""
    
    def put(self, key: str, value: Any) -> None:
        """Put key-value pair"""
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set value using dict[key] = value syntax"""
    
    def pop(self, key: str, default: Any = None) -> Any:
        """Remove and return value for key"""
    
    def __delitem__(self, key: str) -> None:
        """Delete key using del dict[key] syntax"""
    
    def update(self, mapping: Mapping[str, Any]) -> None:
        """Update multiple key-value pairs"""
    
    def clear(self) -> None:
        """Remove all items from the dict"""
    
    def len(self) -> int:
        """Get number of items in the dict"""
    
    def __len__(self) -> int:
        """Get number of items using len(dict) syntax"""
    
    def contains(self, key: str) -> bool:
        """Check if key exists in dict"""
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists using 'key in dict' syntax"""
    
    def keys(self) -> list[str]:
        """Get all keys as a list"""
    
    def values(self) -> list[Any]:
        """Get all values as a list"""
    
    def items(self) -> list[tuple[str, Any]]:
        """Get all key-value pairs as list of tuples"""
    
    def iterate_keys(self) -> AsyncIterator[str]:
        """Async iterator over all keys"""
    
    def iterate_values(self) -> AsyncIterator[Any]:
        """Async iterator over all values"""
    
    def iterate_items(self) -> AsyncIterator[tuple[str, Any]]:
        """Async iterator over all key-value pairs"""

class DictInfo:
    """Information about a Dict object"""
    name: Optional[str]
    created_at: datetime
    created_by: Optional[str]
```

#### Usage Examples

```python
import modal

app = modal.App()
shared_dict = modal.Dict.persist("config-store")

@app.function()
def setup_config():
    # Store configuration data
    shared_dict["database_url"] = "postgresql://..."
    shared_dict["api_keys"] = {"service_a": "key1", "service_b": "key2"}
    shared_dict["feature_flags"] = {"new_feature": True, "beta_mode": False}

@app.function()
def worker_task():
    # Access shared configuration
    db_url = shared_dict["database_url"]
    api_keys = shared_dict.get("api_keys", {})
    
    # Check feature flag
    if shared_dict.get("feature_flags", {}).get("new_feature", False):
        return use_new_algorithm()
    else:
        return use_legacy_algorithm()

@app.function()
def analytics_function():
    # Update metrics
    current_count = shared_dict.get("request_count", 0)
    shared_dict["request_count"] = current_count + 1
    
    # Store processing results
    results = shared_dict.get("daily_results", [])
    results.append({"timestamp": time.time(), "processed": 100})
    shared_dict["daily_results"] = results
```

### Queue - Distributed Task Queue

Distributed queue for asynchronous task processing with automatic serialization and FIFO ordering.

```python { .api }
class Queue:
    @classmethod
    def from_name(cls, label: str, *, environment_name: Optional[str] = None) -> "Queue":
        """Load a Queue by its unique name"""
    
    @classmethod
    def persist(cls, label: str, *, environment_name: Optional[str] = None) -> "Queue":
        """Create a persistent Queue with given name"""
    
    @classmethod
    def ephemeral(cls, **kwargs) -> "Queue":
        """Create an ephemeral Queue"""
    
    def put(self, item: Any, *, block: bool = True) -> None:
        """Put an item into the queue"""
    
    def put_many(self, items: list[Any], *, block: bool = True) -> None:
        """Put multiple items into the queue"""
    
    def get(self, *, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get an item from the queue"""
    
    def get_many(self, n: int, *, block: bool = True, timeout: Optional[float] = None) -> list[Any]:
        """Get multiple items from the queue"""
    
    def iterate(self, *, timeout: Optional[float] = None) -> AsyncIterator[Any]:
        """Async iterator over queue items"""
    
    def len(self) -> int:
        """Get approximate number of items in queue"""
    
    def __len__(self) -> int:
        """Get approximate number of items using len(queue) syntax"""

class QueueInfo:
    """Information about a Queue object"""
    name: Optional[str]
    created_at: datetime
    created_by: Optional[str]
```

#### Usage Examples

```python
import modal

app = modal.App()
task_queue = modal.Queue.persist("work-queue")

# Producer function
@app.function()
def generate_tasks():
    tasks = [{"id": i, "data": f"task_{i}"} for i in range(100)]
    task_queue.put_many(tasks)
    print(f"Added {len(tasks)} tasks to queue")

# Consumer function
@app.function()
def process_tasks():
    while True:
        try:
            # Get task with timeout
            task = task_queue.get(timeout=30)
            
            # Process the task
            result = expensive_operation(task["data"])
            print(f"Processed task {task['id']}: {result}")
            
        except queue.Empty:
            print("No more tasks, worker stopping")
            break

# Batch consumer
@app.function()
def batch_processor():
    # Process tasks in batches for efficiency
    for batch in task_queue.iterate():
        tasks = task_queue.get_many(10)  # Get up to 10 tasks
        results = [process_single_task(task) for task in tasks]
        print(f"Processed batch of {len(results)} tasks")
```

### CloudBucketMount - Cloud Storage Integration

Mount cloud storage buckets (S3, GCS, Azure) as file systems within Modal functions.

```python { .api }
class CloudBucketMount:
    @classmethod
    def from_s3_bucket(
        cls,
        bucket_name: str,
        *,
        key_prefix: str = "",
        secret: Optional["Secret"] = None,
        read_only: bool = True
    ) -> "CloudBucketMount":
        """Mount an S3 bucket"""
    
    @classmethod
    def from_gcs_bucket(
        cls,
        bucket_name: str,
        *,
        key_prefix: str = "",
        secret: Optional["Secret"] = None,
        read_only: bool = True
    ) -> "CloudBucketMount":
        """Mount a Google Cloud Storage bucket"""
    
    @classmethod
    def from_azure_blob_storage(
        cls,
        account_name: str,
        container_name: str,
        *,
        key_prefix: str = "",
        secret: Optional["Secret"] = None,
        read_only: bool = True
    ) -> "CloudBucketMount":
        """Mount an Azure Blob Storage container"""
```

#### Usage Examples

```python
import modal

app = modal.App()

# Mount S3 bucket
s3_mount = modal.CloudBucketMount.from_s3_bucket(
    "my-data-bucket",
    secret=modal.Secret.from_name("aws-credentials"),
    read_only=False
)

@app.function(cloud_bucket_mounts={"/s3-data": s3_mount})
def process_s3_data():
    # Access S3 files as local files
    with open("/s3-data/input/data.csv", "r") as f:
        data = f.read()
    
    # Process data
    result = analyze_data(data)
    
    # Write results back to S3
    with open("/s3-data/output/results.json", "w") as f:
        json.dump(result, f)

# Mount GCS bucket
gcs_mount = modal.CloudBucketMount.from_gcs_bucket(
    "my-gcs-bucket",
    secret=modal.Secret.from_name("gcp-credentials")
)

@app.function(cloud_bucket_mounts={"/gcs-data": gcs_mount})
def backup_to_gcs():
    # Read local data
    local_files = os.listdir("/tmp/data")
    
    # Copy to GCS through mount
    for filename in local_files:
        shutil.copy(f"/tmp/data/{filename}", f"/gcs-data/backup/{filename}")
```

## Storage Patterns

### Data Pipeline with Multiple Storage Types

```python
import modal

app = modal.App()

# Different storage for different use cases
raw_data_volume = modal.Volume.persist("raw-data")        # Large file storage
processed_cache = modal.NetworkFileSystem.persist("cache") # Fast shared access
config_dict = modal.Dict.persist("pipeline-config")       # Configuration
task_queue = modal.Queue.persist("processing-queue")      # Task coordination

@app.function(
    volumes={"/raw": raw_data_volume},
    network_file_systems={"/cache": processed_cache}
)
def data_pipeline():
    # Get configuration
    batch_size = config_dict.get("batch_size", 100)
    
    # Process raw data files
    for filename in os.listdir("/raw/input"):
        # Check cache first
        cache_key = f"/cache/processed_{filename}"
        if os.path.exists(cache_key):
            continue  # Already processed
        
        # Process file
        with open(f"/raw/input/{filename}", "r") as f:
            data = f.read()
        
        result = process_data_file(data)
        
        # Cache result
        with open(cache_key, "w") as f:
            json.dump(result, f)
        
        # Queue downstream tasks
        task_queue.put({"type": "notify", "file": filename, "result": result})
```

### Shared State Between Functions

```python
import modal

app = modal.App()
shared_state = modal.Dict.persist("worker-state")

@app.function()
def coordinator():
    # Initialize shared state
    shared_state["active_workers"] = 0
    shared_state["total_processed"] = 0
    shared_state["status"] = "starting"
    
    # Start workers
    for i in range(5):
        worker.spawn(f"worker-{i}")

@app.function()
def worker(worker_id: str):
    # Register worker
    current_workers = shared_state.get("active_workers", 0)
    shared_state["active_workers"] = current_workers + 1
    
    try:
        # Do work
        for task in get_tasks():
            result = process_task(task)
            
            # Update shared counters
            total = shared_state.get("total_processed", 0)
            shared_state["total_processed"] = total + 1
            
    finally:
        # Unregister worker
        current_workers = shared_state.get("active_workers", 0)
        shared_state["active_workers"] = max(0, current_workers - 1)
        
        # Check if all workers done
        if shared_state["active_workers"] == 0:
            shared_state["status"] = "completed"
```