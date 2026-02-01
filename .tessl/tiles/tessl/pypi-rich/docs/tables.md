# Tables

Comprehensive table system with flexible columns, styling, borders, and automatic sizing. Rich tables support complex layouts, custom formatting, and responsive design with automatic width calculation.

## Capabilities

### Table Class

Advanced table rendering with comprehensive formatting and layout options.

```python { .api }
class Table:
    """
    Renderable table with automatic sizing and formatting.
    
    Args:
        *columns: Column definitions or header strings
        title: Title displayed above the table
        caption: Caption displayed below the table
        width: Fixed table width or None for automatic
        min_width: Minimum table width
        box: Box style for borders
        safe_box: Use safe box characters for compatibility
        padding: Cell padding (top, right, bottom, left)
        collapse_padding: Collapse padding between cells
        pad_edge: Add padding to table edges
        expand: Expand table to fill available width
        show_header: Display header row
        show_footer: Display footer row
        show_edge: Display outer borders
        show_lines: Display lines between rows
        leading: Number of blank lines between rows
        style: Default table style
        row_styles: Alternating row styles
        header_style: Header row style
        footer_style: Footer row style
        border_style: Border style
        title_style: Title style
        caption_style: Caption style
        title_justify: Title justification
        caption_justify: Caption justification
        highlight: Enable cell content highlighting
    """
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
    ) -> None:
        """
        Add a column to the table.
        
        Args:
            header: Column header content
            footer: Column footer content
            header_style: Style for header cell
            footer_style: Style for footer cell
            style: Default style for column cells
            justify: Text justification in column
            vertical: Vertical alignment in column
            overflow: Overflow handling method
            width: Fixed column width
            min_width: Minimum column width
            max_width: Maximum column width
            ratio: Column width ratio for flexible sizing
            no_wrap: Disable text wrapping in column
        """
    
    def add_row(
        self,
        *renderables: Optional[RenderableType],
        style: Optional[StyleType] = None,
        end_section: bool = False,
    ) -> None:
        """
        Add a row to the table.
        
        Args:
            *renderables: Cell contents for each column
            style: Style for the entire row
            end_section: Mark this row as end of a section
        """
    
    def add_section(self) -> None:
        """Add a section break (line) after the current row."""
    
    @classmethod
    def grid(
        cls,
        *,
        padding: PaddingDimensions = 0,
        collapse_padding: bool = True,
        pad_edge: bool = False,
        expand: bool = False,
    ) -> "Table":
        """
        Create a table configured as a grid (no borders).
        
        Args:
            padding: Cell padding
            collapse_padding: Collapse padding between cells
            pad_edge: Add padding to grid edges
            expand: Expand grid to fill available width
            
        Returns:
            New Table configured as grid
        """
    
    # Properties
    @property
    def columns(self) -> List[Column]:
        """Get list of table columns."""
    
    @property
    def rows(self) -> List[Row]:
        """Get list of table rows."""
    
    @property
    def row_count(self) -> int:
        """Get number of rows in table."""
```

### Column Class

Column definition with formatting and sizing options.

```python { .api }
@dataclass
class Column:
    """
    Table column definition.
    
    Attributes:
        header: Header content for the column
        footer: Footer content for the column
        header_style: Style for header cell
        footer_style: Style for footer cell
        style: Default style for column cells
        justify: Text justification method
        vertical: Vertical alignment method
        overflow: Overflow handling method
        width: Fixed column width
        min_width: Minimum column width
        max_width: Maximum column width
        ratio: Width ratio for flexible sizing
        no_wrap: Disable text wrapping
    """
    header: RenderableType = ""
    footer: RenderableType = ""
    header_style: StyleType = ""
    footer_style: StyleType = ""
    style: StyleType = ""
    justify: JustifyMethod = "left"
    vertical: VerticalAlignMethod = "top"
    overflow: OverflowMethod = "ellipsis"
    width: Optional[int] = None
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    ratio: Optional[int] = None
    no_wrap: bool = False
```

### Row Class

Table row data container.

```python { .api }
@dataclass
class Row:
    """
    Table row data.
    
    Attributes:
        style: Style for the entire row
        end_section: Whether this row ends a section
    """
    style: Optional[StyleType] = None
    end_section: bool = False
```

### Box Styles

Predefined box drawing styles for table borders.

```python { .api }
class Box:
    """Box drawing character set for table borders."""
    
    def __init__(
        self,
        box: str,
        *,
        ascii: bool = False,
    ): ...

# Predefined box styles
ASCII: Box  # ASCII characters only
SQUARE: Box  # Square corners
MINIMAL: Box  # Minimal borders
SIMPLE: Box  # Simple lines
SIMPLE_HEAD: Box  # Simple with header separator
SIMPLE_HEAVY: Box  # Simple with heavy lines
HORIZONTALS: Box  # Horizontal lines only
ROUNDED: Box  # Rounded corners
HEAVY: Box  # Heavy lines
HEAVY_EDGE: Box  # Heavy outer edge
HEAVY_HEAD: Box  # Heavy header separator
DOUBLE: Box  # Double lines
DOUBLE_EDGE: Box  # Double outer edge
```

**Usage Examples:**

```python
from rich.console import Console
from rich.table import Table, Column
from rich import box

console = Console()

# Basic table
table = Table()
table.add_column("Name")
table.add_column("Age")
table.add_column("City")

table.add_row("Alice", "25", "New York")
table.add_row("Bob", "30", "London")  
table.add_row("Charlie", "35", "Tokyo")

console.print(table)

# Styled table with title and caption
table = Table(
    title="Employee Directory",
    caption="Last updated: 2024-01-01",
    box=box.ROUNDED,
    title_style="bold blue",
    caption_style="italic dim"
)

table.add_column("ID", justify="center", style="cyan", no_wrap=True)
table.add_column("Name", style="magenta")
table.add_column("Department", justify="right", style="green")
table.add_column("Salary", justify="right", style="yellow")

table.add_row("001", "John Doe", "Engineering", "$75,000")
table.add_row("002", "Jane Smith", "Marketing", "$65,000")
table.add_row("003", "Bob Johnson", "Sales", "$55,000")

console.print(table)

# Table with column configuration
table = Table(show_header=True, header_style="bold red")

# Add columns with specific formatting
table.add_column(
    "Product", 
    header_style="bold blue",
    style="cyan",
    min_width=10,
    max_width=20
)
table.add_column(
    "Price", 
    justify="right",
    style="green",
    header_style="bold green"
)
table.add_column(
    "Status",
    justify="center", 
    style="yellow",
    vertical="middle"
)

table.add_row("Laptop", "$999.99", "In Stock")
table.add_row("Mouse", "$29.99", "Out of Stock")
table.add_row("Keyboard", "$79.99", "In Stock")

console.print(table)

# Grid layout (no borders)
grid = Table.grid(padding=1)
grid.add_column(style="red", justify="right")
grid.add_column(style="blue")
grid.add_column(style="green")

grid.add_row("Label 1:", "Value A", "Extra Info")
grid.add_row("Label 2:", "Value B", "More Info") 
grid.add_row("Label 3:", "Value C", "Additional")

console.print(grid)

# Table with sections
table = Table()
table.add_column("Category")
table.add_column("Item")
table.add_column("Count")

table.add_row("Fruits", "Apples", "10")
table.add_row("Fruits", "Oranges", "15")
table.add_section()  # Add section break

table.add_row("Vegetables", "Carrots", "8")
table.add_row("Vegetables", "Lettuce", "12")

console.print(table)

# Responsive table with ratios
table = Table(expand=True)
table.add_column("Description", ratio=3)  # 3/4 of available width
table.add_column("Value", ratio=1, justify="right")  # 1/4 of width

table.add_row("Very long description that will wrap", "100")
table.add_row("Short desc", "200")

console.print(table)

# Table with rich content
from rich.text import Text
from rich.panel import Panel

table = Table()
table.add_column("Rich Content")
table.add_column("Status")

# Add styled text
styled_text = Text("Important Item", style="bold red")
table.add_row(styled_text, "Active")

# Add panel as cell content
panel = Panel("Wrapped Content", style="blue")
table.add_row(panel, "Pending")

console.print(table)
```