# Rich

Rich is a comprehensive Python terminal formatting library that enables developers to create beautiful, interactive command-line interfaces with advanced text styling, color support, and rich output components. It provides a powerful API for rendering styled text with support for RGB/HEX colors, markup-style formatting, and automatic terminal capability detection.

## Package Information

- **Package Name**: rich
- **Package Type**: pypi
- **Language**: Python
- **Installation**: `pip install rich`
- **Minimum Python**: 3.8+
- **Dependencies**: pygments, markdown-it-py

## Core Imports

```python
import rich
from rich.console import Console
from rich.text import Text
from rich import print
```

Common imports for specific functionality:

```python
from rich.table import Table
from rich.progress import Progress
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.layout import Layout
```

## Basic Usage

```python
from rich.console import Console
from rich.text import Text
from rich import print

# Enhanced print function with markup support
print("Hello [bold magenta]World[/bold magenta]!")
print("[bold red]Alert![/bold red] This is [italic]important[/italic].")

# Console for advanced features
console = Console()
console.print("Hello", "World!", style="bold blue")

# Rich text objects
text = Text("Hello World!")
text.stylize("bold magenta", 0, 6)
console.print(text)

# Simple table
from rich.table import Table
table = Table()
table.add_column("Name")
table.add_column("Score")
table.add_row("Alice", "95")
table.add_row("Bob", "87")
console.print(table)
```

## Architecture

Rich is built around several key components:

- **Console**: Central output manager handling terminal detection, rendering, and export
- **Text Objects**: Styled text with spans for precise formatting control
- **Renderables**: Protocol for objects that can be rendered to the terminal
- **Styles**: Comprehensive styling system with color, typography, and effects
- **Layout System**: Advanced positioning and sizing for complex UIs
- **Live Display**: Real-time updating content for progress bars and dynamic interfaces

## Capabilities

### Console Output and Styling

Core console functionality for printing styled text, handling terminal capabilities, and managing output formatting.

```python { .api }
class Console:
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
    ) -> None: ...

def print(
    *objects: Any,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
) -> None: ...

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
) -> None: ...
```

[Console and Output](./console.md)

### Rich Text and Styling

Advanced text objects with precise styling control, markup support, and comprehensive formatting options.

```python { .api }
class Text:
    def __init__(
        self,
        text: str = "",
        style: StyleType = "",
        *,
        justify: Optional[JustifyMethod] = None,
        overflow: OverflowMethod = "fold",
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: Optional[int] = 8,
        spans: Optional[List[Span]] = None,
    ): ...
    
    def stylize(
        self,
        style: StyleType,
        start: int = 0,
        end: Optional[int] = None,
    ) -> None: ...
    
    @classmethod
    def from_markup(
        cls,
        text: str,
        *,
        style: StyleType = "",
        emoji: bool = True,
        emoji_variant: Optional[EmojiVariant] = None,
    ) -> "Text": ...

class Style:
    def __init__(
        self,
        *,
        color: Optional[ColorType] = None,
        bgcolor: Optional[ColorType] = None,
        bold: Optional[bool] = None,
        dim: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        blink: Optional[bool] = None,
        blink2: Optional[bool] = None,
        reverse: Optional[bool] = None,
        conceal: Optional[bool] = None,
        strike: Optional[bool] = None,
        underline2: Optional[bool] = None,
        frame: Optional[bool] = None,
        encircle: Optional[bool] = None,
        overline: Optional[bool] = None,
        link: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ): ...
```

[Text and Styling](./text-styling.md)

### Tables and Data Display

Comprehensive table system with flexible columns, styling, borders, and automatic sizing.

```python { .api }
class Table:
    def __init__(
        self,
        *columns: Union[Column, str],
        title: Optional[TextType] = None,
        caption: Optional[TextType] = None,
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        box: Optional[Box] = box.HEAVY_HEAD,
        safe_box: Optional[bool] = None,
        padding: PaddingDimensions = (0, 1),
        collapse_padding: bool = False,
        pad_edge: bool = True,
        expand: bool = False,
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        leading: int = 0,
        style: StyleType = "",
        row_styles: Optional[Iterable[StyleType]] = None,
        header_style: Optional[StyleType] = None,
        footer_style: Optional[StyleType] = None,
        border_style: Optional[StyleType] = None,
        title_style: Optional[StyleType] = None,
        caption_style: Optional[StyleType] = None,
        title_justify: JustifyMethod = "center",
        caption_justify: JustifyMethod = "center",
        highlight: bool = False,
    ): ...
    
    def add_column(
        self,
        header: RenderableType = "",
        *,
        footer: RenderableType = "",
        header_style: Optional[StyleType] = None,
        footer_style: Optional[StyleType] = None,
        style: Optional[StyleType] = None,
        justify: JustifyMethod = "left",
        vertical: VerticalAlignMethod = "top",
        overflow: OverflowMethod = "ellipsis",
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        ratio: Optional[int] = None,
        no_wrap: bool = False,
    ) -> None: ...
    
    def add_row(
        self,
        *renderables: Optional[RenderableType],
        style: Optional[StyleType] = None,
        end_section: bool = False,
    ) -> None: ...
```

[Tables](./tables.md)

### Progress Tracking

Advanced progress bar system with customizable columns, multiple tasks, and real-time updates.

```python { .api }
class Progress:
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
    ) -> TaskID: ...
    
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
    ) -> None: ...
    
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
    ) -> Iterable[ProgressType]: ...
```

[Progress Tracking](./progress.md)

### Syntax Highlighting

Code syntax highlighting with theme support and extensive language coverage via Pygments.

```python { .api }
class Syntax:
    def __init__(
        self,
        code: str,
        lexer: Optional[Union[Lexer, str]] = None,
        *,
        theme: Union[str, SyntaxTheme] = "monokai",
        dedent: bool = False,
        line_numbers: bool = False,
        start_line: int = 1,
        line_range: Optional[Tuple[int, int]] = None,
        highlight_lines: Optional[Set[int]] = None,
        code_width: Optional[int] = None,
        tab_size: int = 4,
        word_wrap: bool = False,
        background_color: Optional[str] = None,
        indent_guides: bool = False,
        padding: PaddingDimensions = 0,
    ): ...
    
    @classmethod
    def from_path(
        cls,
        path: Union[str, PathLike[str]],
        encoding: str = "utf-8",
        lexer: Optional[Union[Lexer, str]] = None,
        theme: Union[str, SyntaxTheme] = "monokai",
        dedent: bool = False,
        line_numbers: bool = False,
        line_range: Optional[Tuple[int, int]] = None,
        start_line: int = 1,
        highlight_lines: Optional[Set[int]] = None,
        code_width: Optional[int] = None,
        tab_size: int = 4,
        word_wrap: bool = False,
        background_color: Optional[str] = None,
        indent_guides: bool = False,
        padding: PaddingDimensions = 0,
    ) -> "Syntax": ...
```

[Syntax Highlighting](./syntax.md)

### Interactive Components

Live updating displays, user input prompts, and real-time interface components.

```python { .api }
class Live:
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

class Prompt:
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
    ) -> Any: ...
```

[Interactive Components](./interactive.md)

### Layout and Positioning

Advanced layout system for complex terminal UIs with flexible positioning and sizing.

```python { .api }
class Layout:
    def __init__(
        self,
        renderable: Optional[RenderableType] = None,
        *,
        name: str = "root",
        size: Optional[int] = None,
        minimum_size: int = 1,
        ratio: int = 1,
        visible: bool = True,
    ): ...
    
    def split(
        self,
        *layouts: Union["Layout", RenderableType],
        splitter: Splitter = "column",
    ) -> None: ...
    
    def split_column(self, *layouts: Union["Layout", RenderableType]) -> None: ...
    def split_row(self, *layouts: Union["Layout", RenderableType]) -> None: ...
```

[Layout System](./layout.md)

### Markdown Rendering

CommonMark-compliant markdown rendering with syntax highlighting and Rich formatting.

```python { .api }
class Markdown:
    def __init__(
        self,
        markup: str,
        *,
        code_theme: Union[str, SyntaxTheme] = "monokai",
        justify: Optional[JustifyMethod] = None,
        style: StyleType = "none",
        hyperlinks: bool = True,
        inline_code_lexer: Optional[str] = None,
        inline_code_theme: Optional[Union[str, SyntaxTheme]] = None,
    ): ...
```

[Markdown](./markdown.md)

### Panel and Container Components

Panels, rules, columns, and other container components for organizing content.

```python { .api }
class Panel:
    def __init__(
        self,
        renderable: RenderableType,
        box: Box = box.ROUNDED,
        *,
        safe_box: Optional[bool] = None,
        expand: bool = True,
        style: StyleType = "none",
        border_style: StyleType = "none",
        width: Optional[int] = None,
        height: Optional[int] = None,
        padding: PaddingDimensions = (0, 1),
        highlight: bool = False,
        title: Optional[TextType] = None,
        title_align: AlignMethod = "center",
        subtitle: Optional[TextType] = None,
        subtitle_align: AlignMethod = "center",
    ): ...

class Rule:
    def __init__(
        self,
        title: TextType = "",
        *,
        characters: str = "─",
        style: StyleType = "rule.line",
        end: str = "\n",
        align: AlignMethod = "center",
    ): ...
```

[Panels and Containers](./containers.md)

### Utilities and Helpers

Color handling, measurement, error types, and other utility functions.

```python { .api }
class Color:
    @classmethod
    def parse(cls, color: ColorType) -> "Color": ...
    
    def blend(self, destination: "Color", factor: float) -> "Color": ...

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
) -> None: ...
```

[Utilities](./utilities.md)

## Types

```python { .api }
from typing import Union, Optional, IO, Any, Callable, List, Dict, Tuple, Iterable

# Core types
TextType = Union[str, Text]
StyleType = Union[str, Style]
RenderableType = Union[ConsoleRenderable, RichRenderable, str]
ColorType = Union[int, str, Tuple[int, int, int], Color]

# Method types  
JustifyMethod = Literal["default", "left", "center", "right", "full"]
OverflowMethod = Literal["fold", "crop", "ellipsis", "ignore"]
AlignMethod = Literal["left", "center", "right"]
VerticalAlignMethod = Literal["top", "middle", "bottom"]

# Progress types
TaskID = NewType("TaskID", int)
GetTimeCallable = Callable[[], float]

# Console types
HighlighterType = Callable[[Union[str, Text]], Text]
FormatTimeCallable = Callable[[datetime], Text]

# Padding type
PaddingDimensions = Union[
    int,
    Tuple[int],
    Tuple[int, int],
    Tuple[int, int, int],
    Tuple[int, int, int, int],
]
```