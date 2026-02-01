# Hook System

Core data structures and management functions for pre-commit hooks. The hook system provides the foundation for defining, configuring, and executing individual hooks within the pre-commit framework.

## Capabilities

### Hook Data Structure

Core data structure representing a configured hook with all its properties and execution parameters.

```python { .api }
class Hook(NamedTuple):
    """
    Immutable data structure representing a configured pre-commit hook.
    
    All hook properties are defined at initialization and cannot be modified
    during execution, ensuring consistent behavior across hook runs.
    """
    src: str                                    # Repository source URL or 'local'
    prefix: Prefix                              # Installation directory prefix
    id: str                                     # Unique hook identifier
    name: str                                   # Display name for output
    entry: str                                  # Command or script to execute
    language: str                               # Programming language (python, node, etc.)
    alias: str                                  # Alternative name for hook
    files: str                                  # File pattern regex for inclusion
    exclude: str                                # File pattern regex for exclusion
    types: Sequence[str]                        # File types to include
    types_or: Sequence[str]                     # Alternative file types (OR logic)
    exclude_types: Sequence[str]                # File types to exclude
    additional_dependencies: Sequence[str]       # Extra dependencies to install
    args: Sequence[str]                         # Command-line arguments
    always_run: bool                            # Run even if no files match
    fail_fast: bool                             # Stop execution on first failure
    pass_filenames: bool                        # Pass matched filenames to hook
    description: str                            # Human-readable description
    language_version: str                       # Specific language version
    log_file: str                               # Output log file path
    minimum_pre_commit_version: str             # Required pre-commit version
    require_serial: bool                        # Require serial execution
    stages: Sequence[str]                       # Git hook stages when this runs
    verbose: bool                               # Enable verbose output
```

### Prefix System

Directory management system for hook installations and environments.

```python { .api }
class Prefix(NamedTuple):
    """
    Directory path management for hook installations.
    
    Provides utilities for constructing paths within hook installation
    directories and checking for file existence.
    """
    prefix_dir: str                             # Base installation directory
    
    def path(self, *parts: str) -> str:
        """
        Construct path within prefix directory.
        
        Parameters:
        - parts: Path components to join
        
        Returns:
        - str: Complete path within prefix
        """
    
    def exists(self, *parts: str) -> bool:
        """
        Check if path exists within prefix directory.
        
        Parameters:
        - parts: Path components to check
        
        Returns:
        - bool: True if path exists
        """
    
    def star(self, end: str) -> tuple[str, ...]:
        """
        Glob pattern matching within prefix directory.
        
        Parameters:
        - end: Pattern to match
        
        Returns:
        - tuple: Matching file paths
        """
```

### Hook Management Functions

Functions for processing and managing collections of hooks.

```python { .api }
def all_hooks(root_config: dict[str, Any], store: Store) -> tuple[Hook, ...]:
    """
    Extract all configured hooks from configuration.
    
    Processes the configuration file and creates Hook instances for all
    defined hooks, handling repository cloning and hook resolution.
    
    Parameters:
    - root_config: Loaded configuration dictionary
    - store: Store instance for repository management
    
    Returns:
    - tuple: All configured Hook instances
    """

def install_hook_envs(hooks: Sequence[Hook], store: Store) -> None:
    """
    Install environments for all provided hooks.
    
    Sets up the necessary runtime environments for each hook,
    including language-specific dependencies and tools.
    
    Parameters:
    - hooks: Sequence of hooks to install environments for
    - store: Store instance for environment management
    """
```

### Hook Filtering and Selection

Functions for filtering hooks based on various criteria.

```python { .api }
def filter_by_include_exclude(
    hook: Hook, 
    filenames: Sequence[str],
    include: str = '',
    exclude: str = ''
) -> Sequence[str]:
    """
    Filter filenames based on hook's include/exclude patterns.
    
    Parameters:
    - hook: Hook with filtering configuration
    - filenames: Files to filter  
    - include: Additional include pattern
    - exclude: Additional exclude pattern
    
    Returns:
    - Sequence: Filtered filenames
    """

def classify_by_types(
    filenames: Sequence[str],
    types: Sequence[str],
    types_or: Sequence[str] = (),
    exclude_types: Sequence[str] = ()
) -> Sequence[str]:
    """
    Classify and filter files by type.
    
    Parameters:
    - filenames: Files to classify
    - types: Required file types (AND logic)
    - types_or: Alternative file types (OR logic)  
    - exclude_types: File types to exclude
    
    Returns:
    - Sequence: Files matching type criteria
    """
```

## Hook Execution

### Hook Runner

Core hook execution functionality with environment management and output handling.

```python { .api }
def run_hook(
    hook: Hook,
    file_args: Sequence[str],
    color: bool = True
) -> tuple[int, bytes, int]:
    """
    Execute a single hook with provided file arguments.
    
    Parameters:
    - hook: Hook instance to execute
    - file_args: Files to pass to hook
    - color: Enable colored output
    
    Returns:
    - tuple: (return_code, stdout_bytes, duration_ms)
    """
```

### Hook Output Formatting

Functions for formatting and displaying hook execution results.

```python { .api }
def get_hook_message(
    hook: Hook,
    return_code: int,
    file_count: int,
    duration_ms: int,
    color: bool = True
) -> str:
    """
    Format hook execution result message.
    
    Parameters:
    - hook: Executed hook
    - return_code: Hook exit code
    - file_count: Number of files processed
    - duration_ms: Execution duration
    - color: Use colored output
    
    Returns:
    - str: Formatted status message
    """

def format_hook_output(
    hook: Hook,
    output: bytes,
    use_color: bool = True
) -> str:
    """
    Format hook output for display.
    
    Parameters:
    - hook: Hook that produced output
    - output: Raw output bytes
    - use_color: Enable colored formatting
    
    Returns:
    - str: Formatted output string
    """
```

## Hook Creation and Processing

### Hook Factory Functions

Functions for creating Hook instances from configuration data.

```python { .api }
def _hook_from_config(
    hook: dict[str, Any],
    prefix: Prefix,
    manifest: dict[str, Any],
    root_config: dict[str, Any]
) -> Hook:
    """
    Create Hook instance from configuration and manifest data.
    
    Parameters:
    - hook: Hook configuration from .pre-commit-config.yaml
    - prefix: Installation prefix for hook
    - manifest: Hook definition from .pre-commit-hooks.yaml
    - root_config: Root configuration context
    
    Returns:
    - Hook: Configured hook instance
    """
```

### Local Hook Support

Support for locally defined hooks without external repositories.

```python { .api }
def local_hook(
    hook_dict: dict[str, Any],
    prefix: Prefix
) -> Hook:
    """
    Create hook from local configuration.
    
    Parameters:
    - hook_dict: Local hook configuration
    - prefix: Installation prefix
    
    Returns:
    - Hook: Local hook instance
    """
```

## Hook Stages and Types

### Supported Hook Stages

```python { .api }
HOOK_TYPES = (
    'commit-msg',           # Commit message validation
    'post-checkout',        # After checkout operations  
    'post-commit',          # After successful commit
    'post-merge',           # After merge operations
    'post-rewrite',         # After rewrite operations
    'pre-commit',           # Before commit (default)
    'pre-merge-commit',     # Before merge commits
    'pre-push',             # Before push operations
    'pre-rebase',           # Before rebase operations
    'prepare-commit-msg'    # Commit message preparation
)

STAGES = (*HOOK_TYPES, 'manual')  # All types plus manual execution
```

## Usage Examples

### Working with Hook Instances

```python
from pre_commit.hook import Hook
from pre_commit.prefix import Prefix

# Create a prefix for hook installation
prefix = Prefix('/path/to/hook/env')

# Hook instances are typically created by all_hooks()
# but can be constructed directly for testing
hook = Hook(
    src='https://github.com/psf/black',
    prefix=prefix,
    id='black',
    name='black',
    entry='black',
    language='python',
    alias='',
    files='\.py$',
    exclude='',
    types=['python'],
    types_or=[],
    exclude_types=[],
    additional_dependencies=[],
    args=[],
    always_run=False,
    fail_fast=False,
    pass_filenames=True,
    description='The uncompromising Python code formatter',
    language_version='default',
    log_file='',
    minimum_pre_commit_version='2.9.2',
    require_serial=False,
    stages=['pre-commit'],
    verbose=False
)

# Check hook properties
print(f"Hook: {hook.name} ({hook.language})")
print(f"Files pattern: {hook.files}")
print(f"Always run: {hook.always_run}")
```

### Loading All Hooks from Configuration

```python
from pre_commit.repository import all_hooks
from pre_commit.clientlib import load_config
from pre_commit.store import Store

# Load configuration and create store
config = load_config('.pre-commit-config.yaml')
store = Store()

# Get all configured hooks
hooks = all_hooks(config, store)

print(f"Found {len(hooks)} hooks:")
for hook in hooks:
    print(f"  {hook.id}: {hook.name} ({hook.language})")
```

### Installing Hook Environments

```python
from pre_commit.repository import install_hook_envs

# Install environments for all hooks
install_hook_envs(hooks, store)
print("All hook environments installed")
```