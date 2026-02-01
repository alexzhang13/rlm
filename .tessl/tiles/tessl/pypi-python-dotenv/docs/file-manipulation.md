# File Manipulation

Programmatic functions for reading, writing, and modifying .env files with support for different quote modes and export formats.

## Capabilities

### Reading Values

Retrieve the value of a specific key from a .env file without loading all variables.

```python { .api }
def get_key(
    dotenv_path: Union[str, os.PathLike[str]],
    key_to_get: str,
    encoding: Optional[str] = "utf-8"
) -> Optional[str]:
    """
    Get the value of a given key from the given .env file.

    Parameters:
        dotenv_path: Path to the .env file
        key_to_get: The key to retrieve
        encoding: File encoding (default: "utf-8")

    Returns:
        str or None: Value of the key if found, None if key doesn't exist or has no value
    """
```

Usage examples:

```python
from dotenv import get_key

# Get a specific value
database_url = get_key('.env', 'DATABASE_URL')
if database_url:
    print(f"Database URL: {database_url}")

# Handle missing keys
api_key = get_key('.env', 'API_KEY')
if api_key is None:
    print("API_KEY not found in .env file")
```

### Setting Values

Add or update key/value pairs in .env files with support for different quoting modes and export formats.

```python { .api }
def set_key(
    dotenv_path: Union[str, os.PathLike[str]],
    key_to_set: str,
    value_to_set: str,
    quote_mode: str = "always",
    export: bool = False,
    encoding: Optional[str] = "utf-8"
) -> Tuple[Optional[bool], str, str]:
    """
    Add or update a key/value to the given .env file.

    If the .env path given doesn't exist, fails instead of risking creating
    an orphan .env somewhere in the filesystem.

    Parameters:
        dotenv_path: Path to the .env file
        key_to_set: The key to set
        value_to_set: The value to set
        quote_mode: Quote mode - "always", "auto", or "never"
        export: Whether to prefix the line with "export "
        encoding: File encoding (default: "utf-8")

    Returns:
        tuple: (success_bool, key, value) where success_bool indicates if operation succeeded

    Raises:
        ValueError: If quote_mode is not one of "always", "auto", "never"
    """
```

Usage examples:

```python
from dotenv import set_key

# Set a basic key/value pair
success, key, value = set_key('.env', 'DATABASE_URL', 'postgresql://localhost/mydb')
if success:
    print(f"Set {key}={value}")

# Set with different quote modes
set_key('.env', 'SIMPLE_KEY', 'simple_value', quote_mode='never')     # SIMPLE_KEY=simple_value
set_key('.env', 'SPACED_KEY', 'value with spaces', quote_mode='auto') # SPACED_KEY='value with spaces'
set_key('.env', 'QUOTED_KEY', 'always_quoted', quote_mode='always')   # QUOTED_KEY='always_quoted'

# Set with export prefix for bash compatibility
set_key('.env', 'PATH_VAR', '/usr/local/bin', export=True)
# Results in: export PATH_VAR='/usr/local/bin'

# Handle special characters
set_key('.env', 'PASSWORD', "p@ssw0rd'with\"quotes", quote_mode='always')
```

### Removing Values

Remove keys and their values from .env files.

```python { .api }
def unset_key(
    dotenv_path: Union[str, os.PathLike[str]],
    key_to_unset: str,
    quote_mode: str = "always",
    encoding: Optional[str] = "utf-8"
) -> Tuple[Optional[bool], str]:
    """
    Remove a given key from the given .env file.

    Parameters:
        dotenv_path: Path to the .env file
        key_to_unset: The key to remove
        quote_mode: Quote mode for file operations (currently unused but kept for consistency)
        encoding: File encoding (default: "utf-8")

    Returns:
        tuple: (success_bool, key) where success_bool is True if key was removed,
               None if file doesn't exist or key wasn't found

    Raises:
        Warning logged if file doesn't exist or key doesn't exist
    """
```

Usage examples:

```python
from dotenv import unset_key

# Remove a key
success, key = unset_key('.env', 'OLD_CONFIG_KEY')
if success:
    print(f"Removed {key} from .env file")
elif success is None:
    print("Key not found or file doesn't exist")

# Remove multiple keys
keys_to_remove = ['TEMP_KEY', 'DEPRECATED_SETTING', 'OLD_API_KEY']
for key in keys_to_remove:
    success, removed_key = unset_key('.env', key)
    if success:
        print(f"Removed {removed_key}")
```

## Quote Modes

The `quote_mode` parameter controls how values are quoted in the .env file:

- **"always"** (default): All values are wrapped in single quotes
- **"auto"**: Values containing non-alphanumeric characters are quoted, simple values are not
- **"never"**: Values are never quoted (use with caution for values with spaces or special characters)

Examples:

```python
from dotenv import set_key

# Different quote modes with the same value
value = "hello world"

set_key('.env', 'KEY1', value, quote_mode='always')  # KEY1='hello world'
set_key('.env', 'KEY2', value, quote_mode='auto')    # KEY2='hello world' (has space)
set_key('.env', 'KEY3', value, quote_mode='never')   # KEY3=hello world (may cause issues)

# Auto mode examples
set_key('.env', 'SIMPLE', 'abc123', quote_mode='auto')      # SIMPLE=abc123 (no quotes)
set_key('.env', 'COMPLEX', 'abc-123', quote_mode='auto')    # COMPLEX='abc-123' (has hyphen)
```

## Export Mode

When `export=True` is used with `set_key()`, the resulting line is prefixed with `export `, making the .env file compatible with bash sourcing:

```python
from dotenv import set_key

set_key('.env', 'PATH_ADDITION', '/usr/local/bin', export=True)
# Results in: export PATH_ADDITION='/usr/local/bin'

# Now the .env file can be sourced in bash:
# $ source .env
# $ echo $PATH_ADDITION
```

## Error Handling

The file manipulation functions handle various error conditions:

- **File doesn't exist**: 
  - `get_key()`: Returns `None` and logs warning with verbose=True
  - `unset_key()`: Returns `(None, key)` and logs warning
  - `set_key()`: Raises `IOError` if the file path doesn't exist
- **Key doesn't exist**: 
  - `get_key()`: Returns `None` and logs warning with verbose=True
  - `unset_key()`: Returns `(None, key)` and logs warning
- **Invalid quote mode**: `set_key()` raises `ValueError` for modes other than "always", "auto", "never"
- **File permissions**: OS-level `PermissionError` and `IOError` exceptions are propagated to caller
- **Invalid file encoding**: `UnicodeDecodeError` may be raised if encoding parameter doesn't match file

Examples of error handling:

```python
from dotenv import get_key, set_key, unset_key

# Handle missing files
try:
    value = get_key('nonexistent.env', 'KEY')
    if value is None:
        print("Key not found or file doesn't exist")
except IOError as e:
    print(f"File access error: {e}")

# Handle invalid quote modes
try:
    set_key('.env', 'KEY', 'value', quote_mode='invalid')
except ValueError as e:
    print(f"Invalid quote mode: {e}")

# Handle file creation failure
try:
    set_key('/readonly/path/.env', 'KEY', 'value')
except (IOError, PermissionError) as e:
    print(f"Cannot write to file: {e}")
```