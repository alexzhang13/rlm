# Git Integration

Git repository utilities and integration functions for working with staged files, repository state, and Git workflow integration. Pre-commit provides deep integration with Git operations to enable seamless hook execution within development workflows.

## Capabilities

### Repository Information

Functions for retrieving basic repository information and paths.

```python { .api }
def get_root() -> str:
    """
    Get the root directory of the current Git repository.
    
    Returns:
    - str: Absolute path to repository root
    
    Raises:
    - CalledProcessError: If not in a Git repository
    """

def get_git_dir() -> str:
    """
    Get the .git directory path for the current repository.
    
    Returns:
    - str: Path to .git directory
    """

def get_git_common_dir() -> str:
    """
    Get the common Git directory (for worktrees).
    
    Returns:
    - str: Path to common Git directory
    """
```

### File Status and Listing

Functions for retrieving file lists based on Git status and staging state.

```python { .api }
def get_staged_files(cwd: str | None = None) -> list[str]:
    """
    Get list of files currently staged for commit.
    
    Parameters:
    - cwd: Working directory (defaults to repository root)
    
    Returns:
    - list: Staged file paths relative to repository root
    """

def get_all_files() -> list[str]:
    """
    Get all tracked files in the repository.
    
    Returns:
    - list: All tracked file paths relative to repository root
    """

def get_changed_files(old: str, new: str) -> list[str]:
    """
    Get files changed between two Git references.
    
    Parameters:
    - old: Old Git reference (commit, branch, tag)
    - new: New Git reference (commit, branch, tag)
    
    Returns:
    - list: Changed file paths between references
    """

def get_conflicted_files() -> set[str]:
    """
    Get files currently in merge conflict state.
    
    Returns:
    - set: File paths with unresolved conflicts
    """
```

### Repository State

Functions for checking repository state and conditions.

```python { .api }
def is_in_merge_conflict() -> bool:
    """
    Check if repository is currently in a merge conflict state.
    
    Returns:
    - bool: True if there are unresolved merge conflicts
    """

def is_in_rebase() -> bool:
    """
    Check if repository is currently in a rebase operation.
    
    Returns:
    - bool: True if rebase is in progress
    """

def is_in_cherry_pick() -> bool:
    """
    Check if repository is currently in a cherry-pick operation.
    
    Returns:
    - bool: True if cherry-pick is in progress
    """

def has_unmerged_paths() -> bool:
    """
    Check if repository has unmerged paths.
    
    Returns:
    - bool: True if there are unmerged paths
    """
```

### Git Configuration

Functions for reading and checking Git configuration settings.

```python { .api }
def has_core_hookpaths_set() -> bool:
    """
    Check if Git core.hooksPath configuration is set.
    
    Pre-commit needs to know if custom hook paths are configured
    to handle installation correctly.
    
    Returns:
    - bool: True if core.hooksPath is configured
    """

def get_hook_paths() -> list[str]:
    """
    Get configured Git hook paths.
    
    Returns:
    - list: Hook directory paths
    """
```

### Commit and Reference Operations

Functions for working with commits, branches, and references.

```python { .api }
def get_commit_msg(commit_msg_filename: str) -> str:
    """
    Read commit message from file.
    
    Parameters:
    - commit_msg_filename: Path to commit message file
    
    Returns:
    - str: Commit message content
    """

def set_commit_msg(commit_msg_filename: str, new_msg: str) -> None:
    """
    Write commit message to file.
    
    Parameters:
    - commit_msg_filename: Path to commit message file
    - new_msg: New commit message content
    """

def get_staged_files_intent_to_add() -> list[str]:
    """
    Get files staged with intent-to-add flag.
    
    Returns:
    - list: File paths staged with git add --intent-to-add
    """
```

### Git Command Utilities

Low-level utilities for executing Git commands and processing output.

```python { .api }
def zsplit(s: str) -> list[str]:
    """
    Split null-separated string into list.
    
    Used for processing Git output with null separators.
    
    Parameters:
    - s: Null-separated string
    
    Returns:
    - list: Split string components
    """

def no_git_env(**kwargs) -> dict[str, str]:
    """
    Create environment dictionary with Git variables removed.
    
    Useful for running commands without Git environment influence.
    
    Parameters:
    - kwargs: Additional environment variables
    
    Returns:
    - dict: Environment without Git variables
    """
```

### File Modification Detection

Functions for detecting file changes and modifications.

```python { .api }
def get_diff_files(ref1: str, ref2: str) -> list[str]:
    """
    Get files different between two references.
    
    Parameters:
    - ref1: First Git reference
    - ref2: Second Git reference
    
    Returns:
    - list: Files with differences
    """

def intent_to_add_cleared() -> bool:
    """
    Check if intent-to-add files have been cleared from index.
    
    Returns:
    - bool: True if intent-to-add state is clear
    """
```

## Git Hook Integration

### Hook Installation Paths

Functions for determining where Git hooks should be installed.

```python { .api }
def get_hook_script_path(hook_type: str) -> str:
    """
    Get the file path where a Git hook script should be installed.
    
    Parameters:
    - hook_type: Type of Git hook (pre-commit, pre-push, etc.)
    
    Returns:
    - str: Path to hook script file
    """

def hook_exists(hook_type: str) -> bool:
    """
    Check if a Git hook script already exists.
    
    Parameters:
    - hook_type: Type of Git hook to check
    
    Returns:
    - bool: True if hook script exists
    """
```

### Git Object Utilities

Functions for working with Git objects and SHA values.

```python { .api }
def get_object_name(ref: str) -> str:
    """
    Get the SHA hash for a Git reference.
    
    Parameters:
    - ref: Git reference (branch, tag, commit)
    
    Returns:
    - str: SHA hash of the object
    """

def is_valid_sha(sha: str) -> bool:
    """
    Check if string is a valid Git SHA hash.
    
    Parameters:
    - sha: String to validate
    
    Returns:
    - bool: True if valid SHA format
    """
```

## Usage Examples

### Working with Staged Files

```python
from pre_commit import git

# Get all staged files for processing
staged_files = git.get_staged_files()
print(f"Processing {len(staged_files)} staged files:")
for file_path in staged_files:
    print(f"  {file_path}")

# Check if we're in a merge conflict
if git.is_in_merge_conflict():
    print("Repository is in merge conflict state")
    conflicted = git.get_conflicted_files()
    print(f"Conflicted files: {conflicted}")
else:
    print("Repository is in clean state")
```

### Repository Information

```python
from pre_commit import git

# Get repository root
repo_root = git.get_root()
print(f"Repository root: {repo_root}")

# Check Git configuration
if git.has_core_hookpaths_set():
    print("Custom hook paths are configured")
    paths = git.get_hook_paths()
    print(f"Hook paths: {paths}")
else:
    print("Using default Git hook paths")
```

### File Change Detection

```python
from pre_commit import git

# Get all tracked files
all_files = git.get_all_files()
print(f"Repository contains {len(all_files)} tracked files")

# Get changes between commits
changed_files = git.get_changed_files('HEAD~1', 'HEAD')
print(f"Files changed in last commit: {len(changed_files)}")
for file_path in changed_files:
    print(f"  {file_path}")

# Get files staged with intent-to-add
intent_files = git.get_staged_files_intent_to_add()
if intent_files:
    print(f"Files staged with intent-to-add: {intent_files}")
```

### Environment Management

```python
from pre_commit import git
import subprocess

# Run command without Git environment variables
env = git.no_git_env(CUSTOM_VAR='value')
result = subprocess.run(
    ['some-command'],
    env=env,
    capture_output=True,
    text=True
)
```

### Repository State Checking

```python
from pre_commit import git

# Check various repository states
states = {
    'merge_conflict': git.is_in_merge_conflict(),
    'rebase': git.is_in_rebase(),
    'cherry_pick': git.is_in_cherry_pick(),
    'unmerged_paths': git.has_unmerged_paths()
}

active_states = [name for name, active in states.items() if active]
if active_states:
    print(f"Repository states: {', '.join(active_states)}")
else:
    print("Repository is in normal state")
```