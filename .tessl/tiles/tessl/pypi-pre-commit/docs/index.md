# Pre-commit

A framework for managing and maintaining multi-language pre-commit hooks. Pre-commit enables automatic execution of code quality checks, linting, formatting, and testing before commits are made to version control systems, supporting multiple programming languages and providing a plugin-based architecture for extensibility.

## Package Information

- **Package Name**: pre-commit
- **Package Type**: pypi
- **Language**: Python
- **Installation**: `pip install pre-commit`

## Core Imports

```python
import pre_commit
```

For programmatic API usage:

```python
from pre_commit.main import main
from pre_commit.store import Store
from pre_commit.hook import Hook
from pre_commit.clientlib import load_config, load_manifest, HOOK_TYPES, STAGES
from pre_commit import git
from pre_commit import constants as C
from pre_commit.errors import FatalError, InvalidConfigError, InvalidManifestError
from pre_commit.util import cmd_output, CalledProcessError
from pre_commit.color import format_color, use_color
from pre_commit.output import write_line
```

## Basic Usage

### Command Line Interface

```bash
# Install git hook scripts
pre-commit install

# Run hooks on all files
pre-commit run --all-files

# Run hooks on staged files only
pre-commit run

# Auto-update hook versions
pre-commit autoupdate

# Validate configuration
pre-commit validate-config
```

### Programmatic Usage

```python
from pre_commit.main import main
from pre_commit.store import Store
from pre_commit.clientlib import load_config, InvalidConfigError
from pre_commit.errors import FatalError

# Run pre-commit programmatically
exit_code = main(['run', '--all-files'])

# Load and validate configuration with error handling
try:
    config = load_config('.pre-commit-config.yaml')
    print(f"Loaded config with {len(config['repos'])} repositories")
except InvalidConfigError as e:
    print(f"Configuration error: {e}")
except FatalError as e:
    print(f"Fatal error: {e}")

# Initialize store for hook management
store = Store()

# Example: Clone a repository for hook usage
repo_path = store.clone('https://github.com/psf/black', 'main')
print(f"Repository cloned to: {repo_path}")
```

## Architecture

Pre-commit follows a modular architecture built around several key components:

- **CLI Commands**: Command-line interface providing installation, execution, and management functionality
- **Hook System**: Data structures and execution framework for individual hooks
- **Language Support**: Plugin-based architecture supporting 22+ programming languages
- **Configuration Management**: YAML-based configuration loading and validation
- **Git Integration**: Deep integration with Git workflows and repository operations
- **Repository Management**: Store system for managing hook repositories and environments

This design enables pre-commit to serve as a comprehensive framework for maintaining code quality across diverse development environments and language ecosystems.

## Capabilities

### CLI Commands

Complete command-line interface for installing, managing, and executing pre-commit hooks. Includes installation commands, hook execution, configuration management, and utility operations.

```python { .api }
def main(argv: Sequence[str] | None = None) -> int
```

[CLI Commands](./cli-commands.md)

### Configuration Management

Configuration loading, validation, and schema definitions for .pre-commit-config.yaml and .pre-commit-hooks.yaml files.

```python { .api }
load_config: functools.partial[dict[str, Any]]
# Partial function for loading .pre-commit-config.yaml files
# Usage: config = load_config(filename)

load_manifest: functools.partial[list[dict[str, Any]]]
# Partial function for loading .pre-commit-hooks.yaml files  
# Usage: hooks = load_manifest(filename)
```

[Configuration](./configuration.md)

### Hook System

Core data structures and management functions for pre-commit hooks, including hook representation, execution, and environment management.

```python { .api }
class Hook(NamedTuple):
    src: str
    prefix: Prefix
    id: str
    name: str
    entry: str
    language: str
    alias: str
    files: str
    exclude: str
    types: Sequence[str]
    types_or: Sequence[str]
    exclude_types: Sequence[str]
    additional_dependencies: Sequence[str]
    args: Sequence[str]
    always_run: bool
    fail_fast: bool
    pass_filenames: bool
    description: str
    language_version: str
    log_file: str
    minimum_pre_commit_version: str
    require_serial: bool
    stages: Sequence[str]
    verbose: bool
```

[Hooks](./hooks.md)

### Git Integration

Git repository utilities and integration functions for working with staged files, repository state, and Git workflow integration.

```python { .api }
def get_root() -> str
def get_staged_files(cwd: str | None = None) -> list[str]
def get_all_files() -> list[str]
```

[Git Integration](./git-integration.md)

### Language Support

Multi-language support system with plugin-based architecture for 22+ programming languages including Python, JavaScript, Go, Rust, and more.

```python { .api }
class Language(Protocol):
    def get_default_version(self) -> str
    def install_environment(self, prefix: Prefix, version: str, additional_dependencies: Sequence[str]) -> None
    def run_hook(self, prefix: Prefix, version: str, cmd: Sequence[str], **kwargs) -> tuple[int, bytes]
```

[Language Support](./language-support.md)

### Repository Management

Repository and hook environment management through the Store system, including cloning, caching, and cleanup operations.

```python { .api }
class Store:
    def clone(self, repo: str, ref: str, deps: Sequence[str] = ()) -> str
    def make_local(self, deps: Sequence[str]) -> str
    def select_all_repos(self) -> list[tuple[str, str, str]]
```

[Repository Management](./repository-management.md)

## Constants and Error Handling

### Constants

```python { .api }
CONFIG_FILE: str = '.pre-commit-config.yaml'
MANIFEST_FILE: str = '.pre-commit-hooks.yaml'
LOCAL_REPO_VERSION: str = '1'
DEFAULT: str = 'default'
VERSION: str  # Package version string

# Hook types and stages
HOOK_TYPES: tuple[str, ...] = (
    'commit-msg', 'post-checkout', 'post-commit', 'post-merge',
    'post-rewrite', 'pre-commit', 'pre-merge-commit', 'pre-push',
    'pre-rebase', 'prepare-commit-msg'
)
STAGES: tuple[str, ...] = (*HOOK_TYPES, 'manual')

# Repository types
LOCAL: str = 'local'
META: str = 'meta'

# Color constants
RED: str
GREEN: str
YELLOW: str
TURQUOISE: str
SUBTLE: str
NORMAL: str
COLOR_CHOICES: tuple[str, ...] = ('auto', 'always', 'never')
```

### Exceptions

```python { .api }
class FatalError(RuntimeError):
    """Base exception for fatal errors"""

class InvalidConfigError(FatalError):
    """Configuration validation errors"""

class InvalidManifestError(FatalError):
    """Manifest validation errors"""

class CalledProcessError(RuntimeError):
    """Enhanced subprocess error with stdout/stderr capture"""
    returncode: int
    cmd: tuple[str, ...]
    stdout: bytes
    stderr: bytes | None
```

### Utility Functions

Core utility functions for process execution, file operations, and resource management.

```python { .api }
def cmd_output(*cmd: str, **kwargs: Any) -> tuple[int, str, str | None]:
    """Execute command and return exit code, stdout, stderr as strings"""

def cmd_output_b(*cmd: str, check: bool = True, **kwargs: Any) -> tuple[int, bytes, bytes | None]:
    """Execute command and return exit code, stdout, stderr as bytes"""

def make_executable(filename: str) -> None:
    """Make file executable"""

def resource_text(filename: str) -> str:
    """Read text from package resource file"""

def clean_path_on_failure(path: str) -> Generator[None, None, None]:
    """Context manager that removes path on exception"""
```

### Color Support

Functions for colored terminal output.

```python { .api }
def format_color(text: str, color: str, use_color_setting: bool) -> str:
    """Format text with ANSI color codes"""

def use_color(setting: str) -> bool:
    """Determine if color should be used based on setting"""

def add_color_option(parser: argparse.ArgumentParser) -> None:
    """Add --color argument to argument parser"""
```

### Output Functions

Terminal output utilities with optional logging support.

```python { .api }
def write(s: str, stream: IO[bytes] = sys.stdout.buffer) -> None:
    """Write string to byte stream"""

def write_line(s: str | None = None, **kwargs: Any) -> None:
    """Write line to output with optional logging"""

def write_line_b(s: bytes | None = None, stream: IO[bytes] = sys.stdout.buffer, logfile_name: str | None = None) -> None:
    """Write line as bytes to output with optional logging"""
```