# Utilities

Helper functions for generating CLI commands and working with dotenv programmatically.

## Capabilities

### CLI Command Generation

Generate shell command strings for dotenv operations, useful for automation and integration with other tools.

```python { .api }
def get_cli_string(
    path: Optional[str] = None,
    action: Optional[str] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    quote: Optional[str] = None
) -> str:
    """
    Return a string suitable for running as a shell script.

    Useful for converting arguments passed to a fabric task
    to be passed to a `local` or `run` command.

    Parameters:
        path: Path to the .env file (-f option)
        action: CLI action (get, set, unset, list, run)
        key: Key name for get/set/unset operations
        value: Value for set operations
        quote: Quote mode (-q option: always, auto, never)

    Returns:
        str: Complete dotenv command string ready for shell execution
    """
```

## Usage Examples

### Basic Command Generation

```python
from dotenv import get_cli_string

# Generate basic commands
cmd = get_cli_string(action='list')
print(cmd)  # Output: dotenv list

cmd = get_cli_string(action='get', key='DATABASE_URL')
print(cmd)  # Output: dotenv get DATABASE_URL

cmd = get_cli_string(action='set', key='DEBUG', value='True')
print(cmd)  # Output: dotenv set DEBUG True
```

### Commands with File Paths

```python
# Generate commands with custom file paths
cmd = get_cli_string(path='production.env', action='list')
print(cmd)  # Output: dotenv -f production.env list

cmd = get_cli_string(path='/etc/app/.env', action='get', key='API_KEY')
print(cmd)  # Output: dotenv -f /etc/app/.env get API_KEY

cmd = get_cli_string(path='config.env', action='set', key='HOST', value='localhost')
print(cmd)  # Output: dotenv -f config.env set HOST localhost
```

### Commands with Quote Modes

```python
# Generate commands with different quote modes
cmd = get_cli_string(action='set', key='SIMPLE', value='abc', quote='never')
print(cmd)  # Output: dotenv -q never set SIMPLE abc

cmd = get_cli_string(action='set', key='COMPLEX', value='hello world', quote='auto')
print(cmd)  # Output: dotenv -q auto set COMPLEX "hello world"

cmd = get_cli_string(action='set', key='QUOTED', value='always', quote='always')
print(cmd)  # Output: dotenv -q always set QUOTED always
```

### Complex Command Generation

```python
# Generate complex commands with multiple options
cmd = get_cli_string(
    path='staging.env',
    action='set',
    key='DATABASE_URL',
    value='postgresql://user:pass@localhost/db',
    quote='always'
)
print(cmd)  # Output: dotenv -q always -f staging.env set DATABASE_URL "postgresql://user:pass@localhost/db"
```

### Value Handling

The function automatically handles values that contain spaces by wrapping them in quotes:

```python
# Values with spaces are automatically quoted
cmd = get_cli_string(action='set', key='MESSAGE', value='hello world')
print(cmd)  # Output: dotenv set MESSAGE "hello world"

# Values without spaces remain unquoted
cmd = get_cli_string(action='set', key='PORT', value='8080')
print(cmd)  # Output: dotenv set PORT 8080

# Empty or None values are handled gracefully
cmd = get_cli_string(action='get', key='MISSING_KEY')
print(cmd)  # Output: dotenv get MISSING_KEY
```

## Integration Examples

### Fabric Integration

```python
from fabric import task
from dotenv import get_cli_string

@task
def deploy_config(c, env='production'):
    """Deploy configuration to remote server."""
    
    # Generate commands for different environments
    commands = [
        get_cli_string(path=f'{env}.env', action='set', key='DEPLOYED_AT', value='$(date)'),
        get_cli_string(path=f'{env}.env', action='set', key='VERSION', value='1.2.3'),
        get_cli_string(path=f'{env}.env', action='list', quote='export')
    ]
    
    for cmd in commands:
        c.run(cmd)
```

### Automation Scripts

```python
import subprocess
from dotenv import get_cli_string

def setup_environment(config_file, settings):
    """Automate environment setup using generated commands."""
    
    commands = []
    
    # Generate set commands for all settings
    for key, value in settings.items():
        cmd = get_cli_string(
            path=config_file,
            action='set',
            key=key,
            value=str(value),
            quote='auto'
        )
        commands.append(cmd)
    
    # Execute all commands
    for cmd in commands:
        print(f"Executing: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
    
    # List final configuration
    list_cmd = get_cli_string(path=config_file, action='list')
    subprocess.run(list_cmd, shell=True)

# Usage
settings = {
    'DATABASE_URL': 'postgresql://localhost/myapp',
    'REDIS_URL': 'redis://localhost:6379',
    'DEBUG': 'False',
    'SECRET_KEY': 'production-secret-key'
}

setup_environment('production.env', settings)
```

### Build System Integration

```python
import os
from dotenv import get_cli_string

def generate_build_commands(environment='development'):
    """Generate build commands with environment-specific configuration."""
    
    env_file = f'.env.{environment}'
    
    # Commands for build process
    commands = [
        # Set build-specific variables
        get_cli_string(path=env_file, action='set', key='NODE_ENV', value=environment),
        get_cli_string(path=env_file, action='set', key='BUILD_TIME', value='$(date)'),
        
        # Run build with environment
        get_cli_string(path=env_file, action='run') + ' npm run build',
        get_cli_string(path=env_file, action='run') + ' npm run test',
    ]
    
    return commands

# Generate commands for different environments
dev_commands = generate_build_commands('development')
prod_commands = generate_build_commands('production')

print("Development build commands:")
for cmd in dev_commands:
    print(f"  {cmd}")

print("\nProduction build commands:")
for cmd in prod_commands:
    print(f"  {cmd}")
```

### Testing Integration

```python
import pytest
from dotenv import get_cli_string
import subprocess

class TestEnvironmentCommands:
    """Test environment command generation."""
    
    def test_basic_commands(self):
        """Test basic command generation."""
        assert get_cli_string(action='list') == 'dotenv list'
        assert get_cli_string(action='get', key='TEST') == 'dotenv get TEST'
    
    def test_file_path_commands(self):
        """Test commands with file paths."""
        cmd = get_cli_string(path='test.env', action='list')
        assert cmd == 'dotenv -f test.env list'
    
    def test_quote_modes(self):
        """Test different quote modes."""
        cmd = get_cli_string(action='set', key='KEY', value='value', quote='never')
        assert 'never' in cmd
    
    def test_command_execution(self, tmp_path):
        """Test actual command execution."""
        env_file = tmp_path / '.env'
        
        # Generate and execute set command
        set_cmd = get_cli_string(
            path=str(env_file),
            action='set',
            key='TEST_KEY',
            value='test_value'
        )
        
        subprocess.run(set_cmd, shell=True, check=True)
        
        # Verify the key was set
        get_cmd = get_cli_string(path=str(env_file), action='get', key='TEST_KEY')
        result = subprocess.run(get_cmd, shell=True, capture_output=True, text=True)
        
        assert result.stdout.strip() == 'test_value'
```

## Command String Format

The generated command strings follow this format:

```bash
dotenv [global_options] action [action_arguments]
```

Where:
- **global_options**: `-q quote_mode`, `-f file_path`
- **action**: `list`, `get`, `set`, `unset`, `run`
- **action_arguments**: Depend on the specific action

The function ensures proper ordering and quoting of arguments to generate valid shell commands.