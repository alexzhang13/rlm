# Temporary Operations

dill.temp provides utilities for temporary file operations with serialization, stream capture, and IO buffer management for testing, development workflows, and temporary data handling.

## File Operations

### Temporary File Serialization

```python { .api }
def dump(object, **kwds):
    """
    Dump object to a NamedTemporaryFile using dill.dump.
    
    Serializes an object to a temporary file and returns the file handle,
    useful for quick testing and temporary storage without managing filenames.
    
    Parameters:
    - object: object to serialize to temporary file
    - **kwds: optional keyword arguments including:
        - suffix: str, file name suffix (default: no suffix)  
        - prefix: str, file name prefix (default: system default)
        - other arguments passed to NamedTemporaryFile and dill.dump
    
    Returns:
    file handle: NamedTemporaryFile handle containing serialized object
    
    Raises:
    - PicklingError: when object cannot be serialized
    - IOError: when temporary file operations fail
    """

def load(file, **kwds):
    """
    Load an object that was stored with dill.temp.dump.
    
    Deserializes an object from a file, typically used with temporary
    files created by temp.dump but works with any dill-compatible file.
    
    Parameters:
    - file: file handle or str, file handle or path to file containing serialized object  
    - **kwds: optional keyword arguments including:
        - mode: str, file open mode ('r' or 'rb', default: 'rb')
        - other arguments passed to open() and dill.load
    
    Returns:
    object: deserialized object
    
    Raises:
    - UnpicklingError: when object cannot be deserialized
    - IOError: when file operations fail
    """
```

### Source Code File Operations

```python { .api }
def load_source(file, **kwds):
    """
    Load source code from file.
    
    Reads and executes Python source code from a file, returning
    the executed namespace or specific objects.
    
    Parameters:
    - file: str, path to Python source file
    - **kwds: keyword arguments for source execution control
    
    Returns:
    object: result of source code execution
    
    Raises:
    - SyntaxError: when source code is invalid
    - IOError: when file cannot be read
    """

def dump_source(object, **kwds):
    """
    Dump source code to temporary file.
    
    Extracts source code from an object and writes it to a temporary
    file, useful for code analysis and temporary source storage.
    
    Parameters:
    - object: object to extract source code from
    - **kwds: keyword arguments for source extraction
    
    Returns:
    str: path to temporary file containing source code
    
    Raises:
    - OSError: when source code cannot be extracted
    - IOError: when file operations fail
    """
```

## IO Buffer Operations

### Buffer-based Serialization

```python { .api }
def loadIO(buffer, **kwds):
    """
    Load object from IO buffer.
    
    Deserializes an object from a bytes buffer or file-like object,
    providing memory-based deserialization for testing and processing.
    
    Parameters:
    - buffer: bytes or file-like object containing serialized data
    - **kwds: keyword arguments passed to dill.load
    
    Returns:
    object: deserialized object
    
    Raises:
    - UnpicklingError: when deserialization fails
    - TypeError: when buffer type is not supported
    """

def dumpIO(object, **kwds):
    """
    Dump object to IO buffer.
    
    Serializes an object to a bytes buffer, returning the buffer
    for further processing or storage.
    
    Parameters:
    - object: object to serialize
    - **kwds: keyword arguments passed to dill.dumps
    
    Returns:
    bytes: serialized object as bytes buffer
    
    Raises:
    - PicklingError: when serialization fails
    """

def loadIO_source(buffer, **kwds):
    """
    Load source code from IO buffer.
    
    Reads and executes Python source code from a buffer,
    useful for dynamic code execution and testing.
    
    Parameters:
    - buffer: str or bytes containing Python source code
    - **kwds: keyword arguments for execution control
    
    Returns:
    object: result of source code execution
    
    Raises:
    - SyntaxError: when source code is invalid
    """

def dumpIO_source(object, **kwds):
    """
    Dump source code to IO buffer.
    
    Extracts source code from an object and returns it as a string buffer,
    useful for in-memory source code processing.
    
    Parameters:
    - object: object to extract source code from
    - **kwds: keyword arguments for source extraction
    
    Returns:
    str: source code as string buffer
    
    Raises:
    - OSError: when source code cannot be extracted
    """
```

## Stream Capture

### Output Capture Utilities

```python { .api }
def capture(stream='stdout'):
    """
    Capture stdout or stderr stream.
    
    Context manager that captures output from stdout or stderr,
    useful for testing, logging, and output analysis.
    
    Parameters:
    - stream: str, stream name ('stdout' or 'stderr')
    
    Returns:
    context manager that captures stream output
    
    Usage:
    with dill.temp.capture('stdout') as output:
        print("Hello")
    captured_text = output.getvalue()
    """
```

## Usage Examples

### Basic Temporary File Operations

```python
import dill.temp as temp

# Create some test data
def test_function(x, y):
    return x * y + 42

class TestClass:
    def __init__(self, value):
        self.value = value
    
    def get_doubled(self):
        return self.value * 2

test_data = {
    'function': test_function,
    'class': TestClass,
    'instance': TestClass(10),
    'list': [1, 2, 3, 4, 5]
}

# Dump to temporary file
temp_file = temp.dump(test_data)
print(f"Data saved to temporary file: {temp_file}")

# Load from temporary file
restored_data = temp.load(temp_file)
print(f"Restored data keys: {list(restored_data.keys())}")

# Test restored functionality
restored_function = restored_data['function']
result = restored_function(5, 3)
print(f"Function result: {result}")  # Should be 57

restored_instance = restored_data['instance']
doubled = restored_instance.get_doubled()
print(f"Instance method result: {doubled}")  # Should be 20
```

### Source Code Operations

```python
import dill.temp as temp

# Define a function to work with
def example_algorithm(data, threshold=0.5):
    """Example algorithm for demonstration."""
    processed = []
    for item in data:
        if isinstance(item, (int, float)) and item > threshold:
            processed.append(item * 2)
        else:
            processed.append(item)
    return processed

# Dump source code to temporary file
source_file = temp.dump_source(example_algorithm)
print(f"Source code saved to: {source_file}")

# Load and examine source code
with open(source_file, 'r') as f:
    source_content = f.read()
    print("Source code:")
    print(source_content)

# Load source code as executable
loaded_func = temp.load_source(source_file)
print(f"Loaded function: {loaded_func}")

# Test loaded function
test_data = [0.2, 0.8, 1.5, 0.1, 2.0]
result = loaded_func(test_data, threshold=0.6)
print(f"Algorithm result: {result}")
```

### IO Buffer Operations

```python
import dill.temp as temp
import io

# Complex object for testing
complex_data = {
    'functions': [lambda x: x**2, lambda x: x**3],
    'nested': {'level1': {'level2': [1, 2, 3]}},
    'instance': TestClass(42)
}

# Serialize to buffer
buffer_data = temp.dumpIO(complex_data)
print(f"Serialized to buffer: {len(buffer_data)} bytes")

# Deserialize from buffer
restored_from_buffer = temp.loadIO(buffer_data)
print("Restored from buffer successfully")

# Test functionality
square_func = restored_from_buffer['functions'][0]
print(f"Square function: {square_func(5)}")  # Should be 25

# Source code buffer operations
source_buffer = temp.dumpIO_source(example_algorithm)
print(f"Source code buffer length: {len(source_buffer)} characters")

# Load source from buffer
namespace = {}
exec(source_buffer, namespace)
func_from_buffer = namespace['example_algorithm']
result = func_from_buffer([1, 2, 3], threshold=1.5)
print(f"Function from source buffer: {result}")
```

### Stream Capture

```python
import dill.temp as temp

def noisy_function():
    """Function that produces output."""
    print("Starting processing...")
    print("Processing item 1")
    print("Processing item 2")
    print("Processing complete!")
    return "Result"

def error_function():
    """Function that produces error output."""
    import sys
    print("This goes to stdout")
    print("This goes to stderr", file=sys.stderr)
    return "Done"

# Capture stdout
with temp.capture('stdout') as stdout_capture:
    result = noisy_function()

stdout_output = stdout_capture.getvalue()
print(f"Captured stdout ({len(stdout_output)} chars):")
print(repr(stdout_output))

# Capture stderr
with temp.capture('stderr') as stderr_capture:
    result = error_function()

stderr_output = stderr_capture.getvalue()
print(f"Captured stderr: {repr(stderr_output)}")

# Capture both streams
import sys
from contextlib import redirect_stdout, redirect_stderr

def capture_both_streams(func):
    """Capture both stdout and stderr."""
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = func()
    
    return {
        'result': result,
        'stdout': stdout_buffer.getvalue(),
        'stderr': stderr_buffer.getvalue()
    }

# Usage
captured = capture_both_streams(error_function)
print(f"Function result: {captured['result']}")
print(f"Stdout: {repr(captured['stdout'])}")
print(f"Stderr: {repr(captured['stderr'])}")
```

## Advanced Use Cases

### Testing Framework Integration

```python
import dill.temp as temp
import unittest
import os

class TempFileTestCase(unittest.TestCase):
    """Test case with temporary file management."""
    
    def setUp(self):
        self.temp_files = []
    
    def tearDown(self):
        # Clean up temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
    
    def create_temp_object(self, obj):
        """Create temporary file for object and track it."""
        temp_file = temp.dump(obj)
        self.temp_files.append(temp_file)
        return temp_file
    
    def test_function_serialization(self):
        """Test function serialization via temporary files."""
        def test_func(x):
            return x * 2
        
        # Serialize to temp file
        temp_file = self.create_temp_object(test_func)
        self.assertTrue(os.path.exists(temp_file))
        
        # Load and test
        loaded_func = temp.load(temp_file)
        self.assertEqual(loaded_func(5), 10)
    
    def test_complex_object_roundtrip(self):
        """Test complex object serialization roundtrip."""
        complex_obj = {
            'data': [1, 2, 3, 4, 5],
            'func': lambda x: sum(x),
            'nested': {'key': 'value'}
        }
        
        temp_file = self.create_temp_object(complex_obj)
        loaded_obj = temp.load(temp_file)
        
        # Test loaded functionality
        self.assertEqual(loaded_obj['data'], [1, 2, 3, 4, 5])
        self.assertEqual(loaded_obj['func']([1, 2, 3]), 6)
        self.assertEqual(loaded_obj['nested']['key'], 'value')

# Run tests
if __name__ == '__main__':
    unittest.main()
```

### Development Workflow Tools

```python
import dill.temp as temp
import datetime
import json

class DevelopmentSession:
    """Manage development session with temporary serialization."""
    
    def __init__(self, session_name):
        self.session_name = session_name
        self.snapshots = []
        self.current_objects = {}
    
    def add_object(self, name, obj):
        """Add object to current session."""
        self.current_objects[name] = obj
        print(f"Added {name} to session")
    
    def take_snapshot(self, description=""):
        """Take snapshot of current session state."""
        timestamp = datetime.datetime.now().isoformat()
        
        # Serialize current objects to temporary file
        temp_file = temp.dump(self.current_objects)
        
        snapshot = {
            'timestamp': timestamp,
            'description': description,
            'temp_file': temp_file,
            'object_count': len(self.current_objects)
        }
        
        self.snapshots.append(snapshot)
        print(f"Snapshot taken: {len(self.snapshots)} total snapshots")
        return len(self.snapshots) - 1
    
    def restore_snapshot(self, snapshot_index):
        """Restore session from snapshot."""
        if 0 <= snapshot_index < len(self.snapshots):
            snapshot = self.snapshots[snapshot_index]
            
            # Load objects from temporary file
            self.current_objects = temp.load(snapshot['temp_file'])
            
            print(f"Restored snapshot from {snapshot['timestamp']}")
            print(f"Objects restored: {list(self.current_objects.keys())}")
        else:
            print(f"Invalid snapshot index: {snapshot_index}")
    
    def list_snapshots(self):
        """List all snapshots."""
        for i, snapshot in enumerate(self.snapshots):
            print(f"{i}: {snapshot['timestamp']} - {snapshot['description']} ({snapshot['object_count']} objects)")
    
    def get_object(self, name):
        """Get object from current session."""
        return self.current_objects.get(name)
    
    def export_session_info(self, filename):
        """Export session metadata to JSON."""
        session_info = {
            'session_name': self.session_name,
            'snapshots': [
                {
                    'timestamp': s['timestamp'],
                    'description': s['description'],
                    'object_count': s['object_count']
                }
                for s in self.snapshots
            ],
            'current_objects': list(self.current_objects.keys())
        }
        
        with open(filename, 'w') as f:
            json.dump(session_info, f, indent=2)
        
        print(f"Session info exported to {filename}")

# Usage example
session = DevelopmentSession("algorithm_development")

# Add some objects to work with
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class DataProcessor:
    def __init__(self, multiplier=1):
        self.multiplier = multiplier
    
    def process(self, data):
        return [x * self.multiplier for x in data]

session.add_object('fib_func', fibonacci)
session.add_object('processor', DataProcessor(2))
session.add_object('test_data', [1, 2, 3, 4, 5])

# Take initial snapshot
session.take_snapshot("Initial development state")

# Modify objects
session.add_object('processor', DataProcessor(3))  # Change multiplier
session.add_object('results', session.get_object('processor').process(session.get_object('test_data')))

# Take another snapshot
session.take_snapshot("After modifications")

# Show snapshots
session.list_snapshots()

# Restore previous state
session.restore_snapshot(0)

# Export session info
session.export_session_info('dev_session.json')
```

### Performance Benchmarking

```python
import dill.temp as temp
import time
import sys

class SerializationBenchmark:
    """Benchmark serialization performance with temporary operations."""
    
    def __init__(self):
        self.results = {}
    
    def benchmark_temp_operations(self, test_objects, iterations=10):
        """Benchmark temporary file operations."""
        for name, obj in test_objects.items():
            print(f"Benchmarking {name}...")
            
            # Measure temp.dump performance
            dump_times = []
            load_times = []
            file_sizes = []
            
            for i in range(iterations):
                # Time dump operation
                start_time = time.time()
                temp_file = temp.dump(obj)
                dump_time = time.time() - start_time
                dump_times.append(dump_time)
                
                # Get file size
                file_size = os.path.getsize(temp_file)
                file_sizes.append(file_size)
                
                # Time load operation
                start_time = time.time()
                temp.load(temp_file)
                load_time = time.time() - start_time
                load_times.append(load_time)
                
                # Clean up
                os.remove(temp_file)
            
            self.results[name] = {
                'avg_dump_time': sum(dump_times) / len(dump_times),
                'avg_load_time': sum(load_times) / len(load_times),
                'avg_file_size': sum(file_sizes) / len(file_sizes),
                'min_dump_time': min(dump_times),
                'max_dump_time': max(dump_times),
                'min_load_time': min(load_times),
                'max_load_time': max(load_times)
            }
    
    def benchmark_io_operations(self, test_objects, iterations=10):
        """Benchmark IO buffer operations."""
        for name, obj in test_objects.items():
            print(f"Benchmarking IO operations for {name}...")
            
            dump_times = []
            load_times = []
            buffer_sizes = []
            
            for i in range(iterations):
                # Time dumpIO operation
                start_time = time.time()
                buffer_data = temp.dumpIO(obj)
                dump_time = time.time() - start_time
                dump_times.append(dump_time)
                
                buffer_sizes.append(len(buffer_data))
                
                # Time loadIO operation
                start_time = time.time()
                temp.loadIO(buffer_data)
                load_time = time.time() - start_time
                load_times.append(load_time)
            
            io_results = {
                'avg_dump_time': sum(dump_times) / len(dump_times),
                'avg_load_time': sum(load_times) / len(load_times),
                'avg_buffer_size': sum(buffer_sizes) / len(buffer_sizes)
            }
            
            if name in self.results:
                self.results[name]['io'] = io_results
            else:
                self.results[name] = {'io': io_results}
    
    def print_results(self):
        """Print benchmark results."""
        print("\\nSerialization Benchmark Results")
        print("=" * 60)
        
        for name, results in self.results.items():
            print(f"\\n{name}:")
            print("-" * 30)
            
            if 'avg_dump_time' in results:  # File operations
                print(f"File Operations:")
                print(f"  Avg dump time: {results['avg_dump_time']:.4f}s")
                print(f"  Avg load time: {results['avg_load_time']:.4f}s")
                print(f"  Avg file size: {results['avg_file_size']:,.0f} bytes")
            
            if 'io' in results:  # IO operations
                io = results['io']
                print(f"IO Buffer Operations:")
                print(f"  Avg dump time: {io['avg_dump_time']:.4f}s")
                print(f"  Avg load time: {io['avg_load_time']:.4f}s")
                print(f"  Avg buffer size: {io['avg_buffer_size']:,.0f} bytes")

# Run benchmark
benchmark = SerializationBenchmark()

# Create test objects of varying complexity
test_objects = {
    'simple_list': list(range(1000)),
    'function': lambda x: x**2 + x + 1,
    'class_instance': TestClass(100),
    'nested_dict': {'level1': {'level2': {'level3': list(range(100))}}},
    'mixed_structure': {
        'data': list(range(500)),
        'funcs': [lambda x: x+1, lambda x: x*2],
        'objects': [TestClass(i) for i in range(10)]
    }
}

benchmark.benchmark_temp_operations(test_objects, iterations=5)
benchmark.benchmark_io_operations(test_objects, iterations=5)
benchmark.print_results()
```

## Best Practices

### Temporary File Management

1. **Cleanup**: Always clean up temporary files when done
2. **Path Management**: Store temp file paths for later cleanup
3. **Error Handling**: Handle file operation errors gracefully
4. **Security**: Be aware of temporary file permissions and location

### Performance Optimization

1. **Buffer vs File**: Use IO buffers for small objects, files for large ones
2. **Memory Usage**: Monitor memory usage with large temporary operations
3. **Disk Space**: Monitor disk space usage with temporary files
4. **Cleanup Frequency**: Clean up temporary files regularly in long-running processes