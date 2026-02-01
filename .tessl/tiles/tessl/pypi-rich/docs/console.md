# Console and Output

Core console functionality for printing styled text, handling terminal capabilities, and managing output formatting. The Console class is the central component of Rich, providing comprehensive terminal output management with automatic capability detection.

## Capabilities

### Console Class

The main Console class handles all terminal output with support for styling, color, markup, and advanced formatting features.

```python { .api }
class Console:
    """
    A high level console interface for Rich.
    
    Args:
        color_system: The color system to use ("auto", "standard", "256", "truecolor", "windows", None)
        force_terminal: Force terminal detection
        force_jupyter: Force Jupyter mode detection  
        force_interactive: Force interactive mode
        soft_wrap: Enable soft wrapping of long lines
        theme: Default theme or None for builtin theme
        stderr: Write to stderr instead of stdout
        file: File object to write to or None for stdout
        quiet: Suppress all output if True
        width: Width of output or None to auto-detect
        height: Height of output or None to auto-detect
        style: Default style for console output
        no_color: Disable color output
        tab_size: Size of tabs in characters
        record: Record all output for later playback
        markup: Enable Rich markup processing
        emoji: Enable emoji code rendering
        emoji_variant: Emoji variant preference
        highlight: Enable highlighting of output
        log_time: Include timestamp in log output
        log_path: Include path in log output
        log_time_format: Format for log timestamps
        highlighter: Default highlighter for output
        legacy_windows: Enable legacy Windows terminal support
        safe_box: Disable box characters incompatible with legacy terminals
        get_datetime: Callable to get current datetime
        get_time: Callable to get current time
    """
    def __init__(
        self,
        color_system: Optional[str] = "auto",
        force_terminal: Optional[bool] = None,
        force_jupyter: Optional[bool] = None,
        force_interactive: Optional[bool] = None,
        soft_wrap: bool = False,
        theme: Optional[Theme] = None,
        stderr: bool = False,
        file: Optional[TextIO] = None,
        quiet: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,   
        style: Optional[StyleType] = None,
        no_color: Optional[bool] = None,
        tab_size: int = 8,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        emoji_variant: Optional[EmojiVariant] = None,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        log_time_format: Union[str, FormatTimeCallable] = "[%X]",
        highlighter: Optional[HighlighterType] = ReprHighlighter(),
        legacy_windows: Optional[bool] = None,
        safe_box: bool = True,
        get_datetime: Optional[Callable[[], datetime]] = None,
        get_time: Optional[Callable[[], float]] = None,
        _environ: Optional[Mapping[str, str]] = None,
    ): ...
    
    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[StyleType] = None,
        justify: Optional[JustifyMethod] = None,
        overflow: Optional[OverflowMethod] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: bool = True,
        soft_wrap: Optional[bool] = None,
        new_line_start: bool = False,
    ) -> None:
        """
        Print to the console with rich formatting.
        
        Args:
            *objects: Objects to print
            sep: Separator between objects
            end: String to print at end
            style: Style to apply to output
            justify: Text justification method
            overflow: Overflow handling method
            no_wrap: Disable text wrapping
            emoji: Enable emoji rendering
            markup: Enable markup processing
            highlight: Enable highlighting
            width: Maximum width of output
            height: Maximum height of output
            crop: Crop output to fit console
            soft_wrap: Enable soft wrapping
            new_line_start: Start on new line
        """
    
    def log(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[StyleType] = None,
        justify: Optional[JustifyMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        log_locals: bool = False,
        _stack_offset: int = 1,
    ) -> None:
        """
        Print with timestamp and caller information.
        
        Args:
            *objects: Objects to log
            sep: Separator between objects  
            end: String to print at end
            style: Style to apply to output
            justify: Text justification method
            emoji: Enable emoji rendering
            markup: Enable markup processing
            highlight: Enable highlighting
            log_locals: Include local variables in output
        """
    
    def clear(self, home: bool = True) -> None:
        """
        Clear the console.
        
        Args:
            home: Move cursor to home position
        """
    
    def rule(
        self,
        title: TextType = "",
        *,
        characters: str = "─",
        style: StyleType = "rule.line",
        end: str = "\n",
        align: AlignMethod = "center",
    ) -> None:
        """
        Print a horizontal rule with optional title.
        
        Args:
            title: Title text for the rule
            characters: Characters to use for the rule
            style: Style for the rule
            end: String to print at end
            align: Alignment of title
        """
    
    def status(
        self,
        status: RenderableType,
        *,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
    ) -> "Status":
        """
        Create a status context manager with spinner.
        
        Args:
            status: Status text or renderable
            spinner: Spinner style name
            spinner_style: Style for spinner
            speed: Spinner animation speed
            
        Returns:
            Status context manager
        """
    
    def capture(self) -> "Capture":
        """
        Create a capture context to record console output.
        
        Returns:
            Capture context manager
        """
    
    def pager(
        self, pager: Optional[Pager] = None, styles: bool = False, links: bool = False
    ) -> "PagerContext":
        """
        Create a pager context for scrollable output.
        
        Args:
            pager: Pager instance or None for system pager
            styles: Include styles in paged output
            links: Include links in paged output
            
        Returns:
            Pager context manager
        """
    
    def screen(
        self, *, hide_cursor: bool = True, alt_screen: bool = True
    ) -> "ScreenContext":
        """
        Create a screen context for full-screen applications.
        
        Args:
            hide_cursor: Hide the cursor
            alt_screen: Use alternate screen buffer
            
        Returns:
            Screen context manager
        """
    
    def measure(self, renderable: RenderableType) -> Measurement:
        """
        Measure the dimensions of a renderable.
        
        Args:
            renderable: Object to measure
            
        Returns:
            Measurement with minimum and maximum dimensions
        """
    
    def render(
        self, renderable: RenderableType, options: Optional[ConsoleOptions] = None
    ) -> Iterable[Segment]:
        """
        Render a renderable to segments.
        
        Args:
            renderable: Object to render
            options: Console options or None for default
            
        Returns:
            Iterator of segments
        """
    
    def export_html(
        self,
        *,
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: Optional[str] = None,
        inline_styles: bool = False,
    ) -> str:
        """
        Export console content as HTML.
        
        Args:
            theme: Terminal theme or None for default
            clear: Clear console after export
            code_format: Code format template
            inline_styles: Use inline CSS styles
            
        Returns:
            HTML string
        """
    
    def export_svg(
        self,
        *,
        title: str = "Rich",
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: str = CONSOLE_SVG_FORMAT,
        font_size: float = 14,
        unique_id: Optional[str] = None,
    ) -> str:
        """
        Export console content as SVG.
        
        Args:
            title: SVG title
            theme: Terminal theme or None for default
            clear: Clear console after export  
            code_format: SVG format template
            font_size: Font size in pixels
            unique_id: Unique identifier for SVG elements
            
        Returns:
            SVG string
        """
    
    def export_text(self, *, clear: bool = True, styles: bool = False) -> str:
        """
        Export console content as plain text.
        
        Args:
            clear: Clear console after export
            styles: Include ANSI styles in output
            
        Returns:
            Plain text string
        """
    
    # Properties
    @property
    def size(self) -> ConsoleDimensions:
        """Get console dimensions (width, height)."""
    
    @property
    def width(self) -> int:
        """Get console width in characters."""
        
    @property
    def height(self) -> int:
        """Get console height in lines."""
    
    @property
    def is_terminal(self) -> bool:
        """Check if output is a terminal."""
    
    @property
    def is_dumb_terminal(self) -> bool:
        """Check if terminal has limited capabilities."""
    
    @property
    def is_interactive(self) -> bool:
        """Check if console is interactive."""
    
    @property
    def color_system(self) -> Optional[str]:
        """Get the active color system."""
    
    @property
    def encoding(self) -> str:
        """Get the output encoding."""
    
    @property
    def is_jupyter(self) -> bool:
        """Check if running in Jupyter."""
    
    @property
    def options(self) -> ConsoleOptions:
        """Get default console options."""
```

### Global Functions

Module-level convenience functions for common operations.

```python { .api }
def get_console() -> Console:
    """
    Get a global Console instance.
    
    Returns:
        Global console instance
    """

def reconfigure(*args: Any, **kwargs: Any) -> None:
    """
    Reconfigure the global console.
    
    Args:
        *args: Positional arguments for Console constructor
        **kwargs: Keyword arguments for Console constructor
    """

def print(
    *objects: Any,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
) -> None:
    """
    Rich-enhanced print function with markup support.
    
    Args:
        *objects: Objects to print
        sep: Separator between objects
        end: String to print at end
        file: File to write to or None for stdout
        flush: Force flush output (ignored, Rich always flushes)
    """

def print_json(
    json: Optional[str] = None,
    *,
    data: Any = None,
    indent: Union[None, int, str] = 2,
    highlight: bool = True,
    skip_keys: bool = False,
    ensure_ascii: bool = False,
    check_circular: bool = True,
    allow_nan: bool = True,
    default: Optional[Callable[[Any], Any]] = None,
    sort_keys: bool = False,
) -> None:
    """
    Pretty print JSON with syntax highlighting.
    
    Args:
        json: JSON string to print
        data: Python data to encode as JSON
        indent: Number of spaces to indent
        highlight: Enable syntax highlighting
        skip_keys: Skip keys that are not basic types
        ensure_ascii: Escape non-ASCII characters
        check_circular: Check for circular references
        allow_nan: Allow NaN and Infinity values
        default: Function to handle non-serializable objects
        sort_keys: Sort object keys
    """

def inspect(
    obj: Any,
    *,
    console: Optional[Console] = None,
    title: Optional[str] = None,
    help: bool = False,
    methods: bool = False,
    docs: bool = True,
    private: bool = False,
    dunder: bool = False,
    sort: bool = True,
    all: bool = False,
    value: bool = True,
) -> None:
    """
    Inspect any Python object with rich formatting.
    
    Args:
        obj: Object to inspect
        console: Console instance or None for global console
        title: Title for the inspection or None to use object type
        help: Show full help text instead of summary
        methods: Include callable methods
        docs: Show docstrings
        private: Show private attributes (starting with _)
        dunder: Show dunder attributes (starting with __)
        sort: Sort attributes alphabetically
        all: Show all attributes (equivalent to private=True, dunder=True)
        value: Show attribute values
    """
```

**Usage Examples:**

```python
from rich.console import Console
from rich import print

# Basic console usage
console = Console()
console.print("Hello, World!", style="bold red")

# Enhanced print with markup
print("[bold blue]Information:[/bold blue] Process completed successfully")
print("[red]Error:[/red] Unable to connect to server")

# Logging with timestamps
console.log("Application started")
console.log("Processing data...", style="yellow")

# Status spinner
with console.status("Loading data...") as status:
    time.sleep(2)
    status.update("Processing...")
    time.sleep(2)

# Measuring content
from rich.text import Text
text = Text("Hello World", style="bold")
measurement = console.measure(text)
print(f"Text width: {measurement.minimum}-{measurement.maximum}")

# Exporting output
console.print("This will be exported", style="green")
html_output = console.export_html()
svg_output = console.export_svg()

# Object inspection
inspect([1, 2, 3, 4, 5])
inspect(console, methods=True)
```