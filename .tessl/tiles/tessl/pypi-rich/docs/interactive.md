# Interactive Components

Live updating displays, user input prompts, and real-time interface components. Rich provides comprehensive interactive capabilities for dynamic terminal applications and user input handling.

## Capabilities

### Live Display

Real-time updating display system for dynamic content.

```python { .api }
class Live:
    """
    Live updating display context manager.
    
    Args:
        renderable: Initial content to display
        console: Console instance for output
        screen: Use full screen mode
        auto_refresh: Enable automatic refresh
        refresh_per_second: Refresh rate in Hz
        transient: Remove display when exiting context
        redirect_stdout: Redirect stdout during live display
        redirect_stderr: Redirect stderr during live display
        vertical_overflow: Overflow method for vertical content
        get_renderable: Function to get current renderable
    """
    def __init__(
        self,
        renderable: Optional[RenderableType] = None,
        *,
        console: Optional[Console] = None,
        screen: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: float = 4,
        transient: bool = False,
        redirect_stdout: bool = True,
        redirect_stderr: bool = True,
        vertical_overflow: OverflowMethod = "ellipsis",
        get_renderable: Optional[Callable[[], RenderableType]] = None,
    ): ...
    
    def update(
        self, 
        renderable: RenderableType, 
        *, 
        refresh: bool = False
    ) -> None:
        """
        Update the live display content.
        
        Args:
            renderable: New content to display
            refresh: Force immediate refresh
        """
    
    def refresh(self) -> None:
        """Force refresh of the display."""
    
    def start(self, refresh: bool = False) -> None:
        """
        Start the live display.
        
        Args:
            refresh: Refresh immediately after starting
        """
    
    def stop(self) -> None:
        """Stop the live display."""
    
    # Properties
    @property
    def is_started(self) -> bool:
        """Check if live display is active."""
    
    @property
    def renderable(self) -> RenderableType:
        """Get current renderable content."""
    
    @property 
    def console(self) -> Console:
        """Get the console instance."""
```

### Status Display

Status indicator with animated spinner.

```python { .api }
class Status:
    """
    Status display with spinner animation.
    
    Args:
        status: Status message or renderable
        console: Console instance for output
        spinner: Spinner animation name
        spinner_style: Style for spinner
        speed: Animation speed multiplier
        refresh_per_second: Refresh rate in Hz
    """
    def __init__(
        self,
        status: RenderableType,
        *,
        console: Optional[Console] = None,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ): ...
    
    def update(
        self,
        status: Optional[RenderableType] = None,
        *,
        spinner: Optional[str] = None,
        spinner_style: Optional[StyleType] = None,
        speed: Optional[float] = None,
    ) -> None:
        """
        Update status display.
        
        Args:
            status: New status message
            spinner: New spinner style
            spinner_style: New spinner styling
            speed: New animation speed
        """
    
    def start(self) -> None:
        """Start the status display."""
    
    def stop(self) -> None:
        """Stop the status display."""
    
    # Properties
    @property
    def renderable(self) -> RenderableType:
        """Get current status renderable."""
```

### User Input Prompts

Interactive prompts for user input with validation.

```python { .api }
class PromptBase(Generic[PromptType]):
    """Base class for user input prompts."""
    
    @classmethod
    def ask(
        cls,
        prompt: TextType = "",
        *,
        console: Optional[Console] = None,
        password: bool = False,
        choices: Optional[List[str]] = None,
        show_default: bool = True,
        show_choices: bool = True,
        default: Any = ...,
        stream: Optional[TextIO] = None,
    ) -> PromptType:
        """
        Prompt user for input.
        
        Args:
            prompt: Prompt text to display
            console: Console instance for I/O
            password: Hide input for passwords
            choices: Valid choices for input
            show_default: Show default value in prompt
            show_choices: Show available choices
            default: Default value if no input
            stream: Input stream or None for stdin
            
        Returns:
            User input converted to appropriate type
        """
    
    def get_input(
        self,
        console: Console,
        prompt: TextType,
        password: bool,
        stream: Optional[TextIO] = None,
    ) -> str:
        """
        Get raw input from user.
        
        Args:
            console: Console for output
            prompt: Prompt to display
            password: Hide input characters
            stream: Input stream
            
        Returns:
            Raw input string
        """
    
    def check_choice(self, value: str) -> bool:
        """
        Check if input matches available choices.
        
        Args:
            value: User input to check
            
        Returns:
            True if valid choice
        """
    
    def process_response(self, value: str) -> PromptType:
        """
        Process and validate user response.
        
        Args:
            value: Raw user input
            
        Returns:
            Processed and validated response
        """
    
    def on_validate_error(self, value: str, error: ValueError) -> None:
        """
        Handle validation errors.
        
        Args:
            value: Invalid input value
            error: Validation error
        """
    
    def render_default(self, default: Any) -> Text:
        """
        Render default value for display.
        
        Args:
            default: Default value
            
        Returns:
            Formatted default value
        """

class Prompt(PromptBase[str]):
    """String input prompt."""
    
    @classmethod
    def ask(
        cls,
        prompt: TextType = "",
        *,
        console: Optional[Console] = None,
        password: bool = False,
        choices: Optional[List[str]] = None,
        show_default: bool = True,
        show_choices: bool = True,
        default: str = "",
        stream: Optional[TextIO] = None,
    ) -> str:
        """
        Prompt for string input.
        
        Args:
            prompt: Prompt text
            console: Console instance
            password: Hide input
            choices: Valid string choices
            show_default: Show default in prompt
            show_choices: Show available choices
            default: Default string value
            stream: Input stream
            
        Returns:
            User input string
        """

class IntPrompt(PromptBase[int]):
    """Integer input prompt."""
    
    @classmethod
    def ask(
        cls,
        prompt: TextType = "",
        *,
        console: Optional[Console] = None,
        password: bool = False,
        choices: Optional[List[int]] = None,
        show_default: bool = True,
        show_choices: bool = True,
        default: int = ...,
        stream: Optional[TextIO] = None,
    ) -> int:
        """
        Prompt for integer input.
        
        Args:
            prompt: Prompt text
            console: Console instance
            password: Hide input
            choices: Valid integer choices
            show_default: Show default in prompt
            show_choices: Show available choices
            default: Default integer value
            stream: Input stream
            
        Returns:
            User input as integer
        """

class FloatPrompt(PromptBase[float]):
    """Float input prompt."""
    
    @classmethod
    def ask(
        cls,
        prompt: TextType = "",
        *,
        console: Optional[Console] = None,
        password: bool = False,
        choices: Optional[List[float]] = None,
        show_default: bool = True,
        show_choices: bool = True,
        default: float = ...,
        stream: Optional[TextIO] = None,
    ) -> float:
        """
        Prompt for float input.
        
        Args:
            prompt: Prompt text
            console: Console instance
            password: Hide input
            choices: Valid float choices
            show_default: Show default in prompt
            show_choices: Show available choices
            default: Default float value
            stream: Input stream
            
        Returns:
            User input as float
        """

class Confirm(PromptBase[bool]):
    """Yes/no confirmation prompt."""
    
    @classmethod
    def ask(
        cls,
        prompt: TextType = "",
        *,
        console: Optional[Console] = None,
        password: bool = False,
        choices: Optional[List[str]] = None,
        show_default: bool = True,
        show_choices: bool = True,
        default: bool = False,
        stream: Optional[TextIO] = None,
    ) -> bool:
        """
        Prompt for yes/no confirmation.
        
        Args:
            prompt: Prompt text
            console: Console instance
            password: Hide input (not recommended for confirm)
            choices: Custom yes/no choices
            show_default: Show default in prompt
            show_choices: Show y/n choices
            default: Default boolean value
            stream: Input stream
            
        Returns:
            True for yes, False for no
        """
```

### Spinner Animations

Animated spinner components for loading indicators.

```python { .api }
class Spinner:
    """
    Animated spinner for loading indicators.
    
    Args:
        name: Spinner animation name
        text: Text to display with spinner
        style: Style for spinner and text
        speed: Animation speed multiplier
    """
    def __init__(
        self,
        name: str = "dots",
        text: TextType = "",
        *,
        style: Optional[StyleType] = None,
        speed: float = 1.0,
    ): ...
    
    def render(self, time: float) -> RenderableType:
        """
        Render spinner at given time.
        
        Args:
            time: Current time for animation
            
        Returns:
            Renderable spinner frame
        """
    
    # Properties
    @property
    def name(self) -> str:
        """Get spinner name."""
    
    @property
    def frames(self) -> List[str]:
        """Get animation frames."""
    
    @property
    def interval(self) -> float:
        """Get frame interval in seconds."""
```

**Usage Examples:**

```python
from rich.live import Live
from rich.console import Console
from rich.table import Table
from rich.spinner import Spinner
from rich.status import Status
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
import time

console = Console()

# Basic live display
def generate_table():
    """Generate a sample table."""
    table = Table()
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Status")
    
    table.add_row("1", "Task A", "Running")
    table.add_row("2", "Task B", "Complete")
    table.add_row("3", "Task C", "Pending")
    
    return table

with Live(generate_table(), refresh_per_second=4) as live:
    for i in range(40):
        time.sleep(0.1)
        # Update with new content
        table = generate_table()
        # Add dynamic row
        table.add_row(str(i+4), f"Dynamic {i}", "Active")
        live.update(table)

# Live display with periodic updates
from rich.text import Text

def get_current_time():
    return Text(f"Current time: {time.strftime('%H:%M:%S')}", style="bold green")

with Live(get_current_time(), refresh_per_second=1) as live:
    for _ in range(10):
        time.sleep(1)
        live.update(get_current_time())

# Status with spinner
with console.status("Loading data...") as status:
    time.sleep(2)
    status.update("Processing data...")
    time.sleep(2)
    status.update("Finalizing...")
    time.sleep(1)

# Custom status display
status = Status(
    "Custom loading...",
    spinner="dots",
    spinner_style="bold blue"
)

with status:
    time.sleep(3)

# User input prompts
name = Prompt.ask("What's your name?")
print(f"Hello {name}!")

age = IntPrompt.ask("What's your age?", default=25)
print(f"You are {age} years old")

height = FloatPrompt.ask("What's your height in meters?", default=1.75)
print(f"Your height is {height}m")

# Confirmation prompt
delete_files = Confirm.ask("Delete all files?")
if delete_files:
    print("Files would be deleted")
else:
    print("Operation cancelled")

# Prompt with choices
color = Prompt.ask(
    "Choose a color", 
    choices=["red", "green", "blue"], 
    default="blue"
)
print(f"You chose {color}")

# Password input
password = Prompt.ask("Enter password", password=True)
print("Password entered (hidden)")

# Complex live display with multiple updates
from rich.panel import Panel
from rich.columns import Columns

def create_dashboard():
    """Create a dashboard layout."""
    left_panel = Panel("System Status: OK", title="Status")
    right_panel = Panel(f"Time: {time.strftime('%H:%M:%S')}", title="Clock")
    
    return Columns([left_panel, right_panel])

with Live(create_dashboard(), refresh_per_second=1) as live:
    for i in range(20):
        time.sleep(0.5)
        if i % 4 == 0:  # Update every 2 seconds
            live.update(create_dashboard())

# Progress with live updates
from rich.progress import Progress, TaskID

def live_progress_demo():
    """Demonstrate live progress updates."""
    progress = Progress()
    
    with Live(progress, refresh_per_second=10) as live:
        task1 = progress.add_task("Download", total=1000)
        task2 = progress.add_task("Process", total=1000)
        
        while not progress.finished:
            progress.advance(task1, 3)
            progress.advance(task2, 1)
            time.sleep(0.02)

# Live display with error handling
def safe_live_display():
    """Live display with error handling."""
    try:
        with Live("Starting...", transient=True) as live:
            for i in range(5):
                live.update(f"Step {i+1}/5")
                time.sleep(1)
            live.update("Complete!")
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("Display interrupted by user")

# Interactive menu using prompts
def interactive_menu():
    """Create an interactive menu system."""
    while True:
        console.print("\n[bold blue]Main Menu[/bold blue]")
        console.print("1. View Status")
        console.print("2. Update Settings") 
        console.print("3. Exit")
        
        choice = IntPrompt.ask("Choose option", choices=[1, 2, 3])
        
        if choice == 1:
            console.print("[green]Status: All systems operational[/green]")
        elif choice == 2:
            console.print("[yellow]Settings updated[/yellow]")
        elif choice == 3:
            if Confirm.ask("Really exit?"):
                break
            
    console.print("Goodbye!")

# Example: interactive_menu()
```