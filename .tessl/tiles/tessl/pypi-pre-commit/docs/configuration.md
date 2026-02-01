# Configuration Management

Configuration loading, validation, and schema definitions for pre-commit configuration files. Pre-commit uses YAML-based configuration files to define hooks and their settings.

## Capabilities

### Configuration Loading

Functions for loading and parsing pre-commit configuration files with automatic validation.

```python { .api }
load_config: functools.partial[dict[str, Any]]
# Partial function for loading .pre-commit-config.yaml files
# Usage: config = load_config(filename)
# Raises InvalidConfigError if configuration is invalid

load_manifest: functools.partial[list[dict[str, Any]]]
# Partial function for loading .pre-commit-hooks.yaml files  
# Usage: hooks = load_manifest(filename)
# Raises InvalidManifestError if manifest is invalid
```

### Configuration Validation Functions

Utility functions for validating configuration elements.

```python { .api }
def check_type_tag(tag: str) -> None:
    """Validate file type tag is recognized"""

def parse_version(s: str) -> tuple[int, ...]:
    """Parse version string for comparison"""

def check_min_version(version: str) -> None:
    """Check minimum pre-commit version requirement"""

def transform_stage(stage: str) -> str:
    """Transform legacy stage names to current format"""
```

### Schema Constants

JSON schemas used for validating configuration and manifest files.

```python { .api }
CONFIG_SCHEMA: cfgv.Map
"""Schema for .pre-commit-config.yaml validation"""

MANIFEST_SCHEMA: cfgv.Array
"""Schema for .pre-commit-hooks.yaml validation"""

MINIMAL_MANIFEST_SCHEMA: cfgv.Array
"""Minimal schema for manifest validation"""
```

## Configuration File Formats

### Pre-commit Configuration (.pre-commit-config.yaml)

Main configuration file format for defining repositories and hooks:

```yaml
# .pre-commit-config.yaml example
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        args: [--line-length=88]
        files: \.py$
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
```

#### Configuration Schema Properties

```python { .api }
class ConfigRepo:
    """Configuration repository definition"""
    repo: str               # Repository URL or 'local'
    rev: str                # Git revision (tag, commit, branch)
    hooks: list[ConfigHook] # List of hooks from this repo

class ConfigHook:
    """Hook configuration in .pre-commit-config.yaml"""
    id: str                              # Hook identifier
    alias: str | None = None             # Alternative name
    name: str | None = None              # Display name override
    language_version: str | None = None  # Language version
    files: str | None = None             # File pattern regex
    exclude: str | None = None           # Exclusion pattern
    types: list[str] | None = None       # File types to include
    types_or: list[str] | None = None    # Alternative file types
    exclude_types: list[str] | None = None # File types to exclude
    args: list[str] | None = None        # Additional arguments
    stages: list[str] | None = None      # Git hook stages
    additional_dependencies: list[str] | None = None # Extra deps
    always_run: bool | None = None       # Run even without files
    verbose: bool | None = None          # Verbose output
    log_file: str | None = None          # Log file path
```

### Hook Manifest (.pre-commit-hooks.yaml)

Manifest file format for defining available hooks in a repository:

```yaml
# .pre-commit-hooks.yaml example
- id: black
  name: black
  description: "The uncompromising Python code formatter"
  entry: black
  language: python
  require_serial: false
  types_or: [python, pyi]
  minimum_pre_commit_version: 2.9.2
```

#### Manifest Schema Properties

```python { .api }
class ManifestHook:
    """Hook definition in .pre-commit-hooks.yaml"""
    id: str                                    # Unique identifier
    name: str                                  # Display name
    entry: str                                 # Command to execute
    language: str                              # Programming language
    description: str | None = None             # Hook description
    alias: str | None = None                   # Alternative name
    files: str | None = None                   # File pattern regex
    exclude: str | None = None                 # Exclusion pattern
    types: list[str] | None = None             # File types
    types_or: list[str] | None = None          # Alternative file types
    exclude_types: list[str] | None = None     # Excluded file types
    always_run: bool = False                   # Always execute
    fail_fast: bool = False                    # Stop on first failure
    pass_filenames: bool = True                # Pass filenames to hook
    require_serial: bool = False               # Serial execution required
    stages: list[str] | None = None            # Applicable stages
    args: list[str] | None = None              # Default arguments
    verbose: bool = False                      # Verbose output
    language_version: str = 'default'          # Language version
    log_file: str | None = None                # Log file path
    minimum_pre_commit_version: str = '0.15.0' # Version requirement
    additional_dependencies: list[str] = []     # Extra dependencies
```

## File Type Detection

### Supported File Types

Pre-commit includes built-in file type detection for various programming languages and file formats:

```python { .api }
FILE_TYPES = [
    'bash', 'batch', 'c', 'c++', 'csharp', 'css', 'dart', 'dockerfile',
    'elixir', 'go', 'haskell', 'html', 'java', 'javascript', 'json',
    'jsx', 'kotlin', 'lua', 'markdown', 'perl', 'php', 'python', 'r',
    'ruby', 'rust', 'scala', 'shell', 'sql', 'swift', 'text', 'toml',
    'tsx', 'typescript', 'xml', 'yaml'
]
```

## Configuration Examples

### Loading Configuration

```python
from pre_commit.clientlib import load_config, InvalidConfigError

try:
    config = load_config('.pre-commit-config.yaml')
    print(f"Found {len(config['repos'])} repositories")
    
    for repo in config['repos']:
        print(f"Repository: {repo['repo']}")
        print(f"Hooks: {[hook['id'] for hook in repo['hooks']]}")
        
except InvalidConfigError as e:
    print(f"Configuration error: {e}")
```

### Loading Manifest

```python
from pre_commit.clientlib import load_manifest, InvalidManifestError

try:
    manifest = load_manifest('.pre-commit-hooks.yaml')
    print(f"Found {len(manifest)} hook definitions")
    
    for hook in manifest:
        print(f"Hook: {hook['id']} ({hook['language']})")
        
except InvalidManifestError as e:
    print(f"Manifest error: {e}")
```

### Configuration Validation Functions

```python
from pre_commit.clientlib import check_type_tag, parse_version, check_min_version

# Validate file type tags
try:
    check_type_tag('python')  # Valid tag
    check_type_tag('invalid')  # Would raise ValidationError
except cfgv.ValidationError as e:
    print(f"Invalid type tag: {e}")

# Parse and compare versions
version_tuple = parse_version('1.2.3')  # Returns (1, 2, 3)

# Check minimum version requirement
try:
    check_min_version('2.0.0')
except cfgv.ValidationError as e:
    print(f"Version too old: {e}")
```

## Constants

### Configuration File Names

```python { .api }
CONFIG_FILE: str = '.pre-commit-config.yaml'
"""Default configuration file name"""

MANIFEST_FILE: str = '.pre-commit-hooks.yaml'
"""Default manifest file name"""
```

### Validation Settings

```python { .api }
DEFAULT_LANGUAGE_VERSION: cfgv.Map
"""Schema for default language version configuration"""
```