# Text and Styling

Advanced text objects with precise styling control, markup support, and comprehensive formatting options. Rich provides powerful text handling with styled spans, color support, and flexible rendering capabilities.

## Capabilities

### Text Class

Rich text objects with styling spans and advanced formatting capabilities.

```python { .api }
class Text:
    """
    Styled text with Rich formatting capabilities.
    
    Args:
        text: Plain text content
        style: Default style for the text
        justify: Text justification method
        overflow: Overflow handling method
        no_wrap: Disable text wrapping
        end: String to append at end
        tab_size: Size of tab characters
        spans: List of styled spans
    """
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
    ) -> None:
        """
        Apply style to a range of text.
        
        Args:
            style: Style to apply
            start: Start character index
            end: End character index or None for end of text
        """
    
    def stylize_range(
        self,
        style: StyleType,
        start: int = 0,
        end: Optional[int] = None,
    ) -> None:
        """
        Apply style to a range of text (alias for stylize).
        
        Args:
            style: Style to apply
            start: Start character index
            end: End character index or None for end of text
        """
    
    def stylize_before(
        self,
        style: StyleType,
        start: int = 0,
        end: Optional[int] = None,
    ) -> "Text":
        """
        Apply style before existing styles in a range.
        
        Args:
            style: Style to apply
            start: Start character index  
            end: End character index or None for end of text
            
        Returns:
            New Text instance with applied style
        """
    
    def stylize_after(
        self,
        style: StyleType,
        start: int = 0,
        end: Optional[int] = None,
    ) -> "Text":
        """
        Apply style after existing styles in a range.
        
        Args:
            style: Style to apply
            start: Start character index
            end: End character index or None for end of text
            
        Returns:
            New Text instance with applied style
        """
    
    def highlight_words(
        self,
        words: Iterable[str],
        style: StyleType,
        *,
        case_sensitive: bool = True,
    ) -> int:
        """
        Highlight specific words in the text.
        
        Args:
            words: Words to highlight
            style: Style to apply to highlighted words
            case_sensitive: Enable case-sensitive matching
            
        Returns:
            Number of words highlighted
        """
    
    def highlight_regex(
        self,
        re_highlight: Union[str, Pattern[str]],
        style: Optional[StyleType] = None,
        *,
        style_prefix: str = "",
    ) -> int:
        """
        Highlight text matching a regular expression.
        
        Args:
            re_highlight: Regular expression pattern
            style: Style to apply or None to use groups
            style_prefix: Prefix for group-based style names
            
        Returns:
            Number of matches highlighted
        """
    
    def append(
        self,
        text: Union[str, "Text"],
        style: Optional[StyleType] = None,
    ) -> "Text":
        """
        Append text with optional styling.
        
        Args:
            text: Text to append
            style: Style to apply to appended text
            
        Returns:
            Self for method chaining
        """
    
    def copy(self) -> "Text":
        """
        Create a copy of this text object.
        
        Returns:
            New Text instance with same content and styles
        """
    
    def copy_styles(self, text: "Text") -> None:
        """
        Copy styles from another text object.
        
        Args:
            text: Text object to copy styles from
        """
    
    def split(
        self,
        separator: str = "\n",
        *,
        include_separator: bool = False,
        allow_blank: bool = True,
    ) -> List["Text"]:
        """
        Split text by separator.
        
        Args:
            separator: String to split on
            include_separator: Include separator in results
            allow_blank: Allow blank strings in results
            
        Returns:
            List of Text objects
        """
    
    def divide(
        self, offsets: Iterable[int]
    ) -> List["Text"]:
        """
        Divide text at specific character offsets.
        
        Args:
            offsets: Character positions to split at
            
        Returns:
            List of Text objects
        """
    
    def right_crop(self, amount: int = 1) -> "Text":
        """
        Remove characters from the right.
        
        Args:
            amount: Number of characters to remove
            
        Returns:
            New Text with characters removed
        """
    
    def truncate(
        self,
        max_width: int,
        *,
        overflow: OverflowMethod = "fold",
        pad: bool = False,
    ) -> None:
        """
        Truncate text to maximum width.
        
        Args:
            max_width: Maximum width in characters
            overflow: Overflow handling method
            pad: Pad to exact width with spaces
        """
    
    def pad_left(self, count: int, character: str = " ") -> "Text":
        """
        Add padding to the left.
        
        Args:
            count: Number of characters to add
            character: Character to use for padding
            
        Returns:
            New Text with padding
        """
    
    def pad_right(self, count: int, character: str = " ") -> "Text":
        """
        Add padding to the right.
        
        Args:
            count: Number of characters to add
            character: Character to use for padding
            
        Returns:
            New Text with padding
        """
    
    def align(self, align: AlignMethod, width: int, character: str = " ") -> "Text":
        """
        Align text within a given width.
        
        Args:
            align: Alignment method
            width: Total width
            character: Character to use for padding
            
        Returns:
            New aligned Text
        """
    
    def strip(self, characters: Optional[str] = None) -> "Text":
        """
        Strip characters from both ends.
        
        Args:
            characters: Characters to strip or None for whitespace
            
        Returns:
            New Text with characters stripped
        """
    
    def rstrip(self, characters: Optional[str] = None) -> "Text":
        """
        Strip characters from the right end.
        
        Args:
            characters: Characters to strip or None for whitespace
            
        Returns:
            New Text with characters stripped
        """
    
    def lstrip(self, characters: Optional[str] = None) -> "Text":
        """
        Strip characters from the left end.
        
        Args:
            characters: Characters to strip or None for whitespace
            
        Returns:
            New Text with characters stripped
        """
    
    def expand_tabs(self, tab_size: Optional[int] = None) -> "Text":
        """
        Expand tab characters to spaces.
        
        Args:
            tab_size: Size of tabs or None to use default
            
        Returns:
            New Text with tabs expanded
        """
    
    def replace(
        self,
        old: str,
        new: Union[str, "Text"],
        count: int = -1,
    ) -> "Text":
        """
        Replace occurrences of a substring.
        
        Args:
            old: Substring to replace
            new: Replacement text
            count: Maximum replacements or -1 for all
            
        Returns:
            New Text with replacements
        """
    
    @classmethod
    def from_markup(
        cls,
        text: str,
        *,
        style: StyleType = "",
        emoji: bool = True,
        emoji_variant: Optional[EmojiVariant] = None,
    ) -> "Text":
        """
        Create Text from Rich markup.
        
        Args:
            text: Text with Rich markup tags
            style: Base style to apply
            emoji: Enable emoji rendering
            emoji_variant: Emoji variant preference
            
        Returns:
            New Text object with markup applied
        """
    
    @classmethod
    def from_ansi(
        cls,
        text: str,
        *,
        style: StyleType = "",
        no_color: Optional[bool] = None,
    ) -> "Text":
        """
        Create Text from ANSI escaped string.
        
        Args:
            text: Text with ANSI escape codes
            style: Base style to apply
            no_color: Disable color processing
            
        Returns:
            New Text object with ANSI styles converted
        """
    
    @classmethod
    def styled(
        cls,
        text: str,
        style: StyleType,
    ) -> "Text":
        """
        Create styled Text.
        
        Args:
            text: Plain text
            style: Style to apply
            
        Returns:
            New styled Text object
        """
    
    @classmethod
    def assemble(
        cls,
        *parts: Union[str, "Text", Tuple[str, StyleType]],
        style: StyleType = "",
        justify: Optional[JustifyMethod] = None,
        overflow: OverflowMethod = "fold",
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: int = 8,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "Text":
        """
        Assemble Text from multiple parts.
        
        Args:
            *parts: Text parts as strings, Text objects, or (text, style) tuples
            style: Base style
            justify: Text justification
            overflow: Overflow handling
            no_wrap: Disable wrapping
            end: End string
            tab_size: Tab size
            meta: Metadata dictionary
            
        Returns:
            New assembled Text object
        """
    
    # Properties
    @property
    def plain(self) -> str:
        """Get plain text without styling."""
    
    @property
    def markup(self) -> str:
        """Get text as Rich markup."""
    
    @property
    def spans(self) -> List[Span]:
        """Get list of styled spans."""
    
    @property
    def style(self) -> Style:
        """Get base style."""
```

### Span Class

Represents a styled region within text.

```python { .api }
class Span(NamedTuple):
    """
    A styled span within text.
    
    Attributes:
        start: Start character index
        end: End character index
        style: Style for this span
    """
    start: int
    end: int
    style: Union[str, Style]
    
    def split(self, offset: int) -> Tuple["Span", Optional["Span"]]:
        """
        Split span at offset.
        
        Args:
            offset: Character offset to split at
            
        Returns:
            Tuple of (left_span, right_span or None)
        """
    
    def move(self, offset: int) -> "Span":
        """
        Move span by offset.
        
        Args:
            offset: Number of characters to move
            
        Returns:
            New span with adjusted position
        """
    
    def right_crop(self, offset: int) -> "Span":
        """
        Crop span at offset.
        
        Args:
            offset: Offset to crop at
            
        Returns:
            New cropped span
        """
```

### Style Class

Comprehensive styling system with support for colors, typography, and effects.

```python { .api }
class Style:
    """
    Immutable style definition for text formatting.
    
    Args:
        color: Text color
        bgcolor: Background color
        bold: Bold text
        dim: Dim text
        italic: Italic text
        underline: Underlined text
        blink: Blinking text
        blink2: Fast blinking text
        reverse: Reverse video
        conceal: Concealed text
        strike: Strikethrough text
        underline2: Double underline
        frame: Framed text
        encircle: Encircled text
        overline: Overlined text
        link: Hyperlink URL
        meta: Metadata dictionary
    """
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
    
    def copy(self) -> "Style":
        """
        Create a copy of this style.
        
        Returns:
            New Style with same properties
        """
    
    def update(self, **kwargs: Any) -> "Style":
        """
        Update style properties.
        
        Args:
            **kwargs: Style properties to update
            
        Returns:
            New Style with updated properties
        """
    
    def render(
        self,
        text: str = "",
        *,
        color_system: ColorSystem = ColorSystem.TRUECOLOR,
        legacy_windows: bool = False,
    ) -> str:
        """
        Render style as ANSI codes.
        
        Args:
            text: Text to wrap with codes
            color_system: Target color system
            legacy_windows: Enable legacy Windows compatibility
            
        Returns:
            Text with ANSI escape codes
        """
    
    def test(self, text: Optional[str] = None) -> "Text":
        """
        Create test text with this style applied.
        
        Args:
            text: Test text or None for default
            
        Returns:
            Styled Text object for testing
        """
    
    def without_color(self) -> "Style":
        """
        Create style without color information.
        
        Returns:
            New Style with colors removed
        """
    
    @classmethod
    def parse(cls, style: Union[str, "Style"]) -> "Style":
        """
        Parse style from string or return existing Style.
        
        Args:
            style: Style string or Style object
            
        Returns:
            Parsed Style object
        """
    
    @classmethod
    def combine(cls, styles: Iterable["Style"]) -> "Style":
        """
        Combine multiple styles.
        
        Args:
            styles: Iterable of styles to combine
            
        Returns:
            New combined Style
        """
    
    @classmethod
    def chain(cls, *styles: "Style") -> "Style":
        """
        Chain multiple styles together.
        
        Args:
            *styles: Styles to chain
            
        Returns:
            New chained Style
        """
    
    @classmethod
    def null(cls) -> "Style":
        """
        Create a null style with no formatting.
        
        Returns:
            Empty Style object
        """
    
    # Properties
    @property
    def color(self) -> Optional[Color]:
        """Text color."""
    
    @property 
    def bgcolor(self) -> Optional[Color]:
        """Background color."""
    
    @property
    def bold(self) -> Optional[bool]:
        """Bold flag."""
    
    @property
    def dim(self) -> Optional[bool]:
        """Dim flag."""
    
    @property
    def italic(self) -> Optional[bool]:
        """Italic flag."""
    
    @property
    def underline(self) -> Optional[bool]:
        """Underline flag."""
    
    @property
    def strike(self) -> Optional[bool]:
        """Strikethrough flag."""
    
    @property
    def link(self) -> Optional[str]:
        """Hyperlink URL."""
    
    @property
    def transparent_background(self) -> bool:
        """Check if background is transparent."""
```

**Usage Examples:**

```python
from rich.text import Text, Span
from rich.style import Style
from rich.console import Console

console = Console()

# Basic text creation
text = Text("Hello World!")
text.stylize("bold red", 0, 5)  # Style "Hello"
text.stylize("italic blue", 6, 12)  # Style "World!"
console.print(text)

# Text from markup
markup_text = Text.from_markup("[bold red]Error:[/bold red] Something went wrong")
console.print(markup_text)

# Text assembly
assembled = Text.assemble(
    "Status: ",
    ("OK", "bold green"),
    " - ",
    ("Ready", "italic blue")
)
console.print(assembled)

# Text with highlighting
code_text = Text("def hello_world():")
code_text.highlight_words(["def", "hello_world"], "bold blue")
console.print(code_text)

# Advanced styling
style = Style(
    color="red",
    bgcolor="yellow", 
    bold=True,
    italic=True,
    underline=True
)
styled_text = Text("Important Notice", style=style)
console.print(styled_text)

# Text manipulation
long_text = Text("This is a very long line of text that needs to be processed")
long_text.truncate(20, overflow="ellipsis")
console.print(long_text)

# Working with spans
text = Text("Hello World")
spans = [
    Span(0, 5, "bold red"),
    Span(6, 11, "italic blue")
]
for span in spans:
    text.stylize(span.style, span.start, span.end)
console.print(text)
```