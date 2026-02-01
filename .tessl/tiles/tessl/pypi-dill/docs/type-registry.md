# Type Registry System

dill provides a flexible type registry system that allows registration of custom types and extension of serialization capabilities to handle new object types that are not supported by default.

## Core Registry Functions

### Type Registration

```python { .api }
def register(t):
    """
    Register a type with the pickler.
    
    Decorator function that registers a custom pickling function for a specific
    type, allowing dill to handle objects of that type during serialization.
    
    Parameters:
    - t: type, the type to register for custom pickling
    
    Returns:
    function: decorator function that takes the pickling function
    
    Usage:
    @dill.register(MyCustomType)
    def save_custom_type(pickler, obj):
        # Custom pickling logic
        pass
    """

def pickle(t, func):
    """
    Add a type to the pickle dispatch table.
    
    Directly associates a type with a pickling function in the dispatch table,
    enabling automatic handling of objects of that type.
    
    Parameters:
    - t: type, the type to add to dispatch table
    - func: function, pickling function that handles objects of type t
    
    Returns:
    None
    
    Raises:
    - TypeError: when type or function parameters are invalid
    """

def extend(use_dill=True):
    """
    Add or remove dill types to/from the pickle registry.
    
    Controls whether dill's extended types are available in the standard
    pickle module's dispatch table, allowing integration with existing code.
    
    Parameters:
    - use_dill: bool, if True extend dispatch table with dill types,
                     if False revert to standard pickle types only
    
    Returns:
    None
    """
```

### Registry Inspection

```python { .api }  
def dispatch_table():
    """
    Get the current dispatch table.
    
    Returns the current pickle dispatch table showing all registered
    types and their associated pickling functions.
    
    Returns:
    dict: mapping of types to pickling functions
    """
```

## Usage Examples

### Basic Type Registration

```python
import dill

# Define a custom class
class CustomData:
    def __init__(self, data, metadata=None):
        self.data = data
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"CustomData({self.data}, {self.metadata})"

# Register custom pickling function using decorator
@dill.register(CustomData)
def save_custom_data(pickler, obj):
    """Custom pickling function for CustomData objects."""
    # Save the class reference
    pickler.save_reduce(_restore_custom_data, 
                       (obj.data, obj.metadata), obj=obj)

def _restore_custom_data(data, metadata):
    """Helper function to restore CustomData objects."""
    return CustomData(data, metadata)

# Test the registration
custom_obj = CustomData([1, 2, 3], {"version": "1.0"})

# Now it can be pickled
serialized = dill.dumps(custom_obj)
restored = dill.loads(serialized)

print(f"Original: {custom_obj}")
print(f"Restored: {restored}")
```

### Direct Dispatch Table Modification

```python
import dill

class SpecialContainer:
    def __init__(self, items):
        self.items = list(items)
    
    def __eq__(self, other):
        return isinstance(other, SpecialContainer) and self.items == other.items

def pickle_special_container(pickler, obj):
    """Pickling function for SpecialContainer."""
    # Use pickle protocol to save class and items
    pickler.save_reduce(SpecialContainer, (obj.items,), obj=obj)

# Add to dispatch table directly
dill.pickle(SpecialContainer, pickle_special_container)

# Test the registration
container = SpecialContainer([1, 2, 3, 4])
pickled_data = dill.dumps(container)
unpickled_container = dill.loads(pickled_data)

print(f"Original == Restored: {container == unpickled_container}")
```

### Complex Type Registration

```python
import dill
import weakref

class Node:
    """Tree node with parent/child relationships."""
    def __init__(self, value, parent=None):
        self.value = value
        self.children = []
        self._parent_ref = None
        if parent:
            self.set_parent(parent)
    
    def set_parent(self, parent):
        if self._parent_ref:
            old_parent = self._parent_ref()
            if old_parent:
                old_parent.children.remove(self)
        
        self._parent_ref = weakref.ref(parent) if parent else None
        if parent:
            parent.children.append(self)
    
    @property
    def parent(self):
        return self._parent_ref() if self._parent_ref else None

# Register complex type with custom handling
@dill.register(Node)
def save_node(pickler, obj):
    """Custom pickling for Node objects."""
    # Save value and children (parent will be reconstructed)
    pickler.save_reduce(_restore_node, 
                       (obj.value, obj.children), obj=obj)

def _restore_node(value, children):
    """Restore Node with proper parent/child relationships."""
    node = Node(value)
    
    # Restore children and set parent relationships
    for child in children:
        if isinstance(child, Node):
            child.set_parent(node)
        else:
            # Handle case where child was also pickled/unpickled
            node.children.append(child)
    
    return node

# Test complex type registration
root = Node("root")
child1 = Node("child1", root)
child2 = Node("child2", root)
grandchild = Node("grandchild", child1)

# Pickle the entire tree
tree_data = dill.dumps(root)
restored_root = dill.loads(tree_data)

print(f"Root children: {[child.value for child in restored_root.children]}")
print(f"Child1 parent: {restored_root.children[0].parent.value}")
```

### Registry Management

```python
import dill

class RegistryManager:
    """Manage custom type registrations."""
    
    def __init__(self):
        self.registered_types = {}
        self.original_dispatch = None
    
    def register_type(self, type_class, save_func, restore_func=None):
        """Register a type with save and optional restore functions."""
        if restore_func:
            # Store restore function for later use
            self.registered_types[type_class] = {
                'save': save_func,
                'restore': restore_func
            }
            
            # Create wrapper that includes restore function
            def save_wrapper(pickler, obj):
                pickler.save_reduce(restore_func, save_func(obj), obj=obj)
            
            dill.register(type_class)(save_wrapper)
        else:
            # Direct registration
            dill.register(type_class)(save_func)
            self.registered_types[type_class] = {'save': save_func}
    
    def unregister_type(self, type_class):
        """Remove type from registry."""
        if type_class in self.registered_types:
            # Remove from dill's dispatch table
            dispatch = dill.dispatch_table()
            if type_class in dispatch:
                del dispatch[type_class]
            
            del self.registered_types[type_class]
    
    def list_registered_types(self):
        """List all registered custom types."""
        return list(self.registered_types.keys())
    
    def backup_dispatch_table(self):
        """Backup current dispatch table."""
        self.original_dispatch = dill.dispatch_table().copy()
    
    def restore_dispatch_table(self):
        \"\"\"Restore original dispatch table.\"\"\"
        if self.original_dispatch:
            current_dispatch = dill.dispatch_table()
            current_dispatch.clear()
            current_dispatch.update(self.original_dispatch)

# Usage example
registry = RegistryManager()

# Backup original state
registry.backup_dispatch_table()

# Register multiple types
registry.register_type(
    CustomData,
    lambda obj: (obj.data, obj.metadata),
    lambda data, meta: CustomData(data, meta)
)

registry.register_type(
    SpecialContainer,
    lambda obj: (obj.items,),
    lambda items: SpecialContainer(items)
)

print(f"Registered types: {[t.__name__ for t in registry.list_registered_types()]}")

# Test registrations
test_objects = [
    CustomData([1, 2, 3], {"test": True}),
    SpecialContainer(["a", "b", "c"])
]

for obj in test_objects:
    try:
        data = dill.dumps(obj)
        restored = dill.loads(data)
        print(f"✓ {type(obj).__name__}: Successfully pickled and restored")
    except Exception as e:
        print(f"✗ {type(obj).__name__}: Failed - {e}")

# Clean up
registry.restore_dispatch_table()
```

## Advanced Registry Techniques

### Conditional Type Registration

```python
import dill
import sys

class ConditionalRegistry:
    """Register types based on conditions."""
    
    @staticmethod
    def register_if_available(type_name, module_name, save_func, restore_func=None):
        """Register type only if module is available."""
        try:
            module = __import__(module_name)
            type_class = getattr(module, type_name)
            
            if restore_func:
                def save_wrapper(pickler, obj):
                    pickler.save_reduce(restore_func, save_func(obj), obj=obj)
                dill.register(type_class)(save_wrapper)
            else:
                dill.register(type_class)(save_func)
            
            print(f"✓ Registered {type_name} from {module_name}")
            return True
            
        except (ImportError, AttributeError) as e:
            print(f"✗ Could not register {type_name}: {e}")
            return False
    
    @staticmethod
    def register_for_python_version(min_version, type_class, save_func):
        """Register type only for specific Python versions."""
        if sys.version_info >= min_version:
            dill.register(type_class)(save_func)
            print(f"✓ Registered {type_class.__name__} for Python {sys.version_info[:2]}")
            return True
        else:
            print(f"✗ Skipped {type_class.__name__} - requires Python {min_version}")
            return False

# Example usage
registry = ConditionalRegistry()

# Register numpy array if numpy is available
registry.register_if_available(
    'ndarray', 'numpy',
    lambda obj: (obj.tobytes(), obj.dtype, obj.shape),
    lambda data, dtype, shape: __import__('numpy').frombuffer(data, dtype).reshape(shape)
)

# Register pathlib.Path for Python 3.4+
import pathlib
registry.register_for_python_version(
    (3, 4),
    pathlib.Path,
    lambda obj: str(obj)
)
```

### Dynamic Type Discovery

```python
import dill
import inspect

class AutoRegistry:
    """Automatically discover and register types."""
    
    def __init__(self):
        self.auto_registered = set()
    
    def auto_register_module(self, module, save_pattern=None, exclude=None):
        """Automatically register types from a module."""
        exclude = exclude or []
        registered_count = 0
        
        for name, obj in inspect.getmembers(module):
            # Skip private and excluded items
            if name.startswith('_') or name in exclude:
                continue
            
            # Only register classes
            if inspect.isclass(obj):
                # Check if we can create a default save function
                if self._can_auto_register(obj):
                    self._auto_register_type(obj)
                    registered_count += 1
        
        print(f\"Auto-registered {registered_count} types from {module.__name__}\")\n        return registered_count\n    \n    def _can_auto_register(self, type_class):\n        \"\"\"Check if type can be auto-registered.\"\"\"\n        try:\n            # Check if type has __dict__ or __slots__\n            if hasattr(type_class, '__dict__') or hasattr(type_class, '__slots__'):\n                return True\n            \n            # Check if it's a simple dataclass-like structure\n            if hasattr(type_class, '__init__'):\n                sig = inspect.signature(type_class.__init__)\n                # Simple heuristic: if all parameters have defaults or annotations\n                return len(sig.parameters) <= 5  # Reasonable limit\n        \n        except Exception:\n            pass\n        \n        return False\n    \n    def _auto_register_type(self, type_class):\n        \"\"\"Automatically register a type with default behavior.\"\"\"\n        if type_class in self.auto_registered:\n            return\n        \n        def auto_save_func(pickler, obj):\n            # Generic save function using __dict__ or __getstate__\n            if hasattr(obj, '__getstate__'):\n                state = obj.__getstate__()\n                pickler.save_reduce(_auto_restore_with_state, \n                                  (type_class, state), obj=obj)\n            elif hasattr(obj, '__dict__'):\n                pickler.save_reduce(_auto_restore_with_dict,\n                                  (type_class, obj.__dict__), obj=obj)\n            else:\n                # Fallback to trying __reduce__\n                pickler.save_reduce(type_class, (), obj=obj)\n        \n        dill.register(type_class)(auto_save_func)\n        self.auto_registered.add(type_class)\n        print(f\"Auto-registered {type_class.__name__}\")\n\ndef _auto_restore_with_state(type_class, state):\n    \"\"\"Restore object using __setstate__.\"\"\"\n    obj = type_class.__new__(type_class)\n    if hasattr(obj, '__setstate__'):\n        obj.__setstate__(state)\n    else:\n        obj.__dict__.update(state)\n    return obj\n\ndef _auto_restore_with_dict(type_class, obj_dict):\n    \"\"\"Restore object using __dict__.\"\"\"\n    obj = type_class.__new__(type_class)\n    obj.__dict__.update(obj_dict)\n    return obj\n\n# Example usage\nauto_registry = AutoRegistry()\n\n# Auto-register types from a custom module\n# auto_registry.auto_register_module(my_custom_module, exclude=['BaseClass'])\n```\n\n## Integration with Existing Code\n\n### Backward Compatibility\n\n```python\nimport dill\nimport pickle\n\nclass CompatibilityManager:\n    \"\"\"Manage compatibility between dill and standard pickle.\"\"\"\n    \n    def __init__(self):\n        self.dill_enabled = True\n    \n    def enable_dill_types(self):\n        \"\"\"Enable dill types in pickle dispatch table.\"\"\"\n        dill.extend(use_dill=True)\n        self.dill_enabled = True\n        print(\"Dill types enabled in pickle\")\n    \n    def disable_dill_types(self):\n        \"\"\"Disable dill types, use only standard pickle.\"\"\"\n        dill.extend(use_dill=False)\n        self.dill_enabled = False\n        print(\"Dill types disabled, using standard pickle only\")\n    \n    def test_compatibility(self, test_objects):\n        \"\"\"Test objects with both pickle and dill.\"\"\"\n        results = {}\n        \n        for name, obj in test_objects.items():\n            results[name] = {\n                'dill': self._test_with_dill(obj),\n                'pickle': self._test_with_pickle(obj)\n            }\n        \n        return results\n    \n    def _test_with_dill(self, obj):\n        try:\n            data = dill.dumps(obj)\n            dill.loads(data)\n            return \"✓ Success\"\n        except Exception as e:\n            return f\"✗ Failed: {e}\"\n    \n    def _test_with_pickle(self, obj):\n        try:\n            data = pickle.dumps(obj)\n            pickle.loads(data)\n            return \"✓ Success\"\n        except Exception as e:\n            return f\"✗ Failed: {e}\"\n\n# Usage\ncompat = CompatibilityManager()\n\n# Test various objects\ntest_objects = {\n    'function': lambda x: x + 1,\n    'class': CustomData,\n    'instance': CustomData([1, 2, 3]),\n    'list': [1, 2, 3, 4, 5]\n}\n\nprint(\"Testing with dill types enabled:\")\ncompat.enable_dill_types()\nresults_enabled = compat.test_compatibility(test_objects)\n\nprint(\"\\nTesting with dill types disabled:\")\ncompat.disable_dill_types()\nresults_disabled = compat.test_compatibility(test_objects)\n\n# Compare results\nprint(\"\\nCompatibility Results:\")\nprint(\"-\" * 50)\nfor name in test_objects:\n    print(f\"{name}:\")\n    print(f\"  Dill enabled  - pickle: {results_enabled[name]['pickle']}\")\n    print(f\"  Dill disabled - pickle: {results_disabled[name]['pickle']}\")\n    print(f\"  Dill enabled  - dill:   {results_enabled[name]['dill']}\")\n\n# Re-enable for normal operation\ncompat.enable_dill_types()\n```\n\n## Best Practices\n\n### Registry Guidelines\n\n1. **Performance**: Keep pickling functions simple and fast\n2. **Robustness**: Handle edge cases and provide error recovery\n3. **Compatibility**: Test with different Python versions and environments\n4. **Documentation**: Document custom types and their pickling behavior\n5. **Testing**: Verify that pickled objects restore correctly with full functionality\n\n### Error Handling\n\n```python\nimport dill\nimport logging\n\nclass RobustRegistry:\n    \"\"\"Registry with comprehensive error handling.\"\"\"\n    \n    def __init__(self):\n        self.logger = logging.getLogger(__name__)\n    \n    def safe_register(self, type_class, save_func, restore_func=None):\n        \"\"\"Register type with error handling.\"\"\"\n        try:\n            # Validate inputs\n            if not isinstance(type_class, type):\n                raise TypeError(\"type_class must be a type\")\n            \n            if not callable(save_func):\n                raise TypeError(\"save_func must be callable\")\n            \n            if restore_func and not callable(restore_func):\n                raise TypeError(\"restore_func must be callable\")\n            \n            # Test the registration with a dummy object\n            self._test_registration(type_class, save_func, restore_func)\n            \n            # Perform actual registration\n            if restore_func:\n                def wrapper(pickler, obj):\n                    try:\n                        args = save_func(obj)\n                        pickler.save_reduce(restore_func, args, obj=obj)\n                    except Exception as e:\n                        self.logger.error(f\"Error saving {type_class.__name__}: {e}\")\n                        raise\n                \n                dill.register(type_class)(wrapper)\n            else:\n                dill.register(type_class)(save_func)\n            \n            self.logger.info(f\"Successfully registered {type_class.__name__}\")\n            return True\n            \n        except Exception as e:\n            self.logger.error(f\"Failed to register {type_class.__name__}: {e}\")\n            return False\n    \n    def _test_registration(self, type_class, save_func, restore_func):\n        \"\"\"Test registration with dummy data.\"\"\"\n        # This would need to be implemented based on specific type requirements\n        pass\n\n# Usage\nrobust_registry = RobustRegistry()\nlogging.basicConfig(level=logging.INFO)\n\nsuccess = robust_registry.safe_register(\n    CustomData,\n    lambda obj: (obj.data, obj.metadata),\n    lambda data, meta: CustomData(data, meta)\n)\n\nif success:\n    print(\"Registration successful\")\nelse:\n    print(\"Registration failed - check logs\")\n```