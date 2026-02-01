# Diagnostic Tools

dill provides comprehensive diagnostic tools for analyzing serialization capabilities, identifying problematic objects, and debugging pickling issues with detailed error reporting and analysis.

## Core Diagnostic Functions

### Pickling Capability Testing

```python { .api }
def pickles(obj, exact=False, safe=False, **kwds):
    """
    Check if an object can be pickled.
    
    Tests whether an object can be successfully serialized and deserialized
    using dill, providing a simple boolean result for compatibility checking.
    
    Parameters:
    - obj: object to test for pickling capability
    - exact: bool, use exact type matching for compatibility testing
    - safe: bool, use safe mode to avoid side effects during testing
    - **kwds: additional keyword arguments passed to dumps/loads
    
    Returns:
    bool: True if object can be pickled and unpickled successfully
    
    Raises:
    - Exception: only when safe=False and testing encounters severe errors
    """

def check(obj, *args, **kwds):
    """
    Check for pickling errors and print diagnostic information.
    
    Performs comprehensive pickling analysis and displays detailed
    information about any issues encountered during serialization testing.
    
    Parameters:
    - obj: object to check for pickling errors
    - *args: positional arguments passed to pickles()
    - **kwds: keyword arguments passed to pickles()
    
    Returns:
    bool: True if no errors found, False if pickling issues detected
    """
```

### Problem Object Detection

```python { .api }
def baditems(obj, exact=False, safe=False):
    """
    Find objects that cannot be pickled within a complex structure.
    
    Recursively analyzes an object to identify specific items that
    prevent successful serialization, helping isolate problematic components.
    
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
    
    Analyzes object structure at specific depth levels to identify
    problematic objects that prevent serialization at different nesting levels.
    
    Parameters:
    - obj: object to analyze
    - depth: int, analysis depth (0 for immediate object only, >0 for recursive analysis)
    - exact: bool, use exact type matching
    - safe: bool, use safe mode to avoid side effects
    
    Returns:
    object or dict: at depth=0 returns the object if it fails to pickle (None if it pickles), 
    at depth>0 returns dict mapping attribute names to bad objects
    """

def badtypes(obj, depth=0, exact=False, safe=False):
    """
    Get types for objects that fail to pickle.
    
    Identifies specific types that cause pickling failures, providing
    type-level analysis of serialization compatibility issues.
    
    Parameters:
    - obj: object to analyze for problematic types
    - depth: int, analysis depth (0 for immediate object only, >0 for recursive analysis)
    - exact: bool, use exact type matching
    - safe: bool, use safe mode
    
    Returns:
    type or dict: at depth=0 returns the type if object fails to pickle (None if it pickles),
    at depth>0 returns dict mapping attribute names to problematic types
    """

def errors(obj, depth=0, exact=False, safe=False):
    """
    Get detailed pickling error information.
    
    Provides comprehensive error analysis including specific error messages,
    problematic objects, and suggested solutions for pickling failures.
    
    Parameters:
    - obj: object to analyze for errors
    - depth: int, maximum analysis depth (0 for unlimited)
    - exact: bool, use exact type matching
    - safe: bool, use safe mode to avoid side effects
    
    Returns:
    list: list of detailed error descriptions and diagnostic information
    """
```

## Usage Examples

### Basic Compatibility Testing

```python
import dill

# Test various object types
def test_function():
    return "Hello from function"

class TestClass:
    def __init__(self, value):
        self.value = value
    
    def method(self):
        return self.value * 2

# Test individual objects
print(dill.pickles(test_function))      # True
print(dill.pickles(TestClass))          # True
print(dill.pickles(TestClass(42)))      # True

# Test problematic objects
import threading
lock = threading.Lock()
print(dill.pickles(lock))               # False (locks can't be pickled)

# Use safe mode for testing
print(dill.pickles(dangerous_object, safe=True))
```

### Comprehensive Error Analysis

```python
import dill

# Complex object with potential issues
class ComplexObject:
    def __init__(self):
        self.data = [1, 2, 3]
        self.function = lambda x: x + 1
        self.lock = threading.Lock()  # Problematic
        self.nested = {
            'good': 'string',
            'bad': open('/dev/null', 'r')  # File handle - problematic
        }

complex_obj = ComplexObject()

# Quick check
if not dill.check(complex_obj):
    print("Object has pickling issues")
    
    # Find problematic items
    bad_items = dill.baditems(complex_obj)
    print(f"Found {len(bad_items)} unpickleable items:")
    for item in bad_items:
        print(f"  {type(item)}: {item}")
    
    # Get detailed error information
    error_details = dill.errors(complex_obj)
    print("\nDetailed errors:")
    for error in error_details:
        print(f"  {error}")
```

### Automated Testing Suite

```python
import dill

def comprehensive_pickle_test(obj, name="object"):
    """Comprehensive pickling analysis for an object."""
    print(f"\nTesting {name}...")
    print("=" * 50)
    
    # Basic pickling test
    can_pickle = dill.pickles(obj, safe=True)
    print(f"Can pickle: {can_pickle}")
    
    if not can_pickle:
        # Detailed analysis
        print("\nProblematic items:")
        bad_items = dill.baditems(obj, safe=True)
        for i, item in enumerate(bad_items):
            print(f"  {i+1}. {type(item).__name__}: {repr(item)[:50]}...")
        
        print("\nProblematic types:")
        bad_types = dill.badtypes(obj, safe=True)
        for i, bad_type in enumerate(bad_types):
            print(f"  {i+1}. {bad_type}")
        
        print("\nError details:")
        error_list = dill.errors(obj, safe=True)
        for i, error in enumerate(error_list):
            print(f"  {i+1}. {error}")
    
    return can_pickle

# Test various objects
test_objects = {
    'simple_function': lambda x: x + 1,
    'complex_class': ComplexObject(),
    'nested_structure': {'functions': [lambda x: x, lambda y: y**2]},
    'problematic_object': complex_obj
}

results = {}
for name, obj in test_objects.items():
    results[name] = comprehensive_pickle_test(obj, name)

print(f"\nSummary: {sum(results.values())}/{len(results)} objects can be pickled")
```

### Interactive Debugging Session

```python
import dill

def debug_pickling_issues(obj):
    """Interactive debugging for pickling issues."""
    print("Starting pickling diagnosis...")
    
    # Step 1: Basic test
    if dill.pickles(obj):
        print("✓ Object can be pickled successfully")
        return True
    
    print("✗ Object cannot be pickled")
    
    # Step 2: Identify bad items
    print("\nSearching for problematic items...")
    bad_items = dill.baditems(obj)
    
    if not bad_items:
        print("No specific bad items found - issue may be with object structure")
        return False
    
    print(f"Found {len(bad_items)} problematic items:")
    
    # Step 3: Categorize issues
    by_type = {}
    for item in bad_items:
        item_type = type(item).__name__
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(item)
    
    # Step 4: Provide solutions
    for item_type, items in by_type.items():
        print(f"\n{item_type} objects ({len(items)} found):")
        for i, item in enumerate(items[:3]):  # Show first 3
            print(f"  {i+1}. {repr(item)[:60]}...")
        
        # Suggest solutions
        if item_type == 'Lock':
            print("  → Solution: Remove locks or replace with serializable alternatives")
        elif item_type == 'TextIOWrapper':
            print("  → Solution: Close files or use file paths instead of handles")
        elif item_type == 'module':
            print("  → Solution: Import modules by name rather than storing references")
        else:
            print(f"  → Solution: Remove {item_type} objects or find serializable alternatives")
    
    return False

# Usage
debug_pickling_issues(problematic_object)
```

## Advanced Diagnostic Techniques

### Depth-Based Analysis

```python
import dill

def analyze_by_depth(obj, max_depth=5):
    """Analyze object pickling issues by depth level."""
    print("Depth-based analysis:")
    print("-" * 30)
    
    for depth in range(max_depth + 1):
        bad_objects = dill.badobjects(obj, depth=depth, safe=True)
        bad_types = dill.badtypes(obj, depth=depth, safe=True)
        
        print(f"Depth {depth}:")
        print(f"  Bad objects: {len(bad_objects)}")
        print(f"  Bad types: {len(set(t.__name__ for t in bad_types))}")
        
        if bad_objects:
            # Show sample bad objects at this depth
            sample = bad_objects[:2]
            for obj in sample:
                print(f"    {type(obj).__name__}: {repr(obj)[:40]}...")

# Usage
analyze_by_depth(complex_nested_object)
```

### Custom Diagnostic Rules

```python
import dill

class PicklingDiagnostic:
    """Custom diagnostic tool for pickling analysis."""
    
    def __init__(self):
        self.rules = {
            'file_handles': lambda obj: hasattr(obj, 'read') and hasattr(obj, 'write'),
            'locks': lambda obj: hasattr(obj, 'acquire') and hasattr(obj, 'release'),
            'generators': lambda obj: hasattr(obj, '__next__') and hasattr(obj, '__iter__'),
            'lambda_functions': lambda obj: callable(obj) and obj.__name__ == '<lambda>',
        }
    
    def diagnose(self, obj):
        """Run custom diagnostic rules."""
        issues = {}
        
        # Test overall pickling
        can_pickle = dill.pickles(obj, safe=True)
        issues['can_pickle'] = can_pickle
        
        if can_pickle:
            return issues
        
        # Run custom rules
        bad_items = dill.baditems(obj, safe=True)
        
        for rule_name, rule_func in self.rules.items():
            matching_items = [item for item in bad_items if rule_func(item)]
            if matching_items:
                issues[rule_name] = matching_items
        
        return issues
    
    def report(self, obj, name="object"):
        """Generate diagnostic report."""
        issues = self.diagnose(obj)
        
        print(f"Diagnostic Report for {name}")
        print("=" * 40)
        
        if issues.get('can_pickle', False):
            print("✓ Object can be pickled successfully")
            return
        
        print("✗ Object cannot be pickled")
        print("\nIssues found:")
        
        for issue_type, items in issues.items():
            if issue_type == 'can_pickle':
                continue
            
            print(f"\n{issue_type.replace('_', ' ').title()}:")
            for item in items[:3]:  # Show first 3
                print(f"  - {type(item).__name__}: {repr(item)[:50]}...")

# Usage
diagnostic = PicklingDiagnostic()
diagnostic.report(complex_object, "MyComplexObject")
```

### Performance Impact Analysis

```python
import dill
import time

def performance_diagnostic(obj, name="object"):
    """Analyze performance impact of pickling."""
    print(f"Performance analysis for {name}")
    print("-" * 40)
    
    # Test if object can be pickled
    if not dill.pickles(obj, safe=True):
        print("Object cannot be pickled - skipping performance test")
        return
    
    # Measure serialization time
    start_time = time.time()
    serialized = dill.dumps(obj)
    serialize_time = time.time() - start_time
    
    # Measure deserialization time
    start_time = time.time()
    dill.loads(serialized)
    deserialize_time = time.time() - start_time
    
    # Report results
    print(f"Serialization time: {serialize_time:.4f} seconds")
    print(f"Deserialization time: {deserialize_time:.4f} seconds")
    print(f"Serialized size: {len(serialized):,} bytes")
    print(f"Compression ratio: {len(str(obj).encode()) / len(serialized):.2f}x")

# Usage with different objects
performance_diagnostic(large_data_structure, "Large Data Structure")
performance_diagnostic(complex_function, "Complex Function")
performance_diagnostic(class_instance, "Class Instance")
```

## Integration with Development Workflow

### Pre-commit Pickling Validation

```python
import dill
import sys

def validate_pickling(modules_to_test):
    """Validate that key objects can be pickled before commit."""
    print("Running pickling validation...")
    
    failed_objects = []
    
    for module_name in modules_to_test:
        try:
            module = __import__(module_name)
            
            # Test key objects in module
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    obj = getattr(module, attr_name)
                    
                    if callable(obj) or hasattr(obj, '__dict__'):
                        if not dill.pickles(obj, safe=True):
                            failed_objects.append(f"{module_name}.{attr_name}")
        
        except ImportError:
            print(f"Could not import {module_name}")
    
    if failed_objects:
        print("❌ Pickling validation failed for:")
        for obj in failed_objects:
            print(f"  - {obj}")
        return False
    else:
        print("✓ All objects pass pickling validation")
        return True

# Usage in CI/CD pipeline
if __name__ == "__main__":
    modules = ["mypackage.core", "mypackage.utils", "mypackage.models"]
    success = validate_pickling(modules)
    sys.exit(0 if success else 1)
```