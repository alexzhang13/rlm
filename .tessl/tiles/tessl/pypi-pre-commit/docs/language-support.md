# Language Support

Multi-language support system with plugin-based architecture for 22+ programming languages. Pre-commit provides a standardized interface for integrating hooks written in different programming languages, each with their own environment management and execution requirements.

## Capabilities

### Language Protocol

Base protocol that all language implementations must follow.

```python { .api }
class Language(Protocol):
    """
    Protocol defining the interface for language implementations.
    
    Each supported language must implement this protocol to provide
    consistent environment management and hook execution.
    """
    
    @property
    def ENVIRONMENT_DIR(self) -> str | None:
        """
        Directory name for language-specific environments.
        
        Returns None for languages that don't require separate environments.
        
        Returns:
        - str | None: Environment directory name or None
        """
    
    def get_default_version(self) -> str:
        """
        Get the default version identifier for this language.
        
        Returns:
        - str: Default version string (e.g., 'default', 'system')
        """
    
    def health_check(self, prefix: Prefix, version: str) -> str | None:
        """
        Check if the language environment is healthy and functional.
        
        Parameters:
        - prefix: Installation prefix for the environment
        - version: Language version to check
        
        Returns:
        - str | None: Error message if unhealthy, None if healthy
        """
    
    def install_environment(
        self, 
        prefix: Prefix, 
        version: str, 
        additional_dependencies: Sequence[str]
    ) -> None:
        """
        Install or update the language environment.
        
        Parameters:
        - prefix: Installation prefix for the environment
        - version: Language version to install
        - additional_dependencies: Extra packages to install
        """
    
    def in_env(self, prefix: Prefix, version: str) -> ContextManager[None]:
        """
        Context manager for executing within the language environment.
        
        Parameters:
        - prefix: Installation prefix for the environment
        - version: Language version to use
        
        Returns:
        - ContextManager: Context for environment activation
        """
    
    def run_hook(
        self,
        prefix: Prefix,
        version: str,
        cmd: Sequence[str],
        *,
        file_args: Sequence[str],
        prepend_base_dir: bool,
        require_serial: bool,
        color: bool
    ) -> tuple[int, bytes]:
        """
        Execute a hook within the language environment.
        
        Parameters:
        - prefix: Installation prefix for the environment
        - version: Language version to use
        - cmd: Command and arguments to execute
        - file_args: Files to pass to the hook
        - prepend_base_dir: Whether to prepend base directory to paths
        - require_serial: Whether serial execution is required
        - color: Whether to enable colored output
        
        Returns:
        - tuple: (exit_code, output_bytes)
        """
```

### Supported Languages

Complete registry of supported languages with their implementations.

```python { .api }
languages: dict[str, Language] = {
    'conda': conda,                    # Conda package manager
    'coursier': coursier,              # Scala/Coursier dependency manager
    'dart': dart,                      # Dart programming language
    'docker': docker,                  # Docker containers
    'docker_image': docker_image,      # Pre-built Docker images
    'dotnet': dotnet,                  # .NET framework
    'fail': fail,                      # Always-fail hook for testing
    'golang': golang,                  # Go programming language
    'haskell': haskell,                # Haskell programming language
    'julia': julia,                    # Julia programming language
    'lua': lua,                        # Lua programming language
    'node': node,                      # Node.js/npm
    'perl': perl,                      # Perl programming language
    'pygrep': pygrep,                  # Python regex-based hooks
    'python': python,                  # Python programming language
    'r': r,                            # R programming language
    'ruby': ruby,                      # Ruby programming language
    'rust': rust,                      # Rust programming language
    'script': script,                  # Shell scripts
    'swift': swift,                    # Swift programming language
    'system': system                   # System executables
}
```

## Individual Language Implementations

### Python Language Support

```python { .api }
class PythonLanguage:
    """Python language implementation with virtual environment support."""
    
    ENVIRONMENT_DIR = 'py_env'
    
    def get_default_version(self) -> str:
        """Returns 'python3' as default Python version."""
    
    def install_environment(
        self, 
        prefix: Prefix, 
        version: str, 
        additional_dependencies: Sequence[str]
    ) -> None:
        """
        Create virtual environment and install dependencies.
        
        Creates a Python virtual environment and installs the hook
        package along with any additional dependencies.
        """
    
    def run_hook(self, prefix: Prefix, version: str, cmd: Sequence[str], **kwargs) -> tuple[int, bytes]:
        """Execute hook within Python virtual environment."""
```

### Node.js Language Support

```python { .api }
class NodeLanguage:
    """Node.js language implementation with npm package management."""
    
    ENVIRONMENT_DIR = 'node_env'
    
    def get_default_version(self) -> str:
        """Returns 'node' as default Node.js version."""
    
    def install_environment(
        self, 
        prefix: Prefix, 
        version: str, 
        additional_dependencies: Sequence[str]
    ) -> None:
        """
        Install Node.js packages using npm.
        
        Sets up npm environment and installs hook package with dependencies.
        """
    
    def run_hook(self, prefix: Prefix, version: str, cmd: Sequence[str], **kwargs) -> tuple[int, bytes]:
        """Execute hook with Node.js runtime."""
```

### Go Language Support

```python { .api }
class GolangLanguage:
    """Go language implementation with module support."""
    
    ENVIRONMENT_DIR = 'go_env'
    
    def get_default_version(self) -> str:
        """Returns 'go' as default Go version."""
    
    def install_environment(
        self, 
        prefix: Prefix, 
        version: str, 
        additional_dependencies: Sequence[str]
    ) -> None:
        """
        Install Go modules and build binaries.
        
        Downloads Go modules and builds executable binaries for hook execution.
        """
    
    def run_hook(self, prefix: Prefix, version: str, cmd: Sequence[str], **kwargs) -> tuple[int, bytes]:
        """Execute Go binary hook."""
```

### Ruby Language Support

```python { .api }
class RubyLanguage:
    """Ruby language implementation with gem management."""
    
    ENVIRONMENT_DIR = 'ruby_env'
    
    def get_default_version(self) -> str:
        """Returns 'ruby' as default Ruby version."""
    
    def install_environment(
        self, 
        prefix: Prefix, 
        version: str, 
        additional_dependencies: Sequence[str]
    ) -> None:
        """
        Install Ruby gems in isolated environment.
        
        Creates gem environment and installs hook gem with dependencies.
        """
    
    def run_hook(self, prefix: Prefix, version: str, cmd: Sequence[str], **kwargs) -> tuple[int, bytes]:
        """Execute hook with Ruby runtime."""
```

### Docker Language Support

```python { .api }
class DockerLanguage:
    """Docker language implementation for containerized hooks."""
    
    ENVIRONMENT_DIR = None  # No local environment needed
    
    def get_default_version(self) -> str:
        """Returns 'default' for Docker version."""
    
    def install_environment(
        self, 
        prefix: Prefix, 
        version: str, 
        additional_dependencies: Sequence[str]
    ) -> None:
        """
        Build Docker image for hook execution.
        
        Builds Docker image with hook and its dependencies.
        """
    
    def run_hook(self, prefix: Prefix, version: str, cmd: Sequence[str], **kwargs) -> tuple[int, bytes]:
        """Execute hook within Docker container."""
```

### System Language Support

```python { .api }
class SystemLanguage:
    """System language for executing system-installed binaries."""
    
    ENVIRONMENT_DIR = None  # Uses system executables
    
    def get_default_version(self) -> str:
        """Returns 'system' for system executables."""
    
    def install_environment(
        self, 
        prefix: Prefix, 
        version: str, 
        additional_dependencies: Sequence[str]
    ) -> None:
        """
        No installation needed for system executables.
        
        Validates that required executables are available on system PATH.
        """
    
    def run_hook(self, prefix: Prefix, version: str, cmd: Sequence[str], **kwargs) -> tuple[int, bytes]:
        """Execute system executable directly."""
```

## Language Utilities

### Language Resolution

Functions for resolving and working with language implementations.

```python { .api }
def get_language(language: str) -> Language:
    """
    Get language implementation by name.
    
    Parameters:
    - language: Language name
    
    Returns:
    - Language: Language implementation instance
    
    Raises:
    - ValueError: If language is not supported
    """

def language_version_info(language: str, version: str) -> dict[str, Any]:
    """
    Get version information for a language.
    
    Parameters:
    - language: Language name
    - version: Version string
    
    Returns:
    - dict: Version information and capabilities
    """
```

### Environment Management

Utilities for managing language environments across hooks.

```python { .api }
def clean_environment(prefix: Prefix, language: str) -> None:
    """
    Clean up language environment files.
    
    Parameters:
    - prefix: Installation prefix
    - language: Language name
    """

def environment_exists(prefix: Prefix, language: str, version: str) -> bool:
    """
    Check if language environment is installed.
    
    Parameters:
    - prefix: Installation prefix  
    - language: Language name
    - version: Language version
    
    Returns:
    - bool: True if environment exists
    """
```

## Language-Specific Features

### Python Features

```python { .api }
def python_venv_info(prefix: Prefix) -> dict[str, str]:
    """Get Python virtual environment information."""

def install_python_requirements(prefix: Prefix, requirements: list[str]) -> None:
    """Install Python packages from requirements list."""
```

### Node.js Features

```python { .api }
def node_package_info(prefix: Prefix) -> dict[str, Any]:
    """Get Node.js package information."""

def install_node_packages(prefix: Prefix, packages: list[str]) -> None:
    """Install Node.js packages via npm."""
```

### Docker Features

```python { .api }
def docker_image_exists(image: str) -> bool:
    """Check if Docker image exists locally."""

def pull_docker_image(image: str) -> None:
    """Pull Docker image from registry."""
```

## Usage Examples

### Working with Language Implementations

```python
from pre_commit.languages import languages
from pre_commit.prefix import Prefix

# Get Python language implementation
python_lang = languages['python']
print(f"Python environment dir: {python_lang.ENVIRONMENT_DIR}")
print(f"Default version: {python_lang.get_default_version()}")

# Create prefix for hook installation
prefix = Prefix('/tmp/hook-env')

# Install Python environment with additional dependencies
python_lang.install_environment(
    prefix=prefix,
    version='python3.9',
    additional_dependencies=['black', 'flake8']
)

# Check environment health
health_result = python_lang.health_check(prefix, 'python3.9')
if health_result is None:
    print("Python environment is healthy")
else:
    print(f"Environment issue: {health_result}")
```

### Executing Hooks with Language Support

```python
from pre_commit.languages import languages

# Get language implementation
node_lang = languages['node']

# Execute hook within Node.js environment
with node_lang.in_env(prefix, 'node'):
    exit_code, output = node_lang.run_hook(
        prefix=prefix,
        version='node',
        cmd=['eslint', '--fix'],
        file_args=['src/app.js', 'src/utils.js'],
        prepend_base_dir=True,
        require_serial=False,
        color=True
    )

print(f"Hook exit code: {exit_code}")
if output:
    print(f"Hook output: {output.decode()}")
```

### Language Environment Management

```python
from pre_commit.languages import get_language, environment_exists

# Work with Go language
go_lang = get_language('golang')

# Check if environment exists
if environment_exists(prefix, 'golang', 'go1.19'):
    print("Go environment already installed")
else:
    print("Installing Go environment...")
    go_lang.install_environment(prefix, 'go1.19', [])

# Get language version info
version_info = language_version_info('golang', 'go1.19')
print(f"Go version info: {version_info}")
```

### Multi-Language Hook Processing

```python
from pre_commit.languages import languages

# Process hooks for different languages
hook_configs = [
    {'language': 'python', 'version': 'python3.9', 'deps': ['black']},
    {'language': 'node', 'version': 'node16', 'deps': ['eslint']},
    {'language': 'golang', 'version': 'go1.19', 'deps': []},
]

for config in hook_configs:
    lang_impl = languages[config['language']]
    
    # Install environment
    lang_impl.install_environment(
        prefix=prefix,
        version=config['version'],
        additional_dependencies=config['deps']
    )
    
    print(f"Installed {config['language']} environment")
```