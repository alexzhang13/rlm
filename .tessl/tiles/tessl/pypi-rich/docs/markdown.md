# Markdown

CommonMark-compliant markdown rendering with syntax highlighting and Rich formatting. Rich provides comprehensive markdown support for displaying formatted documents in the terminal.

## Capabilities

### Markdown Class

Main markdown rendering component with full CommonMark support.

```python { .api }
class Markdown:
    """
    Markdown document renderer.
    
    Args:
        markup: Markdown text to render
        code_theme: Theme for code blocks
        justify: Text justification
        style: Base style for markdown
        hyperlinks: Enable hyperlink rendering
        inline_code_lexer: Lexer for inline code
        inline_code_theme: Theme for inline code
    """
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

**Usage Examples:**

```python
from rich.console import Console
from rich.markdown import Markdown

console = Console()

markdown_text = """
# My Document

This is **bold** and *italic* text.

## Code Example

```python
def hello():
    print("Hello, World!")
```

- List item 1
- List item 2
- List item 3
"""

md = Markdown(markdown_text)
console.print(md)
```