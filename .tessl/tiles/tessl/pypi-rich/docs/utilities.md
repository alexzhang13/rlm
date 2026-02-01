# Utilities

Color handling, measurement, error types, and other utility functions. Rich provides various utility functions and classes for working with colors, measurements, and other common operations.

## Capabilities

### Color System

Comprehensive color handling and conversion.

```python { .api }
class Color:
    """Color representation with conversion capabilities."""
    
    @classmethod
    def parse(cls, color: ColorType) -> "Color":
        """Parse color from various formats."""
    
    def blend(self, destination: "Color", factor: float) -> "Color":
        """Blend with another color."""
    
    def get_truecolor(self) -> Tuple[int, int, int]:
        """Get RGB values."""

class ColorTriplet(NamedTuple):
    """RGB color triplet."""
    red: int
    green: int 
    blue: int

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
    """Inspect Python objects with rich formatting."""

class Measurement(NamedTuple):
    """Content measurement with min/max dimensions."""
    minimum: int
    maximum: int
    
    def with_maximum(self, maximum: int) -> "Measurement": ...
    def with_minimum(self, minimum: int) -> "Measurement": ...
    def clamp(self, min_width: int, max_width: int) -> "Measurement": ...
```

**Usage Examples:**

```python
from rich.color import Color
from rich import inspect
from rich.console import Console

console = Console()

# Color operations
red = Color.parse("red")
blue = Color.parse("#0000FF")
purple = red.blend(blue, 0.5)

# Object inspection
inspect([1, 2, 3, 4, 5])
inspect(console, methods=True)
```