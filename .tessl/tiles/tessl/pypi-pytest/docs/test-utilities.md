# Test Utilities and Environment Control

Utilities for controlling test environments including monkeypatching, output capture, temporary paths, and specialized tools for testing pytest plugins. These utilities provide comprehensive control over the test execution environment.

## Capabilities

### Environment Modification

MonkeyPatch provides safe, temporary modifications to objects, environment variables, and system paths.

```python { .api }
class MonkeyPatch:
    """Helper for temporarily modifying objects, environment, and sys.path."""
    
    def setattr(self, target, name, value=<notset>, raising: bool = True) -> None:
        """Set attribute on target object."""
    
    def setitem(self, dic, name, value) -> None:
        """Set dictionary item."""
    
    def setenv(self, name: str, value: str, prepend: str | None = None) -> None:
        """Set environment variable."""
    
    def syspath_prepend(self, path) -> None:
        """Prepend to sys.path."""
    
    def chdir(self, path) -> None:
        """Change current working directory."""
    
    def undo(self) -> None:
        """Undo all changes."""
```

**Usage Example:**

```python
def test_monkeypatch(monkeypatch):
    # Modify object attribute
    monkeypatch.setattr("os.getcwd", lambda: "/fake/path")
    
    # Set environment variable
    monkeypatch.setenv("TEST_MODE", "true")
    
    # Modify dictionary
    import sys
    monkeypatch.setitem(sys.modules, "fake_module", FakeModule())
    
    # Change directory
    monkeypatch.chdir("/tmp")
    
    # All changes are automatically undone after test
```

### Output Capture

Capture stdout, stderr, and file descriptor output during test execution.

```python { .api }
class CaptureFixture:
    """Captures stdout/stderr output during tests."""
    
    def readouterr(self) -> CaptureResult:
        """Read and return captured output."""
    
    def disabled(self):
        """Context manager to temporarily disable capturing."""

class CaptureResult:
    """Result of captured output."""
    out: str  # Captured stdout
    err: str  # Captured stderr
```

**Usage Example:**

```python
def test_output_capture(capsys):
    print("Hello stdout")
    print("Hello stderr", file=sys.stderr)
    
    captured = capsys.readouterr()
    assert captured.out == "Hello stdout\\n"
    assert captured.err == "Hello stderr\\n"
    
    # Temporarily disable capture
    with capsys.disabled():
        print("This will be printed normally")

# Different capture fixtures available:
def test_capture_variants(capsys, capsysbinary, capfd, capfdbinary):
    # capsys: capture sys.stdout/stderr (text)
    # capsysbinary: capture sys.stdout/stderr (binary)  
    # capfd: capture file descriptors 1/2 (text)
    # capfdbinary: capture file descriptors 1/2 (binary)
    pass
```

### Log Capture

Capture and inspect log messages during test execution.

```python { .api }
class LogCaptureFixture:
    """Provides access and control of log capturing."""
    
    # Attributes
    handler: LogCaptureHandler  # Log handler
    records: list[logging.LogRecord]  # Captured log records
    
    def get_records(self, when: str) -> list[logging.LogRecord]:
        """Get log records for specific test phase."""
    
    def clear(self) -> None:
        """Clear captured records."""
    
    def set_level(self, level: int | str, logger: str | None = None) -> None:
        """Set logging level."""
```

**Usage Example:**

```python
import logging

def test_logging(caplog):
    with caplog.at_level(logging.INFO):
        logging.info("This is an info message")
        logging.warning("This is a warning")
    
    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == "INFO"
    assert "info message" in caplog.records[0].message
    
    # Clear records
    caplog.clear()
    assert len(caplog.records) == 0
    
    # Check specific logger
    logger = logging.getLogger("myapp")
    logger.error("Application error")
    
    assert any("Application error" in record.message 
              for record in caplog.records)
```

### Temporary Paths

Factory for creating temporary directories and files.

```python { .api }
class TempPathFactory:
    """Factory for creating temporary directories."""
    
    def mktemp(self, basename: str, numbered: bool = True) -> Path:
        """Create temporary directory."""
    
    def getbasetemp(self) -> Path:
        """Get base temporary directory."""

# Built-in fixtures
def test_temp_paths(tmp_path, tmp_path_factory):
    # tmp_path: pathlib.Path to temporary directory (function scope)
    # tmp_path_factory: TempPathFactory instance
    
    # Create file in temporary directory
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")
    assert file_path.read_text() == "test content"
    
    # Create additional temp directory
    another_temp = tmp_path_factory.mktemp("custom_dir")
    assert another_temp.exists()
```

### Plugin Testing Framework

Comprehensive tools for testing pytest plugins and functionality.

```python { .api }
class Pytester:
    """Facilities for testing pytest plugins and functionality."""
    
    def makepyfile(self, **kwargs) -> Path:
        """Create Python file with content."""
    
    def makeconftest(self, source: str) -> Path:
        """Create conftest.py file."""
    
    def makefile(self, ext: str, **kwargs) -> Path:
        """Create file with given extension."""
    
    def mkdir(self, name: str) -> Path:
        """Create directory."""
    
    def runpytest(self, *args, **kwargs) -> RunResult:
        """Run pytest in subprocess."""
    
    def runpytest_subprocess(self, *args, **kwargs) -> RunResult:
        """Run pytest in subprocess with isolation."""
    
    def runpytest_inprocess(self, *args, **kwargs) -> RunResult:
        """Run pytest in same process."""

class RunResult:
    """Result of running pytest in subprocess."""
    
    # Attributes
    ret: int  # Return code
    outlines: list[str]  # stdout lines
    errlines: list[str]  # stderr lines  
    stdout: str  # Full stdout
    stderr: str  # Full stderr
    duration: float  # Execution duration
    
    def parseoutcomes(self) -> dict[str, int]:
        """Parse test outcomes from output."""
    
    def assert_outcomes(self, **expected) -> None:
        \"\"\"Assert expected test outcomes.\"\"\"\n\nclass HookRecorder:\n    \"\"\"Records hook calls for testing.\"\"\"\n    \n    def getcalls(self, names: str | list[str]) -> list[RecordedHookCall]:\n        \"\"\"Get recorded calls for hook names.\"\"\"\n    \n    def assert_contains(self, entries) -> None:\n        \"\"\"Assert recorder contains specific entries.\"\"\"\n    \n    def pop(self, name: str) -> RecordedHookCall:\n        \"\"\"Remove and return last call for hook name.\"\"\"\n\nclass RecordedHookCall:\n    \"\"\"Represents a recorded hook call.\"\"\"\n    pass\n\nclass LineMatcher:\n    \"\"\"Flexible matching of text output lines.\"\"\"\n    \n    def fnmatch_lines(self, lines2: list[str]) -> None:\n        \"\"\"Assert lines match using fnmatch patterns.\"\"\"\n    \n    def re_match_lines(self, lines2: list[str]) -> None:\n        \"\"\"Assert lines match using regex patterns.\"\"\"\n    \n    def no_fnmatch_line(self, pat: str) -> None:\n        \"\"\"Assert no line matches fnmatch pattern.\"\"\"\n```\n\n**Usage Example:**\n\n```python\ndef test_my_plugin(pytester):\n    # Create test files\n    pytester.makepyfile(\"\"\"\n        def test_example():\n            assert True\n    \"\"\")\n    \n    pytester.makeconftest(\"\"\"\n        import pytest\n        \n        @pytest.fixture\n        def my_fixture():\n            return \"test_value\"\n    \"\"\")\n    \n    # Run pytest\n    result = pytester.runpytest(\"-v\")\n    \n    # Check results\n    result.assert_outcomes(passed=1)\n    assert result.ret == 0\n    \n    # Check output\n    result.stdout.fnmatch_lines([\n        \"*test_example PASSED*\"\n    ])\n\ndef test_hook_recording(pytester):\n    pytester.makepyfile(\"\"\"\n        def test_foo(): pass\n    \"\"\")\n    \n    # Record hooks\n    rec = pytester.runpytest(\"--collect-only\")\n    \n    # Check hook calls\n    calls = rec.getcalls(\"pytest_collection_modifyitems\")\n    assert len(calls) == 1\n```\n\n### Legacy Path Support (Deprecated)\n\nLegacy support for py.path and testdir (deprecated in favor of pathlib.Path).\n\n```python { .api }\nclass TempdirFactory:\n    \"\"\"Legacy factory for temporary directories (deprecated).\"\"\"\n    pass\n\nclass Testdir:\n    \"\"\"Legacy test directory helper (deprecated).\"\"\"\n    pass\n```\n\n## Built-in Utility Fixtures\n\nSummary of built-in fixtures for test utilities:\n\n```python\ndef test_with_all_utilities(\n    monkeypatch,      # MonkeyPatch instance\n    capsys,           # Capture sys.stdout/stderr (text)\n    capsysbinary,     # Capture sys.stdout/stderr (binary)\n    capfd,            # Capture file descriptors (text)\n    capfdbinary,      # Capture file descriptors (binary)  \n    caplog,           # LogCaptureFixture instance\n    tmp_path,         # pathlib.Path to temp directory\n    tmp_path_factory, # TempPathFactory instance\n    pytester,         # Pytester instance (for plugin testing)\n    recwarn,          # WarningsRecorder instance\n    # Legacy (deprecated)\n    tmpdir,           # py.path.local temp directory\n    tmpdir_factory,   # TempdirFactory instance\n    testdir           # Testdir instance\n):\n    pass\n```