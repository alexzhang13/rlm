# Configuration and Settings

dill provides global configuration options and settings that control serialization behavior, protocol selection, and various operational modes for optimal performance and compatibility.

## Global Settings

### Settings Dictionary

```python { .api }
# Global settings dictionary
settings = {
    'protocol': DEFAULT_PROTOCOL,  # int: Default pickle protocol version
    'byref': False,               # bool: Pickle by reference when possible
    'fmode': 0,                   # int: File mode setting (0=HANDLE_FMODE, 1=CONTENTS_FMODE, 2=FILE_FMODE)
    'recurse': False,             # bool: Recursively pickle nested objects
    'ignore': False               # bool: Ignore certain errors during serialization
}
```

### Protocol Constants

```python { .api }
DEFAULT_PROTOCOL = 3    # Default pickle protocol version
HIGHEST_PROTOCOL = 5    # Highest supported pickle protocol version

# File mode constants
HANDLE_FMODE = 0       # Preserve file handles during serialization
CONTENTS_FMODE = 1     # Save file contents instead of handles
FILE_FMODE = 2         # Save file metadata and paths
```

### Extension Control

```python { .api }
def extend(use_dill=True):
    """
    Add or remove dill types to/from the pickle registry.
    
    Controls whether dill's extended types are available in the standard
    pickle module's dispatch table for backward compatibility.
    
    Parameters:
    - use_dill: bool, if True extend dispatch table with dill types,
                     if False revert to standard pickle types only
    
    Returns:
    None
    """
```

## Usage Examples

### Basic Configuration

```python
import dill

# Check current settings
print("Current settings:")
for key, value in dill.settings.items():
    print(f"  {key}: {value}")

# Modify settings
original_protocol = dill.settings['protocol']
dill.settings['protocol'] = dill.HIGHEST_PROTOCOL
dill.settings['byref'] = True

print(f"\\nChanged protocol from {original_protocol} to {dill.settings['protocol']}")
print(f"Enabled byref: {dill.settings['byref']}")

# Test with new settings
def test_function():
    return "Hello with new settings!"

serialized = dill.dumps(test_function)
restored = dill.loads(serialized)
print(f"Function result: {restored()}")

# Restore original settings
dill.settings['protocol'] = original_protocol
dill.settings['byref'] = False
```

### Protocol Selection and Performance

```python
import dill
import time

def benchmark_protocols(obj, protocols=None):
    """Benchmark different pickle protocols."""
    if protocols is None:
        protocols = [0, 1, 2, 3, 4, dill.HIGHEST_PROTOCOL]
    
    results = {}
    
    for protocol in protocols:
        try:
            # Set protocol
            original_protocol = dill.settings['protocol']
            dill.settings['protocol'] = protocol
            
            # Time serialization
            start_time = time.time()
            serialized = dill.dumps(obj)
            serialize_time = time.time() - start_time
            
            # Time deserialization
            start_time = time.time()
            dill.loads(serialized)
            deserialize_time = time.time() - start_time
            
            results[protocol] = {
                'serialize_time': serialize_time,
                'deserialize_time': deserialize_time,
                'size': len(serialized),
                'total_time': serialize_time + deserialize_time
            }
            
            # Restore original protocol
            dill.settings['protocol'] = original_protocol
            
        except Exception as e:
            results[protocol] = {'error': str(e)}
    
    return results

# Test with complex object
complex_obj = {
    'functions': [lambda x: x**i for i in range(5)],
    'data': list(range(1000)),
    'nested': {'level1': {'level2': [i*j for i in range(10) for j in range(10)]}}
}

protocol_results = benchmark_protocols(complex_obj)

print("Protocol Performance Comparison:")
print("-" * 50)
for protocol, result in protocol_results.items():
    if 'error' in result:
        print(f"Protocol {protocol}: ERROR - {result['error']}")
    else:
        print(f"Protocol {protocol}:")
        print(f"  Serialize: {result['serialize_time']:.4f}s")
        print(f"  Deserialize: {result['deserialize_time']:.4f}s")
        print(f"  Size: {result['size']:,} bytes")
        print(f"  Total: {result['total_time']:.4f}s")
```

### File Mode Configuration

```python
import dill
import tempfile
import io

def demonstrate_file_modes():
    """Demonstrate different file mode behaviors."""
    
    # Create object with file handle
    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    temp_file.write("Test data for file mode demonstration")
    temp_file.seek(0)
    
    obj_with_file = {
        'file_handle': temp_file,
        'file_path': temp_file.name,
        'data': [1, 2, 3, 4, 5]
    }
    
    # Test different file modes
    modes = {
        dill.HANDLE_FMODE: "HANDLE_FMODE (preserve handles)",
        dill.CONTENTS_FMODE: "CONTENTS_FMODE (save contents)",
        dill.FILE_FMODE: "FILE_FMODE (save metadata)"
    }
    
    for fmode, description in modes.items():
        print(f"\\nTesting {description}:")
        print("-" * 40)
        
        try:
            # Set file mode
            original_fmode = dill.settings['fmode']
            dill.settings['fmode'] = fmode
            
            # Serialize
            serialized = dill.dumps(obj_with_file)
            print(f"✓ Serialization successful ({len(serialized)} bytes)")
            
            # Deserialize
            restored = dill.loads(serialized)
            print(f"✓ Deserialization successful")
            
            # Test restored file behavior
            if 'file_handle' in restored:
                file_obj = restored['file_handle']
                if hasattr(file_obj, 'read'):
                    try:
                        content = file_obj.read()
                        print(f"✓ File content: {repr(content[:50])}")
                    except:
                        print("✗ File handle not functional")
                else:
                    print("○ File handle replaced with alternative representation")
            
            # Restore original setting
            dill.settings['fmode'] = original_fmode
            
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    # Cleanup
    temp_file.close()
    import os
    os.unlink(temp_file.name)

demonstrate_file_modes()
```

### Reference vs Value Serialization

```python
import dill

def demonstrate_byref_setting():
    """Demonstrate byref setting effects."""
    
    # Create shared object
    shared_list = [1, 2, 3, 4, 5]
    
    # Create objects that reference the shared list
    obj1 = {'data': shared_list, 'name': 'object1'}
    obj2 = {'data': shared_list, 'name': 'object2'}
    container = {'obj1': obj1, 'obj2': obj2, 'shared': shared_list}
    
    # Test with byref=False (default)
    print("Testing with byref=False (value serialization):")
    dill.settings['byref'] = False
    
    serialized_value = dill.dumps(container)
    restored_value = dill.loads(serialized_value)
    
    # Modify shared list in restored object
    restored_value['shared'].append(999)
    
    print(f"  Original obj1 data: {container['obj1']['data']}")
    print(f"  Restored obj1 data: {restored_value['obj1']['data']}")
    print(f"  Restored obj2 data: {restored_value['obj2']['data']}")
    print(f"  Objects share data in restored: {restored_value['obj1']['data'] is restored_value['obj2']['data']}")
    
    # Test with byref=True
    print("\\nTesting with byref=True (reference serialization):")
    dill.settings['byref'] = True
    
    serialized_ref = dill.dumps(container)  
    restored_ref = dill.loads(serialized_ref)
    
    # Modify shared list in restored object
    restored_ref['shared'].append(888)
    
    print(f"  Restored obj1 data: {restored_ref['obj1']['data']}")
    print(f"  Restored obj2 data: {restored_ref['obj2']['data']}")
    print(f"  Objects share data in restored: {restored_ref['obj1']['data'] is restored_ref['obj2']['data']}")
    
    print(f"\\nSerialized sizes:")
    print(f"  Value mode: {len(serialized_value)} bytes")
    print(f"  Reference mode: {len(serialized_ref)} bytes")
    
    # Restore default
    dill.settings['byref'] = False

demonstrate_byref_setting()
```

### Recursive Serialization Control

```python
import dill

def demonstrate_recursive_setting():
    """Demonstrate recursive serialization setting."""
    
    # Create nested structure with functions
    def outer_function(x):
        def inner_function(y):
            def innermost_function(z):
                return x + y + z
            return innermost_function
        return inner_function
    
    nested_func = outer_function(10)
    deeply_nested = nested_func(20)
    
    test_obj = {
        'outer': outer_function,
        'nested': nested_func,
        'deep': deeply_nested,
        'data': {'level1': {'level2': {'level3': [1, 2, 3]}}}
    }
    
    # Test with recurse=False (default)
    print("Testing with recurse=False:")
    dill.settings['recurse'] = False
    
    try:
        serialized_no_recurse = dill.dumps(test_obj)
        restored_no_recurse = dill.loads(serialized_no_recurse)
        
        # Test functionality
        result = restored_no_recurse['deep'](30)
        print(f"  ✓ Serialization successful, result: {result}")
        print(f"  Size: {len(serialized_no_recurse)} bytes")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    # Test with recurse=True
    print("\\nTesting with recurse=True:")
    dill.settings['recurse'] = True
    
    try:
        serialized_recurse = dill.dumps(test_obj)
        restored_recurse = dill.loads(serialized_recurse)
        
        # Test functionality
        result = restored_recurse['deep'](30)
        print(f"  ✓ Serialization successful, result: {result}")
        print(f"  Size: {len(serialized_recurse)} bytes")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    # Restore default
    dill.settings['recurse'] = False

demonstrate_recursive_setting()
```

## Advanced Configuration Management

### Configuration Context Manager

```python
import dill
from contextlib import contextmanager

@contextmanager
def dill_config(**settings):
    """Context manager for temporary dill configuration."""
    # Save original settings
    original = dill.settings.copy()
    
    # Apply new settings
    dill.settings.update(settings)
    
    try:
        yield dill.settings
    finally:
        # Restore original settings
        dill.settings.clear()
        dill.settings.update(original)

# Usage examples
def test_function():
    return "Test result"

# Temporary high-performance configuration
with dill_config(protocol=dill.HIGHEST_PROTOCOL, byref=True):
    print(f"Using protocol: {dill.settings['protocol']}")
    serialized = dill.dumps(test_function)
    print(f"Serialized size: {len(serialized)} bytes")

# Back to default settings
print(f"Back to protocol: {dill.settings['protocol']}")

# Temporary memory-efficient configuration
with dill_config(fmode=dill.CONTENTS_FMODE, recurse=True):
    complex_obj = {'data': [1, 2, 3], 'func': lambda x: x*2}
    serialized = dill.dumps(complex_obj)
    restored = dill.loads(serialized)
    print(f"Function result: {restored['func'](5)}")
```

### Configuration Profiles

```python
import dill

class DillProfile:
    """Predefined configuration profiles for different use cases."""
    
    # Performance-optimized profile
    PERFORMANCE = {
        'protocol': dill.HIGHEST_PROTOCOL,
        'byref': False,
        'fmode': dill.HANDLE_FMODE,
        'recurse': False,
        'ignore': False
    }
    
    # Size-optimized profile
    COMPACT = {
        'protocol': dill.HIGHEST_PROTOCOL,
        'byref': True,
        'fmode': dill.CONTENTS_FMODE,
        'recurse': True, 
        'ignore': False
    }
    
    # Compatibility profile
    COMPATIBLE = {
        'protocol': 2,  # Widely supported protocol
        'byref': False,
        'fmode': dill.CONTENTS_FMODE,
        'recurse': False,
        'ignore': True
    }
    
    # Debug profile
    DEBUG = {
        'protocol': 0,  # Human-readable protocol
        'byref': False,
        'fmode': dill.CONTENTS_FMODE,
        'recurse': True,
        'ignore': False
    }

class ConfigManager:
    """Configuration management utility."""
    
    def __init__(self):
        self.saved_configs = {}
        self.current_profile = None
    
    def apply_profile(self, profile_name):
        """Apply a predefined profile."""
        profiles = {
            'performance': DillProfile.PERFORMANCE,
            'compact': DillProfile.COMPACT,
            'compatible': DillProfile.COMPATIBLE,
            'debug': DillProfile.DEBUG
        }
        
        if profile_name in profiles:
            # Save current config
            self.save_config('pre_profile')
            
            # Apply profile
            dill.settings.update(profiles[profile_name])
            self.current_profile = profile_name
            
            print(f"Applied {profile_name} profile:")
            for key, value in profiles[profile_name].items():
                print(f"  {key}: {value}")
        else:
            print(f"Unknown profile: {profile_name}")
    
    def save_config(self, name):
        """Save current configuration."""
        self.saved_configs[name] = dill.settings.copy()
        print(f"Saved configuration as '{name}'")
    
    def restore_config(self, name):
        """Restore saved configuration."""
        if name in self.saved_configs:
            dill.settings.clear()
            dill.settings.update(self.saved_configs[name])
            self.current_profile = None
            print(f"Restored configuration '{name}'")
        else:
            print(f"No saved configuration named '{name}'")
    
    def list_configs(self):
        """List saved configurations."""
        print("Saved configurations:")
        for name in self.saved_configs:
            print(f"  - {name}")
    
    def show_current_config(self):
        """Show current configuration."""
        print("Current configuration:")
        for key, value in dill.settings.items():
            print(f"  {key}: {value}")
        if self.current_profile:
            print(f"Profile: {self.current_profile}")

# Usage example
config_manager = ConfigManager()

# Test different profiles
test_obj = {
    'function': lambda x: x**2,
    'data': list(range(100)),
    'nested': {'level1': {'level2': 'deep_value'}}
}

profiles_to_test = ['performance', 'compact', 'compatible', 'debug']

for profile in profiles_to_test:
    print(f"\\n{'='*50}")
    print(f"Testing {profile.upper()} profile")
    print('='*50)
    
    config_manager.apply_profile(profile)
    
    try:
        serialized = dill.dumps(test_obj)
        restored = dill.loads(serialized)
        
        print(f"✓ Serialization successful")
        print(f"  Size: {len(serialized):,} bytes")
        print(f"  Function test: {restored['function'](5)}")
        
    except Exception as e:
        print(f"✗ Failed: {e}")

# Restore original configuration
config_manager.restore_config('pre_profile')
```

### Environment-Specific Configuration

```python
import dill
import os
import platform
import sys

class EnvironmentConfig:
    """Automatically configure dill based on environment."""
    
    @staticmethod
    def auto_configure():
        """Automatically configure based on environment."""
        config = {}
        
        # Python version considerations
        if sys.version_info >= (3, 8):
            config['protocol'] = dill.HIGHEST_PROTOCOL
        else:
            config['protocol'] = 3  # Safe for older versions
        
        # Platform considerations
        if platform.system() == 'Windows':
            config['fmode'] = dill.CONTENTS_FMODE  # Better Windows compatibility
        else:
            config['fmode'] = dill.HANDLE_FMODE
        
        # Memory considerations
        import psutil
        available_memory = psutil.virtual_memory().available
        if available_memory < 1024**3:  # Less than 1GB
            config['byref'] = True  # Save memory
            config['recurse'] = False
        else:
            config['byref'] = False
            config['recurse'] = True
        
        # Development vs production
        if os.environ.get('DILL_DEBUG'):
            config['protocol'] = 0  # Human-readable
            config['ignore'] = False  # Strict error handling
        elif os.environ.get('DILL_PRODUCTION'):
            config['ignore'] = True  # Lenient error handling
        
        # Apply configuration
        dill.settings.update(config)
        
        print("Auto-configured dill based on environment:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        return config
    
    @staticmethod
    def validate_config():
        """Validate current configuration."""
        issues = []
        
        # Check protocol compatibility
        if dill.settings['protocol'] > 4 and sys.version_info < (3, 8):
            issues.append("Protocol 5 requires Python 3.8+")
        
        # Check memory usage with byref setting
        if not dill.settings['byref'] and dill.settings['recurse']:
            issues.append("High memory usage: recurse=True with byref=False")
        
        # Check file mode compatibility
        if dill.settings['fmode'] == dill.HANDLE_FMODE and platform.system() == 'Windows':
            issues.append("HANDLE_FMODE may have issues on Windows")
        
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print("✓ Configuration validation passed")
        
        return len(issues) == 0

# Example usage
print("Current system information:")
print(f"  Python: {sys.version}")
print(f"  Platform: {platform.system()}")
print(f"  Memory: {psutil.virtual_memory().total / (1024**3):.1f}GB")

# Auto-configure
env_config = EnvironmentConfig()
env_config.auto_configure()

# Validate configuration
env_config.validate_config()

# Test with auto-configuration
test_function = lambda x: x * 2 + 1
serialized = dill.dumps(test_function)
restored = dill.loads(serialized)
print(f"\\nTest result: {restored(10)}")
print(f"Serialized size: {len(serialized)} bytes")
```

## Best Practices

### Configuration Management Guidelines

1. **Profile Usage**: Use predefined profiles for common scenarios
2. **Context Managers**: Use context managers for temporary configuration changes
3. **Environment Awareness**: Configure based on deployment environment
4. **Performance Testing**: Benchmark different configurations for your use case
5. **Documentation**: Document configuration choices and their rationale

### Performance Considerations

1. **Protocol Selection**: Higher protocols generally offer better performance
2. **Memory vs Speed**: `byref=True` saves memory but may slow deserialization
3. **File Mode Impact**: Choose file mode based on your file handling needs
4. **Recursive Overhead**: Enable recursion only when necessary for complex objects