# Test Reporting and Results

Comprehensive reporting system for test execution results, collection reports, and terminal output formatting. These classes provide detailed information about test outcomes and handle presentation of results to users.

## Capabilities

### Test Execution Reports

Classes representing the results of test execution.

```python { .api }
@dataclasses.dataclass
class CallInfo(Generic[TResult]):
    """Result/Exception info of a function invocation."""
    
    def __init__(
        self,
        result: TResult | None,
        excinfo: ExceptionInfo[BaseException] | None,
        start: float,
        stop: float,
        duration: float,
        when: Literal["collect", "setup", "call", "teardown"],
        _ispytest: bool = False,
    ) -> None:
        """
        Initialize call information.
        
        Parameters:
        - result: Return value (None if exception occurred)
        - excinfo: Exception info if raised
        - start: Start time (seconds since epoch)
        - stop: End time (seconds since epoch)
        - duration: Call duration in seconds
        - when: Invocation context
        - _ispytest: Internal pytest flag
        """
    
    # Attributes
    _result: TResult | None  # Private result storage
    excinfo: ExceptionInfo[BaseException] | None  # Captured exception
    start: float  # Start timestamp
    stop: float  # End timestamp
    duration: float  # Execution duration
    when: str  # Context of invocation ("collect", "setup", "call", "teardown")
    
    @property
    def result(self) -> TResult:
        """
        Get the call result.
        
        Returns:
            The function result
            
        Raises:
            AttributeError: If excinfo is not None (exception occurred)
        """
    
    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: str,
        reraise=None
    ) -> CallInfo[TResult]:
        """
        Execute function and capture call information.
        
        Parameters:
        - func: Function to execute
        - when: Context identifier
        - reraise: Exception types to reraise immediately
        
        Returns:
            CallInfo with execution results and timing
        """

class TestReport(BaseReport):
    """Basic test report object for test execution results.
    
    Also used for setup and teardown calls if they fail.
    Reports can contain arbitrary extra attributes.
    """
    
    def __init__(
        self,
        nodeid: str,
        location: tuple[str, int | None, str],
        keywords: Mapping[str, Any],
        outcome: Literal["passed", "failed", "skipped"],
        longrepr: None | ExceptionInfo | tuple[str, int, str] | str | TerminalRepr,
        when: Literal["setup", "call", "teardown"],
        sections: Iterable[tuple[str, str]] = (),
        duration: float = 0,
        start: float = 0,
        stop: float = 0,
        user_properties: Iterable[tuple[str, object]] | None = None,
        **extra
    ) -> None:
        """
        Initialize test report.
        
        Parameters:
        - nodeid: Normalized collection nodeid
        - location: File path, line number, domain info
        - keywords: Name->value dict of keywords/markers
        - outcome: Test outcome ("passed", "failed", "skipped")
        - longrepr: Failure representation
        - when: Test phase ("setup", "call", "teardown")
        - sections: Extra information tuples (heading, content)
        - duration: Test execution time in seconds
        - start: Start time (seconds since epoch)
        - stop: End time (seconds since epoch)
        - user_properties: User-defined properties
        - **extra: Additional arbitrary attributes
        """
    
    # Core attributes
    nodeid: str  # Test identifier
    location: tuple[str, int | None, str]  # Test location info
    keywords: Mapping[str, Any]  # Associated keywords and markers
    outcome: str  # One of "passed", "failed", "skipped"
    longrepr  # Failure representation (None for passed tests)
    when: str  # Phase: "setup", "call", or "teardown"
    user_properties: list[tuple[str, object]]  # User-defined test properties
    sections: list[tuple[str, str]]  # Captured output sections
    duration: float  # Execution duration
    start: float  # Start timestamp
    stop: float  # End timestamp
    wasxfail: str  # XFail reason (if applicable)
    
    @classmethod
    def from_item_and_call(cls, item: Item, call: CallInfo[None]) -> TestReport:
        """
        Create TestReport from test item and call info.
        
        Parameters:
        - item: Test item that was executed
        - call: Call information from execution
        
        Returns:
            TestReport with complete execution information
        """
    
    def _to_json(self) -> dict[str, Any]:
        """
        Serialize report to JSON-compatible dict.
        
        Returns:
            Dictionary representation for JSON serialization
        """
    
    @classmethod
    def _from_json(cls, reportdict: dict[str, object]) -> TestReport:
        """
        Deserialize TestReport from JSON dict.
        
        Parameters:
        - reportdict: Dictionary from JSON deserialization
        
        Returns:
            TestReport instance
        """

class CollectReport(BaseReport):
    """Collection report object representing collection results.
    
    Reports can contain arbitrary extra attributes.
    """
    
    def __init__(
        self,
        nodeid: str,
        outcome: Literal["passed", "failed", "skipped"],
        longrepr: None | ExceptionInfo | tuple[str, int, str] | str | TerminalRepr,
        result: list[Item | Collector] | None,
        sections: Iterable[tuple[str, str]] = (),
        **extra
    ) -> None:
        """
        Initialize collection report.
        
        Parameters:
        - nodeid: Normalized collection nodeid
        - outcome: Collection outcome ("passed", "failed", "skipped")
        - longrepr: Failure representation
        - result: Collected items and nodes
        - sections: Extra information sections
        - **extra: Additional arbitrary attributes
        """
    
    # Attributes
    when = "collect"  # Always "collect" for collection reports
    nodeid: str  # Collection node identifier
    outcome: str  # Collection result
    longrepr  # Collection failure details (if any)
    result: list[Item | Collector]  # Successfully collected items
    sections: list[tuple[str, str]]  # Captured output during collection
    
    @property
    def location(self) -> tuple[str, None, str]:
        """
        Get collection location.
        
        Returns:
            Tuple of (fspath, None, fspath)
        """
    
    def _to_json(self) -> dict[str, Any]:
        """
        Serialize report to JSON-compatible dict.
        
        Returns:
            Dictionary representation for JSON serialization
        """
    
    @classmethod
    def _from_json(cls, reportdict: dict[str, object]) -> CollectReport:
        """
        Deserialize CollectReport from JSON dict.
        
        Parameters:
        - reportdict: Dictionary from JSON deserialization
        
        Returns:
            CollectReport instance
        """
```

### Terminal Output and Formatting

Classes controlling terminal output during test execution.

```python { .api }
class TestShortLogReport(NamedTuple):
    """Container for test status information used in terminal reporting.
    
    Used to store the test status result category, shortletter and verbose word.
    For example "rerun", "R", ("RERUN", {"yellow": True}).
    """
    
    category: str  # Result class ("passed", "skipped", "error", or empty)
    letter: str  # Short letter for progress (".", "s", "E", or empty)
    word: str | tuple[str, Mapping[str, bool]]  # Verbose word or (word, markup) tuple

class TerminalReporter:
    """Controls terminal output formatting and reporting during test execution.
    
    Main class responsible for all terminal output including progress indicators,
    test results, summaries, and formatting.
    """
    
    def __init__(self, config: Config, file: TextIO | None = None) -> None:
        """
        Initialize terminal reporter.
        
        Parameters:
        - config: pytest configuration object
        - file: Output stream (defaults to sys.stdout)
        """
    
    # Core attributes
    config: Config  # pytest configuration
    stats: dict[str, list[Any]]  # Statistics by category (failed, passed, etc.)
    _tw: TerminalWriter  # Terminal writer for output
    reportchars: str  # Characters controlling what to report
    hasmarkup: bool  # Whether terminal supports markup
    isatty: bool  # Whether output is to a terminal
    verbosity: int  # Verbosity level
    showfspath: bool  # Whether to show file paths
    showlongtestinfo: bool  # Whether to show detailed test info
    _session: Session | None  # Current test session
    _numcollected: int  # Number of collected items
    currentfspath: Path | str | int | None  # Current file being processed
    
    def write(self, content: str, *, flush: bool = False, **markup: bool) -> None:
        """
        Write content to terminal.
        
        Parameters:
        - content: Content to write
        - flush: Whether to flush output immediately
        - **markup: Markup options (bold, red, etc.)
        """
    
    def write_line(self, line: str | bytes, **markup: bool) -> None:
        """
        Write line with newline to terminal.
        
        Parameters:
        - line: Line content
        - **markup: Markup options
        """
    
    def write_sep(self, sep: str, title: str | None = None, **markup: bool) -> None:
        """
        Write separator line.
        
        Parameters:
        - sep: Separator character
        - title: Optional title to include
        - **markup: Markup options
        """
    
    def rewrite(self, line: str, **markup: bool) -> None:
        """
        Rewrite current line (for progress indicators).
        
        Parameters:
        - line: New line content
        - **markup: Markup options
        """
    
    def section(self, title: str, sep: str = "=", **kw: bool) -> None:
        """
        Write section header.
        
        Parameters:
        - title: Section title
        - sep: Separator character
        - **kw: Keyword arguments for formatting
        """
    
    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """
        Handle test report logging.
        
        Parameters:
        - report: Test execution report
        """
    
    def pytest_collectreport(self, report: CollectReport) -> None:
        """
        Handle collection report logging.
        
        Parameters:
        - report: Collection report
        """
    
    def pytest_sessionstart(self, session: Session) -> None:
        """
        Handle session start.
        
        Parameters:
        - session: Test session
        """
    
    def pytest_sessionfinish(self, session: Session, exitstatus: int | ExitCode) -> None:
        """
        Handle session finish.
        
        Parameters:
        - session: Test session
        - exitstatus: Exit status code
        """
    
    def summary_failures(self) -> None:
        """Show failure summary section."""
    
    def summary_errors(self) -> None:
        """Show error summary section."""
    
    def summary_warnings(self) -> None:
        """Show warning summary section."""
    
    def short_test_summary(self) -> None:
        """Show short test summary section."""
    
    def build_summary_stats_line(self) -> tuple[list[tuple[str, dict[str, bool]]], str]:
        """
        Build final statistics line.
        
        Returns:
            Tuple of (stat_parts, duration_string)
        """
```

## Usage Examples

### Creating Custom Reports

```python
import pytest
from _pytest.reports import TestReport, CollectReport

# Custom plugin to process test reports
class CustomReportPlugin:
    def __init__(self):
        self.test_results = []
    
    def pytest_runtest_logreport(self, report: TestReport):
        # Process test reports
        if report.when == "call":  # Only process main test execution
            self.test_results.append({
                'nodeid': report.nodeid,
                'outcome': report.outcome,
                'duration': report.duration,
                'location': report.location,
                'user_properties': report.user_properties,
            })
    
    def pytest_collection_finish(self, session):
        # Process collection results
        for item in session.items:
            print(f"Collected test: {item.nodeid}")

# Register plugin
pytest.main(["-p", "no:terminal", "--tb=no"], plugins=[CustomReportPlugin()])
```

### Custom Terminal Output

```python
from _pytest.terminal import TerminalReporter

class ColorfulReporter(TerminalReporter):
    def pytest_runtest_logreport(self, report):
        # Custom colored output
        if report.when == "call":
            if report.outcome == "passed":
                self.write("✓ ", green=True)
            elif report.outcome == "failed":
                self.write("✗ ", red=True)
            elif report.outcome == "skipped":
                self.write("- ", yellow=True)
            
            self.write_line(f"{report.nodeid}")
        
        # Call parent implementation for other functionality
        super().pytest_runtest_logreport(report)

# Use custom reporter
def pytest_configure(config):
    if config.pluginmanager.get_plugin("terminalreporter"):
        config.pluginmanager.unregister(name="terminalreporter")
    
    config.pluginmanager.register(ColorfulReporter(config), "terminalreporter")
```

### Accessing Call Information

```python
from _pytest.runner import CallInfo

def test_with_call_info():
    # CallInfo is typically used internally, but can be accessed in hooks
    def example_function():
        return "result"
    
    # Capture call information
    call_info = CallInfo.from_call(example_function, when="call")
    
    assert call_info.result == "result"
    assert call_info.excinfo is None
    assert call_info.duration > 0
    assert call_info.when == "call"

# Plugin to access call information in hooks
def pytest_runtest_call(pyfuncitem):
    # This hook has access to CallInfo through the test execution
    pass

def pytest_runtest_makereport(item, call):
    # call parameter is a CallInfo object
    if call.when == "call" and call.excinfo is None:
        print(f"Test {item.nodeid} passed in {call.duration:.2f}s")
```

## Integration with Reporting Tools

### JSON Report Generation

```python
import json
from _pytest.reports import TestReport, CollectReport

class JSONReporter:
    def __init__(self):
        self.reports = []
    
    def pytest_runtest_logreport(self, report: TestReport):
        # Convert TestReport to JSON-serializable format
        report_data = report._to_json()
        self.reports.append(report_data)
    
    def pytest_sessionfinish(self, session):
        # Write JSON report
        with open("test_report.json", "w") as f:
            json.dump(self.reports, f, indent=2)

# Usage
pytest.main(["--tb=short"], plugins=[JSONReporter()])
```

### Database Integration

```python
import sqlite3
from _pytest.reports import TestReport

class DatabaseReporter:
    def __init__(self):
        self.conn = sqlite3.connect("test_results.db")
        self.setup_database()
    
    def setup_database(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                nodeid TEXT,
                outcome TEXT,
                duration REAL,
                when_phase TEXT,
                timestamp REAL,
                location_file TEXT,
                location_line INTEGER
            )
        """)
    
    def pytest_runtest_logreport(self, report: TestReport):
        if report.when == "call":
            self.conn.execute("""
                INSERT INTO test_results 
                (nodeid, outcome, duration, when_phase, timestamp, location_file, location_line)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report.nodeid,
                report.outcome,
                report.duration,
                report.when,
                report.start,
                report.location[0],
                report.location[1]
            ))
            self.conn.commit()

# Usage with database integration
pytest.main(["-v"], plugins=[DatabaseReporter()])
```