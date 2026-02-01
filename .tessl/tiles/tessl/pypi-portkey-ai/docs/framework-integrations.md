# Framework Integrations

Pre-built integrations with popular AI frameworks including LangChain and LlamaIndex callback handlers.

## Capabilities

### LangChain Integration

```python { .api }
from portkey_ai.langchain import PortkeyLangchainCallbackHandler

class PortkeyLangchainCallbackHandler:
    """Callback handler for LangChain integration with Portkey observability"""
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ): ...
```

### LlamaIndex Integration

```python { .api }
from portkey_ai.llamaindex import PortkeyLlamaCallbackHandler

class PortkeyLlamaCallbackHandler:
    """Callback handler for LlamaIndex integration with Portkey observability"""
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ): ...  
```

## Usage Examples

```python
# LangChain integration
from langchain.llms import OpenAI
from portkey_ai.langchain import PortkeyLangchainCallbackHandler

handler = PortkeyLangchainCallbackHandler(
    api_key="PORTKEY_API_KEY"
)

llm = OpenAI(callbacks=[handler])
response = llm("What is AI?")

# LlamaIndex integration
from llama_index.core import SimpleDirectoryReader
from portkey_ai.llamaindex import PortkeyLlamaCallbackHandler

handler = PortkeyLlamaCallbackHandler(
    api_key="PORTKEY_API_KEY"
)

# Use with LlamaIndex operations
```