# Panels and Containers

Panels, rules, columns, and other container components for organizing content. Rich provides various container components for structuring and organizing terminal output.

## Capabilities

### Panel Class

Decorative panels with borders and titles.

```python { .api }
class Panel:
    """
    Panel with border and optional title.
    
    Args:
        renderable: Content to display in panel
        box: Box style for borders
        safe_box: Use safe box characters
        expand: Expand to fit available width
        style: Panel style
        border_style: Border style
        width: Fixed width or None for auto
        height: Fixed height or None for auto
        padding: Internal padding
        highlight: Enable content highlighting
        title: Panel title
        title_align: Title alignment
        subtitle: Panel subtitle
        subtitle_align: Subtitle alignment
    """
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
    
    @classmethod
    def fit(
        cls,
        renderable: RenderableType,
        box: Box = box.ROUNDED,
        *,
        safe_box: Optional[bool] = None,
        style: StyleType = "none",
        border_style: StyleType = "none",
        padding: PaddingDimensions = (0, 1),
        title: Optional[TextType] = None,
        title_align: AlignMethod = "center",
    ) -> "Panel":
        """Create a panel that fits content exactly."""

class Rule:
    """Horizontal rule with optional title."""
    def __init__(
        self,
        title: TextType = "",
        *,
        characters: str = "─",
        style: StyleType = "rule.line",
        end: str = "\n",
        align: AlignMethod = "center",
    ): ...

class Columns:
    """Multi-column layout for renderables."""
    def __init__(
        self,
        renderables: Optional[Iterable[RenderableType]] = None,
        width: Optional[int] = None,
        padding: PaddingDimensions = (0, 1),
        expand: bool = False,
        equal: bool = False,
        column_first: bool = False,
        right_to_left: bool = False,
        align: AlignMethod = "left",
        title: Optional[TextType] = None,
    ): ...
```

**Usage Examples:**

```python
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.columns import Columns

console = Console()

# Basic panel
panel = Panel("Hello, World!", title="Greeting")
console.print(panel)

# Rule
console.print(Rule("Section 1"))
console.print("Content here")
console.print(Rule())

# Columns
columns = Columns([
    Panel("Column 1"),
    Panel("Column 2"),
    Panel("Column 3")
])
console.print(columns)
```