# Session Management

dill provides powerful capabilities for saving and restoring complete interpreter sessions and individual modules, enabling persistence of development environments, interactive workflows, and computational state.

## Session Operations

### Complete Session Management

```python { .api }
def dump_session(filename=None, main=None, byref=False, **kwds):
    """
    Save complete interpreter session to a file (deprecated).
    
    DEPRECATED: This function has been renamed to dump_module().
    Captures the entire state of the Python interpreter including all
    variables, functions, classes, and imported modules from the main namespace.
    
    Parameters:
    - filename: str, output filename (default: auto-generated in temp directory)
    - main: module, main module to save (default: __main__ module)
    - byref: bool, pickle objects by reference when possible
    - **kwds: additional keyword arguments passed to dump_module
    
    Returns:
    None
    
    Raises:
    - PicklingError: when session cannot be serialized
    - IOError: when file operations fail
    """

def load_session(filename=None, main=None, **kwds):
    """
    Load complete interpreter session from a file (deprecated).
    
    DEPRECATED: This function has been renamed to load_module().
    Restores the entire state of a Python interpreter session including
    all variables, functions, classes, and module dependencies.
    
    Parameters:
    - filename: str, input filename to load from
    - main: module, target module to restore into (default: __main__)
    - **kwds: additional keyword arguments passed to load_module
    
    Returns:
    None (modifies current interpreter state)
    
    Raises:
    - UnpicklingError: when session cannot be deserialized
    - IOError: when file operations fail
    """
```

### Individual Module Management

```python { .api }
def dump_module(filename=None, module=None, refimported=False, **kwds):
    """
    Save a specific module to a file.
    
    Serializes a module's complete state including all attributes,
    functions, classes, and internal variables while preserving
    cross-module references.
    
    Parameters:
    - filename: str or PathLike, output filename for module dump
    - module: module or str, specific module object to save (default: __main__)
    - refimported: bool, save imported modules by reference when possible
    - **kwds: additional keyword arguments passed to Pickler
    
    Returns:
    None
    
    Raises:
    - PicklingError: when module cannot be serialized
    - IOError: when file operations fail
    """

def load_module(name=None, module=None, main=None, **kwds):
    """
    Load a module from a file.
    
    Restores a module's complete state and integrates it into the
    current interpreter environment with proper reference resolution.
    
    Parameters:
    - name: str, input filename containing module dump
    - module: str, name for the restored module in sys.modules
    - main: module, main module context for integration
    - **kwds: additional keyword arguments passed to Unpickler
    
    Returns:
    module: loaded module object
    
    Raises:
    - UnpicklingError: when module cannot be deserialized
    - IOError: when file operations fail
    """

def load_module_asdict(name=None, main=None, **kwds):
    """
    Load a module from a file as a dictionary.
    
    Restores module contents as a dictionary rather than a module object,
    useful for inspecting module contents without side effects.
    
    Parameters:
    - name: str, input filename containing module dump
    - main: module, main module context for reference resolution
    - **kwds: additional keyword arguments passed to load_module
    
    Returns:
    dict: module contents as dictionary
    
    Raises:
    - UnpicklingError: when module cannot be deserialized
    - IOError: when file operations fail
    """
```

## Usage Examples

### Interactive Session Persistence

```python
import dill

# During interactive session, define some variables and functions
x = 42
data = [1, 2, 3, 4, 5]

def process_data(items):
    return [item * 2 for item in items]

class DataProcessor:
    def __init__(self, multiplier=1):
        self.multiplier = multiplier
    
    def process(self, data):
        return [x * self.multiplier for x in data]

processor = DataProcessor(3)

# Save entire session
dill.dump_session('my_analysis_session.pkl')

# Later, in a new Python session:
import dill
dill.load_session('my_analysis_session.pkl')

# All variables and functions are now available
result = process_data(data)  # [2, 4, 6, 8, 10]
processed = processor.process(data)  # [3, 6, 9, 12, 15]
```

### Module-specific Operations

```python
import dill
import mymodule

# Save specific module
dill.dump_module('mymodule_backup.pkl', module=mymodule)

# Modify module during development
mymodule.some_function = lambda x: x * 10

# Restore original module state
original_module = dill.load_module('mymodule_backup.pkl')
```

### Development Workflow Integration

```python
import dill
import sys

# Save current development state
def save_checkpoint(name):
    """Save current session as a development checkpoint."""
    filename = f'checkpoint_{name}.pkl'
    dill.dump_session(filename)
    print(f"Session saved to {filename}")

def load_checkpoint(name):
    """Load a development checkpoint."""
    filename = f'checkpoint_{name}.pkl'
    dill.load_session(filename)
    print(f"Session loaded from {filename}")

# Usage in development
save_checkpoint('before_experiment')

# Run experiments, make changes...

# Restore if needed
load_checkpoint('before_experiment')
```

### Module Inspection

```python
import dill

# Load module as dictionary for inspection
module_dict = dill.load_module_asdict('saved_module.pkl')

# Inspect contents without side effects
print("Module contents:")
for name, obj in module_dict.items():
    if not name.startswith('_'):
        print(f"  {name}: {type(obj)}")

# Selectively restore specific items
my_function = module_dict.get('my_function')
if my_function:
    # Use the function without restoring entire module
    result = my_function(input_data)
```

## Advanced Features

### Session Filtering

```python
import dill

# Custom session dumping with filtering
def dump_filtered_session(filename, exclude_patterns=None):
    """Dump session excluding certain patterns."""
    import __main__
    
    # Get current main module
    main_dict = __main__.__dict__.copy()
    
    # Filter out unwanted items
    if exclude_patterns:
        filtered_dict = {}
        for name, obj in main_dict.items():
            if not any(pattern in name for pattern in exclude_patterns):
                filtered_dict[name] = obj
        
        # Temporarily replace main dict
        original_dict = __main__.__dict__
        __main__.__dict__ = filtered_dict
        
        try:
            dill.dump_session(filename)
        finally:
            __main__.__dict__ = original_dict
    else:
        dill.dump_session(filename)

# Usage
dump_filtered_session('clean_session.pkl', exclude_patterns=['_temp', 'debug_'])
```

### Cross-Environment Session Transfer

```python
import dill
import sys
import os

# Save session with environment info
def save_portable_session(filename):
    """Save session with environment metadata."""
    # Save session
    dill.dump_session(filename)
    
    # Save environment info
    env_info = {
        'python_version': sys.version,
        'platform': sys.platform,
        'path': sys.path.copy(),
        'modules': list(sys.modules.keys()),
        'cwd': os.getcwd()
    }
    
    env_filename = filename.replace('.pkl', '_env.pkl')
    with open(env_filename, 'wb') as f:
        dill.dump(env_info, f)

def load_portable_session(filename):
    """Load session with environment validation."""
    # Load environment info
    env_filename = filename.replace('.pkl', '_env.pkl')
    
    try:
        with open(env_filename, 'rb') as f:
            env_info = dill.load(f)
        
        # Validate compatibility
        if env_info['python_version'] != sys.version:
            print(f"Warning: Python version mismatch")
            print(f"  Saved: {env_info['python_version']}")
            print(f"  Current: {sys.version}")
        
        # Load session
        dill.load_session(filename)
        
    except FileNotFoundError:
        print("Environment info not found, loading session anyway...")
        dill.load_session(filename)
```

## Integration with Development Tools

### Jupyter Notebook Integration

```python
# In Jupyter notebook cells
import dill

# Save notebook state
def save_notebook_session():
    """Save current notebook session."""
    dill.dump_session('notebook_session.pkl')
    print("Notebook session saved")

def load_notebook_session():
    """Load notebook session."""
    dill.load_session('notebook_session.pkl')
    print("Notebook session loaded")

# Magic command integration (requires IPython)
from IPython.core.magic import register_line_magic

@register_line_magic
def save_dill(line):
    """Magic command to save session."""
    filename = line.strip() or 'session.pkl'
    dill.dump_session(filename)
    print(f"Session saved to {filename}")

@register_line_magic  
def load_dill(line):
    """Magic command to load session."""
    filename = line.strip() or 'session.pkl'
    dill.load_session(filename)
    print(f"Session loaded from {filename}")

# Usage: %save_dill my_session.pkl
```

## Best Practices

### Session Management Guidelines

- **Regular Checkpoints**: Save session state before major experiments or changes
- **Descriptive Naming**: Use meaningful filenames that describe the session state
- **Environment Documentation**: Include metadata about the environment when sharing sessions
- **Selective Restoration**: Use `load_module_asdict` to inspect before full restoration
- **Clean-up**: Remove temporary variables before saving to reduce file size

### Performance Considerations

- **Large Sessions**: Break down large sessions into smaller, focused modules
- **Memory Usage**: Be aware that session files can be large for complex environments
- **Loading Time**: Session restoration can take time for environments with many dependencies
- **Cross-platform**: Test session files across different platforms if portability is needed