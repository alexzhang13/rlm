# Sessions

Session objects provide a way to persist certain parameters across requests, enabling connection pooling, cookie persistence, and default configuration. Sessions are essential for maintaining state across multiple requests and improving performance through connection reuse.

## Capabilities

### Session Class

The Session class provides persistent configuration and connection pooling across multiple requests.

```python { .api }
class Session:
    """
    Session object for persisting settings across requests.
    
    Attributes:
    - headers: Default headers for all requests
    - cookies: Cookie jar for persistent cookies
    - auth: Default authentication
    - proxies: Default proxy configuration
    - hooks: Event hooks
    - params: Default URL parameters
    - verify: Default SSL verification setting
    - cert: Default client certificate
    - max_redirects: Maximum number of redirects to follow
    - trust_env: Whether to trust environment variables for configuration
    - stream: Default streaming setting
    - adapters: OrderedDict of mounted transport adapters
    """

    def __init__(self):
        """Initialize a new Session."""

    def __enter__(self):
        """Context manager entry."""
        
    def __exit__(self, *args):
        """Context manager exit."""

    def prepare_request(self, request: Request) -> PreparedRequest:
        """
        Prepare a Request object for sending.
        
        Parameters:
        - request: Request object to prepare
        
        Returns:
        PreparedRequest object ready to send
        """

    def request(self, method: str, url: str, **kwargs) -> Response:
        """
        Send a request using the session configuration.
        
        Parameters:
        - method: HTTP method
        - url: URL for the request
        - **kwargs: additional request parameters
        
        Returns:
        Response object
        """

    def get(self, url: str, **kwargs) -> Response:
        """Send a GET request using session configuration."""

    def options(self, url: str, **kwargs) -> Response:
        """Send an OPTIONS request using session configuration."""

    def head(self, url: str, **kwargs) -> Response:
        """Send a HEAD request using session configuration."""

    def post(self, url: str, data=None, json=None, **kwargs) -> Response:
        """Send a POST request using session configuration."""

    def put(self, url: str, data=None, **kwargs) -> Response:
        """Send a PUT request using session configuration."""

    def patch(self, url: str, data=None, **kwargs) -> Response:
        """Send a PATCH request using session configuration."""

    def delete(self, url: str, **kwargs) -> Response:
        """Send a DELETE request using session configuration."""

    def send(self, request: PreparedRequest, **kwargs) -> Response:
        """
        Send a prepared request.
        
        Parameters:
        - request: PreparedRequest object
        - **kwargs: additional sending parameters like timeout, verify, etc.
        
        Returns:
        Response object
        """

    def merge_environment_settings(self, url: str, proxies: dict, stream: bool, 
                                 verify: Union[bool, str], cert: Union[str, tuple]):
        """
        Merge environment settings with session settings.
        
        Parameters:
        - url: Request URL
        - proxies: Proxy configuration
        - stream: Stream setting
        - verify: SSL verification setting
        - cert: Client certificate setting
        
        Returns:
        Dict of merged settings
        """

    def get_adapter(self, url: str):
        """
        Get the appropriate adapter for the given URL.
        
        Parameters:
        - url: URL to get adapter for
        
        Returns:
        Adapter instance
        """

    def close(self):
        """Close the session and clean up resources."""

    def mount(self, prefix: str, adapter):
        """
        Register an adapter for a URL prefix.
        
        Parameters:
        - prefix: URL prefix (e.g., 'https://')
        - adapter: Adapter instance to mount
        """
```

### Session Factory Function

Convenience function to create a new session.

```python { .api }
def session() -> Session:
    """
    Create and return a new Session object.
    
    Returns:
    New Session instance
    """
```

## Usage Examples

### Basic Session Usage

```python
import requests

# Create a session
s = requests.Session()

# Set default headers and authentication
s.headers.update({'User-Agent': 'MyApp/1.0'})
s.auth = ('username', 'password')

# Make requests using the session
response1 = s.get('https://api.example.com/data')
response2 = s.post('https://api.example.com/update', json={'key': 'value'})

# Cookies are automatically persisted
response3 = s.get('https://api.example.com/profile')  # Cookies from previous requests are sent

# Close the session
s.close()
```

### Session as Context Manager

```python
import requests

# Use session as a context manager for automatic cleanup
with requests.Session() as s:
    s.headers.update({'Authorization': 'Bearer token123'})
    
    response = s.get('https://api.example.com/protected')
    data = response.json()
    
    # Process data...
    
# Session is automatically closed when exiting the context
```

### Persistent Configuration

```python
import requests

s = requests.Session()

# Set persistent configuration
s.headers.update({
    'User-Agent': 'MyApp/2.0',
    'Accept': 'application/json'
})
s.auth = ('api_user', 'api_pass')
s.proxies = {'http': 'http://proxy.example.com:8080'}
s.verify = '/path/to/ca-bundle.crt'

# All requests will use these settings by default
response1 = s.get('https://api.example.com/users')
response2 = s.post('https://api.example.com/data', json={'name': 'John'})

# Override settings for specific requests
response3 = s.get('https://other-api.com/data', auth=None, verify=False)
```

### Connection Pooling Benefits

```python
import requests

# Without session - new connection for each request
for i in range(10):
    requests.get('https://api.example.com/data/' + str(i))  # 10 separate connections

# With session - connection pooling
with requests.Session() as s:
    for i in range(10):
        s.get('https://api.example.com/data/' + str(i))  # Reuses connections
```

## Session Attributes

Sessions have several configurable attributes:

- **headers**: `CaseInsensitiveDict` - Default headers for all requests
- **cookies**: `RequestsCookieJar` - Persistent cookie storage
- **auth**: `AuthType` - Default authentication handler
- **proxies**: `Dict[str, str]` - Default proxy configuration
- **hooks**: `Dict[str, List[Callable]]` - Event hooks for request/response processing
- **params**: `Dict[str, str]` - Default URL parameters
- **verify**: `Union[bool, str]` - Default SSL certificate verification
- **cert**: `Union[str, Tuple[str, str]]` - Default client certificate
- **max_redirects**: `int` - Maximum redirects to follow (default: 30)
- **trust_env**: `bool` - Trust environment variables for proxy config
- **stream**: `bool` - Default streaming behavior

## Session Methods vs Module Functions

Session methods provide the same interface as module-level functions but with persistent configuration:

| Module Function | Session Method | Benefit |
|----------------|----------------|---------|
| `requests.get()` | `session.get()` | Persistent headers, cookies, auth |
| `requests.post()` | `session.post()` | Connection pooling |
| `requests.put()` | `session.put()` | Proxy configuration |
| `requests.delete()` | `session.delete()` | SSL settings |

Session methods inherit all session configuration but can be overridden with method-specific parameters.