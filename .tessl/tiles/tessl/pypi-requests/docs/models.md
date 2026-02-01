# Request and Response Objects

Core objects that represent HTTP requests and responses, providing full control over request preparation and response handling. These objects form the foundation of the requests library's functionality.

## Capabilities

### Request Class

User-created Request objects that represent HTTP requests before they are sent.

```python { .api }
class Request:
    """
    A user-created Request object.
    
    Used to prepare a PreparedRequest, which is sent to the server.
    """

    def __init__(self, method=None, url=None, headers=None, files=None, 
                 data=None, params=None, auth=None, cookies=None, 
                 hooks=None, json=None):
        """
        Initialize a Request object.
        
        Parameters:
        - method: HTTP method to use ('GET', 'POST', etc.)
        - url: URL to send the request to
        - headers: dict of headers to send
        - files: dict of {filename: fileobject} for multipart upload
        - data: request body data (dict, list of tuples, bytes, or file-like)
        - params: URL parameters to append (dict or list of tuples)
        - auth: authentication tuple or handler
        - cookies: cookies to send (dict or CookieJar)
        - hooks: event hooks dict
        - json: JSON serializable object for request body
        """

    def prepare(self) -> 'PreparedRequest':
        """
        Prepare the request for sending.
        
        Returns:
        PreparedRequest object ready to send
        """
```

### PreparedRequest Class

Fully prepared request objects containing the exact bytes that will be sent to the server.

```python { .api }
class PreparedRequest:
    """
    The fully mutable PreparedRequest object.
    
    Contains the exact bytes that will be sent to the server.
    Should not be instantiated manually.
    
    Attributes:
    - method: HTTP method (str)
    - url: Full URL (str)
    - headers: Request headers (CaseInsensitiveDict)
    - body: Request body (bytes or str or None)
    - hooks: Event hooks (dict)
    - _cookies: CookieJar for cookie header generation
    - _body_position: Position marker for rewindable request bodies
    """

    def __init__(self):
        """Initialize a PreparedRequest object."""

    def prepare(self, method=None, url=None, files=None, data=None, 
                headers=None, params=None, auth=None, cookies=None, 
                hooks=None, json=None):
        """
        Prepare all aspects of the request.
        
        Parameters: Same as Request.__init__
        """

    def prepare_method(self, method: str):
        """Prepare the HTTP method."""

    def prepare_url(self, url: str, params):
        """Prepare the URL with parameters."""

    def prepare_headers(self, headers):
        """Prepare the headers."""

    def prepare_cookies(self, cookies):
        """Prepare the cookies."""

    def prepare_body(self, data, files, json=None):
        """Prepare the request body."""

    def prepare_auth(self, auth, url=''):
        """Prepare authentication."""

    def prepare_content_length(self, body):
        """Prepare Content-Length header."""

    def prepare_hooks(self, hooks):
        """Prepare event hooks."""

    def copy(self) -> 'PreparedRequest':
        """Create a copy of the PreparedRequest."""
```

### Response Class

Response objects containing server responses to HTTP requests.

```python { .api }
class Response:
    """
    The Response object contains a server's response to an HTTP request.
    """

    # Response attributes
    content: bytes  # Response content as bytes
    text: str  # Response content as text
    encoding: str  # Response encoding
    status_code: int  # HTTP status code
    headers: 'CaseInsensitiveDict'  # Response headers
    cookies: 'RequestsCookieJar'  # Response cookies
    url: str  # Final URL location of response
    history: list['Response']  # List of Response objects (redirects)
    reason: str  # Textual reason of response (e.g., 'OK', 'Not Found')
    request: 'PreparedRequest'  # PreparedRequest that generated this response
    elapsed: 'timedelta'  # Time elapsed between request and response
    raw: object  # Raw response object (urllib3.HTTPResponse)

    def __init__(self):
        """Initialize a Response object."""

    def __enter__(self):
        """Context manager entry."""

    def __exit__(self, *args):
        """Context manager exit."""

    def __bool__(self) -> bool:
        """Boolean evaluation based on status code."""

    def __nonzero__(self) -> bool:
        """Boolean evaluation for Python 2 compatibility."""

    def __iter__(self):
        """Iterate over response content in chunks."""

    @property
    def ok(self) -> bool:
        """True if status code is less than 400."""

    @property
    def is_redirect(self) -> bool:
        """True if response is a redirect."""

    @property
    def is_permanent_redirect(self) -> bool:
        """True if response is a permanent redirect."""

    @property
    def next(self):
        """Returns parsed header links if present."""

    @property
    def apparent_encoding(self) -> str:
        """Apparent encoding of response content."""

    def iter_content(self, chunk_size: int = 1, decode_unicode: bool = False):
        """
        Iterate over response data in chunks.
        
        Parameters:
        - chunk_size: Size of chunks to read
        - decode_unicode: Whether to decode content to unicode
        
        Yields:
        Chunks of response content
        """

    def iter_lines(self, chunk_size: int = 512, decode_unicode: bool = False, 
                   delimiter=None):
        """
        Iterate over response lines.
        
        Parameters:
        - chunk_size: Size of chunks to read
        - decode_unicode: Whether to decode content to unicode
        - delimiter: Line delimiter
        
        Yields:
        Lines from response content
        """

    def json(self, **kwargs) -> Union[dict, list]:
        """
        Parse response content as JSON.
        
        Parameters:
        - **kwargs: Arguments passed to json.loads()
        
        Returns:
        Parsed JSON data
        
        Raises:
        JSONDecodeError: If response is not valid JSON
        """

    @property
    def links(self) -> dict:
        """Returns parsed header links."""

    def raise_for_status(self):
        """
        Raise HTTPError for bad responses (4xx or 5xx status codes).
        
        Raises:
        HTTPError: If status code indicates an error
        """

    def close(self):
        """Release the connection back to the pool."""
```

## Usage Examples

### Basic Request Creation

```python
import requests

# Create a request object
req = requests.Request('GET', 'https://api.github.com/user', 
                      auth=('username', 'password'))

# Prepare the request
prepared = req.prepare()

# Send the prepared request
with requests.Session() as s:
    response = s.send(prepared)
    print(response.status_code)
```

### Working with Response Objects

```python
import requests

response = requests.get('https://api.github.com/users/octocat')

# Access response properties
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"URL: {response.url}")
print(f"Encoding: {response.encoding}")

# Check if request was successful
if response.ok:
    print("Request successful")

# Parse JSON response
try:
    data = response.json()
    print(f"User: {data['login']}")
except requests.exceptions.JSONDecodeError:
    print("Response is not valid JSON")

# Check for errors
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
```

### Streaming Large Responses

```python
import requests

# Stream large file download
url = 'https://example.com/large-file.zip'
response = requests.get(url, stream=True)

with open('large-file.zip', 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

# Stream and process lines
response = requests.get('https://example.com/large-text-file.txt', stream=True)
for line in response.iter_lines(decode_unicode=True):
    print(line)

response.close()  # Important to close streamed responses
```

### Response Context Manager

```python
import requests

# Use response as context manager for automatic cleanup
with requests.get('https://example.com/data.json', stream=True) as response:
    response.raise_for_status()
    data = response.json()
    # Process data...
# Response is automatically closed
```

### Advanced Request Preparation

```python
import requests

# Create and customize a request
req = requests.Request(
    method='POST',
    url='https://api.example.com/data',
    json={'key': 'value'},
    headers={'User-Agent': 'MyApp/1.0'},
    auth=('user', 'pass')
)

# Prepare and inspect before sending
prepared = req.prepare()
print(f"Method: {prepared.method}")
print(f"URL: {prepared.url}")
print(f"Headers: {prepared.headers}")
print(f"Body: {prepared.body}")

# Send the prepared request
with requests.Session() as s:
    response = s.send(prepared, timeout=30)
```

### Response History and Redirects

```python
import requests

response = requests.get('https://github.com')

# Check redirect history
if response.history:
    print("Request was redirected")
    for resp in response.history:
        print(f"Redirect from: {resp.url} -> {resp.status_code}")
    print(f"Final URL: {response.url}")

# Check redirect type
if response.is_redirect:
    print("Response is a redirect")
if response.is_permanent_redirect:
    print("Response is a permanent redirect")
```

## Constants

```python { .api }
# Redirect status codes
REDIRECT_STATI: tuple  # (301, 302, 303, 307, 308)

# Default limits
DEFAULT_REDIRECT_LIMIT: int  # 30
CONTENT_CHUNK_SIZE: int  # 10 * 1024
ITER_CHUNK_SIZE: int  # 512
```

## Request/Response Lifecycle

1. **Request Creation**: User creates a Request object with parameters
2. **Request Preparation**: Request is converted to PreparedRequest with exact bytes
3. **Request Sending**: PreparedRequest is sent via adapter (usually HTTPAdapter)
4. **Response Creation**: Server response is converted to Response object
5. **Response Processing**: User accesses response data, headers, status, etc.
6. **Cleanup**: Response connection is returned to pool or closed