# Exception Handling

Comprehensive exception hierarchy for handling various error conditions that can occur during HTTP requests. The requests library provides specific exceptions for different types of errors, allowing for precise error handling.

## Capabilities

### Base Exception

All requests exceptions inherit from the base RequestException class.

```python { .api }
class RequestException(IOError):
    """
    Base exception for all request-related errors.
    
    Attributes:
    - response: Response object (if available)
    - request: Request object that caused the exception
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize RequestException.
        
        Parameters:
        - response: Response object (optional)
        - request: Request object (optional)
        """
```

### HTTP Errors

Exceptions related to HTTP status codes and server responses.

```python { .api }
class HTTPError(RequestException):
    """
    An HTTP error occurred.
    
    Raised by Response.raise_for_status() for 4xx and 5xx status codes.
    """

class InvalidJSONError(RequestException):
    """A JSON error occurred."""

class JSONDecodeError(InvalidJSONError):
    """Couldn't decode the text into JSON."""
```

### Connection Errors

Exceptions related to network connectivity and connection issues.

```python { .api }
class ConnectionError(RequestException):
    """A connection error occurred."""

class ProxyError(ConnectionError):
    """A proxy error occurred."""

class SSLError(ConnectionError):
    """An SSL error occurred."""
```

### Timeout Errors

Exceptions related to request timeouts.

```python { .api }
class Timeout(RequestException):
    """
    The request timed out.
    
    Catching this error will catch both ConnectTimeout and ReadTimeout.
    """

class ConnectTimeout(ConnectionError, Timeout):
    """
    The request timed out while trying to connect to the remote server.
    
    Requests that produced this error are safe to retry.
    """

class ReadTimeout(Timeout):
    """The server did not send any data in the allotted amount of time."""
```

### URL and Request Errors

Exceptions related to malformed URLs and invalid requests.

```python { .api }
class URLRequired(RequestException):
    """A valid URL is required to make a request."""

class MissingSchema(RequestException, ValueError):
    """The URL scheme (e.g. http or https) is missing."""

class InvalidSchema(RequestException, ValueError):
    """The URL scheme is invalid."""

class InvalidURL(RequestException, ValueError):
    """The URL provided is invalid."""

class InvalidHeader(RequestException, ValueError):
    """The header provided is invalid."""

class InvalidProxyURL(InvalidURL):
    """The proxy URL provided is invalid."""
```

### Redirect Errors

Exceptions related to HTTP redirects.

```python { .api }
class TooManyRedirects(RequestException):
    """Too many redirects occurred."""
```

### Content and Encoding Errors

Exceptions related to response content processing.

```python { .api }
class ChunkedEncodingError(RequestException):
    """The server declared chunked encoding but sent an invalid chunk."""

class ContentDecodingError(RequestException):
    """Failed to decode response content."""

class StreamConsumedError(RequestException, TypeError):
    """The content for this response was already consumed."""

class RetryError(RequestException):
    """Custom retries logic failed."""

class UnrewindableBodyError(RequestException):
    """The request body cannot be rewound for a retry."""
```

### Warning Classes

Warning classes for non-fatal issues.

```python { .api }
class RequestsWarning(Warning):
    """Base warning for requests-related warnings."""

class FileModeWarning(RequestsWarning, DeprecationWarning):
    """Warning for file mode issues."""

class RequestsDependencyWarning(RequestsWarning):
    """Warning for dependency-related issues."""
```

## Usage Examples

### Basic Exception Handling

```python
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

try:
    response = requests.get('https://api.example.com/data', timeout=5)
    response.raise_for_status()  # Raises HTTPError for bad status codes
    data = response.json()
except HTTPError as e:
    print(f"HTTP error occurred: {e}")
    print(f"Status code: {e.response.status_code}")
except ConnectionError as e:
    print(f"Connection error occurred: {e}")
except Timeout as e:
    print(f"Request timed out: {e}")
except RequestException as e:
    print(f"An error occurred: {e}")
```

### Specific Exception Handling

```python
import requests
from requests.exceptions import (
    ConnectTimeout, ReadTimeout, SSLError, 
    JSONDecodeError, TooManyRedirects
)

def robust_api_call(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=(5, 10))  # (connect, read) timeout
            response.raise_for_status()
            return response.json()
            
        except ConnectTimeout:
            print(f"Connection timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise
                
        except ReadTimeout:
            print(f"Read timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise
                
        except SSLError as e:
            print(f"SSL error: {e}")
            # SSL errors usually shouldn't be retried
            raise
            
        except JSONDecodeError:
            print("Response is not valid JSON")
            # Try to return raw text instead
            return response.text
            
        except TooManyRedirects:
            print("Too many redirects")
            raise
            
        except HTTPError as e:
            if e.response.status_code >= 500:
                # Server errors might be temporary, retry
                print(f"Server error {e.response.status_code} on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise
            else:
                # Client errors usually shouldn't be retried
                print(f"Client error {e.response.status_code}")
                raise

result = robust_api_call('https://api.example.com/data')
```

### Connection Error Handling

```python
import requests
from requests.exceptions import ConnectionError, ProxyError, SSLError

def handle_connection_errors(url):
    try:
        response = requests.get(url)
        return response
        
    except ProxyError as e:
        print(f"Proxy error: {e}")
        # Try without proxy
        return requests.get(url, proxies={'http': '', 'https': ''})
        
    except SSLError as e:
        print(f"SSL error: {e}")
        # Option 1: Use HTTP instead (not recommended for production)
        # return requests.get(url.replace('https://', 'http://'))
        
        # Option 2: Disable SSL verification (not recommended for production)
        # return requests.get(url, verify=False)
        
        # Option 3: Provide custom CA bundle
        return requests.get(url, verify='/path/to/ca-bundle.crt')
        
    except ConnectionError as e:
        print(f"Connection error: {e}")
        raise  # Re-raise if no recovery is possible
```

### URL and Request Error Handling

```python
import requests
from requests.exceptions import (
    URLRequired, MissingSchema, InvalidSchema, 
    InvalidURL, InvalidHeader
)

def validate_and_request(url, headers=None):
    try:
        response = requests.get(url, headers=headers)
        return response
        
    except URLRequired:
        raise ValueError("URL is required")
        
    except MissingSchema:
        # Try adding https://
        return requests.get(f"https://{url}")
        
    except InvalidSchema as e:
        print(f"Invalid URL scheme: {e}")
        raise ValueError(f"URL must start with http:// or https://")
        
    except InvalidURL as e:
        print(f"Invalid URL: {e}")
        raise ValueError("Please provide a valid URL")
        
    except InvalidHeader as e:
        print(f"Invalid header: {e}")
        raise ValueError("Please check header format")

# Example usage
try:
    response = validate_and_request("example.com")  # Missing schema
except ValueError as e:
    print(f"Validation error: {e}")
```

### JSON Error Handling

```python
import requests
from requests.exceptions import JSONDecodeError

def safe_json_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Try to parse JSON
        return response.json()
        
    except JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {response.text[:200]}...")  # First 200 chars
        
        # Return raw text or None based on content type
        content_type = response.headers.get('content-type', '')
        if 'json' in content_type.lower():
            # Expected JSON but got invalid JSON
            raise ValueError("Expected JSON response but got invalid JSON")
        else:
            # Not JSON, return text
            return response.text

data = safe_json_request('https://api.example.com/data')
```

### Comprehensive Error Handling Pattern

```python
import requests
from requests.exceptions import RequestException
import time

def reliable_request(url, max_retries=3, backoff_factor=1):
    """
    Make a reliable HTTP request with exponential backoff retry logic.
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=(5, 30))
            response.raise_for_status()
            return response
            
        except requests.exceptions.ConnectTimeout:
            print(f"Connect timeout on attempt {attempt + 1}")
            last_exception = sys.exc_info()[1]
            
        except requests.exceptions.ReadTimeout:
            print(f"Read timeout on attempt {attempt + 1}")
            last_exception = sys.exc_info()[1]
            
        except requests.exceptions.HTTPError as e:
            if 500 <= e.response.status_code < 600:
                # Server error - retry
                print(f"Server error {e.response.status_code} on attempt {attempt + 1}")
                last_exception = e
            else:
                # Client error - don't retry
                raise
                
        except requests.exceptions.ConnectionError:
            print(f"Connection error on attempt {attempt + 1}")
            last_exception = sys.exc_info()[1]
            
        except RequestException as e:
            # Other request exceptions
            print(f"Request exception on attempt {attempt + 1}: {e}")
            last_exception = e
            
        # Wait before retrying (exponential backoff)
        if attempt < max_retries - 1:
            wait_time = backoff_factor * (2 ** attempt)
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    # All retries failed
    raise last_exception

# Usage
try:
    response = reliable_request('https://api.example.com/unreliable-endpoint')
    data = response.json()
except Exception as e:
    print(f"Request ultimately failed: {e}")
```

### Exception Information Access

```python
import requests
from requests.exceptions import HTTPError, RequestException

try:
    response = requests.get('https://httpbin.org/status/404')
    response.raise_for_status()
except HTTPError as e:
    print(f"HTTP Error: {e}")
    print(f"Status Code: {e.response.status_code}")
    print(f"Response Text: {e.response.text}")
    print(f"Request URL: {e.request.url}")
    print(f"Request Method: {e.request.method}")
except RequestException as e:
    print(f"Request Exception: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response Status: {e.response.status_code}")
    if hasattr(e, 'request') and e.request is not None:
        print(f"Request URL: {e.request.url}")
```

## Best Practices

1. **Always catch specific exceptions** before more general ones
2. **Use `response.raise_for_status()`** to automatically raise HTTPError for bad status codes
3. **Set appropriate timeouts** to avoid hanging requests
4. **Implement retry logic** for transient errors (timeouts, 5xx errors)
5. **Don't retry client errors** (4xx status codes) as they indicate request problems
6. **Log exception details** for debugging
7. **Provide meaningful error messages** to users
8. **Handle SSL errors carefully** - avoid disabling verification in production