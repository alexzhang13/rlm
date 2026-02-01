# Syntax Highlighting

Code syntax highlighting with theme support and extensive language coverage via Pygments. Rich provides comprehensive syntax highlighting capabilities for displaying source code with proper formatting and color schemes.

## Capabilities

### Syntax Class

Main syntax highlighting component with theme and formatting options.

```python { .api }
class Syntax:
    """
    Syntax highlighted code display.
    
    Args:
        code: Source code to highlight
        lexer: Pygments lexer name or instance
        theme: Color theme name or SyntaxTheme instance
        dedent: Remove common leading whitespace
        line_numbers: Show line numbers
        start_line: Starting line number
        line_range: Range of lines to highlight (start, end)
        highlight_lines: Set of line numbers to highlight
        code_width: Fixed width for code or None for auto
        tab_size: Size of tab characters in spaces
        word_wrap: Enable word wrapping
        background_color: Override background color
        indent_guides: Show indentation guides
        padding: Padding around code block
    """
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
    ) -> "Syntax":
        """
        Create Syntax from file path.
        
        Args:
            path: Path to source code file
            encoding: File encoding
            lexer: Lexer name or None to auto-detect
            theme: Syntax theme
            dedent: Remove common indentation
            line_numbers: Show line numbers
            line_range: Range of lines to show
            start_line: Starting line number
            highlight_lines: Lines to highlight
            code_width: Fixed code width
            tab_size: Tab size in spaces
            word_wrap: Enable word wrapping
            background_color: Background color override
            indent_guides: Show indentation guides
            padding: Code block padding
            
        Returns:
            New Syntax instance with file contents
        """
    
    @classmethod
    def guess_lexer(cls, path: Union[str, PathLike[str]], code: str) -> str:
        """
        Guess lexer from file path and content.
        
        Args:
            path: File path for extension hints
            code: Source code content
            
        Returns:
            Lexer name for the code
        """
    
    def highlight(self, code: str) -> Text:
        """
        Apply syntax highlighting to code.
        
        Args:
            code: Source code to highlight
            
        Returns:
            Highlighted text object
        """
    
    # Properties
    @property
    def lexer(self) -> Optional[Lexer]:
        """Get the Pygments lexer."""
    
    @property
    def theme(self) -> SyntaxTheme:
        """Get the syntax theme."""
```

### Syntax Themes

Theme system for syntax highlighting colors.

```python { .api }
class SyntaxTheme(ABC):
    """Abstract base for syntax highlighting themes."""
    
    @abstractmethod
    def get_style_for_token(self, token_type: TokenType) -> Style:
        """
        Get style for a token type.
        
        Args:
            token_type: Pygments token type
            
        Returns:
            Rich Style for the token
        """
    
    @abstractmethod
    def get_background_style(self) -> Style:
        """
        Get background style for code blocks.
        
        Returns:
            Rich Style for background
        """

class PygmentsSyntaxTheme(SyntaxTheme):
    """Syntax theme based on Pygments themes."""
    
    def __init__(
        self, 
        theme: Union[str, Type[PygmentsStyle]]
    ): ...
    
    @classmethod
    def get_theme_names(cls) -> List[str]:
        """
        Get list of available Pygments theme names.
        
        Returns:
            List of theme names
        """

class ANSISyntaxTheme(SyntaxTheme):
    """Syntax theme using ANSI color codes."""
    
    def __init__(self, style_map: Dict[TokenType, Style]): ...

# Default themes
DEFAULT_THEME: str  # Default theme name
RICH_SYNTAX_THEMES: Dict[str, SyntaxTheme]  # Available themes
```

**Usage Examples:**

```python
from rich.console import Console
from rich.syntax import Syntax
import tempfile
import os

console = Console()

# Basic syntax highlighting
python_code = '''
def fibonacci(n):
    """Generate Fibonacci sequence up to n."""
    a, b = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a + b
    print()

fibonacci(100)
'''

syntax = Syntax(python_code, "python")
console.print(syntax)

# Syntax with line numbers
syntax = Syntax(
    python_code, 
    "python", 
    line_numbers=True,
    start_line=1
)
console.print(syntax)

# Highlight specific lines
syntax = Syntax(
    python_code,
    "python",
    line_numbers=True,
    highlight_lines={2, 4, 5}  # Highlight lines 2, 4, and 5
)
console.print(syntax)

# Different themes
themes = ["monokai", "github-dark", "one-dark", "solarized-light"]
for theme in themes:
    console.print(f"\n[bold]Theme: {theme}[/bold]")
    syntax = Syntax(python_code, "python", theme=theme, line_numbers=True)
    console.print(syntax)

# Load from file
# Create temporary file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(python_code)
    temp_path = f.name

try:
    # Load and highlight from file
    syntax = Syntax.from_path(
        temp_path,
        line_numbers=True,
        theme="monokai"
    )
    console.print(syntax)
finally:
    os.unlink(temp_path)

# JavaScript example
js_code = '''
function quickSort(arr) {
    if (arr.length <= 1) {
        return arr;
    }
    
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    
    return [...quickSort(left), ...middle, ...quickSort(right)];
}

const numbers = [64, 34, 25, 12, 22, 11, 90];
console.log(quickSort(numbers));
'''

syntax = Syntax(js_code, "javascript", theme="github-dark", line_numbers=True)
console.print(syntax)

# SQL example with custom settings
sql_code = '''
SELECT 
    customers.name,
    orders.order_date,
    products.product_name,
    order_items.quantity * products.price AS total_price
FROM customers
JOIN orders ON customers.customer_id = orders.customer_id
JOIN order_items ON orders.order_id = order_items.order_id
JOIN products ON order_items.product_id = products.product_id
WHERE orders.order_date >= '2024-01-01'
ORDER BY orders.order_date DESC, total_price DESC;
'''

syntax = Syntax(
    sql_code,
    "sql",
    theme="one-dark",
    line_numbers=True,
    word_wrap=True,
    indent_guides=True
)
console.print(syntax)

# Show line range
long_code = '''
import os
import sys
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional

class DataProcessor:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.session = requests.Session()
    
    def load_config(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return json.load(f)
    
    def process_data(self, data: List[Dict]) -> List[Dict]:
        results = []
        for item in data:
            processed = self.transform_item(item)
            if self.validate_item(processed):
                results.append(processed)
        return results
    
    def transform_item(self, item: Dict) -> Dict:
        # Transform logic here
        return {
            'id': item.get('id'),
            'timestamp': datetime.now().isoformat(),
            'value': item.get('value', 0) * 2
        }
    
    def validate_item(self, item: Dict) -> bool:
        return all(key in item for key in ['id', 'timestamp', 'value'])
'''

# Show only lines 10-20
syntax = Syntax(
    long_code,
    "python",
    line_numbers=True,
    line_range=(10, 20),
    start_line=10,
    theme="monokai"
)
console.print(syntax)

# Code with custom background
syntax = Syntax(
    python_code,
    "python",
    theme="github-dark",
    background_color="black",
    padding=1
)
console.print(syntax)

# Dedent code (remove common indentation)
indented_code = '''
    def helper_function():
        print("This is indented")
        return True
    
    def another_function():
        if helper_function():
            print("Success!")
'''

syntax = Syntax(
    indented_code,
    "python",
    dedent=True,
    line_numbers=True
)
console.print(syntax)

# Auto-detect lexer from filename
def highlight_file_content(filename: str, content: str):
    """Highlight code with auto-detected lexer."""
    lexer = Syntax.guess_lexer(filename, content)
    syntax = Syntax(content, lexer, line_numbers=True)
    console.print(f"[bold]File: {filename} (Lexer: {lexer})[/bold]")
    console.print(syntax)

# Examples of auto-detection
highlight_file_content("script.py", "print('Hello, World!')")
highlight_file_content("style.css", "body { color: red; }")
highlight_file_content("config.json", '{"name": "example", "value": 42}')

# Syntax in panels
from rich.panel import Panel

code_panel = Panel(
    Syntax(python_code, "python", theme="monokai"),
    title="Python Code",
    border_style="blue"
)
console.print(code_panel)

# Multiple code blocks in columns
from rich.columns import Columns

python_syntax = Syntax("print('Python')", "python", theme="github-dark")
js_syntax = Syntax("console.log('JavaScript');", "javascript", theme="github-dark")

columns = Columns([
    Panel(python_syntax, title="Python"),
    Panel(js_syntax, title="JavaScript")
])
console.print(columns)
```