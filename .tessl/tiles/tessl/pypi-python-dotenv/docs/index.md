# python-dotenv

A Python library that reads key-value pairs from a `.env` file and can set them as environment variables. It helps in the development of applications following the 12-factor principles by providing a convenient way to manage configuration through environment variables.

## Package Information

- **Package Name**: python-dotenv
- **Language**: Python
- **Installation**: `pip install python-dotenv`
- **CLI Installation**: `pip install "python-dotenv[cli]"`

## Core Imports

```python
from dotenv import load_dotenv, dotenv_values
```

Complete imports for all functionality:

```python
from dotenv import (
    load_dotenv,
    dotenv_values,
    find_dotenv,
    get_key,
    set_key,
    unset_key,
    get_cli_string,
    load_ipython_extension
)
```

## Basic Usage

```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now you can access environment variables
database_url = os.getenv('DATABASE_URL')
debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'

# Use environment variables in your application
print(f"Database URL: {database_url}")
print(f"Debug mode: {debug_mode}")
```

Alternative approach without modifying environment:

```python
from dotenv import dotenv_values

# Parse .env file and return as dictionary
config = dotenv_values(".env")
database_url = config.get('DATABASE_URL')
debug_mode = config.get('DEBUG', 'False').lower() == 'true'
```

## Architecture

python-dotenv follows a modular architecture:

- **Loading Functions**: `load_dotenv()` and `dotenv_values()` provide the primary interfaces for loading configuration
- **File Discovery**: `find_dotenv()` automatically discovers .env files in the directory hierarchy
- **File Manipulation**: `get_key()`, `set_key()`, `unset_key()` provide programmatic access to .env file contents
- **Variable Expansion**: Built-in support for POSIX-style variable expansion using `${VAR}` syntax
- **CLI Interface**: Complete command-line tool for .env file manipulation
- **IPython Integration**: Magic commands for interactive development environments

## Capabilities

### Environment Loading

Load environment variables from .env files with automatic file discovery, variable expansion, and flexible override options.

```python { .api }
def load_dotenv(
    dotenv_path: Optional[Union[str, os.PathLike[str]]] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    override: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = "utf-8"
) -> bool: ...

def dotenv_values(
    dotenv_path: Optional[Union[str, os.PathLike[str]]] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = "utf-8"
) -> Dict[str, Optional[str]]: ...

def find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False
) -> str: ...
```

[Environment Loading](./environment-loading.md)

### File Manipulation

Programmatically read, write, and modify .env files with support for different quote modes and export formats.

```python { .api }
def get_key(
    dotenv_path: Union[str, os.PathLike[str]],
    key_to_get: str,
    encoding: Optional[str] = "utf-8"
) -> Optional[str]: ...

def set_key(
    dotenv_path: Union[str, os.PathLike[str]],
    key_to_set: str,
    value_to_set: str,
    quote_mode: str = "always",
    export: bool = False,
    encoding: Optional[str] = "utf-8"
) -> Tuple[Optional[bool], str, str]: ...

def unset_key(
    dotenv_path: Union[str, os.PathLike[str]],
    key_to_unset: str,
    quote_mode: str = "always",
    encoding: Optional[str] = "utf-8"
) -> Tuple[Optional[bool], str]: ...
```

[File Manipulation](./file-manipulation.md)

### Command Line Interface

Complete CLI tool for managing .env files with list, get, set, unset, and run commands supporting multiple output formats.

```bash { .api }
dotenv list [--format=FORMAT]
dotenv get KEY
dotenv set KEY VALUE
dotenv unset KEY
dotenv run [--override/--no-override] COMMAND
```

[Command Line Interface](./cli.md)

### IPython Integration

Magic commands for loading .env files in IPython and Jupyter notebook environments with override and verbose options.

```python { .api }
def load_ipython_extension(ipython: Any) -> None: ...

# Magic command usage:
# %load_ext dotenv
# %dotenv [-o] [-v] [dotenv_path]
```

[IPython Integration](./ipython.md)

### Utility Functions

Helper functions for generating CLI commands and working with dotenv programmatically.

```python { .api }
def get_cli_string(
    path: Optional[str] = None,
    action: Optional[str] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    quote: Optional[str] = None
) -> str: ...
```

[Utilities](./utilities.md)

## Types

```python { .api }
# Type aliases
StrPath = Union[str, os.PathLike[str]]

# Core classes (internal, accessed via functions)
class DotEnv:
    def __init__(
        self,
        dotenv_path: Optional[StrPath],
        stream: Optional[IO[str]] = None,
        verbose: bool = False,
        encoding: Optional[str] = None,
        interpolate: bool = True,
        override: bool = True
    ) -> None: ...
    
    def dict(self) -> Dict[str, Optional[str]]: ...
    def parse(self) -> Iterator[Tuple[str, Optional[str]]]: ...
    def set_as_environment_variables(self) -> bool: ...
    def get(self, key: str) -> Optional[str]: ...

# Parser types (internal implementation)
class Binding(NamedTuple):
    key: Optional[str]
    value: Optional[str]
    original: "Original"
    error: bool

class Original(NamedTuple):
    string: str
    line: int
```