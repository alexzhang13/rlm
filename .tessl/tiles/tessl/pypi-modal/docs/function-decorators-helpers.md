# Function Decorators & Helpers

Modal provides specialized decorators and helper functions for enhancing function behavior, defining class lifecycle methods, enabling batched execution, and controlling concurrency. These tools allow fine-grained control over how functions execute in the Modal environment.

## Capabilities

### Method Decorator

Decorator for defining methods within Modal classes, enabling stateful serverless computing with shared instance state.

```python { .api }
def method(func: Callable) -> Callable:
    """Decorator to define methods within Modal classes"""
```

#### Usage Examples

```python
import modal

app = modal.App()

@app.cls()
class DataProcessor:
    def __init__(self, model_path: str):
        # Constructor runs during instance creation
        self.model = load_model(model_path)
        self.cache = {}
    
    @modal.method()
    def process_single(self, data: str) -> str:
        # Method can access instance state
        if data in self.cache:
            return self.cache[data]
        
        result = self.model.predict(data)
        self.cache[data] = result
        return result
    
    @modal.method()
    def process_batch(self, data_list: list[str]) -> list[str]:
        # Another method sharing the same instance state
        return [self.process_single(data) for data in data_list]
    
    @modal.method()
    def get_cache_size(self) -> int:
        return len(self.cache)

# Usage
@app.local_entrypoint()
def main():
    processor = DataProcessor("path/to/model")
    
    # Call methods on the remote instance
    result1 = processor.process_single.remote("input1")
    result2 = processor.process_batch.remote(["input2", "input3"])
    cache_size = processor.get_cache_size.remote()
    
    print(f"Results: {result1}, {result2}")
    print(f"Cache size: {cache_size}")
```

### Parameter Helper

Helper function for defining class initialization parameters with validation and default values, similar to dataclass fields.

```python { .api }
def parameter(*, default: Any = _no_default, init: bool = True) -> Any:
    """Define class initialization parameters with options"""
```

#### Usage Examples

```python
import modal

app = modal.App()

@app.cls()
class ConfigurableService:
    # Parameters with type annotations and defaults
    model_name: str = modal.parameter()
    batch_size: int = modal.parameter(default=32)
    temperature: float = modal.parameter(default=0.7)
    debug_mode: bool = modal.parameter(default=False)
    
    # Internal field not used in constructor
    _internal_cache: dict = modal.parameter(init=False)
    
    def __post_init__(self):
        # Initialize internal state after parameter injection
        self._internal_cache = {}
        print(f"Service initialized with model={self.model_name}, batch_size={self.batch_size}")
    
    @modal.method()
    def configure_service(self):
        # Use parameters in methods
        if self.debug_mode:
            print(f"Debug: Processing with temperature={self.temperature}")
        
        return {
            "model": self.model_name,
            "batch_size": self.batch_size,
            "temperature": self.temperature
        }

# Usage with different configurations
@app.local_entrypoint()
def main():
    # Create instances with different parameters
    service1 = ConfigurableService("gpt-4", batch_size=64, debug_mode=True)
    service2 = ConfigurableService("claude-3", temperature=0.5)
    
    config1 = service1.configure_service.remote()
    config2 = service2.configure_service.remote()
    
    print("Service 1 config:", config1)
    print("Service 2 config:", config2)
```

### Lifecycle Decorators

Decorators for defining class lifecycle methods that run during container startup and shutdown.

```python { .api }
def enter(func: Callable) -> Callable:
    """Decorator for class enter lifecycle method (runs on container startup)"""

def exit(func: Callable) -> Callable:
    """Decorator for class exit lifecycle method (runs on container shutdown)"""
```

#### Usage Examples

```python
import modal

app = modal.App()

@app.cls()
class DatabaseService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.cache = None
    
    @modal.enter()
    def setup_connections(self):
        """Run once when container starts"""
        print("Setting up database connection...")
        self.connection = create_database_connection(self.connection_string)
        self.cache = initialize_cache()
        print("Database service ready!")
    
    @modal.exit()
    def cleanup_connections(self):
        """Run once when container shuts down"""
        print("Cleaning up database connections...")
        if self.connection:
            self.connection.close()
        if self.cache:
            self.cache.clear()
        print("Cleanup complete!")
    
    @modal.method()
    def query_data(self, sql: str) -> list[dict]:
        # Connection is already established from enter()
        cursor = self.connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    
    @modal.method()
    def cached_query(self, sql: str) -> list[dict]:
        # Use cache initialized in enter()
        if sql in self.cache:
            return self.cache[sql]
        
        result = self.query_data(sql)
        self.cache[sql] = result
        return result

# Usage
@app.local_entrypoint()
def main():
    db_service = DatabaseService("postgresql://user:pass@host:5432/db")
    
    # First call triggers enter() lifecycle
    results = db_service.query_data.remote("SELECT * FROM users LIMIT 10")
    
    # Subsequent calls reuse the established connection
    cached_results = db_service.cached_query.remote("SELECT COUNT(*) FROM users")
    
    print("Query results:", results)
    print("Cached results:", cached_results)
    
    # Container shutdown triggers exit() lifecycle automatically
```

### Execution Control Decorators

Decorators for controlling how functions execute, including batching and concurrency patterns.

```python { .api }
def batched(max_batch_size: int = 10) -> Callable:
    """Decorator to enable batched function calls for improved throughput"""

def concurrent(func: Callable) -> Callable:
    """Decorator to enable concurrent function execution"""
```

#### Usage Examples

```python
import modal

app = modal.App()

@app.function()
@modal.batched(max_batch_size=50)
def process_items_batched(items: list[str]) -> list[str]:
    """Process multiple items in a single function call"""
    print(f"Processing batch of {len(items)} items")
    
    # Expensive setup that benefits from batching
    model = load_expensive_model()
    
    # Process all items in the batch
    results = []
    for item in items:
        result = model.process(item)
        results.append(result)
    
    return results

@app.function()
@modal.concurrent
def process_item_concurrent(item: str) -> str:
    """Process items with concurrent execution"""
    # Each call can run concurrently with others
    return expensive_processing(item)

@app.local_entrypoint()
def main():
    # Batched processing - items are automatically grouped
    items = [f"item_{i}" for i in range(100)]
    
    # These calls will be automatically batched up to max_batch_size
    batch_results = []
    for item in items:
        result = process_items_batched.remote([item])  # Each call adds to batch
        batch_results.append(result)
    
    print(f"Batched processing completed: {len(batch_results)} results")
    
    # Concurrent processing - items run in parallel
    concurrent_futures = []
    for item in items[:10]:  # Process first 10 concurrently
        future = process_item_concurrent.spawn(item)
        concurrent_futures.append(future)
    
    # Collect concurrent results
    concurrent_results = [future.get() for future in concurrent_futures]
    print(f"Concurrent processing completed: {len(concurrent_results)} results")
```

## Advanced Patterns

### Stateful Service with Lifecycle Management

```python
import modal

app = modal.App()

@app.cls()
class MLInferenceService:
    model_name: str = modal.parameter()
    cache_size: int = modal.parameter(default=1000)
    
    @modal.enter()
    def load_model(self):
        """Load model and initialize cache on container start"""
        print(f"Loading model: {self.model_name}")
        self.model = download_and_load_model(self.model_name)
        self.prediction_cache = LRUCache(maxsize=self.cache_size)
        self.stats = {"requests": 0, "cache_hits": 0}
        print("Model loaded and ready for inference")
    
    @modal.exit()
    def save_stats(self):
        """Save statistics before container shutdown"""
        print(f"Final stats: {self.stats}")
        save_stats_to_database(self.stats)
    
    @modal.method()
    @modal.batched(max_batch_size=32)
    def predict_batch(self, inputs: list[str]) -> list[dict]:
        """Batched prediction with caching"""
        results = []
        uncached_inputs = []
        uncached_indices = []
        
        # Check cache for each input
        for i, inp in enumerate(inputs):
            if inp in self.prediction_cache:
                results.append(self.prediction_cache[inp])
                self.stats["cache_hits"] += 1
            else:
                results.append(None)  # Placeholder
                uncached_inputs.append(inp)
                uncached_indices.append(i)
        
        # Batch process uncached inputs
        if uncached_inputs:
            batch_predictions = self.model.predict(uncached_inputs)
            for idx, prediction in zip(uncached_indices, batch_predictions):
                self.prediction_cache[inputs[idx]] = prediction
                results[idx] = prediction
        
        self.stats["requests"] += len(inputs)
        return results
    
    @modal.method()
    def get_stats(self) -> dict:
        """Get current service statistics"""
        return self.stats.copy()

# Usage
@app.local_entrypoint()
def main():
    # Create service instance
    ml_service = MLInferenceService(model_name="bert-base-uncased", cache_size=500)
    
    # Make predictions (automatically batched)
    test_inputs = [f"test sentence {i}" for i in range(100)]
    predictions = ml_service.predict_batch.remote(test_inputs)
    
    # Check service statistics
    stats = ml_service.get_stats.remote()
    print(f"Service stats: {stats}")
    
    # Make some repeated predictions to test caching
    repeat_predictions = ml_service.predict_batch.remote(test_inputs[:10])
    final_stats = ml_service.get_stats.remote()
    print(f"Final stats with cache hits: {final_stats}")
```

### Concurrent Task Processing with Shared State

```python
import modal

app = modal.App()

@app.cls()
class TaskProcessor:
    max_workers: int = modal.parameter(default=10)
    
    @modal.enter()
    def setup_processor(self):
        """Initialize shared resources"""
        self.task_queue = initialize_task_queue()
        self.result_store = initialize_result_store()
        self.worker_stats = {}
    
    @modal.method()
    @modal.concurrent
    def process_task_concurrent(self, task_id: str, worker_id: str) -> dict:
        """Process individual tasks concurrently"""
        # Track worker statistics
        if worker_id not in self.worker_stats:
            self.worker_stats[worker_id] = {"processed": 0, "errors": 0}
        
        try:
            # Process the task
            task_data = self.task_queue.get_task(task_id)
            result = expensive_task_processing(task_data)
            
            # Store result
            self.result_store.put(task_id, result)
            self.worker_stats[worker_id]["processed"] += 1
            
            return {"status": "success", "task_id": task_id, "worker": worker_id}
            
        except Exception as e:
            self.worker_stats[worker_id]["errors"] += 1
            return {"status": "error", "task_id": task_id, "error": str(e)}
    
    @modal.method()
    def get_worker_stats(self) -> dict:
        """Get statistics for all workers"""
        return self.worker_stats.copy()

@app.local_entrypoint()
def main():
    processor = TaskProcessor(max_workers=20)
    
    # Process many tasks concurrently
    task_ids = [f"task_{i}" for i in range(100)]
    futures = []
    
    for i, task_id in enumerate(task_ids):
        worker_id = f"worker_{i % 20}"  # Distribute across workers
        future = processor.process_task_concurrent.spawn(task_id, worker_id)
        futures.append(future)
    
    # Collect results
    results = [future.get() for future in futures]
    
    # Check worker statistics
    stats = processor.get_worker_stats.remote()
    print(f"Worker statistics: {stats}")
    
    # Analyze results
    successful = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"Processed {successful} tasks successfully, {errors} errors")
```