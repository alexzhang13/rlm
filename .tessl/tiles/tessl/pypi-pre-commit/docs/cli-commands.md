# CLI Commands

Complete command-line interface for pre-commit hook management. All commands are executed through the `pre-commit` console script entry point, which routes to the appropriate command implementations.

## Capabilities

### Main Entry Point

Primary entry point for all CLI commands that parses arguments and routes to appropriate command handlers.

```python { .api }
def main(argv: Sequence[str] | None = None) -> int:
    """
    Main CLI entry point for pre-commit commands.
    
    Parameters:
    - argv: Optional command-line arguments array
    
    Returns:
    - int: Exit code (0 for success, non-zero for failure)
    """
```

### Installation Commands

Commands for installing and managing pre-commit hook scripts in Git repositories.

```python { .api }
def install(
    config_file: str,
    store: Store,
    hook_types: list[str] | None,
    overwrite: bool = False,
    hooks: bool = False,
    skip_on_missing_config: bool = False,
    git_dir: str | None = None,
) -> int:
    """
    Install git hook scripts.
    
    Parameters:
    - config_file: Path to configuration file
    - store: Store instance for hook management
    - hook_types: List of git hook types to install
    - overwrite: Whether to overwrite existing hooks
    - hooks: Whether to install hook environments too
    - skip_on_missing_config: Skip installation if config missing
    - git_dir: Git directory path (optional)
    
    Returns:
    - int: Exit code
    """

def uninstall(config_file: str, hook_types: list[str] | None) -> int:
    """
    Remove git hook scripts.
    
    Parameters:
    - config_file: Path to configuration file
    - hook_types: List of git hook types to uninstall
    
    Returns:
    - int: Exit code
    """

def install_hooks(config_file: str, store: Store) -> int:
    """
    Install hook environments for all configured hooks.
    
    Parameters:
    - config_file: Path to configuration file
    - store: Store instance for hook management
    
    Returns:
    - int: Exit code
    """

def init_templatedir(
    config_file: str,
    store: Store,
    directory: str,
    hook_types: list[str] | None,
    skip_on_missing_config: bool = True,
) -> int:
    """
    Setup hooks in git template directory.
    
    Parameters:
    - config_file: Path to configuration file
    - store: Store instance for hook management
    - directory: Template directory path
    - hook_types: List of git hook types to install
    - skip_on_missing_config: Skip installation if config missing
    
    Returns:
    - int: Exit code
    """
```

### Hook Execution Commands

Commands for running pre-commit hooks on files with various filtering and execution options.

```python { .api }
def run(
    config_file: str,
    store: Store,
    args: argparse.Namespace,
    environ: MutableMapping[str, str] = os.environ,
) -> int:
    """
    Execute hooks with file filtering and staging options.
    
    Parameters:
    - config_file: Path to configuration file
    - store: Store instance for hook management
    - all_files: Run on all files instead of just staged
    - files: Specific files to run on
    - hook_stage: Git hook stage to run
    - hook: Run only specific hook by id
    - from_ref: Git ref to compare from
    - to_ref: Git ref to compare to
    - show_diff_on_failure: Show diff when hooks fail
    - color: Color output mode ('auto', 'always', 'never')
    - verbose: Verbose output
    
    Returns:
    - int: Exit code (0 if all hooks pass)
    """

def hook_impl(config_file: str, hook_type: str, hook_dir: str | None = None,
             skip_on_missing_config: bool = False, **kwargs) -> int:
    """
    Internal hook implementation (not for direct user use).
    
    Parameters:
    - config_file: Path to configuration file
    - hook_type: Type of git hook being executed
    - hook_dir: Hook directory path
    - skip_on_missing_config: Skip if config missing
    
    Returns:
    - int: Exit code
    """
```

### Configuration Management Commands

Commands for managing, validating, and updating pre-commit configuration files.

```python { .api }
def autoupdate(config_file: str = '.pre-commit-config.yaml', store: Store | None = None,
              tags_only: bool = False, bleeding_edge: bool = False,
              freeze: bool = False, repo: Sequence[str] = (),
              jobs: int = 1) -> int:
    """
    Auto-update repository versions in configuration.
    
    Parameters:
    - config_file: Path to configuration file
    - store: Store instance for repository management
    - tags_only: Only use tagged versions
    - bleeding_edge: Use latest commit instead of latest tag
    - freeze: Store exact commit hash instead of tag
    - repo: Update only specific repositories
    - jobs: Number of concurrent jobs
    
    Returns:
    - int: Exit code
    """

def migrate_config(config_file: str = '.pre-commit-config.yaml') -> int:
    """
    Migrate configuration file to latest format.
    
    Parameters:
    - config_file: Path to configuration file
    
    Returns:
    - int: Exit code
    """

def validate_config(filenames: Sequence[str]) -> int:
    """
    Validate .pre-commit-config.yaml files.
    
    Parameters:
    - filenames: List of config files to validate
    
    Returns:
    - int: Exit code (0 if all valid)
    """

def validate_manifest(filenames: Sequence[str]) -> int:
    """
    Validate .pre-commit-hooks.yaml manifest files.
    
    Parameters:
    - filenames: List of manifest files to validate
    
    Returns:
    - int: Exit code (0 if all valid)
    """
```

### Utility Commands

Utility commands for testing, configuration generation, and maintenance operations.

```python { .api }
def sample_config() -> int:
    """
    Generate sample .pre-commit-config.yaml configuration.
    
    Returns:
    - int: Exit code
    """

def try_repo(repo: str, ref: str = 'HEAD', **kwargs) -> int:
    """
    Test hooks from a repository without modifying configuration.
    
    Parameters:
    - repo: Repository URL or path
    - ref: Git reference to use
    
    Returns:
    - int: Exit code
    """

def clean(store: Store | None = None) -> int:
    """
    Clean pre-commit cache and temporary files.
    
    Parameters:
    - store: Store instance for cleanup operations
    
    Returns:
    - int: Exit code
    """

def gc(store: Store | None = None) -> int:
    """
    Garbage collect unused repositories and environments.
    
    Parameters:
    - store: Store instance for garbage collection
    
    Returns:
    - int: Exit code
    """
```

## Hook Types and Stages

### Supported Git Hook Types

```python { .api }
HOOK_TYPES = (
    'commit-msg', 'post-checkout', 'post-commit', 'post-merge',
    'post-rewrite', 'pre-commit', 'pre-merge-commit', 'pre-push',
    'pre-rebase', 'prepare-commit-msg'
)

STAGES = (*HOOK_TYPES, 'manual')
```

### Commands Without Git Repository Requirement

```python { .api }
COMMANDS_NO_GIT = {
    'clean', 'gc', 'init-templatedir', 'sample-config',
    'validate-config', 'validate-manifest',
}
```

## Usage Examples

### Basic Command Usage

```python
from pre_commit.main import main

# Install hooks
exit_code = main(['install'])

# Run all hooks
exit_code = main(['run', '--all-files'])

# Auto-update configuration
exit_code = main(['autoupdate'])

# Validate configuration
exit_code = main(['validate-config', '.pre-commit-config.yaml'])
```

### Advanced Command Usage

```python
# Run specific hook with verbose output
exit_code = main(['run', '--hook', 'flake8', '--verbose'])

# Run on specific files
exit_code = main(['run', '--files', 'file1.py', 'file2.py'])

# Show diff on failure
exit_code = main(['run', '--show-diff-on-failure'])

# Try hooks from external repository
exit_code = main(['try-repo', 'https://github.com/psf/black'])
```