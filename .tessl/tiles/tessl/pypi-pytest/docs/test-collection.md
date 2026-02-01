# Test Collection and Execution

Collection tree components for test discovery, organization, and execution. The collection system builds a hierarchical tree of collectors and items that represent the structure of your test suite.

## Capabilities

### Base Collection Classes

Foundation classes for all collection tree components.

```python { .api }
class Node:
    """Base class for all collection tree components."""
    
    # Core attributes
    name: str  # Node name
    parent: Node | None  # Parent node
    config: Config  # pytest configuration
    session: Session  # Test session
    path: Path  # File system path
    nodeid: str  # Unique node identifier
    
    @classmethod
    def from_parent(cls, parent: Node, **kwargs):
        """Create node with parent reference."""
    
    def listchain(self) -> list[Node]:
        """Return list of all parent nodes."""
    
    def add_marker(self, marker) -> None:
        """Add marker to this node."""
    
    def iter_markers(self, name: str | None = None):
        """Iterate over markers."""
    
    def get_closest_marker(self, name: str):
        """Get closest marker with given name."""

class Collector(Node, abc.ABC):
    """Base class for collection tree internal nodes.
    
    Collectors create children through collect() and iteratively build
    the collection tree.
    """
    
    class CollectError(Exception):
        """An error during collection, contains a custom message."""
    
    @abc.abstractmethod
    def collect(self) -> Iterable[Item | Collector]:
        """
        Collect children (items and collectors) for this collector.
        
        Returns:
            Iterable of Item or Collector objects
        """
    
    def repr_failure(self, excinfo: ExceptionInfo[BaseException]) -> str | TerminalRepr:
        """
        Return a representation of a collection failure.
        
        Parameters:
        - excinfo: Exception information for the failure
        
        Returns:
            String or TerminalRepr representation of the failure
        """

class Item(Node, abc.ABC):
    """Base class for collection tree leaf nodes (test items).
    
    Note that for a single function there might be multiple test invocation items.
    """
    
    nextitem = None  # Reference to next item
    
    def __init__(
        self,
        name,
        parent=None,
        config: Config | None = None,
        session: Session | None = None,
        nodeid: str | None = None,
        **kw,
    ) -> None:
        """
        Initialize test item.
        
        Parameters:
        - name: Item name
        - parent: Parent collector
        - config: pytest configuration
        - session: Test session
        - nodeid: Node identifier
        """
    
    @abc.abstractmethod
    def runtest(self) -> None:
        """
        Run the test case (abstract method).
        
        Must be implemented by subclasses to execute the actual test.
        """
    
    def setup(self) -> None:
        """Set up test execution."""
    
    def teardown(self) -> None:
        """Tear down after test execution."""
    
    def add_report_section(self, when: str, key: str, content: str) -> None:
        """
        Add report section to test results.
        
        Parameters:
        - when: Test phase ("setup", "call", "teardown")
        - key: Section identifier
        - content: Section content
        """
    
    def reportinfo(self) -> tuple[os.PathLike[str] | str, int | None, str]:
        """
        Return location information for reporting.
        
        Returns:
            Tuple of (filename, line_number, test_name)
        """
    
    @property
    def location(self) -> tuple[str, int | None, str]:
        """Get test location as (relfspath, lineno, testname)."""
    
    # Attributes
    user_properties: list[tuple[str, object]]  # User-defined properties
    _report_sections: list[tuple[str, str, str]]  # Report sections
```

### File System Collectors

Collectors for file system entities.

```python { .api }
class FSCollector(Collector, abc.ABC):
    """Base class for filesystem-based collectors."""
    
    def __init__(
        self,
        path: Path,
        parent: Collector | None = None,
        config: Config | None = None,
        session: Session | None = None,
        nodeid: str | None = None,
    ) -> None:
        """Initialize filesystem collector with path."""

class File(FSCollector, abc.ABC):
    """Base class for collecting tests from files."""
    
    @abc.abstractmethod
    def collect(self) -> Iterable[Item | Collector]:
        """Collect tests from file (abstract method)."""

class Directory(FSCollector, abc.ABC):
    """Base class for collecting from directories."""
    
    @abc.abstractmethod
    def collect(self) -> Iterable[Item | Collector]:
        """Collect from directory contents (abstract method)."""

class Dir(Directory):
    """Directory collector implementation.
    
    Used for directories without __init__.py files.
    """
    
    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        """
        Collect files and subdirectories.
        
        Returns:
            Iterable of collectors for Python files and subdirectories
        """
    
    @classmethod
    def from_parent(cls, parent: nodes.Collector, *, path: Path) -> Self:
        """
        Create Dir collector from parent.
        
        Parameters:
        - parent: Parent collector
        - path: Directory path
        
        Returns:
            Dir collector instance
        """
```

### Python-Specific Collectors

Collectors specialized for Python test code.

```python { .api }
class PyCollector(Collector, abc.ABC):
    """Base class for Python-specific collectors."""
    
    def _getobj(self):
        """Import and return the Python object."""

class Module(nodes.File, PyCollector):
    """Collector for test classes and functions in Python modules."""
    
    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        """
        Collect test classes and functions from module.
        
        Returns:
            Iterable of Class collectors and Function items
        """
    
    def _getobj(self):
        """
        Import and return the module object.
        
        Returns:
            The imported module
        """
    
    def _register_setup_module_fixture(self) -> None:
        """Register setup/teardown module fixtures."""
    
    def _register_setup_function_fixture(self) -> None:
        """Register setup/teardown function fixtures."""

class Package(nodes.Directory):
    """Collector for Python packages (directories with __init__.py)."""
    
    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        """
        Collect modules and subpackages.
        
        Returns:
            Iterable of Module and Package collectors
        """
    
    def setup(self) -> None:
        """Set up package-level fixtures."""

class Class(PyCollector):
    """Collector for test methods (and nested classes) in Python classes."""
    
    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        """
        Collect test methods from class.
        
        Returns:
            Iterable of Function items and nested Class collectors
        """
    
    def newinstance(self):
        """
        Create new instance of the class.
        
        Returns:
            New instance of the test class
        """
    
    @classmethod
    def from_parent(cls, parent, *, name, obj=None, **kw) -> Self:
        """
        Create Class collector from parent.
        
        Parameters:
        - parent: Parent collector
        - name: Class name
        - obj: Class object (optional)
        
        Returns:
            Class collector instance
        """
    
    def _register_setup_class_fixture(self) -> None:
        """Register class-level setup/teardown fixtures."""
    
    def _register_setup_method_fixture(self) -> None:
        """Register method-level setup/teardown fixtures."""

class Function(Item):
    """Item for Python test functions."""
    
    # Core attributes
    function: Callable  # Test function object
    fixturenames: frozenset[str]  # Required fixture names
    callspec: CallSpec2 | None  # Parametrization info
    
    def runtest(self) -> None:
        """Execute the test function."""
    
    def setup(self) -> None:
        """Set up fixtures and test environment."""
    
    def teardown(self) -> None:
        """Tear down fixtures and clean up."""
```

### Session Management

Root-level session management for test execution coordination.

```python { .api }
class Session(Collector):
    """Root of collection tree, collects initial paths."""
    
    def collect(self) -> list[Node]:
        """Collect from initial file paths."""
    
    def pytest_runtest_protocol(self, item: Item) -> bool:
        """Run test protocol for item."""
    
    def pytest_collection_modifyitems(self, items: list[Item]) -> None:
        """Modify collected items."""
```

### Test Parametrization

Metafunc object for parametrizing tests during collection.

```python { .api }
class Metafunc:
    """Used in pytest_generate_tests hook for parametrizing tests."""
    
    # Core attributes
    function: Callable  # Test function
    module: Any  # Test module
    cls: type | None  # Test class (if applicable)
    config: Config  # pytest configuration
    definition: FunctionDefinition  # Function definition
    fixturenames: frozenset[str]  # Fixture names used by function
    
    def parametrize(
        self,
        argnames: str | list[str] | tuple[str, ...],
        argvalues,
        *,
        indirect: bool | list[str] = False,
        ids=None,
        scope: str | None = None
    ) -> None:
        """Parametrize test function."""
    
    def addcall(self, **kwargs) -> None:
        """Add individual test call (deprecated, use parametrize)."""
```

**Usage Example:**

```python
# conftest.py
def pytest_generate_tests(metafunc):
    if "browser" in metafunc.fixturenames:
        metafunc.parametrize(
            "browser", 
            ["chrome", "firefox", "safari"],
            ids=["Chrome", "Firefox", "Safari"]
        )
    
    if "database" in metafunc.fixturenames:
        metafunc.parametrize(
            "database",
            [("sqlite", ":memory:"), ("postgresql", "test_db")],
            ids=["SQLite", "PostgreSQL"]
        )

# Test will run 6 times (3 browsers × 2 databases)
def test_web_app(browser, database):
    pass
```

### Doctest Integration

Support for running doctests as part of the test suite.

```python { .api }
class DoctestItem(Item):
    """Test item for executing doctests."""
    
    def __init__(
        self,
        name: str,
        parent: DoctestTextfile | DoctestModule,
        runner: doctest.DocTestRunner,
        dtest: doctest.DocTest,
    ) -> None:
        """
        Initialize doctest item.
        
        Parameters:
        - name: Item name
        - parent: Parent collector (DoctestTextfile or DoctestModule)
        - runner: Doctest runner
        - dtest: Doctest object
        """
    
    # Attributes
    runner: doctest.DocTestRunner  # Doctest runner
    dtest: doctest.DocTest  # Doctest object
    obj = None  # No underlying Python object
    _fixtureinfo: fixtures.FuncFixtureInfo  # Fixture information
    fixturenames: frozenset[str]  # Required fixture names
    
    def runtest(self) -> None:
        """
        Execute the doctest.
        
        Runs the doctest using the configured runner and handles
        any failures according to pytest conventions.
        """
    
    def setup(self) -> None:
        """Set up doctest fixtures and environment."""
    
    def repr_failure(self, excinfo: ExceptionInfo[BaseException]) -> str | TerminalRepr:
        """
        Format doctest failures for display.
        
        Parameters:
        - excinfo: Exception information
        
        Returns:
            Formatted failure representation
        """
    
    def reportinfo(self) -> tuple[os.PathLike[str] | str, int | None, str]:
        """
        Get doctest location information for reporting.
        
        Returns:
            Tuple of (filename, line_number, doctest_name)
        """
    
    @classmethod
    def from_parent(
        cls,
        parent: DoctestTextfile | DoctestModule,
        *,
        name: str,
        runner: doctest.DocTestRunner,
        dtest: doctest.DocTest,
    ) -> Self:
        """
        Create DoctestItem from parent collector.
        
        Parameters:
        - parent: Parent collector
        - name: Item name
        - runner: Doctest runner
        - dtest: Doctest object
        
        Returns:
            DoctestItem instance
        """
```

## Collection Process

The collection process follows these steps:

1. **Start Collection**: Session.collect() begins from initial paths
2. **Directory Collection**: Dir collectors process directories
3. **File Collection**: Module collectors process Python files  
4. **Class Collection**: Class collectors process test classes
5. **Function Collection**: Function collectors process test functions
6. **Parametrization**: Metafunc.parametrize() creates multiple test variants
7. **Item Modification**: pytest_collection_modifyitems hook allows final changes

**Usage Example:**

```python
# Custom collector example
class YamlFile(pytest.File):
    def collect(self):
        # Parse YAML file and create test items
        raw = yaml.safe_load(self.path.open())
        for name, spec in raw.items():
            yield YamlTest.from_parent(self, name=name, spec=spec)

class YamlTest(pytest.Item):
    def __init__(self, name, parent, spec):
        super().__init__(name, parent)
        self.spec = spec
    
    def runtest(self):
        # Execute test based on YAML spec
        pass

def pytest_collect_file(parent, path):
    if path.suffix == ".yaml" and path.name.startswith("test_"):
        return YamlFile.from_parent(parent, path=path)
```

## Types

```python { .api }
from typing import Any, Callable
from pathlib import Path

class CallSpec2:
    """Represents parametrized test call specification."""
    
    # Attributes
    params: dict[str, Any]  # Parameter values
    funcargs: dict[str, Any]  # Function arguments
    id: str | None  # Parameter set ID
    marks: list[Mark]  # Applied marks
    
    def setmulti(self, **kwargs) -> None:
        """Set multiple parameters."""

class FunctionDefinition:
    """Definition of a test function for collection."""
    
    # Attributes
    name: str  # Function name
    obj: Callable  # Function object
    parent: Node  # Parent collector
    
    def getparent(self, cls: type) -> Node | None:
        """Get parent of specific type."""
```