# Utility Classes

Modal provides essential utility classes for error handling and file pattern matching. These utilities support robust error management and flexible file filtering capabilities across Modal applications.

## Capabilities

### Package Version

Package version string for the Modal client library.

```python { .api }
__version__: str  # Current package version (e.g., "1.1.4")
```

### Error - Base Exception Class

Base exception class for all Modal-specific errors, providing a hierarchy of specialized error types for different failure scenarios.

```python { .api }
class Error(Exception):
    """Base class for all Modal errors"""

# Specialized error types
class AlreadyExistsError(Error):
    """Raised when a resource creation conflicts with an existing resource"""

class RemoteError(Error):
    """Raised when an error occurs on the Modal server"""

class TimeoutError(Error):
    """Base class for Modal timeouts"""

class FunctionTimeoutError(TimeoutError):
    """Raised when a Function exceeds its execution duration limit"""

class SandboxTimeoutError(TimeoutError):
    """Raised when a Sandbox exceeds its execution duration limit"""

class VolumeUploadTimeoutError(TimeoutError):
    """Raised when a Volume upload times out"""

class MountUploadTimeoutError(TimeoutError):
    """Raised when a Mount upload times out"""

class InteractiveTimeoutError(TimeoutError):
    """Raised when interactive frontends time out while connecting"""

class OutputExpiredError(TimeoutError):
    """Raised when the Output exceeds expiration"""

class AuthError(Error):
    """Raised when a client has missing or invalid authentication"""

class ConnectionError(Error):
    """Raised when an issue occurs while connecting to Modal servers"""

class InvalidError(Error):
    """Raised when user does something invalid"""

class VersionError(Error):
    """Raised when the current client version is unsupported"""

class NotFoundError(Error):
    """Raised when a requested resource was not found"""

class ExecutionError(Error):
    """Raised when something unexpected happened during runtime"""

class DeserializationError(Error):
    """Raised when an error is encountered during deserialization"""

class SerializationError(Error):
    """Raised when an error is encountered during serialization"""
```

#### Usage Examples

```python
import modal

app = modal.App("error-handling")

@app.function()
def error_prone_function(data: dict):
    """Function demonstrating Modal error handling"""
    
    try:
        # Operation that might fail with different error types
        result = risky_operation(data)
        return {"success": True, "result": result}
        
    except modal.FunctionTimeoutError as e:
        print(f"Function timed out: {e}")
        return {"error": "timeout", "message": str(e)}
        
    except modal.DeserializationError as e:
        print(f"Data deserialization failed: {e}")
        return {"error": "invalid_data", "message": str(e)}
        
    except modal.RemoteError as e:
        print(f"Server error occurred: {e}")
        return {"error": "server_error", "message": str(e)}
        
    except modal.Error as e:
        # Catch any Modal-specific error
        print(f"Modal error: {e}")
        return {"error": "modal_error", "type": type(e).__name__, "message": str(e)}
        
    except Exception as e:
        # Non-Modal errors
        print(f"Unexpected error: {e}")
        return {"error": "unexpected", "message": str(e)}

@app.function()
def resource_creation_function(resource_name: str):
    """Function that handles resource creation errors"""
    
    try:
        # Attempt to create a new resource
        volume = modal.Volume.persist(resource_name)
        return {"success": True, "resource": resource_name}
        
    except modal.AlreadyExistsError:
        # Resource already exists - use existing one
        print(f"Volume {resource_name} already exists, using existing volume")
        volume = modal.Volume.from_name(resource_name)
        return {"success": True, "resource": resource_name, "status": "existing"}
        
    except modal.AuthError as e:
        print(f"Authentication failed: {e}")
        return {"error": "auth_failed", "message": str(e)}
        
    except modal.InvalidError as e:
        print(f"Invalid resource name: {e}")
        return {"error": "invalid_name", "message": str(e)}

@app.function()
def upload_with_timeout_handling(local_path: str, remote_path: str):
    """Function that handles upload timeout errors"""
    
    volume = modal.Volume.from_name("upload-volume")
    
    try:
        volume.put_file(local_path, remote_path)
        return {"success": True, "uploaded": remote_path}
        
    except modal.VolumeUploadTimeoutError as e:
        print(f"Volume upload timed out: {e}")
        # Implement retry logic or alternative approach
        return {"error": "upload_timeout", "retry_recommended": True}
        
    except modal.NotFoundError as e:
        print(f"File not found: {e}")
        return {"error": "file_not_found", "path": local_path}

# Custom error handling with context
def handle_modal_errors(func):
    """Decorator for comprehensive Modal error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except modal.TimeoutError as e:
            return {"error": "timeout", "type": type(e).__name__, "message": str(e)}
        except modal.AuthError as e:
            return {"error": "authentication", "message": str(e)}
        except modal.ConnectionError as e:
            return {"error": "connection", "message": str(e)}
        except modal.Error as e:
            return {"error": "modal", "type": type(e).__name__, "message": str(e)}
        except Exception as e:
            return {"error": "unknown", "message": str(e)}
    return wrapper

@app.function()
@handle_modal_errors
def decorated_function(data: str):
    """Function with decorator-based error handling"""
    return process_data_safely(data)

@app.local_entrypoint()
def main():
    # Test error handling
    result1 = error_prone_function.remote({"test": "data"})
    print("Error handling result:", result1)
    
    # Test resource creation
    result2 = resource_creation_function.remote("test-volume")
    print("Resource creation result:", result2)
    
    # Test upload timeout handling
    result3 = upload_with_timeout_handling.remote("local_file.txt", "/remote/path.txt")
    print("Upload result:", result3)
```

### FilePatternMatcher - File Pattern Matching

Pattern matching utility for filtering files based on glob patterns, similar to Docker's pattern matching with support for exclusion and complex patterns.

```python { .api }
class FilePatternMatcher:
    def __init__(self, *patterns: str) -> None:
        """Create a file pattern matcher from glob patterns"""
    
    def __call__(self, path: Path) -> bool:
        """Check if a path matches any of the patterns"""
    
    def __invert__(self) -> "FilePatternMatcher":
        """Invert the matcher to exclude matching patterns"""
    
    def can_prune_directories(self) -> bool:
        """Check if directory pruning is safe for optimization"""
```

#### Usage Examples

```python
import modal
from pathlib import Path

app = modal.App("pattern-matching")

# Basic pattern matching
python_matcher = modal.FilePatternMatcher("*.py")
assert python_matcher(Path("script.py"))
assert not python_matcher(Path("README.md"))

# Multiple patterns
code_matcher = modal.FilePatternMatcher("*.py", "*.js", "*.ts")
assert code_matcher(Path("app.js"))
assert code_matcher(Path("component.ts"))
assert not code_matcher(Path("config.json"))

# Complex patterns with wildcards
deep_matcher = modal.FilePatternMatcher("**/*.py", "src/**/*.js")
assert deep_matcher(Path("deep/nested/script.py"))
assert deep_matcher(Path("src/components/app.js"))

# Inverted patterns (exclusion)
non_python_matcher = ~modal.FilePatternMatcher("*.py")
assert not non_python_matcher(Path("script.py"))
assert non_python_matcher(Path("README.md"))

@app.function()
def filter_files_function(file_paths: list[str]) -> dict:
    """Function that filters files using pattern matching"""
    
    # Create different matchers for different file types
    source_files = modal.FilePatternMatcher("*.py", "*.js", "*.ts", "*.java")
    config_files = modal.FilePatternMatcher("*.json", "*.yaml", "*.yml", "*.toml")
    doc_files = modal.FilePatternMatcher("*.md", "*.txt", "*.rst")
    
    # Exclude certain patterns
    exclude_matcher = modal.FilePatternMatcher(
        "**/__pycache__/**",
        "**/node_modules/**", 
        "**/.git/**",
        "*.pyc",
        "*.tmp"
    )
    
    results = {
        "source_files": [],
        "config_files": [],
        "doc_files": [],
        "other_files": [],
        "excluded_files": []
    }
    
    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        
        # Check if file should be excluded
        if exclude_matcher(file_path):
            results["excluded_files"].append(file_path_str)
            continue
        
        # Categorize files by type
        if source_files(file_path):
            results["source_files"].append(file_path_str)
        elif config_files(file_path):
            results["config_files"].append(file_path_str)
        elif doc_files(file_path):
            results["doc_files"].append(file_path_str)
        else:
            results["other_files"].append(file_path_str)
    
    return results

@app.function()
def advanced_pattern_matching(directory_paths: list[str]) -> dict:
    """Advanced pattern matching with multiple criteria"""
    
    # Different matchers for different purposes
    test_files = modal.FilePatternMatcher("**/test_*.py", "**/*_test.py", "**/tests/**/*.py")
    build_artifacts = modal.FilePatternMatcher(
        "**/build/**", 
        "**/dist/**",
        "**/*.egg-info/**"
    )
    hidden_files = modal.FilePatternMatcher(".*", "**/.*/**")
    
    # Inverted matchers for inclusion patterns
    include_source = ~modal.FilePatternMatcher(
        "**/__pycache__/**",
        "**/.*/**",
        "**/node_modules/**"
    )
    
    analysis = {
        "test_files": [],
        "build_artifacts": [],
        "hidden_files": [],
        "source_files": [],
        "total_processed": 0
    }
    
    for dir_path_str in directory_paths:
        dir_path = Path(dir_path_str)
        
        # Walk through directory structure
        if dir_path.exists() and dir_path.is_dir():
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    analysis["total_processed"] += 1
                    relative_path = file_path.relative_to(dir_path)
                    
                    # Categorize files
                    if test_files(relative_path):
                        analysis["test_files"].append(str(relative_path))
                    elif build_artifacts(relative_path):
                        analysis["build_artifacts"].append(str(relative_path))
                    elif hidden_files(relative_path):
                        analysis["hidden_files"].append(str(relative_path))
                    elif include_source(relative_path):
                        analysis["source_files"].append(str(relative_path))
    
    return analysis

@app.function()
def custom_file_processing():
    """Demonstrate custom pattern matching logic"""
    
    # Create matcher for Python files, excluding tests
    python_no_tests = modal.FilePatternMatcher("*.py") & ~modal.FilePatternMatcher("test_*.py", "*_test.py")
    
    # Process files with custom logic
    files_to_process = [
        "app.py",
        "test_app.py",
        "utils.py", 
        "config_test.py",
        "main.py"
    ]
    
    results = []
    for filename in files_to_process:
        file_path = Path(filename)
        
        if python_no_tests(file_path):
            # Custom processing for source files
            result = {
                "file": filename,
                "type": "source",
                "processed": True,
                "action": "analyze_code"
            }
        else:
            result = {
                "file": filename,
                "type": "test" if "test" in filename else "other",
                "processed": False,
                "action": "skip"
            }
        
        results.append(result)
    
    return results

# Utility function for complex pattern combinations
def create_project_filter():
    """Create a comprehensive project file filter"""
    
    # Include source files
    include_patterns = modal.FilePatternMatcher(
        "**/*.py",
        "**/*.js", 
        "**/*.ts",
        "**/*.json",
        "**/*.yaml",
        "**/*.yml",
        "**/*.md"
    )
    
    # Exclude build artifacts and temporary files
    exclude_patterns = modal.FilePatternMatcher(
        "**/__pycache__/**",
        "**/node_modules/**",
        "**/.git/**",
        "**/build/**",
        "**/dist/**",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.egg-info/**",
        "**/coverage/**",
        "**/.pytest_cache/**"
    )
    
    # Combine patterns: include source files but exclude artifacts
    return lambda path: include_patterns(path) and not exclude_patterns(path)

@app.local_entrypoint()
def main():
    # Test file filtering
    sample_files = [
        "src/app.py",
        "src/utils.py", 
        "tests/test_app.py",
        "config.json",
        "README.md",
        "build/output.js",
        "__pycache__/app.cpython-39.pyc",
        "node_modules/package/index.js"
    ]
    
    filter_result = filter_files_function.remote(sample_files)
    print("File filtering result:", filter_result)
    
    # Test advanced pattern matching
    directories = ["./src", "./tests", "./config"]
    advanced_result = advanced_pattern_matching.remote(directories)
    print("Advanced pattern matching:", advanced_result)
    
    # Test custom processing
    custom_result = custom_file_processing.remote()
    print("Custom processing result:", custom_result)
```

## Advanced Utility Patterns

### Comprehensive Error Recovery System

```python
import modal
import time
import random

app = modal.App("error-recovery")

class RetryableError(modal.Error):
    """Custom error type for retryable operations"""
    pass

def with_error_recovery(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for automatic error recovery"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except modal.TimeoutError as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"Timeout on attempt {attempt + 1}, retrying in {delay}s")
                        time.sleep(delay)
                    else:
                        print(f"All {max_retries + 1} attempts failed due to timeout")
                        
                except modal.ConnectionError as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay * (1.5 ** attempt)
                        print(f"Connection error on attempt {attempt + 1}, retrying in {delay}s")
                        time.sleep(delay)
                    else:
                        print(f"All {max_retries + 1} attempts failed due to connection issues")
                        
                except RetryableError as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay + random.uniform(0, 1)  # Jittered delay
                        print(f"Retryable error on attempt {attempt + 1}, retrying in {delay:.2f}s")
                        time.sleep(delay)
                    else:
                        print(f"All {max_retries + 1} attempts failed due to retryable errors")
                        
                except modal.Error as e:
                    # Non-retryable Modal errors
                    print(f"Non-retryable Modal error: {type(e).__name__}: {e}")
                    raise
                    
                except Exception as e:
                    # Unknown errors
                    print(f"Unknown error: {type(e).__name__}: {e}")
                    raise
            
            # All retries exhausted
            raise last_error
            
        return wrapper
    return decorator

@app.function()
@with_error_recovery(max_retries=5, base_delay=2.0)
def resilient_operation(data: dict):
    """Operation with comprehensive error recovery"""
    
    # Simulate various failure modes
    failure_mode = data.get("failure_mode", "none")
    
    if failure_mode == "timeout":
        raise modal.FunctionTimeoutError("Simulated timeout")
    elif failure_mode == "connection":
        raise modal.ConnectionError("Simulated connection error")
    elif failure_mode == "retryable":
        raise RetryableError("Simulated retryable error")
    elif failure_mode == "auth":
        raise modal.AuthError("Simulated auth error")  # Non-retryable
    
    # Success case
    return {"status": "success", "data": data}

@app.local_entrypoint()
def main():
    # Test different error scenarios
    test_cases = [
        {"data": {"value": 1}, "expected": "success"},
        {"data": {"value": 2, "failure_mode": "timeout"}, "expected": "retry_success"},
        {"data": {"value": 3, "failure_mode": "connection"}, "expected": "retry_success"},
        {"data": {"value": 4, "failure_mode": "retryable"}, "expected": "retry_success"},
        {"data": {"value": 5, "failure_mode": "auth"}, "expected": "immediate_failure"},
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i + 1}: {test_case['expected']}")
        try:
            result = resilient_operation.remote(test_case["data"])
            print(f"Result: {result}")
        except Exception as e:
            print(f"Final error: {type(e).__name__}: {e}")
```

### Intelligent File Processing Pipeline

```python
import modal
from pathlib import Path
import json

app = modal.App("file-processing-pipeline")

class FileProcessor:
    """Advanced file processing with pattern matching"""
    
    def __init__(self):
        # Define processing rules based on file patterns
        self.processors = {
            "python": {
                "matcher": modal.FilePatternMatcher("*.py"),
                "action": self.process_python_file,
                "priority": 1
            },
            "javascript": {
                "matcher": modal.FilePatternMatcher("*.js", "*.ts"),
                "action": self.process_js_file,
                "priority": 1
            },
            "config": {
                "matcher": modal.FilePatternMatcher("*.json", "*.yaml", "*.yml"),
                "action": self.process_config_file,
                "priority": 2
            },
            "documentation": {
                "matcher": modal.FilePatternMatcher("*.md", "*.rst", "*.txt"),
                "action": self.process_doc_file,
                "priority": 3
            },
            "tests": {
                "matcher": modal.FilePatternMatcher("**/test_*.py", "**/*_test.py", "**/tests/**/*.py"),
                "action": self.process_test_file,
                "priority": 0  # Highest priority
            }
        }
        
        # Files to exclude from processing
        self.exclude_matcher = modal.FilePatternMatcher(
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.git/**",
            "**/venv/**",
            "**/*.pyc"
        )
    
    def process_python_file(self, file_path: Path) -> dict:
        """Process Python source files"""
        return {
            "type": "python",
            "analysis": "syntax_check_passed",
            "metrics": {"lines": 100, "functions": 5},
            "issues": []
        }
    
    def process_js_file(self, file_path: Path) -> dict:
        """Process JavaScript/TypeScript files"""
        return {
            "type": "javascript",
            "analysis": "linting_passed",
            "metrics": {"lines": 75, "functions": 3},
            "issues": []
        }
    
    def process_config_file(self, file_path: Path) -> dict:
        """Process configuration files"""
        return {
            "type": "config",
            "analysis": "valid_format",
            "validation": "schema_compliant",
            "issues": []
        }
    
    def process_doc_file(self, file_path: Path) -> dict:
        """Process documentation files"""
        return {
            "type": "documentation",
            "analysis": "spell_check_passed",
            "metrics": {"word_count": 500},
            "issues": []
        }
    
    def process_test_file(self, file_path: Path) -> dict:
        """Process test files"""
        return {
            "type": "test",
            "analysis": "test_discovery_complete",
            "metrics": {"test_count": 10, "coverage": 85.5},
            "issues": []
        }
    
    def classify_file(self, file_path: Path) -> tuple[str, dict]:
        """Classify file and return appropriate processor"""
        # Check exclusions first
        if self.exclude_matcher(file_path):
            return "excluded", {}
        
        # Find matching processor with highest priority
        matches = []
        for name, processor in self.processors.items():
            if processor["matcher"](file_path):
                matches.append((processor["priority"], name, processor))
        
        if matches:
            # Sort by priority (lower number = higher priority)
            matches.sort(key=lambda x: x[0])
            _, name, processor = matches[0]
            return name, processor
        
        return "unknown", {}

@app.function()
def intelligent_file_processing(file_paths: list[str]) -> dict:
    """Process files using intelligent pattern matching"""
    
    processor = FileProcessor()
    results = {
        "processed": {},
        "excluded": [],
        "unknown": [], 
        "errors": [],
        "statistics": {
            "total_files": len(file_paths),
            "processed_count": 0,
            "excluded_count": 0,
            "unknown_count": 0,
            "error_count": 0
        }
    }
    
    for file_path_str in file_paths:
        try:
            file_path = Path(file_path_str)
            file_type, processor_info = processor.classify_file(file_path)
            
            if file_type == "excluded":
                results["excluded"].append(file_path_str)
                results["statistics"]["excluded_count"] += 1
                
            elif file_type == "unknown":
                results["unknown"].append(file_path_str)
                results["statistics"]["unknown_count"] += 1
                
            else:
                # Process the file
                process_result = processor_info["action"](file_path)
                results["processed"][file_path_str] = {
                    "file_type": file_type,
                    "priority": processor_info["priority"],
                    "result": process_result
                }
                results["statistics"]["processed_count"] += 1
                
        except Exception as e:
            error_info = {
                "file": file_path_str,
                "error": str(e),
                "error_type": type(e).__name__
            }
            results["errors"].append(error_info)
            results["statistics"]["error_count"] += 1
    
    return results

@app.function() 
def batch_file_analysis(directory_paths: list[str]) -> dict:
    """Analyze entire directories with pattern-based filtering"""
    
    processor = FileProcessor()
    analysis = {
        "directories": {},
        "summary": {
            "total_directories": len(directory_paths),
            "total_files": 0,
            "file_type_counts": {},
            "processing_time": 0
        }
    }
    
    start_time = time.time()
    
    for dir_path_str in directory_paths:
        dir_path = Path(dir_path_str)
        dir_analysis = {
            "files": [],
            "file_counts": {},
            "excluded_files": []
        }
        
        if dir_path.exists() and dir_path.is_dir():
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    analysis["summary"]["total_files"] += 1
                    relative_path = file_path.relative_to(dir_path)
                    
                    file_type, processor_info = processor.classify_file(relative_path)
                    
                    if file_type == "excluded":
                        dir_analysis["excluded_files"].append(str(relative_path))
                    else:
                        dir_analysis["files"].append({
                            "path": str(relative_path),
                            "type": file_type,
                            "priority": processor_info.get("priority", 999)
                        })
                        
                        # Update counts
                        dir_analysis["file_counts"][file_type] = dir_analysis["file_counts"].get(file_type, 0) + 1
                        analysis["summary"]["file_type_counts"][file_type] = analysis["summary"]["file_type_counts"].get(file_type, 0) + 1
        
        analysis["directories"][dir_path_str] = dir_analysis
    
    analysis["summary"]["processing_time"] = time.time() - start_time
    return analysis

@app.local_entrypoint()
def main():
    # Test intelligent file processing
    sample_files = [
        "src/main.py",
        "src/utils.py",  
        "tests/test_main.py",
        "config/settings.json",
        "docs/README.md",
        "package.json",
        "node_modules/lib/index.js",  # Should be excluded
        "__pycache__/main.cpython-39.pyc",  # Should be excluded
        "data/sample.csv",  # Unknown type
        "Dockerfile"  # Unknown type
    ]
    
    processing_result = intelligent_file_processing.remote(sample_files)
    print("Intelligent processing result:")
    print(json.dumps(processing_result, indent=2))
    
    # Test batch directory analysis
    directories = ["./src", "./tests", "./config"]
    analysis_result = batch_file_analysis.remote(directories)
    print("\nBatch analysis result:")
    print(json.dumps(analysis_result, indent=2))
```