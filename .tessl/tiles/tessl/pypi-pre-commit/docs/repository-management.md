# Repository Management

Repository and hook environment management through the Store system. The Store provides centralized management of hook repositories, environment caching, and cleanup operations for efficient hook execution and storage.

## Capabilities

### Store Class

Central repository and environment management system that handles cloning, caching, and lifecycle management of hook repositories.

```python { .api }
class Store:
    """
    Centralized store for managing hook repositories and environments.
    
    Provides caching, cloning, and cleanup functionality for hook repositories
    and their associated environments. Manages the complete lifecycle from
    initial repository cloning through environment installation to cleanup.
    """
    
    def __init__(self, directory: str | None = None) -> None:
        """
        Initialize store with optional custom directory.
        
        Parameters:
        - directory: Custom store directory path (uses default if None)
        """
    
    def clone(self, repo: str, ref: str, deps: Sequence[str] = ()) -> str:
        """
        Clone repository and return installation path.
        
        Clones the specified repository at the given reference and prepares
        it for hook installation. Handles caching to avoid duplicate clones.
        
        Parameters:
        - repo: Repository URL or local path
        - ref: Git reference (tag, commit, branch)
        - deps: Additional dependencies for environment
        
        Returns:
        - str: Path to cloned repository installation
        """
    
    def make_local(self, deps: Sequence[str]) -> str:
        """
        Create local repository installation for local hooks.
        
        Sets up environment for locally defined hooks without external repository.
        
        Parameters:
        - deps: Dependencies for local hook environment
        
        Returns:
        - str: Path to local installation
        """
    
    def mark_config_used(self, path: str) -> None:
        """
        Mark configuration as recently used for garbage collection.
        
        Parameters:
        - path: Configuration file path to mark as used
        """
    
    def select_all_configs(self) -> list[str]:
        """
        Get all configuration files tracked by the store.
        
        Returns:
        - list: Paths to all tracked configuration files
        """
    
    def delete_configs(self, configs: list[str]) -> None:
        """
        Delete specified configuration files from tracking.
        
        Parameters:
        - configs: List of configuration paths to delete
        """
    
    def select_all_repos(self) -> list[tuple[str, str, str]]:
        """
        Get all repositories managed by the store.
        
        Returns:
        - list: Tuples of (repo_name, ref, path) for each repository
        """
    
    def delete_repo(self, db_repo_name: str, ref: str, path: str) -> None:
        """
        Delete repository from store and filesystem.
        
        Parameters:
        - db_repo_name: Database repository name
        - ref: Git reference
        - path: Repository path to delete
        """
    
    @staticmethod
    def get_default_directory() -> str:
        """
        Get the default store directory path.
        
        Returns:
        - str: Default store directory (typically ~/.cache/pre-commit)
        """
```

### Repository Operations

High-level functions for working with repositories through the store system.

```python { .api }
def all_hooks(root_config: dict[str, Any], store: Store) -> tuple[Hook, ...]:
    """
    Extract all configured hooks from configuration using store.
    
    Processes the complete configuration file, clones required repositories
    through the store, and creates Hook instances for all defined hooks.
    
    Parameters:
    - root_config: Loaded configuration dictionary
    - store: Store instance for repository management
    
    Returns:
    - tuple: All configured Hook instances
    """

def install_hook_envs(hooks: Sequence[Hook], store: Store) -> None:
    """
    Install environments for all provided hooks using store.
    
    Coordinates with the store to ensure all hook environments are properly
    installed and configured with their dependencies.
    
    Parameters:
    - hooks: Sequence of hooks requiring environment installation
    - store: Store instance for environment management
    """
```

### Store Database Management

Internal database operations for tracking repositories and configurations.

```python { .api }
def _get_store_db(store_dir: str) -> sqlite3.Connection:
    """
    Get database connection for store operations.
    
    Parameters:
    - store_dir: Store directory path
    
    Returns:
    - Connection: SQLite database connection
    """

def _init_store_db(db: sqlite3.Connection) -> None:
    """
    Initialize store database with required tables.
    
    Parameters:
    - db: Database connection to initialize
    """
```

## Store Configuration

### Directory Structure

The store maintains a structured directory layout for efficient organization:

```
~/.cache/pre-commit/          # Default store directory
├── db.db                     # SQLite database for tracking
├── repos/                    # Cloned repositories
│   ├── <repo-hash>/         # Individual repository directories
│   │   ├── .git/           # Git repository data
│   │   └── <hook-files>    # Hook implementation files
│   └── ...
└── <language-envs>/         # Language-specific environments
    ├── py_env-<hash>/      # Python virtual environments
    ├── node_env-<hash>/    # Node.js environments
    └── ...
```

### Store Initialization

```python { .api }
def initialize_store(directory: str | None = None) -> Store:
    """
    Initialize a new store instance.
    
    Parameters:
    - directory: Custom directory (uses default if None)
    
    Returns:
    - Store: Initialized store instance
    """
```

## Repository Caching

### Cache Management

Functions for managing repository and environment caches.

```python { .api }
def clean_unused_repos(store: Store, configs_in_use: set[str]) -> None:
    """
    Clean repositories not referenced by active configurations.
    
    Parameters:
    - store: Store instance to clean
    - configs_in_use: Set of configuration files still in use
    """

def get_cache_stats(store: Store) -> dict[str, Any]:
    """
    Get statistics about store cache usage.
    
    Parameters:
    - store: Store instance to analyze
    
    Returns:
    - dict: Cache statistics including size, file counts, etc.
    """
```

### Garbage Collection

```python { .api }
def garbage_collect_repos(store: Store) -> int:
    """
    Perform garbage collection on unused repositories.
    
    Removes repositories and environments that are no longer referenced
    by any active configurations.
    
    Parameters:
    - store: Store instance to garbage collect
    
    Returns:
    - int: Number of items removed
    """
```

## Environment Management

### Environment Installation

```python { .api }
def ensure_environment(
    hook: Hook, 
    store: Store,
    language_version: str
) -> None:
    """
    Ensure hook environment is installed and ready.
    
    Parameters:
    - hook: Hook requiring environment
    - store: Store instance for management
    - language_version: Specific language version to use
    """
```

### Environment Health Checks

```python { .api }
def check_environment_health(
    prefix: Prefix,
    language: str,
    version: str
) -> str | None:
    """
    Check if environment is healthy and functional.
    
    Parameters:
    - prefix: Environment installation prefix
    - language: Programming language
    - version: Language version
    
    Returns:
    - str | None: Error message if unhealthy, None if healthy
    """
```

## Usage Examples

### Basic Store Operations

```python
from pre_commit.store import Store
from pre_commit.clientlib import load_config
from pre_commit.repository import all_hooks, install_hook_envs

# Initialize store (uses default directory)
store = Store()

# Or initialize with custom directory
custom_store = Store('/path/to/custom/store')

# Load configuration and get all hooks
config = load_config('.pre-commit-config.yaml')
hooks = all_hooks(config, store)

print(f"Found {len(hooks)} hooks from {len(config['repos'])} repositories")

# Install environments for all hooks
install_hook_envs(hooks, store)
print("All hook environments installed")
```

### Repository Cloning and Management

```python
from pre_commit.store import Store

store = Store()

# Clone specific repository
repo_path = store.clone(
    repo='https://github.com/psf/black',
    ref='22.3.0',
    deps=['black[jupyter]']
)
print(f"Repository cloned to: {repo_path}")

# Create local environment
local_path = store.make_local(deps=['flake8', 'mypy'])
print(f"Local environment created at: {local_path}")

# Mark configuration as used (for garbage collection)
store.mark_config_used('.pre-commit-config.yaml')
```

### Store Maintenance

```python
from pre_commit.store import Store

store = Store()

# Get all repositories managed by store
repos = store.select_all_repos()
print(f"Store manages {len(repos)} repositories:")
for repo_name, ref, path in repos:
    print(f"  {repo_name}@{ref} -> {path}")

# Get all tracked configurations
configs = store.select_all_configs()
print(f"Tracking {len(configs)} configurations:")
for config_path in configs:
    print(f"  {config_path}")

# Clean up unused configurations
# (In practice, you'd determine which are actually unused)
# store.delete_configs(['/path/to/unused/config.yaml'])
```

### Cache Statistics and Cleanup

```python
from pre_commit.store import Store, get_cache_stats, garbage_collect_repos

store = Store()

# Get cache statistics
stats = get_cache_stats(store)
print(f"Cache statistics:")
print(f"  Total repositories: {stats.get('repo_count', 0)}")
print(f"  Total size: {stats.get('total_size', 0)} bytes")
print(f"  Environments: {stats.get('env_count', 0)}")

# Perform garbage collection
removed_count = garbage_collect_repos(store)
print(f"Garbage collection removed {removed_count} unused items")
```

### Working with Store Directory

```python
from pre_commit.store import Store

# Get default store directory
default_dir = Store.get_default_directory()
print(f"Default store directory: {default_dir}")

# Initialize store with explicit directory
store = Store(directory='/tmp/pre-commit-store')

# Verify store is using correct directory
# (Store doesn't expose directory directly, but you can check filesystem)
import os
if os.path.exists('/tmp/pre-commit-store'):
    print("Custom store directory created successfully")
```

### Advanced Repository Operations

```python
from pre_commit.store import Store

store = Store()

# Work with multiple repositories
repositories = [
    ('https://github.com/psf/black', '22.3.0'),
    ('https://github.com/pycqa/flake8', '4.0.1'),
    ('https://github.com/pre-commit/mirrors-mypy', 'v0.950')
]

repo_paths = []
for repo_url, ref in repositories:
    path = store.clone(repo=repo_url, ref=ref)
    repo_paths.append(path)
    print(f"Cloned {repo_url}@{ref} to {path}")

print(f"Successfully cloned {len(repo_paths)} repositories")

# Clean up specific repository if needed
# store.delete_repo('repo-name', 'ref', '/path/to/repo')
```