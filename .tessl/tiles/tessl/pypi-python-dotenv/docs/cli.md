# Command Line Interface

Complete command-line tool for managing .env files with list, get, set, unset, and run commands supporting multiple output formats.

## Installation

```bash
pip install "python-dotenv[cli]"
```

## Global Options

All commands support these global options:

```bash { .api }
dotenv [OPTIONS] COMMAND [ARGS]...

Options:
  -f, --file PATH           Location of the .env file, defaults to .env file in current working directory
  -q, --quote [always|never|auto]  Whether to quote or not the variable values. Default mode is always
  -e, --export              Whether to write the dot file as an executable bash script
  --version                 Show the version and exit
  --help                    Show help message and exit
```

## Capabilities

### Listing Variables

Display all stored key/value pairs with support for multiple output formats.

```bash { .api }
dotenv list [OPTIONS]

Options:
  --format [simple|json|shell|export]  The format in which to display the list (default: simple)
```

Usage examples:

```bash
# List all variables in simple format
dotenv list

# List in JSON format
dotenv list --format=json

# List in shell format (with proper quoting)
dotenv list --format=shell

# List in export format (prefixed with 'export')
dotenv list --format=export

# List from custom file
dotenv -f /path/to/custom.env list
```

Output examples:

```bash
# Simple format
DATABASE_URL=postgresql://localhost/mydb
DEBUG=True
API_KEY=secret123

# JSON format
{
  "API_KEY": "secret123",
  "DATABASE_URL": "postgresql://localhost/mydb",
  "DEBUG": "True"
}

# Shell format (properly quoted)
DATABASE_URL='postgresql://localhost/mydb'
DEBUG=True
API_KEY=secret123

# Export format
export DATABASE_URL='postgresql://localhost/mydb'
export DEBUG=True
export API_KEY=secret123
```

### Getting Values

Retrieve the value for a specific key.

```bash { .api }
dotenv get KEY
```

Usage examples:

```bash
# Get a specific value
dotenv get DATABASE_URL

# Get from custom file
dotenv -f production.env get API_KEY

# Handle missing keys (exits with code 1)
dotenv get NONEXISTENT_KEY
echo $?  # Returns 1
```

### Setting Values

Store key/value pairs in the .env file.

```bash { .api }
dotenv set KEY VALUE
```

Usage examples:

```bash
# Set a basic key/value pair
dotenv set DATABASE_URL "postgresql://localhost/mydb"

# Set with different quote modes
dotenv -q never set SIMPLE_KEY simple_value
dotenv -q auto set SPACED_KEY "value with spaces"
dotenv -q always set QUOTED_KEY always_quoted

# Set with export prefix
dotenv -e set PATH_ADDITION "/usr/local/bin"

# Set in custom file
dotenv -f production.env set API_KEY "prod-secret-123"

# Set complex values
dotenv set JSON_CONFIG '{"host": "localhost", "port": 5432}'
dotenv set MULTILINE_VALUE "line1
line2
line3"
```

### Removing Values

Remove keys from the .env file.

```bash { .api }
dotenv unset KEY
```

Usage examples:

```bash
# Remove a key
dotenv unset OLD_CONFIG

# Remove from custom file
dotenv -f staging.env unset TEMP_KEY

# Handle missing keys (exits with code 1)
dotenv unset NONEXISTENT_KEY
echo $?  # Returns 1
```

### Running Commands

Execute commands with environment variables loaded from the .env file.

```bash { .api }
dotenv run [OPTIONS] COMMAND [ARGS]...

Options:
  --override/--no-override  Override variables from the environment file with those from the .env file (default: --override)
```

Usage examples:

```bash
# Run a Python script with .env variables
dotenv run python app.py

# Run with arguments
dotenv run python manage.py migrate

# Run from custom .env file
dotenv -f production.env run python app.py

# Don't override existing environment variables
dotenv run --no-override python app.py

# Run complex commands
dotenv run sh -c 'echo "Database: $DATABASE_URL"'

# Run commands that need specific environment
dotenv run pytest tests/
dotenv run npm start
dotenv run make build
```

The `run` command:
- Loads variables from the .env file
- Merges them with existing environment variables
- Executes the specified command with the combined environment
- **With `--override` (default)**: .env file variables take precedence over existing environment variables
- **With `--no-override`**: existing environment variables take precedence over .env file variables
- Variables that exist only in .env file or only in environment are always included

## File Selection

Use the `-f/--file` option to specify a custom .env file:

```bash
# Different .env files for different environments
dotenv -f .env.development list
dotenv -f .env.staging set API_URL "https://staging-api.example.com"
dotenv -f .env.production run python deploy.py

# Absolute paths
dotenv -f /etc/myapp/.env list

# Relative paths
dotenv -f ../shared.env get SHARED_KEY
```

## Quote Modes

Control how values are quoted using the `-q/--quote` option:

```bash
# Always quote (default)
dotenv -q always set KEY "value"  # KEY='value'

# Never quote
dotenv -q never set KEY value     # KEY=value

# Auto quote (quotes only when necessary)
dotenv -q auto set SIMPLE abc     # SIMPLE=abc
dotenv -q auto set COMPLEX "a b"  # COMPLEX='a b'
```

## Export Mode

Generate bash-compatible output using the `-e/--export` option:

```bash
# Set with export prefix
dotenv -e set PATH_VAR "/usr/local/bin"
# Results in: export PATH_VAR='/usr/local/bin'

# List with export format
dotenv -e list --format=export
# Shows all variables prefixed with 'export'

# Create sourceable .env file
dotenv -e -f bash-compatible.env set DATABASE_URL "postgresql://localhost/mydb"
# Now you can: source bash-compatible.env
```

## Exit Codes

The CLI tool uses standard exit codes:

- **0**: Success
- **1**: Command failed (key not found, file doesn't exist, etc.)
- **2**: File access error (permissions, file not readable, etc.)

## Examples

```bash
# Complete workflow example
cd myproject

# Initialize with some variables
dotenv set DATABASE_URL "postgresql://localhost/mydb"
dotenv set DEBUG "True"
dotenv set SECRET_KEY "dev-secret-key"

# List all variables
dotenv list

# Get specific value
echo "Database: $(dotenv get DATABASE_URL)"

# Run application with environment
dotenv run python app.py

# Export for bash sourcing
dotenv -e list --format=export > environment.sh
source environment.sh

# Clean up
dotenv unset SECRET_KEY
```