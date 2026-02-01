# IPython Integration

Magic commands for loading .env files in IPython and Jupyter notebook environments with override and verbose options.

## Installation

The IPython extension is included with the base python-dotenv package:

```bash
pip install python-dotenv
```

## Capabilities

### Loading the Extension

Load the dotenv extension to enable the `%dotenv` magic command.

```python { .api }
def load_ipython_extension(ipython: Any) -> None:
    """
    Register the %dotenv magic command.
    
    This function is called automatically when the extension is loaded.
    """
```

Usage in IPython/Jupyter:

```python
# Load the extension
%load_ext dotenv

# Extension is now available for the current session
```

### Magic Command

Use the `%dotenv` magic command to load environment variables from .env files.

```python { .api }
%dotenv [OPTIONS] [dotenv_path]

Options:
  -o, --override    Indicate to override existing variables
  -v, --verbose     Indicate function calls to be verbose

Arguments:
  dotenv_path       Search in increasingly higher folders for the dotenv_path (default: '.env')
```

## Usage Examples

### Basic Usage

```python
# Load extension
%load_ext dotenv

# Load from default .env file
%dotenv

# Now environment variables from .env are available
import os
database_url = os.getenv('DATABASE_URL')
print(f"Database URL: {database_url}")
```

### Loading from Specific Files

```python
# Load from specific file in current directory
%dotenv config.env

# Load from relative path
%dotenv ../shared.env

# Load from absolute path
%dotenv /path/to/production.env
```

### Using Options

```python
# Load with verbose output
%dotenv -v
# Output: Loading .env file found at: /current/directory/.env

# Override existing environment variables
%dotenv -o

# Combine options
%dotenv -o -v production.env
```

### Multiple Environment Files

```python
# Load multiple files in sequence
%dotenv shared.env
%dotenv -o local.env    # Override with local settings

# Load different files for different purposes
%dotenv database.env    # Database configuration
%dotenv api.env         # API keys and endpoints
%dotenv -o debug.env    # Debug settings (override existing)
```

## Integration with Jupyter Notebooks

The IPython integration is particularly useful in Jupyter notebooks for data science and development workflows:

```python
# Cell 1: Load environment configuration
%load_ext dotenv
%dotenv -v config.env

# Cell 2: Use environment variables
import os
import pandas as pd
from sqlalchemy import create_engine

# Get database connection from environment
database_url = os.getenv('DATABASE_URL')
engine = create_engine(database_url)

# Load data
df = pd.read_sql('SELECT * FROM users', engine)
df.head()
```

```python
# Example: Different environments for different notebook sections
# Development section
%dotenv -v development.env

# Load development data
dev_api_key = os.getenv('API_KEY')
dev_data = fetch_data(dev_api_key)

# Production comparison section  
%dotenv -o production.env

# Load production data
prod_api_key = os.getenv('API_KEY')
prod_data = fetch_data(prod_api_key)

# Compare datasets
compare_data(dev_data, prod_data)
```

## Options Details

### Override Option (`-o, --override`)

Controls whether environment variables from the .env file override existing environment variables:

```python
# Without override (default behavior)
import os
os.environ['DEBUG'] = 'False'    # Set in current environment
%dotenv                          # .env contains DEBUG=True
print(os.getenv('DEBUG'))        # Prints: False (existing value preserved)

# With override
import os
os.environ['DEBUG'] = 'False'    # Set in current environment
%dotenv -o                       # .env contains DEBUG=True  
print(os.getenv('DEBUG'))        # Prints: True (overridden by .env)
```

### Verbose Option (`-v, --verbose`)

Enables verbose output to show which .env file is being loaded:

```python
# Without verbose
%dotenv config.env
# (no output)

# With verbose
%dotenv -v config.env
# Output: Loading .env file found at: /current/directory/config.env
```

## Error Handling

The magic command handles common error scenarios gracefully:

```python
# File not found
%dotenv nonexistent.env
# Output: cannot find .env file

# No file specified and no default .env
%dotenv
# (silently continues if no .env file found)

# With verbose, shows search behavior
%dotenv -v
# Output: Loading .env file found at: /path/to/.env
# Or: python-dotenv could not find configuration file .env
```

## Automatic Extension Loading

For convenience, you can automatically load the extension when starting IPython by adding it to your IPython configuration:

```python
# In ~/.ipython/profile_default/ipython_config.py
c.InteractiveShellApp.extensions = ['dotenv']

# Or add to startup file
# In ~/.ipython/profile_default/startup/00-dotenv.py
get_ipython().magic('load_ext dotenv')
```

## Working with Virtual Environments

The IPython integration works seamlessly with virtual environments:

```python
# In a virtual environment
%load_ext dotenv
%dotenv -v

# Variables are loaded for the current Python session
import os
print(f"Virtual env: {os.getenv('VIRTUAL_ENV')}")
print(f"App config: {os.getenv('APP_CONFIG')}")
```

## Best Practices

1. **Load early**: Load your .env files early in your notebook before importing other modules
2. **Use verbose mode**: Use `-v` for debugging to see which files are being loaded
3. **Organize by purpose**: Use separate .env files for different configurations (database, API keys, debug settings)
4. **Override carefully**: Use `-o` only when you need to override existing environment variables
5. **Document in notebooks**: Add markdown cells explaining which .env files are needed

```python
# Good practice example
%load_ext dotenv

# Load base configuration
%dotenv -v base.env

# Load environment-specific overrides
%dotenv -o -v development.env

# Now proceed with analysis
import pandas as pd
import requests

api_key = os.getenv('API_KEY')
database_url = os.getenv('DATABASE_URL')
```