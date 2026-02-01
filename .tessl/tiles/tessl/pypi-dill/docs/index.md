# dill

dill is an extended Python serialization library that extends Python's pickle module to handle a broader range of Python objects including functions with yields, nested functions, lambdas, classes, and more exotic Python types. It provides a drop-in replacement for pickle with enhanced capabilities for serializing complex Python objects that standard pickle cannot handle, making it particularly useful for distributed computing, parallel processing, and saving interpreter sessions.

The library offers additional features like source code inspection, interactive pickling diagnostics, and the ability to save and restore complete interpreter sessions, with applications in scientific computing, debugging, and development tools that require comprehensive Python object serialization.

## Package Information

- **Package Name**: dill
- **Language**: Python  
- **Installation**: `pip install dill`
- **Optional Features**: `pip install dill[graph]` for object graph diagnostics, `pip install dill[profile]` for profiling tools

## Core Imports

```python
import dill
```

Common usage patterns:

```python
import dill as pickle  # Drop-in replacement for pickle
from dill import dump, dumps, load, loads  # Direct function imports
```

## Basic Usage

```python
import dill

# Basic serialization - works like pickle but handles more types
def example_function():
    return "Hello from dill!"

# Serialize function to bytes
serialized = dill.dumps(example_function)

# Deserialize function
restored_function = dill.loads(serialized)
result = restored_function()  # "Hello from dill!"

# Serialize to file
with open('function.pkl', 'wb') as f:
    dill.dump(example_function, f)

# Load from file
with open('function.pkl', 'rb') as f:
    loaded_function = dill.load(f)
```

## Architecture

dill is designed as an extended version of Python's pickle module, maintaining full compatibility while adding support for previously unpickleable objects. The architecture consists of:

- **Core Serialization Engine**: Extended pickler/unpickler classes that handle complex Python objects
- **Type Registry System**: Automatic detection and registration of new types for serialization
- **Session Management**: Capability to save and restore entire interpreter sessions including modules
- **Source Code Analysis**: Tools for inspecting and extracting source code from objects
- **Diagnostic Framework**: Utilities for identifying and debugging serialization issues

dill integrates seamlessly with the broader Python ecosystem, supporting distributed computing frameworks like multiprocessing, concurrent.futures, and third-party libraries like Celery and Dask.

## Capabilities

### Core Serialization

Primary serialization and deserialization functions that extend pickle's capabilities to handle complex Python objects including functions, classes, and nested structures.

```python { .api }
def dump(obj, file, protocol=None, byref=None, fmode=None, recurse=None, **kwds):
    """
    Serialize object to a file.
    
    Parameters:
    - obj: object to serialize
    - file: file-like object to write to
    - protocol: int, pickle protocol version (default: DEFAULT_PROTOCOL)
    - byref: bool, pickle by reference when possible
    - fmode: int, file mode for handle management
    - recurse: bool, recursively pickle nested objects
    - **kwds: additional keyword arguments
    
    Returns:
    None
    """

def dumps(obj, protocol=None, byref=None, fmode=None, recurse=None, **kwds):
    """
    Serialize object to a bytes string.
    
    Parameters:
    - obj: object to serialize
    - protocol: int, pickle protocol version (default: DEFAULT_PROTOCOL) 
    - byref: bool, pickle by reference when possible
    - fmode: int, file mode for handle management
    - recurse: bool, recursively pickle nested objects
    - **kwds: additional keyword arguments
    
    Returns:
    bytes: serialized object as bytes string
    """

def load(file, ignore=None, **kwds):
    """
    Deserialize object from a file.
    
    Parameters:
    - file: file-like object to read from
    - ignore: bool, ignore certain unpickling errors
    - **kwds: additional keyword arguments
    
    Returns:
    object: deserialized object
    """

def loads(str, ignore=None, **kwds):
    """
    Deserialize object from a bytes string.
    
    Parameters:
    - str: bytes string containing serialized object
    - ignore: bool, ignore certain unpickling errors  
    - **kwds: additional keyword arguments
    
    Returns:
    object: deserialized object
    """

def copy(obj, *args, **kwds):
    """
    Create a deep copy of an object using serialization.
    
    Parameters:
    - obj: object to copy
    - *args: positional arguments passed to dumps/loads
    - **kwds: keyword arguments passed to dumps/loads
    
    Returns:
    object: deep copy of the input object
    """
```

[Core Serialization](./core-serialization.md)

### Extended Pickler Classes

Enhanced Pickler and Unpickler classes that provide fine-grained control over the serialization process and support for complex Python objects.

```python { .api }
class Pickler:
    """
    Extended pickler with additional capabilities for complex objects.
    
    Provides enhanced serialization support beyond standard pickle.Pickler,
    including functions, classes, and other previously unpickleable types.
    """

class Unpickler:
    """
    Extended unpickler with additional capabilities for complex objects.
    
    Provides enhanced deserialization support beyond standard pickle.Unpickler,
    with improved error handling and type restoration.
    """
```

[Extended Pickler Classes](./pickler-classes.md)

### Session Management

Functions for saving and restoring complete interpreter sessions and individual modules, enabling persistence of development environments and interactive workflows.

```python { .api }
def dump_session(filename=None, main=None, byref=False, **kwds):
    """
    Save interpreter session to a file.
    
    Parameters:
    - filename: str, output filename (default: temporary file)
    - main: module, main module to save (default: __main__)
    - byref: bool, pickle by reference when possible
    - **kwds: additional keyword arguments
    
    Returns:
    None
    """

def load_session(filename=None, main=None, **kwds):
    """
    Load interpreter session from a file.
    
    Parameters:
    - filename: str, input filename
    - main: module, target module (default: __main__)
    - **kwds: additional keyword arguments
    
    Returns:
    None
    """

def dump_module(name=None, module=None, main=None, **kwds):
    """
    Save a module to a file.
    
    Parameters:
    - name: str, output filename
    - module: module, module object to save
    - main: module, main module context
    - **kwds: additional keyword arguments
    
    Returns:
    None
    """

def load_module(name=None, module=None, main=None, **kwds):
    """
    Load a module from a file.
    
    Parameters:
    - name: str, input filename
    - module: str, module name to load into
    - main: module, main module context
    - **kwds: additional keyword arguments
    
    Returns:
    module: loaded module object
    """
```

[Session Management](./session-management.md)

### Source Code Analysis

Tools for extracting, analyzing, and manipulating source code from Python objects, enabling introspection and code generation capabilities.

```python { .api }
def getsource(object, alias='', lstrip=False, enclosing=False, force=False, builtin=False):
    """
    Get source code for an object.
    
    Parameters:
    - object: object to get source for (module, class, method, function, traceback, frame, or code object)
    - alias: str, alias name for the object (adds line of code that renames the object)
    - lstrip: bool, ensure there is no indentation in the first line of code
    - enclosing: bool, include enclosing code and dependencies
    - force: bool, catch (TypeError,IOError) and try to use import hooks
    - builtin: bool, force an import for any builtins
    
    Returns:
    str: source code as single string
    
    Raises:
    - IOError: when source code cannot be retrieved
    - TypeError: for objects where source code is unavailable (e.g. builtins)
    """

def getimport(obj, alias='', verify=True, builtin=False, enclosing=False):
    """
    Get the likely import string for the given object.
    
    Parameters:
    - obj: object to inspect and generate import for
    - alias: str, alias name to use (renames the object on import)
    - verify: bool, test the import string before returning it
    - builtin: bool, force an import for builtins where possible
    - enclosing: bool, get the import for the outermost enclosing callable
    
    Returns:
    str: import statement as string
    """
```

[Source Code Analysis](./source-analysis.md)

### Diagnostic Tools

Utilities for analyzing serialization capabilities, identifying problems, and debugging pickling issues with detailed error reporting.

```python { .api }
def pickles(obj, exact=False, safe=False, **kwds):
    """
    Check if an object can be pickled.
    
    Parameters:
    - obj: object to test for pickling capability
    - exact: bool, use exact type matching for compatibility testing
    - safe: bool, use safe mode to avoid side effects during testing
    - **kwds: additional keyword arguments passed to dumps/loads
    
    Returns:
    bool: True if object can be pickled and unpickled successfully
    """

def check(obj, *args, **kwds):
    """
    Check for pickling errors and print diagnostic information.
    
    Parameters:
    - obj: object to check for pickling errors
    - *args: positional arguments passed to pickles()
    - **kwds: keyword arguments passed to pickles()
    
    Returns:
    bool: True if no errors found, False if pickling issues detected
    """

def baditems(obj, exact=False, safe=False):
    """
    Find objects that cannot be pickled within a complex structure.
    
    Parameters:
    - obj: object to analyze for unpickleable items
    - exact: bool, use exact type matching for analysis
    - safe: bool, use safe mode to avoid side effects
    
    Returns:
    list: list of unpickleable objects found in the structure
    """

def badobjects(obj, depth=0, exact=False, safe=False):
    """
    Get objects that fail to pickle.
    
    Parameters:
    - obj: object to analyze
    - depth: int, analysis depth (0 for immediate object only, >0 for recursive analysis)
    - exact: bool, use exact type matching
    - safe: bool, use safe mode to avoid side effects
    
    Returns:
    object or dict: at depth=0 returns the object if it fails to pickle (None if it pickles), 
    at depth>0 returns dict mapping attribute names to bad objects
    """

def errors(obj, depth=0, exact=False, safe=False):
    """
    Get detailed pickling error information.
    
    Parameters:
    - obj: object to analyze for errors
    - depth: int, analysis depth (0 for immediate object only, >0 for recursive analysis)
    - exact: bool, use exact type matching
    - safe: bool, use safe mode to avoid side effects
    
    Returns:
    Exception or dict: detailed error information for pickling failures
    """
```

[Diagnostic Tools](./diagnostic-tools.md)

### Type Registry System

Functions for registering custom types and extending dill's serialization capabilities to handle new object types.

```python { .api }
def register(t):
    """
    Register a type with the pickler.
    
    Parameters:
    - t: type, type to register
    
    Returns:
    function: decorator function
    """

def pickle(t, func):
    """
    Add a type to the pickle dispatch table.
    
    Parameters:
    - t: type, type to add
    - func: function, pickling function for the type
    
    Returns:
    None
    """

def extend(use_dill=True):
    """
    Add or remove dill types to/from the pickle registry.
    
    Parameters:
    - use_dill: bool, if True extend dispatch table, if False revert
    
    Returns:
    None
    """
```

[Type Registry System](./type-registry.md)

### Temporary Operations

Utilities for temporary file operations with serialization, stream capture, and IO buffer management for testing and development workflows.

```python { .api }
def dump(object, **kwds):
    """
    Dump object to a NamedTemporaryFile using dill.dump.
    
    Parameters:
    - object: object to serialize to temporary file
    - **kwds: optional keyword arguments including suffix, prefix, and NamedTemporaryFile options
    
    Returns:
    file handle: NamedTemporaryFile handle containing serialized object
    """

def load(file, **kwds):
    """
    Load an object that was stored with dill.temp.dump.
    
    Parameters:
    - file: file handle or str, file handle or path to file containing serialized object
    - **kwds: optional keyword arguments including mode ('r' or 'rb', default: 'rb')
    
    Returns:
    object: deserialized object
    """

def capture(stream='stdout'):
    """
    Capture stdout or stderr stream.
    
    Parameters:
    - stream: str, stream name ('stdout' or 'stderr')
    
    Returns:
    context manager for stream capture
    """
```

[Temporary Operations](./temp-operations.md)

### Configuration and Settings

Global configuration options and settings that control dill's behavior, protocol selection, and serialization modes.

```python { .api }
# Global settings dictionary
settings = {
    'protocol': DEFAULT_PROTOCOL,  # Default pickle protocol  
    'byref': False,               # Pickle by reference
    'fmode': 0,                   # File mode setting
    'recurse': False,             # Recursive pickling
    'ignore': False               # Ignore errors
}
```

[Configuration and Settings](./configuration.md)