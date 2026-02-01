# Transport Adapters

Transport adapters handle the actual HTTP communication, providing the interface between requests and underlying HTTP libraries. Adapters enable connection pooling, SSL/TLS handling, and protocol-specific optimizations.

## Capabilities

### BaseAdapter Class

Abstract base class that all transport adapters inherit from.

```python { .api }
class BaseAdapter:
    """
    The base adapter class for transports.
    
    All transport adapters should inherit from this class.
    """

    def __init__(self):
        """Initialize the adapter."""

    def send(self, request, stream=False, timeout=None, verify=True, 
             cert=None, proxies=None) -> 'Response':
        """
        Send a PreparedRequest and return a Response.
        
        Parameters:
        - request: PreparedRequest object to send
        - stream: Whether to stream the response content
        - timeout: Timeout value in seconds
        - verify: SSL verification setting
        - cert: Client certificate
        - proxies: Proxy configuration
        
        Returns:
        Response object
        
        Raises:
        NotImplementedError: Must be implemented by subclasses
        """

    def close(self):
        """
        Clean up adapter resources.
        
        Called when session is closed.
        """
```

### HTTPAdapter Class

Built-in HTTP/HTTPS adapter using urllib3 for connection pooling and transport.

```python { .api }
class HTTPAdapter(BaseAdapter):
    """
    Built-in HTTP adapter using urllib3.
    
    Provides connection pooling, SSL/TLS handling, and HTTP protocol support.
    """

    def __init__(self, pool_connections=10, pool_maxsize=10, max_retries=0, 
                 pool_block=False):
        """
        Initialize HTTPAdapter.
        
        Parameters:
        - pool_connections: Number of urllib3 connection pools to cache
        - pool_maxsize: Maximum connections per pool
        - max_retries: Maximum number of retries per request
        - pool_block: Whether to block when pool is full
        """

    def send(self, request, stream=False, timeout=None, verify=True, 
             cert=None, proxies=None) -> 'Response':
        """
        Send a request using urllib3.
        
        Parameters:
        - request: PreparedRequest to send
        - stream: Stream response content
        - timeout: Request timeout (connect, read) tuple or single value
        - verify: SSL certificate verification (bool or CA bundle path)
        - cert: Client certificate (path or (cert, key) tuple)
        - proxies: Proxy configuration dict
        
        Returns:
        Response object
        """

    def close(self):
        """Close all pooled connections."""

    # Connection management
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        """
        Initialize urllib3 PoolManager.
        
        Parameters:
        - connections: Number of connection pools
        - maxsize: Maximum connections per pool
        - block: Whether to block when pool is full
        - **pool_kwargs: Additional pool arguments
        """

    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        """
        Get connection pool with TLS context.
        
        Parameters:
        - request: Request object
        - verify: SSL verification setting
        - proxies: Proxy configuration
        - cert: Client certificate
        
        Returns:
        ConnectionPool instance
        """

    def get_connection(self, url, proxies=None):
        """
        DEPRECATED: Get connection for URL.
        
        Parameters:
        - url: URL to get connection for
        - proxies: Proxy configuration
        
        Returns:
        ConnectionPool instance
        """

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        """
        Get ProxyManager for proxy URL.
        
        Parameters:
        - proxy: Proxy URL
        - **proxy_kwargs: Additional proxy arguments
        
        Returns:
        ProxyManager instance
        """

    # Request/Response processing
    def build_response(self, req, resp) -> 'Response':
        """
        Build Response object from urllib3 response.
        
        Parameters:
        - req: PreparedRequest object
        - resp: urllib3 HTTPResponse object
        
        Returns:
        Response object
        """

    def request_url(self, request, proxies) -> str:
        """
        Get the URL to use for the request.
        
        Parameters:
        - request: PreparedRequest object
        - proxies: Proxy configuration
        
        Returns:
        URL string to use
        """

    def add_headers(self, request, **kwargs):
        """
        Add headers to the request.
        
        Parameters:
        - request: PreparedRequest object
        - **kwargs: Additional arguments
        """

    def proxy_headers(self, proxy) -> dict:
        """
        Get headers to add for proxy requests.
        
        Parameters:
        - proxy: Proxy URL
        
        Returns:
        Dict of headers
        """

    # SSL/TLS handling
    def cert_verify(self, conn, url, verify, cert):
        """
        Verify SSL certificates and configure client certs.
        
        Parameters:
        - conn: Connection object
        - url: Request URL
        - verify: SSL verification setting
        - cert: Client certificate
        """

    def build_connection_pool_key_attributes(self, request, verify, cert=None) -> tuple:
        """
        Build key attributes for connection pooling.
        
        Parameters:
        - request: PreparedRequest object
        - verify: SSL verification setting
        - cert: Client certificate
        
        Returns:
        Tuple of (pool_kwargs, connection_pool_kwargs)
        """
```

### Adapter Constants

```python { .api }
DEFAULT_POOLBLOCK: bool     # False
DEFAULT_POOLSIZE: int       # 10
DEFAULT_RETRIES: int        # 0
DEFAULT_POOL_TIMEOUT: None  # None
```

## Usage Examples

### Basic Adapter Usage

```python
import requests
from requests.adapters import HTTPAdapter

# Adapters are used automatically
response = requests.get('https://httpbin.org/get')
print(f"Status: {response.status_code}")

# Access session adapters
session = requests.Session()
print("Mounted adapters:")
for prefix, adapter in session.adapters.items():
    print(f"  {prefix}: {adapter}")
```

### Custom Adapter Configuration

```python
import requests
from requests.adapters import HTTPAdapter

# Create adapter with custom settings
adapter = HTTPAdapter(
    pool_connections=20,    # More connection pools
    pool_maxsize=50,       # More connections per pool
    max_retries=3,         # Retry failed requests
    pool_block=True        # Wait when pool is full
)

# Mount adapter to session
session = requests.Session()
session.mount('https://', adapter)
session.mount('http://', adapter)

# Requests will use the custom adapter
response = session.get('https://httpbin.org/get')
```

### Protocol-Specific Adapters

```python
import requests
from requests.adapters import HTTPAdapter

# Different adapters for different hosts
class APIAdapter(HTTPAdapter):
    """Custom adapter for API endpoints."""
    
    def __init__(self, api_key, **kwargs):
        self.api_key = api_key
        super().__init__(**kwargs)
    
    def add_headers(self, request, **kwargs):
        request.headers['Authorization'] = f'Bearer {self.api_key}'
        super().add_headers(request, **kwargs)

# Mount custom adapter
session = requests.Session()
api_adapter = APIAdapter(api_key='your-api-key', max_retries=3)
session.mount('https://api.example.com/', api_adapter)

# Regular adapter for other URLs
session.mount('https://', HTTPAdapter(max_retries=1))

# Different adapters used based on URL
api_response = session.get('https://api.example.com/data')      # Uses APIAdapter
web_response = session.get('https://other-site.com/page')      # Uses HTTPAdapter
```

### Connection Pool Management

```python
import requests
from requests.adapters import HTTPAdapter

# Configure connection pooling
adapter = HTTPAdapter(
    pool_connections=10,    # 10 connection pools
    pool_maxsize=100,      # 100 connections per pool
    pool_block=False       # Don't block when pool full
)

session = requests.Session()
session.mount('https://', adapter)

# Make many requests - connections are pooled and reused
urls = [f'https://httpbin.org/delay/{i}' for i in range(5)]

for url in urls:
    response = session.get(url)
    print(f"Response from {url}: {response.status_code}")

# Close session to clean up connection pools
session.close()
```

### SSL/TLS Configuration

```python
import requests
from requests.adapters import HTTPAdapter

# Custom adapter with SSL settings
class SecureAdapter(HTTPAdapter):
    def cert_verify(self, conn, url, verify, cert):
        # Custom SSL verification logic
        super().cert_verify(conn, url, verify, cert)
        print(f"SSL verification for {url}: verify={verify}")

# Use secure adapter
session = requests.Session()
session.mount('https://', SecureAdapter())

# Configure SSL verification
response = session.get('https://httpbin.org/get', 
                      verify=True,  # Verify SSL certificates
                      cert=None)    # No client certificate
```

### Retry Configuration

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure retry strategy
retry_strategy = Retry(
    total=3,                    # Total retries
    status_forcelist=[429, 500, 502, 503, 504],  # Status codes to retry
    method_whitelist=["HEAD", "GET", "OPTIONS"], # Methods to retry
    backoff_factor=1           # Backoff between retries
)

# Create adapter with retry strategy
adapter = HTTPAdapter(max_retries=retry_strategy)

session = requests.Session()
session.mount('http://', adapter)
session.mount('https://', adapter)

# Requests will automatically retry on failures
response = session.get('https://httpbin.org/status/500')
```

### Custom Transport Adapter

```python
import requests
from requests.adapters import BaseAdapter
from requests.models import Response

class MockAdapter(BaseAdapter):
    """Mock adapter for testing."""
    
    def __init__(self, responses=None):
        super().__init__()
        self.responses = responses or {}
    
    def send(self, request, **kwargs):
        """Return mock response."""
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'application/json'
        
        # Mock response based on URL
        if request.url in self.responses:
            response._content = self.responses[request.url].encode('utf-8')
        else:
            response._content = b'{"mock": "response"}'
        
        response.url = request.url
        response.request = request
        return response
    
    def close(self):
        pass

# Use mock adapter for testing
mock_responses = {
    'https://api.example.com/data': '{"users": [{"name": "John"}]}'
}

session = requests.Session()
session.mount('https://api.example.com/', MockAdapter(mock_responses))

# This returns the mock response
response = session.get('https://api.example.com/data')
print(response.json())  # {'users': [{'name': 'John'}]}
```

### Proxy Adapter Configuration

```python
import requests
from requests.adapters import HTTPAdapter

class ProxyAdapter(HTTPAdapter):
    """Adapter with proxy configuration."""
    
    def __init__(self, proxy_url, **kwargs):
        self.proxy_url = proxy_url
        super().__init__(**kwargs)
    
    def proxy_headers(self, proxy):
        """Add custom proxy headers."""
        headers = super().proxy_headers(proxy)
        headers['Proxy-Authorization'] = 'Basic dXNlcjpwYXNz'  # base64 user:pass
        return headers

# Configure proxy adapter
proxy_adapter = ProxyAdapter('http://proxy.example.com:8080')

session = requests.Session()
session.mount('http://', proxy_adapter)
session.mount('https://', proxy_adapter)

# Requests go through the proxy
response = session.get('https://httpbin.org/ip')
print(response.json())  # Shows proxy IP
```

### Performance Monitoring Adapter

```python
import requests
import time
from requests.adapters import HTTPAdapter

class TimingAdapter(HTTPAdapter):
    """Adapter that measures request timing."""
    
    def send(self, request, **kwargs):
        start_time = time.time()
        response = super().send(request, **kwargs)
        end_time = time.time()
        
        # Add timing information to response
        response.elapsed_total = end_time - start_time
        print(f"Request to {request.url} took {response.elapsed_total:.3f}s")
        
        return response

# Use timing adapter
session = requests.Session()
session.mount('https://', TimingAdapter())

response = session.get('https://httpbin.org/delay/2')
print(f"Total time: {response.elapsed_total:.3f}s")
```

### Adapter Debugging

```python
import requests
from requests.adapters import HTTPAdapter

class DebugAdapter(HTTPAdapter):
    """Adapter with detailed logging."""
    
    def send(self, request, **kwargs):
        print(f"Sending {request.method} request to {request.url}")
        print(f"Headers: {dict(request.headers)}")
        
        if request.body:
            print(f"Body: {request.body[:100]}...")
        
        response = super().send(request, **kwargs)
        
        print(f"Received {response.status_code} response")
        print(f"Response headers: {dict(response.headers)}")
        
        return response

# Use debug adapter
session = requests.Session()
session.mount('https://', DebugAdapter())

response = session.post('https://httpbin.org/post', 
                       json={'key': 'value'})
```

## Adapter Best Practices

### Resource Management

```python
import requests
from requests.adapters import HTTPAdapter

# Always close sessions to clean up connection pools
session = requests.Session()
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=50)
session.mount('https://', adapter)

try:
    # Use session
    response = session.get('https://api.example.com/data')
    # Process response...
finally:
    # Ensure cleanup
    session.close()

# Or use context manager
with requests.Session() as session:
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=50)
    session.mount('https://', adapter)
    response = session.get('https://api.example.com/data')
# Session automatically closed
```

### Adapter Selection

```python
import requests
from requests.adapters import HTTPAdapter

# Different configurations for different services
session = requests.Session()

# High-performance adapter for API calls
api_adapter = HTTPAdapter(
    pool_connections=20,
    pool_maxsize=100,
    max_retries=3
)

# Conservative adapter for file downloads
download_adapter = HTTPAdapter(
    pool_connections=5,
    pool_maxsize=10,
    max_retries=1
)

# Mount adapters with specific prefixes
session.mount('https://api.fastservice.com/', api_adapter)
session.mount('https://downloads.example.com/', download_adapter)
session.mount('https://', HTTPAdapter())  # Default adapter

# Requests automatically use appropriate adapter
api_response = session.get('https://api.fastservice.com/data')
file_response = session.get('https://downloads.example.com/file.zip')
other_response = session.get('https://other-site.com/page')
```