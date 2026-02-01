# Source Code Analysis

dill provides powerful tools for extracting, analyzing, and manipulating source code from Python objects, enabling introspection, code generation, and dynamic analysis capabilities.

## Source Code Extraction

### Primary Source Functions

```python { .api }
def getsource(object, alias='', lstrip=False, enclosing=False, force=False, builtin=False):
    """
    Get source code for an object.
    
    Extracts the source code of functions, classes, methods, and other
    code objects, providing string representation of the original code.
    The source code for interactively-defined objects are extracted from
    the interpreter's history.
    
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

def getsourcelines(object, lstrip=False, enclosing=False):
    """
    Get source lines for an object.
    
    Returns the source code as a list of lines along with the starting
    line number in the original file.
    
    Parameters:
    - object: object to get source lines for
    - lstrip: bool, left-strip whitespace from source lines
    - enclosing: bool, include enclosing scope
    
    Returns:
    tuple: (list of source lines, starting line number)
    
    Raises:
    - OSError: when source cannot be found
    """

def findsource(object):
    """
    Find source code for an object.
    
    Locate the source code for an object by examining the file system,
    module imports, and other available sources.
    
    Parameters:
    - object: object to find source for
    
    Returns:
    tuple: (list of all source lines, starting line number)
    
    Raises:
    - OSError: when source cannot be located
    """
```

### Source Code Utilities

```python { .api }
def getblocks(object, lstrip=False, enclosing=False, locate=False):
    """
    Get code blocks for an object.
    
    Extracts logical code blocks (functions, classes, methods) associated
    with an object, providing structured access to code components.
    
    Parameters:
    - object: object to get code blocks for
    - lstrip: bool, left-strip whitespace from blocks
    - enclosing: bool, include enclosing blocks
    - locate: bool, include location information
    
    Returns:
    list: list of code blocks with metadata
    """

def dumpsource(object, alias='', new=False, enclose=True):
    """
    Dump source code with additional metadata.
    
    Creates a comprehensive source dump including dependencies,
    imports, and context information needed for code reconstruction.
    
    Parameters:
    - object: object to dump source for
    - alias: str, alias name for the object
    - new: bool, create new-style source dump format
    - enclose: bool, enclose source with additional context
    
    Returns:
    str: comprehensive source dump
    """
```

## Import Analysis

### Import Statement Generation

```python { .api }
def getimport(obj, alias='', verify=True, builtin=False, enclosing=False):
    """
    Get the likely import string for the given object.
    
    Generates the appropriate import statement needed to access an object,
    including module path resolution and alias handling.
    
    Parameters:
    - obj: object to inspect and generate import for
    - alias: str, alias name to use (renames the object on import)
    - verify: bool, test the import string before returning it
    - builtin: bool, force an import for builtins where possible
    - enclosing: bool, get the import for the outermost enclosing callable
    
    Returns:
    str: import statement as string
    """

def getimportable(obj, alias='', byname=True, explicit=False):
    """
    Get importable representation of an object.
    
    Creates a representation that can be used to recreate the object
    through import statements and attribute access.
    
    Parameters:
    - obj: object to make importable
    - alias: str, alias name to use
    - byname: bool, prefer name-based imports over direct references
    - explicit: bool, use explicit import paths
    
    Returns:
    str: importable representation
    """

def likely_import(obj, passive=False, explicit=False):
    """
    Get likely import statement for an object.
    
    Attempts to determine the most likely import statement that would
    provide access to the given object.
    
    Parameters:
    - obj: object to analyze
    - passive: bool, use passive analysis without side effects
    - explicit: bool, prefer explicit import statements
    
    Returns:
    str: likely import statement
    """
```

### Object Identification

```python { .api }
def getname(obj, force=False, fqn=False):
    """
    Get the name of an object.
    
    Attempts to determine the canonical name of an object by examining
    its attributes, module context, and definition location.
    
    Parameters:
    - obj: object to get name for
    - force: bool, force name extraction even if not directly available
    - fqn: bool, return fully qualified name including module path
    
    Returns:
    str: object name or None if name cannot be determined
    """

def isfrommain(obj):
    """
    Check if object is from __main__ module.
    
    Determines whether an object originates from the main module,
    which affects how it should be serialized and imported.
    
    Parameters:
    - obj: object to check
    
    Returns:
    bool: True if object is from __main__ module
    """

def isdynamic(obj):
    """
    Check if object is dynamically created.
    
    Determines whether an object was created dynamically at runtime
    rather than being defined in source code.
    
    Parameters:
    - obj: object to check
    
    Returns:
    bool: True if object is dynamically created
    """
```

## Usage Examples

### Basic Source Extraction

```python
import dill.source as source

# Define a function
def example_function(x, y=10):
    """Example function with default parameter."""
    result = x + y
    return result * 2

# Get source code
source_code = source.getsource(example_function)
print(source_code)
# Output: Full function definition as string

# Get source lines with line numbers
lines, start_line = source.getsourcelines(example_function)
print(f"Function starts at line {start_line}")
for i, line in enumerate(lines):
    print(f"{start_line + i}: {line.rstrip()}")
```

### Advanced Source Analysis

```python
import dill.source as source

class ExampleClass:
    """Example class for source analysis."""
    
    def __init__(self, value):
        self.value = value
    
    def method(self, multiplier=2):
        return self.value * multiplier
    
    @staticmethod
    def static_method(x):
        return x ** 2

# Analyze class source
class_source = source.getsource(ExampleClass)
print("Class source:")
print(class_source)

# Get method source separately
method_source = source.getsource(ExampleClass.method)
print("\nMethod source:")
print(method_source)

# Get source blocks
blocks = source.getblocks(ExampleClass)
print(f"\nFound {len(blocks)} code blocks in class")
```

### Import Generation

```python
import dill.source as source
import json
from collections import defaultdict

# Generate import statements for various objects
objects_to_import = [
    json.dumps,
    defaultdict,
    ExampleClass,
    example_function
]

for obj in objects_to_import:
    try:
        import_stmt = source.getimport(obj)
        name = source.getname(obj) or str(obj)
        print(f"{name}: {import_stmt}")
    except Exception as e:
        print(f"Could not generate import for {obj}: {e}")

# Generate imports with aliases
alias_import = source.getimport(json.dumps, alias='json_serialize')
print(f"With alias: {alias_import}")
```

### Dynamic Code Analysis

```python
import dill.source as source

# Create dynamic function
exec('''
def dynamic_function(x):
    return x * 3 + 1
''')

# Analyze dynamic objects
if source.isdynamic(dynamic_function):
    print("Function was created dynamically")

if source.isfrommain(dynamic_function):
    print("Function is from __main__ module")

# Try to get source of dynamic function
try:
    dynamic_source = source.getsource(dynamic_function)
    print("Dynamic function source:")
    print(dynamic_source)
except OSError:
    print("Cannot get source for dynamic function")
```

### Source Code Modification

```python
import dill.source as source

def modify_function_source(func, modifications):
    """Modify function source code."""
    try:
        # Get original source
        original_source = source.getsource(func)
        
        # Apply modifications
        modified_source = original_source
        for old, new in modifications.items():
            modified_source = modified_source.replace(old, new)
        
        # Create new function from modified source
        namespace = {}
        exec(modified_source, namespace)
        
        # Find the function in the namespace
        func_name = source.getname(func)
        if func_name in namespace:
            return namespace[func_name]
        
        return None
    
    except Exception as e:
        print(f"Failed to modify function: {e}")
        return None

# Example usage
def original_add(a, b):
    return a + b

# Modify to multiply instead
modifications = {'a + b': 'a * b'}
modified_func = modify_function_source(original_add, modifications)

if modified_func:
    print(f"Original: {original_add(3, 4)}")  # 7
    print(f"Modified: {modified_func(3, 4)}")  # 12
```

## Advanced Features

### Source Code Archival

```python
import dill.source as source
import json

def archive_source_code(objects, filename):
    """Archive source code for multiple objects."""
    archive = {}
    
    for name, obj in objects.items():
        try:
            obj_info = {
                'source': source.getsource(obj),
                'import': source.getimport(obj, verify=False),
                'name': source.getname(obj),
                'is_dynamic': source.isdynamic(obj),
                'is_from_main': source.isfrommain(obj)
            }
            archive[name] = obj_info
        except Exception as e:
            archive[name] = {'error': str(e)}
    
    with open(filename, 'w') as f:
        json.dump(archive, f, indent=2)
    
    return archive

# Archive important functions and classes
objects_to_archive = {
    'example_function': example_function,
    'ExampleClass': ExampleClass,
    'json_dumps': json.dumps
}

archive = archive_source_code(objects_to_archive, 'source_archive.json')
print(f"Archived {len(archive)} objects")
```

### Code Dependency Analysis

```python
import dill.source as source
import dill.detect as detect
import ast

def analyze_dependencies(func):
    """Analyze function dependencies."""
    try:
        # Get source code
        source_code = source.getsource(func)
        
        # Parse AST
        tree = ast.parse(source_code)
        
        # Find imports and name references
        dependencies = {
            'imports': [],
            'globals': [],
            'builtins': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies['imports'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    dependencies['imports'].append(f"{module}.{alias.name}")
        
        # Get global variables referenced
        global_vars = detect.referredglobals(func, recurse=True)
        dependencies['globals'] = list(global_vars.keys())
        
        return dependencies
    
    except Exception as e:
        return {'error': str(e)}

# Analyze function dependencies
deps = analyze_dependencies(example_function)
print("Function dependencies:")
for dep_type, items in deps.items():
    if items:
        print(f"  {dep_type}: {items}")
```

### Interactive Source Browser

```python
import dill.source as source

class SourceBrowser:
    """Interactive source code browser."""
    
    def __init__(self):
        self.history = []
    
    def browse(self, obj):
        """Browse source code for an object."""
        try:
            obj_name = source.getname(obj) or str(obj)
            self.history.append(obj_name)
            
            print(f"\n{'='*60}")
            print(f"Source for {obj_name}")
            print(f"{'='*60}")
            
            # Show basic info
            print(f"Type: {type(obj).__name__}")
            print(f"From main: {source.isfrommain(obj)}")
            print(f"Dynamic: {source.isdynamic(obj)}")
            
            # Show import statement
            try:
                import_stmt = source.getimport(obj, verify=False)
                print(f"Import: {import_stmt}")
            except:
                print("Import: Not available")
            
            print(f"\nSource code:")
            print("-" * 40)
            
            # Show source
            source_code = source.getsource(obj)
            print(source_code)
            
        except Exception as e:
            print(f"Error browsing {obj}: {e}")
    
    def show_history(self):
        """Show browsing history."""
        print("\nBrowsing history:")
        for i, item in enumerate(self.history):
            print(f"  {i+1}. {item}")

# Usage
browser = SourceBrowser()
browser.browse(example_function)
browser.browse(ExampleClass)
browser.show_history()
```

## Integration with Serialization

### Source-Aware Pickling

```python
import dill
import dill.source as source

def pickle_with_source(obj, filename):
    """Pickle object along with its source code."""
    # Create enhanced object with source
    enhanced_obj = {
        'object': obj,
        'metadata': {
            'source': None,
            'import': None,
            'name': source.getname(obj),
            'type': type(obj).__name__
        }
    }
    
    # Try to get source and import info
    try:
        enhanced_obj['metadata']['source'] = source.getsource(obj)
    except:
        pass
    
    try:
        enhanced_obj['metadata']['import'] = source.getimport(obj, verify=False)
    except:
        pass
    
    # Pickle enhanced object
    with open(filename, 'wb') as f:
        dill.dump(enhanced_obj, f)

def unpickle_with_source(filename):
    """Unpickle object and display source information."""
    with open(filename, 'rb') as f:
        enhanced_obj = dill.load(f)
    
    obj = enhanced_obj['object']
    metadata = enhanced_obj['metadata']
    
    print(f"Loaded {metadata['type']}: {metadata['name']}")
    
    if metadata['import']:
        print(f"Import: {metadata['import']}")
    
    if metadata['source']:
        print("Source code:")
        print(metadata['source'])
    
    return obj

# Usage
pickle_with_source(example_function, 'function_with_source.pkl')
restored_func = unpickle_with_source('function_with_source.pkl')
```