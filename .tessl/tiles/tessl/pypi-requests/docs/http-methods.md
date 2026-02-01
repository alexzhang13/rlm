# HTTP Methods

Core HTTP method functions that provide the primary interface for making HTTP requests. These functions handle the most common HTTP verbs and automatically manage sessions internally.

## Capabilities

### Main Request Function

The core request function that all other HTTP method functions use internally. Provides full control over HTTP method and request parameters.

```python { .api }
def request(method: str, url: str, **kwargs) -> Response:
    """
    Constructs and sends a Request.

    Parameters:
    - method: HTTP method ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS')
    - url: URL for the request
    - params: dict, list of tuples or bytes for query string parameters
    - data: dict, list of tuples, bytes, or file-like object for request body
    - json: JSON serializable Python object for request body
    - headers: dict of HTTP headers
    - cookies: dict or CookieJar object
    - files: dict of file-like objects for multipart encoding
    - auth: auth tuple or auth handler instance
    - timeout: float or (connect timeout, read timeout) tuple in seconds
    - allow_redirects: bool to enable/disable redirects
    - proxies: dict mapping protocol to proxy URL
    - verify: bool or path to CA bundle for SSL verification
    - stream: bool to download response content immediately
    - cert: path to SSL client cert file or (cert, key) tuple

    Returns:
    Response object
    """
```

### GET Requests

Send HTTP GET requests to retrieve data from servers.

```python { .api }
def get(url: str, params=None, **kwargs) -> Response:
    """
    Sends a GET request.

    Parameters:
    - url: URL for the request
    - params: dict, list of tuples or bytes for query string parameters
    - **kwargs: optional arguments that request() accepts

    Returns:
    Response object
    """
```

Usage example:

```python
import requests

# Simple GET request
response = requests.get('https://api.github.com/users/octocat')

# GET with query parameters
params = {'q': 'python', 'sort': 'stars'}
response = requests.get('https://api.github.com/search/repositories', params=params)

# GET with headers and authentication
headers = {'User-Agent': 'MyApp/1.0'}
response = requests.get('https://api.example.com/data', 
                       headers=headers, 
                       auth=('username', 'password'))
```

### POST Requests

Send HTTP POST requests to submit data to servers.

```python { .api }
def post(url: str, data=None, json=None, **kwargs) -> Response:
    """
    Sends a POST request.

    Parameters:
    - url: URL for the request
    - data: dict, list of tuples, bytes, or file-like object for request body
    - json: JSON serializable Python object for request body
    - **kwargs: optional arguments that request() accepts

    Returns:
    Response object
    """
```

Usage example:

```python
import requests

# POST with form data
data = {'key1': 'value1', 'key2': 'value2'}
response = requests.post('https://httpbin.org/post', data=data)

# POST with JSON data
json_data = {'user': 'john', 'age': 30}
response = requests.post('https://api.example.com/users', json=json_data)

# POST with file upload
files = {'file': open('document.pdf', 'rb')}
response = requests.post('https://httpbin.org/post', files=files)
```

### PUT Requests

Send HTTP PUT requests to create or update resources.

```python { .api }
def put(url: str, data=None, **kwargs) -> Response:
    """
    Sends a PUT request.

    Parameters:
    - url: URL for the request
    - data: dict, list of tuples, bytes, or file-like object for request body
    - **kwargs: optional arguments that request() accepts

    Returns:
    Response object
    """
```

### PATCH Requests

Send HTTP PATCH requests to partially update resources.

```python { .api }
def patch(url: str, data=None, **kwargs) -> Response:
    """
    Sends a PATCH request.

    Parameters:
    - url: URL for the request
    - data: dict, list of tuples, bytes, or file-like object for request body
    - **kwargs: optional arguments that request() accepts

    Returns:
    Response object
    """
```

### DELETE Requests

Send HTTP DELETE requests to remove resources.

```python { .api }
def delete(url: str, **kwargs) -> Response:
    """
    Sends a DELETE request.

    Parameters:
    - url: URL for the request
    - **kwargs: optional arguments that request() accepts

    Returns:
    Response object
    """
```

### HEAD Requests

Send HTTP HEAD requests to retrieve headers without response body.

```python { .api }
def head(url: str, **kwargs) -> Response:
    """
    Sends a HEAD request.

    Parameters:
    - url: URL for the request
    - **kwargs: optional arguments that request() accepts
    Note: allow_redirects defaults to False for HEAD requests

    Returns:
    Response object with empty content
    """
```

### OPTIONS Requests

Send HTTP OPTIONS requests to determine allowed methods and capabilities.

```python { .api }
def options(url: str, **kwargs) -> Response:
    """
    Sends an OPTIONS request.

    Parameters:
    - url: URL for the request
    - **kwargs: optional arguments that request() accepts

    Returns:
    Response object
    """
```

## Common Parameters

All HTTP method functions accept these common optional parameters:

- **headers**: `Dict[str, str]` - HTTP headers to send
- **auth**: `AuthType` - Authentication tuple or handler
- **timeout**: `Union[float, Tuple[float, float]]` - Request timeout in seconds
- **proxies**: `Dict[str, str]` - Proxy configuration
- **verify**: `Union[bool, str]` - SSL certificate verification
- **cert**: `Union[str, Tuple[str, str]]` - Client certificate
- **stream**: `bool` - Stream download response content
- **allow_redirects**: `bool` - Follow redirects (default True, except HEAD)
- **cookies**: `CookiesType` - Cookies to send

## Error Handling

All HTTP method functions can raise these exceptions:

- **RequestException**: Base exception for all request-related errors
- **HTTPError**: 4xx or 5xx status codes (when raise_for_status() is called)
- **ConnectionError**: Connection-related errors
- **Timeout**: Request timeout errors
- **URLRequired**: Invalid or missing URL