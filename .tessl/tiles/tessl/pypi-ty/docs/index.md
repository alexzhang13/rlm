# ty

An extremely fast Python type checker and language server written in Rust. ty provides comprehensive type checking for Python codebases with advanced error reporting, configuration options, and Language Server Protocol support for seamless editor integration.

## Package Information

- **Package Name**: ty
- **Package Type**: pypi
- **Language**: Python (with Rust backend)
- **Installation**: `pip install ty` or `uv tool install ty` or `pipx install ty`
- **Version**: 0.0.1-alpha.20
- **License**: MIT
- **Repository**: https://github.com/astral-sh/ty
- **Documentation**: https://docs.astral.sh/ty/

## Core Imports

The ty package can be imported as a Python module but provides minimal programmatic API:

```python
import ty
```

However, ty is primarily used as a command-line tool:

```bash
ty check
```

## Basic Usage

```bash
# Basic type checking
ty check

# Check specific files
ty check src/main.py tests/

# Watch mode with auto-recheck
ty check --watch

# Use specific Python version
ty check --python-version 3.11

# Start language server
ty server
```

For project integration:

```bash
# Add to project as dev dependency
uv add --dev ty

# Run with uv
uv run ty check
```

## Architecture

ty consists of several key components:

- **Type Checker Core**: Rust-based high-performance type analysis engine
- **CLI Interface**: Command-line interface for type checking operations
- **Language Server**: LSP implementation for real-time editor integration
- **Configuration System**: Flexible TOML-based configuration for projects
- **Module Resolution**: Sophisticated Python package and module discovery
- **Binary Wrapper**: Python wrapper that locates and executes the Rust binary

The architecture prioritizes performance through Rust implementation while maintaining compatibility with Python tooling and ecosystems.

## Capabilities

### Command Line Interface

Core command-line functionality for type checking, language server operation, and tool management.

```bash { .api }
# Main command
ty <COMMAND>

# Type checking
ty check [OPTIONS] [PATHS]...

# Language server
ty server

# Version information
ty version

# Shell completion
ty generate-shell-completion <SHELL>

# Help
ty help [COMMAND]
```

**Arguments:**
- `PATHS`: List of files or directories to check (optional, defaults to project root)
- `SHELL`: Shell type for completion generation (bash, zsh, fish, powershell, elvish)
- `COMMAND`: Subcommand to get help for (optional)

**Global Options for `ty check`:**

File and path options:
- `--project <project>`: Run within specific project directory
- `--exclude <exclude>`: Glob patterns to exclude from checking

Python environment options:
- `--python <path>`: Path to Python environment or interpreter. ty uses this to resolve type information and third-party dependencies. If not specified, ty attempts to infer from VIRTUAL_ENV/CONDA_PREFIX or discover .venv directory. If interpreter path is provided (e.g., .venv/bin/python3), ty attempts to find environment two directories up. Does not invoke interpreter, so won't resolve dynamic executables like shims.
- `--python-version <version>`, `--target-version <version>`: Target Python version (3.7-3.13). If not specified, ty tries: 1) project.requires-python in pyproject.toml, 2) infer from Python environment, 3) fallback to 3.13
- `--python-platform <platform>`, `--platform <platform>`: Target platform (win32/darwin/linux/android/ios/all). Used to specialize sys.platform type. If 'all', no platform assumptions are made. Defaults to current system platform.
- `--extra-search-path <path>`: Additional module resolution paths (can be repeated)
- `--typeshed <path>`, `--custom-typeshed-dir <path>`: Custom typeshed directory for standard library types

Configuration options:
- `--config-file <path>`: Path to ty.toml configuration file
- `--config <config-option>`, `-c <config-option>`: TOML key=value configuration override

Rule control options:
- `--error <rule>`: Treat rule as error-level (can be repeated)
- `--warn <rule>`: Treat rule as warning-level (can be repeated)
- `--ignore <rule>`: Disable rule (can be repeated)

Output options:
- `--output-format <format>`: Message format (full/concise)
- `--color <when>`: Color output control (auto/always/never)
- `--quiet/-q`: Quiet output (use -qq for silent)
- `--verbose/-v`: Verbose output (use -vv, -vvv for more verbose)
- `--help/-h`: Print help information

Behavior options:
- `--watch/-W`: Watch mode for continuous checking
- `--error-on-warning`: Exit code 1 on warnings
- `--exit-zero`: Always exit with code 0
- `--respect-ignore-files`: Respect file exclusions via .gitignore and other standard ignore files (use --no-respect-gitignore to disable)

### Python Module API

Limited programmatic access through Python module wrapper.

```python { .api }
def find_ty_bin() -> str:
    """
    Return the ty binary path.
    
    Searches various installation locations including:
    - System scripts directory
    - User-specific installation paths
    - Virtual environment paths
    - pip build environments
    - Adjacent bin directories
    
    Returns:
        str: Absolute path to ty binary executable
        
    Raises:
        FileNotFoundError: If ty binary cannot be located
    """
```

**Usage Example:**
```python
from ty import find_ty_bin
import subprocess

# Get ty binary path
ty_path = find_ty_bin()

# Run type checking programmatically
result = subprocess.run([ty_path, "check", "src/"], capture_output=True, text=True)
print(result.stdout)
```

### Configuration System

Comprehensive TOML-based configuration supporting project-level and user-level settings.

```toml { .api }
# pyproject.toml format
[tool.ty.rules]
rule_name = "ignore" | "warn" | "error"

[tool.ty.environment]
extra-paths = ["./shared/my-search-path"]
python = "./.venv"
python-platform = "win32" | "darwin" | "android" | "ios" | "linux" | "all"
python-version = "3.7" | "3.8" | "3.9" | "3.10" | "3.11" | "3.12" | "3.13"
root = ["./src", "./lib"]
typeshed = "/path/to/custom/typeshed"

[tool.ty.src]
include = ["src", "tests"]
exclude = ["generated", "*.proto", "tests/fixtures/**"]  # Additional excludes beyond defaults
respect-ignore-files = true

[tool.ty.terminal]
output-format = "full" | "concise"
error-on-warning = false

[[tool.ty.overrides]]
include = ["tests/**"]
exclude = ["tests/fixtures/**"]

[tool.ty.overrides.rules]
rule_name = "ignore" | "warn" | "error"
```

**Configuration File Locations:**
- Project: `pyproject.toml` (under `[tool.ty]`) or `ty.toml`
- User: `~/.config/ty/ty.toml` or `$XDG_CONFIG_HOME/ty/ty.toml` (Linux/macOS)
- User: `%APPDATA%\ty\ty.toml` (Windows)

**Precedence:** Command line > project config > user config

### Language Server Protocol

Language server implementation providing real-time type checking and editor integration.

```bash { .api }
# Start language server
ty server
```

**LSP Features:**
- Real-time type checking as you type
- Diagnostic reporting with error/warning details
- Hover information for type details
- Go-to-definition support
- Symbol search and workspace analysis
- Configuration synchronization

**Editor Integration:**

VS Code:
```json
{
  "ty.enable": true,
  "ty.path": "/path/to/ty",
  "ty.settings": {
    "python-version": "3.11"
  }
}
```

Neovim (nvim-lspconfig):
```lua
require('lspconfig').ty.setup({
  settings = {
    ty = {
      -- ty language server settings
    }
  }
})
```

Neovim 0.11+ (vim.lsp.config):
```lua
vim.lsp.config('ty', {
  settings = {
    ty = {
      -- ty language server settings
    }
  }
})
vim.lsp.enable('ty')
```

### Environment Variables

Environment variables that control ty's behavior and configuration.

```bash { .api }
# Configuration file path
export TY_CONFIG_FILE="/path/to/ty.toml"

# Python environment detection
export VIRTUAL_ENV="/path/to/venv"
export CONDA_PREFIX="/path/to/conda/env"
```

**Environment Variables:**
- `TY_CONFIG_FILE`: Override configuration file location
- `VIRTUAL_ENV`: Active virtual environment path (auto-detected)
- `CONDA_PREFIX`: Conda environment path (auto-detected)

### Exit Codes

ty uses standard exit codes to indicate the result of operations.

```bash { .api }
# Exit codes
0  # Success (no errors, or only warnings without --error-on-warning)
1  # Type errors found, or warnings with --error-on-warning
2  # Configuration or runtime errors
```

## Module Discovery

ty implements sophisticated module resolution for Python projects:

### First-party Modules
- Searches project root and `src/` directories by default
- Configurable via `environment.root` setting
- Supports src-layout, flat-layout, and custom project structures
- Automatically includes `tests/` if it's not a package

### Third-party Modules
- Resolves from configured Python environment
- Searches `site-packages` directories
- Supports virtual environments and conda environments
- Uses `--python` or auto-discovery via `VIRTUAL_ENV`/`CONDA_PREFIX`

### Standard Library
- Uses built-in typeshed stubs (bundled as zip in binary)
- Version-specific based on target Python version
- Customizable via `--typeshed` option

## Rule System

ty provides a comprehensive rule system for type checking configuration:

### Rule Categories
- Type compatibility and assignment checking
- Import resolution and missing import detection
- Attribute access validation
- Function call signature validation
- Variable binding and scope analysis

### Rule Configuration
```toml
[tool.ty.rules]
# Examples of common rules
possibly-unresolved-reference = "warn"
division-by-zero = "ignore"
index-out-of-bounds = "error"
redundant-cast = "ignore"
unused-ignore-comment = "warn"
```

### Rule Overrides
```toml
# File-specific rule overrides
[[tool.ty.overrides]]
include = ["tests/**", "**/test_*.py"]

[tool.ty.overrides.rules]
possibly-unresolved-reference = "ignore"  # Relax for tests
```

## Performance Features

ty is optimized for speed and efficiency:

- **Rust Implementation**: Core type checker written in Rust for maximum performance
- **Incremental Checking**: Only re-analyzes changed files and dependencies
- **Watch Mode**: Continuous checking with file system monitoring
- **Fast Startup**: Minimal initialization overhead
- **Memory Efficient**: Optimized memory usage for large codebases
- **Parallel Analysis**: Multi-threaded processing where possible

## Integration Patterns

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Type check with ty
  run: |
    uv tool install ty
    ty check --error-on-warning
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ty
    rev: v0.0.1-alpha.20
    hooks:
      - id: ty
```

### Development Workflow
```bash
# Development commands
ty check --watch          # Continuous checking
ty check --verbose        # Detailed output
ty check src/ tests/      # Specific paths
ty check --python .venv   # Specific environment
```

### Editor Integration
- **VS Code**: Official extension (astral-sh.ty)
- **Neovim**: Built-in LSP support
- **Vim**: LSP client configuration
- **Emacs**: lsp-mode integration
- **Any LSP-compatible editor**: Generic LSP server support

## Types

```python { .api }
# Configuration types (for reference)
RuleName = str  # Rule identifier (e.g., "possibly-unresolved-reference")
Severity = "ignore" | "warn" | "error"
PythonVersion = "3.7" | "3.8" | "3.9" | "3.10" | "3.11" | "3.12" | "3.13"
Platform = "win32" | "darwin" | "android" | "ios" | "linux" | "all"
OutputFormat = "full" | "concise"
ColorOption = "auto" | "always" | "never"

# Path specifications
Path = str  # File or directory path
GlobPattern = str  # Gitignore-style pattern
```