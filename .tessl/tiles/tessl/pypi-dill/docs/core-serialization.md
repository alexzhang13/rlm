# Core Serialization

dill's core serialization functions provide extended pickle functionality that can handle complex Python objects including functions, classes, lambdas, and nested structures that standard pickle cannot serialize.

## Primary Serialization Functions

### File-based Operations

```python { .api }
def dump(obj, file, protocol=None, byref=None, fmode=None, recurse=None, **kwds):
    """
    Serialize object to a file.
    
    Provides enhanced serialization capabilities beyond standard pickle.dump,
    supporting complex objects like functions, classes, and nested structures.
    
    Parameters:
    - obj: object to serialize
    - file: file-like object to write to (must have write() method)
    - protocol: int, pickle protocol version (default: DEFAULT_PROTOCOL)
    - byref: bool, pickle by reference when possible to reduce file size
    - fmode: int, file mode for handle management (0=HANDLE_FMODE, 1=CONTENTS_FMODE, 2=FILE_FMODE)
    - recurse: bool, recursively pickle nested objects and their dependencies
    - **kwds: additional keyword arguments passed to Pickler
    
    Returns:
    None
    
    Raises:
    - PicklingError: when object cannot be serialized
    - IOError: when file operations fail
    """

def load(file, ignore=None, **kwds):
    """
    Deserialize object from a file.
    
    Provides enhanced deserialization capabilities beyond standard pickle.load,
    with improved error handling and support for complex object restoration.
    
    Parameters:
    - file: file-like object to read from (must have read() method)
    - ignore: bool, ignore certain unpickling errors and continue
    - **kwds: additional keyword arguments passed to Unpickler
    
    Returns:
    object: deserialized object with full functionality restored
    
    Raises:
    - UnpicklingError: when deserialization fails
    - IOError: when file operations fail
    """
```

### String-based Operations

```python { .api }
def dumps(obj, protocol=None, byref=None, fmode=None, recurse=None, **kwds):
    """
    Serialize object to a bytes string.
    
    Converts any Python object to a bytes representation that can be
    stored, transmitted, or restored later with full functionality.
    
    Parameters:
    - obj: object to serialize (any Python object)
    - protocol: int, pickle protocol version (default: DEFAULT_PROTOCOL)
    - byref: bool, pickle by reference when possible to reduce size
    - fmode: int, file mode for handle management
    - recurse: bool, recursively pickle nested objects and dependencies
    - **kwds: additional keyword arguments passed to Pickler
    
    Returns:
    bytes: serialized object as bytes string
    
    Raises:
    - PicklingError: when object cannot be serialized
    """

def loads(str, ignore=None, **kwds): 
    """
    Deserialize object from a bytes string.
    
    Restores a Python object from its bytes representation with
    full functionality and state preservation.
    
    Parameters:
    - str: bytes, bytes string containing serialized object
    - ignore: bool, ignore certain unpickling errors and continue
    - **kwds: additional keyword arguments passed to Unpickler
    
    Returns:
    object: deserialized object with original functionality
    
    Raises:
    - UnpicklingError: when deserialization fails
    - TypeError: when input is not bytes
    """
```

### Deep Copy Operation

```python { .api }
def copy(obj, *args, **kwds):
    """
    Create a deep copy of an object using serialization.
    
    Uses dill's enhanced serialization to create deep copies of complex
    objects that standard copy.deepcopy cannot handle.
    
    Parameters:
    - obj: object to copy (any Python object)
    - *args: positional arguments passed to dumps/loads
    - **kwds: keyword arguments passed to dumps/loads
    
    Returns:
    object: deep copy of the input object with independent state
    
    Raises:
    - PicklingError: when object cannot be serialized for copying
    """
```

## Usage Examples

### Basic Function Serialization

```python
import dill

# Serialize a function with closure
def create_multiplier(factor):
    def multiply(x):
        return x * factor
    return multiply

# Create function with closure
times_three = create_multiplier(3)

# Serialize to bytes
serialized = dill.dumps(times_three)

# Deserialize and use
restored_function = dill.loads(serialized)
result = restored_function(4)  # Returns 12
```

### Class and Instance Serialization

```python
import dill

# Define a class with methods
class Calculator:
    def __init__(self, precision=2):
        self.precision = precision
    
    def add(self, a, b):
        return round(a + b, self.precision)

# Create instance
calc = Calculator(precision=3)

# Serialize to file
with open('calculator.pkl', 'wb') as f:
    dill.dump(calc, f)

# Load from file
with open('calculator.pkl', 'rb') as f:
    restored_calc = dill.load(f)

result = restored_calc.add(1.2345, 2.6789)  # Returns 3.913
```

### Lambda and Nested Function Handling

```python
import dill

# Complex nested structure with lambdas
operations = {
    'square': lambda x: x * x,
    'cube': lambda x: x ** 3,
    'factorial': lambda n: 1 if n <= 1 else n * operations['factorial'](n-1)
}

# Serialize complex structure
data = dill.dumps(operations)

# Restore and use
restored_ops = dill.loads(data)
print(restored_ops['square'](5))      # 25
print(restored_ops['factorial'](5))   # 120
```

### Error Handling

```python
import dill
from dill import PicklingError, UnpicklingError

# Handle serialization errors
def safe_serialize(obj):
    try:
        return dill.dumps(obj)
    except PicklingError as e:
        print(f"Cannot serialize object: {e}")
        return None

# Handle deserialization errors  
def safe_deserialize(data):
    try:
        return dill.loads(data)
    except UnpicklingError as e:
        print(f"Cannot deserialize data: {e}")
        return None
```

## Advanced Features

### Protocol Selection

```python
import dill

# Use specific protocol version
data = dill.dumps(my_object, protocol=dill.HIGHEST_PROTOCOL)

# Check protocol compatibility
print(f"Default protocol: {dill.DEFAULT_PROTOCOL}")
print(f"Highest protocol: {dill.HIGHEST_PROTOCOL}")
```

### File Mode Options

```python
import dill

# Different file modes for handle management
obj = complex_object_with_files

# Handle mode - preserve file handles
dill.dump(obj, file, fmode=dill.HANDLE_FMODE)

# Contents mode - save file contents
dill.dump(obj, file, fmode=dill.CONTENTS_FMODE)

# File mode - save file metadata
dill.dump(obj, file, fmode=dill.FILE_FMODE)
```

### Recursive Serialization

```python
import dill

# Enable recursive pickling for nested dependencies
nested_structure = create_complex_nested_object()

# Recursively serialize all dependencies
data = dill.dumps(nested_structure, recurse=True)
```

## Integration with Standard Library

dill functions as a drop-in replacement for pickle:

```python
# Replace pickle with dill
import dill as pickle

# All pickle functionality works
data = pickle.dumps(obj)
restored = pickle.loads(data)

# Plus extended capabilities
function_data = pickle.dumps(my_function)  # Works with dill, fails with pickle
```

## Performance Considerations

- **Protocol Selection**: Higher protocols generally provide better performance and smaller file sizes
- **Recursive Mode**: Use `recurse=True` cautiously as it can significantly increase serialization time for large object graphs
- **File vs String**: File-based operations are more memory-efficient for large objects
- **Reference Mode**: `byref=True` can reduce file size but may affect object independence after deserialization