# Extended Pickler Classes

dill provides enhanced Pickler and Unpickler classes that extend Python's standard pickle classes with support for complex objects including functions, classes, lambdas, and other previously unpickleable types.

## Enhanced Pickler Class

```python { .api }
class Pickler:
    """
    Extended pickler with additional capabilities for complex objects.
    
    Provides enhanced serialization support beyond standard pickle.Pickler,
    including functions, classes, nested structures, and other complex types
    that standard pickle cannot handle.
    
    Attributes:
    - memo: dict, memoization cache for object references
    - bin: bool, binary mode flag
    - fast: bool, fast mode for performance optimization
    - dispatch_table: dict, custom type dispatch table
    
    Methods:
    - dump(obj): serialize object to file
    - save(obj): internal save method
    - persistent_id(obj): handle persistent object references
    """
```

## Enhanced Unpickler Class

```python { .api }
class Unpickler:
    """
    Extended unpickler with additional capabilities for complex objects.
    
    Provides enhanced deserialization support beyond standard pickle.Unpickler,
    with improved error handling, type restoration, and support for complex
    object reconstruction.
    
    Attributes:
    - memo: dict, memoization cache for object reconstruction
    - encoding: str, text encoding for string objects
    - errors: str, error handling mode
    
    Methods:
    - load(): deserialize object from file
    - persistent_load(pid): handle persistent object loading
    """
```

## Usage Examples

### Basic Pickler Usage

```python
import dill
import io

# Create a function with closure
def create_counter(start=0):
    count = start
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

counter = create_counter(10)

# Use Pickler class directly
buffer = io.BytesIO()
pickler = dill.Pickler(buffer)
pickler.dump(counter)

# Use Unpickler class directly
buffer.seek(0)
unpickler = dill.Unpickler(buffer)
restored_counter = unpickler.load()

print(restored_counter())  # 11
print(restored_counter())  # 12
```

### Custom Protocol and Options

```python
import dill
import io

# Advanced pickler configuration
buffer = io.BytesIO()
pickler = dill.Pickler(buffer, protocol=dill.HIGHEST_PROTOCOL)

# Configure pickler options through settings
original_settings = dill.settings.copy()
dill.settings['byref'] = True
dill.settings['recurse'] = True

complex_object = create_complex_nested_structure()
pickler.dump(complex_object)

# Restore original settings
dill.settings.update(original_settings)

# Unpickle with custom error handling
buffer.seek(0)
unpickler = dill.Unpickler(buffer)
try:
    restored_object = unpickler.load()
except dill.UnpicklingError as e:
    print(f"Unpickling failed: {e}")
```

### Integration with File Objects

```python
import dill

# Direct file usage
with open('complex_data.pkl', 'wb') as f:
    pickler = dill.Pickler(f)
    pickler.dump(my_function)
    pickler.dump(my_class)
    pickler.dump(my_instance)

# Load multiple objects
with open('complex_data.pkl', 'rb') as f:
    unpickler = dill.Unpickler(f)
    restored_function = unpickler.load()
    restored_class = unpickler.load()
    restored_instance = unpickler.load()
```

## Advanced Features

### Custom Dispatch Tables

```python
import dill
import io

# Custom type handling
def save_custom_type(pickler, obj):
    # Custom serialization logic
    pickler.write(b'custom_marker')
    pickler.save(obj.__dict__)

# Create pickler with custom dispatch
buffer = io.BytesIO()
pickler = dill.Pickler(buffer)

# Add custom type handler
if not hasattr(pickler, 'dispatch_table'):
    pickler.dispatch_table = {}
pickler.dispatch_table[MyCustomType] = save_custom_type

# Use with custom type
custom_obj = MyCustomType()
pickler.dump(custom_obj)
```

### Memory-Efficient Streaming

```python
import dill

def serialize_large_dataset(data_iterator, filename):
    """Serialize large dataset in streaming fashion."""
    with open(filename, 'wb') as f:
        pickler = dill.Pickler(f)
        
        # Stream objects one by one
        for item in data_iterator:
            pickler.dump(item)

def deserialize_large_dataset(filename):
    """Deserialize large dataset in streaming fashion."""
    with open(filename, 'rb') as f:
        unpickler = dill.Unpickler(f)
        
        while True:
            try:
                item = unpickler.load()
                yield item
            except EOFError:
                break

# Usage
large_data = [complex_object(i) for i in range(10000)]
serialize_large_dataset(large_data, 'large_dataset.pkl')

# Process items one by one without loading all into memory
for item in deserialize_large_dataset('large_dataset.pkl'):
    process_item(item)
```

## Error Handling and Debugging

```python
import dill
import io
from dill import PicklingError, UnpicklingError

def safe_pickle_with_diagnostics(obj, buffer):
    """Pickle with comprehensive error handling."""
    try:
        pickler = dill.Pickler(buffer)
        pickler.dump(obj)
        return True
    except PicklingError as e:
        print(f"Pickling failed: {e}")
        
        # Use diagnostic tools
        bad_items = dill.detect.baditems(obj)
        if bad_items:
            print("Unpickleable items found:")
            for item in bad_items:
                print(f"  {item}")
        
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def safe_unpickle_with_recovery(buffer):
    """Unpickle with error recovery."""
    try:
        buffer.seek(0)
        unpickler = dill.Unpickler(buffer)
        return unpickler.load()
    except UnpicklingError as e:
        print(f"Unpickling failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during unpickling: {e}")
        return None
```

## Performance Optimization

```python
import dill
import io

# Optimize for speed
def fast_pickle_config():
    """Configure dill for maximum speed."""
    # Use highest protocol
    protocol = dill.HIGHEST_PROTOCOL
    
    # Configure for speed over size
    settings = {
        'protocol': protocol,
        'byref': False,  # Avoid reference resolution overhead
        'recurse': False  # Avoid deep recursion overhead
    }
    
    return settings

# Optimize for size
def compact_pickle_config():
    """Configure dill for minimum size."""
    settings = {
        'protocol': dill.HIGHEST_PROTOCOL,
        'byref': True,  # Use references to reduce duplication
        'recurse': True  # Ensure complete object graphs
    }
    
    return settings

# Apply configuration
fast_settings = fast_pickle_config()
buffer = io.BytesIO()

# Create optimized pickler
pickler = dill.Pickler(buffer, protocol=fast_settings['protocol'])

# Apply settings through global configuration
original_settings = dill.settings.copy()
dill.settings.update(fast_settings)

try:
    pickler.dump(large_complex_object)
finally:
    # Restore original settings
    dill.settings.update(original_settings)
```

## Thread Safety Considerations

```python
import dill
import threading
import io

class ThreadSafePickler:
    """Thread-safe wrapper for dill pickler operations."""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def dump_to_bytes(self, obj, **kwargs):
        """Thread-safe serialization to bytes."""
        with self._lock:
            return dill.dumps(obj, **kwargs)
    
    def load_from_bytes(self, data, **kwargs):
        """Thread-safe deserialization from bytes."""
        with self._lock:
            return dill.loads(data, **kwargs)
    
    def dump_to_file(self, obj, filename, **kwargs):
        """Thread-safe serialization to file."""
        with self._lock:
            with open(filename, 'wb') as f:
                pickler = dill.Pickler(f)
                pickler.dump(obj)
    
    def load_from_file(self, filename, **kwargs):
        """Thread-safe deserialization from file."""
        with self._lock:
            with open(filename, 'rb') as f:
                unpickler = dill.Unpickler(f)
                return unpickler.load()

# Usage in multithreaded environment
safe_pickler = ThreadSafePickler()

def worker_thread(obj, thread_id):
    data = safe_pickler.dump_to_bytes(obj)
    restored = safe_pickler.load_from_bytes(data)
    print(f"Thread {thread_id}: Object successfully serialized and restored")

# Start multiple threads
threads = []
for i in range(5):
    t = threading.Thread(target=worker_thread, args=(complex_object, i))
    threads.append(t)
    t.start()

# Wait for completion
for t in threads:
    t.join()
```