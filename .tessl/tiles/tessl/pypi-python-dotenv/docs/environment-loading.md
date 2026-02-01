# Environment Loading

Core functionality for loading environment variables from .env files with automatic file discovery, variable expansion, and flexible configuration options.

## Capabilities

### Loading Environment Variables

Load environment variables from .env files directly into the system environment, with support for override control and variable interpolation.

```python { .api }
def load_dotenv(
    dotenv_path: Optional[Union[str, os.PathLike[str]]] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    override: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = "utf-8"
) -> bool:
    """
    Parse a .env file and then load all the variables found as environment variables.

    Parameters:
        dotenv_path: Absolute or relative path to .env file
        stream: Text stream (such as io.StringIO) with .env content, used if dotenv_path is None
        verbose: Whether to output a warning if the .env file is missing
        override: Whether to override the system environment variables with variables from the .env file
        interpolate: Whether to interpolate variables using POSIX variable expansion
        encoding: Encoding to be used to read the file

    Returns:
        bool: True if at least one environment variable is set, else False
    """
```

Usage examples:

```python
from dotenv import load_dotenv
import os

# Load from default .env file
load_dotenv()

# Load from specific file
load_dotenv('/path/to/custom.env')

# Override existing environment variables
load_dotenv(override=True)

# Load from string stream
from io import StringIO
config = StringIO("DATABASE_URL=sqlite:///app.db\nDEBUG=True")
load_dotenv(stream=config)

# Disable variable interpolation
load_dotenv(interpolate=False)
```

### Parsing Without Environment Modification

Parse .env files and return their contents as a dictionary without modifying the system environment.

```python { .api }
def dotenv_values(
    dotenv_path: Optional[Union[str, os.PathLike[str]]] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = "utf-8"
) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return its content as a dict.

    The returned dict will have None values for keys without values in the .env file.
    For example, 'foo=bar' results in {"foo": "bar"} whereas 'foo' alone results in {"foo": None}

    Parameters:
        dotenv_path: Absolute or relative path to the .env file
        stream: StringIO object with .env content, used if dotenv_path is None
        verbose: Whether to output a warning if the .env file is missing
        interpolate: Whether to interpolate variables using POSIX variable expansion
        encoding: Encoding to be used to read the file

    Returns:
        dict: Dictionary with keys and values from the .env file
    """
```

Usage examples:

```python
from dotenv import dotenv_values
import os

# Parse .env file to dictionary
config = dotenv_values(".env")
database_url = config.get('DATABASE_URL')

# Advanced configuration management
config = {
    **dotenv_values(".env.shared"),    # load shared development variables
    **dotenv_values(".env.secret"),    # load sensitive variables
    **os.environ,                      # override loaded values with environment variables
}

# Parse from stream
from io import StringIO
env_stream = StringIO("USER=foo\nEMAIL=foo@example.org")
config = dotenv_values(stream=env_stream)
# Returns: {"USER": "foo", "EMAIL": "foo@example.org"}
```

### File Discovery

Automatically discover .env files by searching in increasingly higher folders from the current directory or script location.

```python { .api }
def find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False
) -> str:
    """
    Search in increasingly higher folders for the given file.

    Parameters:
        filename: Name of the file to search for (default: ".env")
        raise_error_if_not_found: Whether to raise IOError if file is not found
        usecwd: Whether to start search from current working directory instead of script location

    Returns:
        str: Path to the file if found, or an empty string otherwise

    Raises:
        IOError: If raise_error_if_not_found is True and file is not found
    """
```

Usage examples:

```python
from dotenv import find_dotenv, load_dotenv

# Find .env file automatically
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)

# Search for custom filename
config_path = find_dotenv('.config')

# Raise error if not found
try:
    env_path = find_dotenv(raise_error_if_not_found=True)
    load_dotenv(env_path)
except IOError:
    print("No .env file found")

# Search from current working directory
env_path = find_dotenv(usecwd=True)
```

## Variable Expansion

python-dotenv supports POSIX-style variable expansion using `${VAR}` syntax with optional default values:

```bash
# .env file example
DOMAIN=example.org
ADMIN_EMAIL=admin@${DOMAIN}
ROOT_URL=${DOMAIN}/app
API_KEY=${SECRET_KEY:-default-key}

# More complex examples
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=myapp
DATABASE_URL=postgresql://${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}

# Using defaults for optional configuration
REDIS_URL=${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}
LOG_LEVEL=${DEBUG:-false}
MAX_WORKERS=${WORKER_COUNT:-4}

# Nested variable expansion
APP_ENV=production
CONFIG_FILE=config.${APP_ENV}.json
CONFIG_PATH=/etc/myapp/${CONFIG_FILE}
```

With `load_dotenv(override=True)` or `dotenv_values()`, variable resolution follows this priority:
1. Value of that variable in the .env file
2. Value of that variable in the environment  
3. Default value (if provided with `:-` syntax)
4. Empty string

With `load_dotenv(override=False)`, the priority is:
1. Value of that variable in the environment
2. Value of that variable in the .env file
3. Default value (if provided with `:-` syntax)
4. Empty string