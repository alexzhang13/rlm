# Progress Tracking

Advanced progress bar system with customizable columns, multiple tasks, and real-time updates. Rich provides comprehensive progress tracking capabilities for long-running operations with flexible display options.

## Capabilities

### Progress Class

Main progress tracking system with support for multiple concurrent tasks.

```python { .api }
class Progress:
    """
    Multi-task progress tracker with customizable display.
    
    Args:
        *columns: Progress display columns
        console: Console instance for output
        auto_refresh: Enable automatic refresh
        refresh_per_second: Refresh rate in Hz
        speed_estimate_period: Period for speed calculation
        transient: Remove progress display when complete
        redirect_stdout: Redirect stdout during progress
        redirect_stderr: Redirect stderr during progress
        get_time: Function to get current time
        disable: Disable progress display
        expand: Expand progress bar to fit console width
    """
    def __init__(
        self,
        *columns: Union[str, ProgressColumn],
        console: Optional[Console] = None,
        auto_refresh: bool = True,
        refresh_per_second: float = 10,
        speed_estimate_period: float = 30.0,
        transient: bool = False,
        redirect_stdout: bool = True,
        redirect_stderr: bool = True,
        get_time: Optional[GetTimeCallable] = None,
        disable: bool = False,
        expand: bool = False,
    ): ...
    
    def add_task(
        self,
        description: str,
        start: bool = True,
        total: Optional[float] = 100.0,
        completed: float = 0,
        visible: bool = True,
        **fields: Any,
    ) -> TaskID:
        """
        Add a new progress task.
        
        Args:
            description: Task description
            start: Start the task immediately
            total: Total amount of work or None for indeterminate
            completed: Initial completed amount
            visible: Show task in display
            **fields: Additional custom fields
            
        Returns:
            Task ID for future operations
        """
    
    def remove_task(self, task_id: TaskID) -> None:
        """
        Remove a task from progress tracking.
        
        Args:
            task_id: ID of task to remove
        """
    
    def update(
        self,
        task_id: TaskID,
        *,
        total: Optional[float] = None,
        completed: Optional[float] = None,
        advance: Optional[float] = None,
        description: Optional[str] = None,
        visible: Optional[bool] = None,
        refresh: bool = False,
        **fields: Any,
    ) -> None:
        """
        Update a progress task.
        
        Args:
            task_id: Task to update
            total: New total amount
            completed: New completed amount
            advance: Amount to advance by
            description: New description
            visible: Show/hide task
            refresh: Force display refresh
            **fields: Update custom fields
        """
    
    def advance(self, task_id: TaskID, advance: float = 1.0) -> None:
        """
        Advance a task by specified amount.
        
        Args:
            task_id: Task to advance
            advance: Amount to advance by
        """
    
    def start_task(self, task_id: TaskID) -> None:
        """
        Start a paused task.
        
        Args:
            task_id: Task to start
        """
    
    def stop_task(self, task_id: TaskID) -> None:
        """
        Stop/pause a task.
        
        Args:
            task_id: Task to stop
        """
    
    def reset(
        self,
        task_id: TaskID,
        *,
        start: bool = True,
        total: Optional[float] = None,
        completed: float = 0,
        visible: Optional[bool] = None,
        description: Optional[str] = None,
        **fields: Any,
    ) -> None:
        """
        Reset a task to initial state.
        
        Args:
            task_id: Task to reset
            start: Start task after reset
            total: New total amount
            completed: Reset completed amount
            visible: Task visibility
            description: New description
            **fields: Reset custom fields
        """
    
    def get_task(self, task_id: TaskID) -> Task:
        """
        Get task information.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task object with current state
        """
    
    def refresh(self) -> None:
        """Force refresh of progress display."""
    
    def start(self) -> None:
        """Start progress display."""
    
    def stop(self) -> None:
        """Stop progress display."""
    
    def track(
        self,
        sequence: Iterable[ProgressType],
        task_id: Optional[TaskID] = None,
        description: str = "Working...",
        total: Optional[float] = None,
        auto_refresh: bool = True,
        console: Optional[Console] = None,
        transient: bool = False,
        get_time: Optional[GetTimeCallable] = None,
        refresh_per_second: float = 10,
        style: StyleType = "bar.back",
        complete_style: StyleType = "bar.complete",
        finished_style: StyleType = "bar.finished",
        pulse_style: StyleType = "bar.pulse",
        update_period: float = 0.1,
        disable: bool = False,
        show_speed: bool = True,
    ) -> Iterable[ProgressType]:
        """
        Track progress of an iterable.
        
        Args:
            sequence: Iterable to track
            task_id: Existing task ID or None for new task
            description: Task description
            total: Total items or None to auto-detect
            auto_refresh: Enable automatic refresh
            console: Console for output
            transient: Remove when complete
            get_time: Time function
            refresh_per_second: Refresh rate
            style: Progress bar style
            complete_style: Completed portion style
            finished_style: Finished bar style
            pulse_style: Indeterminate pulse style
            update_period: Update frequency
            disable: Disable progress display
            show_speed: Show processing speed
            
        Returns:
            Iterator that yields items while tracking progress
        """
    
    @contextmanager
    def wrap_file(
        self,
        file: BinaryIO,
        total: int,
        *,
        task_id: Optional[TaskID] = None,
        description: str = "Reading...",
    ) -> Iterator[BinaryIO]:
        """
        Wrap a file for progress tracking.
        
        Args:
            file: File object to wrap
            total: Total file size in bytes
            task_id: Existing task ID or None for new task
            description: Task description
            
        Yields:
            Wrapped file object that updates progress
        """
    
    @contextmanager
    def open(
        self,
        file: Union[str, "PathLike[str]", IO[bytes]],
        mode: str = "rb",
        *,
        buffering: int = -1,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
        description: str = "Reading...",
        auto_refresh: bool = True,
        console: Optional[Console] = None,
        transient: bool = False,
        get_time: Optional[GetTimeCallable] = None,
        refresh_per_second: float = 10,
        style: StyleType = "bar.back",
        complete_style: StyleType = "bar.complete",
        finished_style: StyleType = "bar.finished",
        pulse_style: StyleType = "bar.pulse",
        disable: bool = False,
    ) -> Iterator[IO[Any]]:
        """
        Open a file with progress tracking.
        
        Args:
            file: File path or file object
            mode: File open mode
            buffering: Buffer size
            encoding: Text encoding
            errors: Error handling
            newline: Newline handling
            description: Task description
            auto_refresh: Enable automatic refresh
            console: Console for output
            transient: Remove when complete
            get_time: Time function
            refresh_per_second: Refresh rate
            style: Progress bar style
            complete_style: Completed portion style
            finished_style: Finished bar style
            pulse_style: Indeterminate pulse style
            disable: Disable progress display
            
        Yields:
            File object with progress tracking
        """
    
    # Properties
    @property
    def tasks(self) -> List[Task]:
        """Get list of all tasks."""
    
    @property
    def task_ids(self) -> List[TaskID]:
        """Get list of all task IDs."""
    
    @property
    def finished(self) -> bool:
        """Check if all tasks are finished."""
    
    @property
    def live(self) -> Live:
        """Get the underlying Live display."""
```

### Task Class

Task information and state.

```python { .api }
class Task:
    """
    Progress task data and state.
    
    Attributes:
        id: Unique task identifier
        description: Task description text
        total: Total amount of work or None for indeterminate
        completed: Amount of work completed
        visible: Whether task is visible in display
        fields: Custom data fields
        created_time: Time when task was created
        started_time: Time when task was started
        stopped_time: Time when task was stopped
        finished_time: Time when task finished
    """
    id: TaskID
    description: str
    total: Optional[float]
    completed: float
    visible: bool
    fields: Dict[str, Any]
    created_time: float
    started_time: Optional[float]
    stopped_time: Optional[float]
    finished_time: Optional[float]
    
    @property
    def elapsed(self) -> Optional[float]:
        """Get elapsed time since task started."""
    
    @property
    def finished(self) -> bool:
        """Check if task is finished."""
    
    @property
    def percentage(self) -> float:
        """Get completion percentage (0-100)."""
    
    @property 
    def speed(self) -> Optional[float]:
        """Get current processing speed."""
    
    @property
    def time_remaining(self) -> Optional[float]:
        """Get estimated time remaining."""
```

### Progress Columns

Customizable display columns for progress bars.

```python { .api }
class ProgressColumn(ABC):
    """Base class for progress display columns."""
    
    @abstractmethod
    def render(self, task: Task) -> RenderableType:
        """
        Render column content for a task.
        
        Args:
            task: Task to render
            
        Returns:
            Renderable content
        """

class RenderableColumn(ProgressColumn):
    """Column that displays a fixed renderable."""
    
    def __init__(self, renderable: RenderableType, *, table_column: Optional[Column] = None): ...

class SpinnerColumn(ProgressColumn):
    """Column with animated spinner."""
    
    def __init__(
        self,
        spinner_name: str = "dots",
        style: Optional[StyleType] = None,
        speed: float = 1.0,
        finished_text: TextType = "✓",
        table_column: Optional[Column] = None,
    ): ...

class TextColumn(ProgressColumn):
    """Column displaying task text/description."""
    
    def __init__(
        self,
        text_format: str = "[progress.description]{task.description}",
        style: StyleType = "",
        justify: JustifyMethod = "left",
        markup: bool = True,
        highlighter: Optional[Highlighter] = None,
        table_column: Optional[Column] = None,
    ): ...

class BarColumn(ProgressColumn):
    """Progress bar column."""
    
    def __init__(
        self,
        bar_width: Optional[int] = 40,
        style: StyleType = "bar.back",
        complete_style: StyleType = "bar.complete",
        finished_style: StyleType = "bar.finished",
        pulse_style: StyleType = "bar.pulse",
        table_column: Optional[Column] = None,
    ): ...

class TaskProgressColumn(TextColumn):
    """Column showing task progress percentage."""
    
    def __init__(
        self,
        text_format: str = "[progress.percentage]{task.percentage:>3.1f}%",
        style: StyleType = "",
        justify: JustifyMethod = "left",
        markup: bool = True,
        highlighter: Optional[Highlighter] = None,
        table_column: Optional[Column] = None,
    ): ...

class TimeElapsedColumn(ProgressColumn):
    """Column showing elapsed time."""
    
    def __init__(self, table_column: Optional[Column] = None): ...

class TimeRemainingColumn(ProgressColumn):
    """Column showing estimated time remaining."""
    
    def __init__(
        self,
        compact: bool = False,
        elapsed_when_finished: bool = False,
        table_column: Optional[Column] = None,
    ): ...

class FileSizeColumn(ProgressColumn):
    """Column showing file size completed."""
    
    def __init__(self, table_column: Optional[Column] = None): ...

class TotalFileSizeColumn(ProgressColumn):
    """Column showing total file size."""
    
    def __init__(self, table_column: Optional[Column] = None): ...

class MofNCompleteColumn(ProgressColumn):
    """Column showing 'M of N' completion."""
    
    def __init__(
        self,
        separator: str = "/",
        table_column: Optional[Column] = None,
    ): ...

class DownloadColumn(ProgressColumn):
    """Column for download progress with speed."""
    
    def __init__(
        self,
        binary_units: bool = False,
        table_column: Optional[Column] = None,
    ): ...

class TransferSpeedColumn(ProgressColumn):
    """Column showing transfer speed."""
    
    def __init__(self, table_column: Optional[Column] = None): ...
```

**Usage Examples:**

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
import time

# Basic progress bar
with Progress() as progress:
    task = progress.add_task("Processing...", total=100)
    
    for i in range(100):
        time.sleep(0.1)
        progress.update(task, advance=1)

# Custom progress layout
progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    TimeElapsedColumn(),
)

with progress:
    task1 = progress.add_task("Download", total=1000)
    task2 = progress.add_task("Process", total=500)
    
    # Simulate work
    for i in range(1000):
        time.sleep(0.01)
        progress.update(task1, advance=1)
        if i % 2 == 0:
            progress.update(task2, advance=1)

# Multiple concurrent tasks
with Progress() as progress:
    tasks = [
        progress.add_task("Task 1", total=100),
        progress.add_task("Task 2", total=200),
        progress.add_task("Task 3", total=150),
    ]
    
    # Process tasks concurrently
    import threading
    
    def work(task_id, total):
        for i in range(total):
            time.sleep(0.05)
            progress.update(task_id, advance=1)
    
    threads = []
    for task_id, total in zip(tasks, [100, 200, 150]):
        thread = threading.Thread(target=work, args=(task_id, total))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

# Track iterable
from rich.progress import track

items = range(100)
for item in track(items, description="Processing items..."):
    time.sleep(0.1)  # Simulate work

# File download simulation
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn

def download_file(url, size):
    """Simulate file download."""
    progress = Progress(
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeElapsedColumn(),
    )
    
    with progress:
        task = progress.add_task("download", filename=url, total=size)
        for chunk_size in [500, 600, 300, 400, 800, 200]:
            time.sleep(0.5)  # Simulate network delay
            progress.update(task, advance=chunk_size)

# Example: download_file("example.zip", 3000)

# Indeterminate progress (no known total)
with Progress() as progress:
    task = progress.add_task("Scanning...", total=None)
    
    for i in range(50):
        time.sleep(0.1)
        progress.update(task, advance=1)  # Still advances for timing

# Progress with custom fields
with Progress() as progress:
    task = progress.add_task("Custom Task", total=100, status="Starting")
    
    for i in range(100):
        status = f"Processing item {i+1}"
        progress.update(task, advance=1, status=status)
        time.sleep(0.05)

# File processing with progress
from rich.progress import Progress

def process_files(file_paths):
    with Progress() as progress:
        main_task = progress.add_task("Processing files", total=len(file_paths))
        
        for file_path in file_paths:
            # Process individual file
            file_task = progress.add_task(f"Processing {file_path}", total=100)
            
            for chunk in range(100):
                time.sleep(0.01)  # Simulate file processing
                progress.update(file_task, advance=1)
            
            progress.update(main_task, advance=1)
            progress.remove_task(file_task)

# Example: process_files(["file1.txt", "file2.txt", "file3.txt"])
```