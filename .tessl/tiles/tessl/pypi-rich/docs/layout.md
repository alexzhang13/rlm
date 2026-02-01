# Layout System

Advanced layout system for complex terminal UIs with flexible positioning and sizing. Rich provides powerful layout management for creating sophisticated terminal applications with responsive design.

## Capabilities

### Layout Class

Main layout management system with flexible splitting and positioning.

```python { .api }
class Layout:
    """
    Layout management for terminal UIs.
    
    Args:
        renderable: Initial content to display
        name: Layout identifier
        size: Fixed size or None for flexible
        minimum_size: Minimum size constraint
        ratio: Size ratio for flexible layouts
        visible: Layout visibility
    """
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
    ) -> None:
        """
        Split layout into multiple sections.
        
        Args:
            *layouts: Child layouts or renderables
            splitter: Split direction ("column" or "row")
        """
    
    def split_column(self, *layouts: Union["Layout", RenderableType]) -> None:
        """Split layout vertically."""
    
    def split_row(self, *layouts: Union["Layout", RenderableType]) -> None:
        """Split layout horizontally."""
    
    def add_split(self, *layouts: Union["Layout", RenderableType]) -> None:
        """Add layouts to existing split."""
    
    def unsplit(self) -> "Layout":
        """Remove split and return to single layout."""
    
    def update(self, renderable: RenderableType) -> None:
        """Update layout content."""
    
    def refresh_screen(self, console: Console, size: ConsoleDimensions) -> None:
        """Refresh layout display."""

class Splitter(ABC):
    """Abstract base for layout splitters."""
    
    @abstractmethod
    def divide(
        self, 
        children: Sequence[Layout], 
        size: int
    ) -> List[int]: ...

class RowSplitter(Splitter):
    """Horizontal layout splitter."""

class ColumnSplitter(Splitter):
    """Vertical layout splitter."""
```

**Usage Examples:**

```python
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel

console = Console()

# Basic layout
layout = Layout()
layout.split_column(
    Layout(Panel("Header", style="blue")),
    Layout(Panel("Content", style="green")),
    Layout(Panel("Footer", style="red"))
)
console.print(layout)

# Complex layout with ratios
layout = Layout()
layout.split_column(
    Layout(Panel("Header"), size=3),
    Layout(name="main"),
    Layout(Panel("Footer"), size=3)
)
layout["main"].split_row(
    Layout(Panel("Left"), name="left"),
    Layout(Panel("Right"), name="right")
)
console.print(layout)
```