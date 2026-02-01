# Authentication

Authentication handlers for various HTTP authentication schemes. The requests library provides built-in support for the most common authentication methods and allows for custom authentication handlers.

## Capabilities

### Base Authentication Class

All authentication handlers inherit from the AuthBase class.

```python { .api }
class AuthBase:
    """Base class that all authentication implementations derive from."""

    def __call__(self, request):
        """
        Apply authentication to a request.
        
        Parameters:
        - request: PreparedRequest object to modify
        
        Returns:
        Modified PreparedRequest object
        """
```

### HTTP Basic Authentication

Implements HTTP Basic Authentication using username and password.

```python { .api }
class HTTPBasicAuth(AuthBase):
    """Attaches HTTP Basic Authentication to the given Request object."""

    def __init__(self, username: str, password: str):
        """
        Initialize Basic Authentication.
        
        Parameters:
        - username: Username for authentication
        - password: Password for authentication
        """

    def __call__(self, request) -> 'PreparedRequest':
        """Apply Basic Authentication to request."""

    def __eq__(self, other) -> bool:
        """Check equality with another auth object."""

    def __ne__(self, other) -> bool:
        """Check inequality with another auth object."""
```

### HTTP Digest Authentication

Implements HTTP Digest Authentication for enhanced security over Basic auth.

```python { .api }
class HTTPDigestAuth(AuthBase):
    """Attaches HTTP Digest Authentication to the given Request object."""

    def __init__(self, username: str, password: str):
        """
        Initialize Digest Authentication.
        
        Parameters:
        - username: Username for authentication
        - password: Password for authentication
        """

    def __call__(self, request) -> 'PreparedRequest':
        """Apply Digest Authentication to request."""
```

### HTTP Proxy Authentication

Implements HTTP Proxy Authentication, extending Basic Authentication for proxy servers.

```python { .api }
class HTTPProxyAuth(HTTPBasicAuth):
    """Attaches HTTP Proxy Authentication to a given Request object."""

    def __call__(self, request) -> 'PreparedRequest':
        """Apply Proxy Authentication to request."""
```

## Usage Examples

### Basic Authentication

```python
import requests
from requests.auth import HTTPBasicAuth

# Using auth tuple (shorthand)
response = requests.get('https://api.example.com/data', auth=('username', 'password'))

# Using HTTPBasicAuth class
basic_auth = HTTPBasicAuth('username', 'password')
response = requests.get('https://api.example.com/data', auth=basic_auth)

# With sessions for persistent auth
session = requests.Session()
session.auth = ('username', 'password')
response = session.get('https://api.example.com/data')
```

### Digest Authentication

```python
import requests
from requests.auth import HTTPDigestAuth

# Digest authentication for enhanced security
digest_auth = HTTPDigestAuth('username', 'password')
response = requests.get('https://api.example.com/secure', auth=digest_auth)

# With sessions
session = requests.Session()
session.auth = HTTPDigestAuth('user', 'pass')
response = session.get('https://api.example.com/data')
```

### Proxy Authentication

```python
import requests
from requests.auth import HTTPProxyAuth

# Authenticate with proxy server
proxy_auth = HTTPProxyAuth('proxy_user', 'proxy_pass')
proxies = {'http': 'http://proxy.example.com:8080'}

response = requests.get('https://api.example.com/data', 
                       auth=proxy_auth, 
                       proxies=proxies)
```

### Custom Authentication

```python
import requests
from requests.auth import AuthBase

class TokenAuth(AuthBase):
    """Custom token-based authentication."""
    
    def __init__(self, token):
        self.token = token
    
    def __call__(self, request):
        request.headers['Authorization'] = f'Bearer {self.token}'
        return request

# Use custom authentication
token_auth = TokenAuth('your-api-token')
response = requests.get('https://api.example.com/data', auth=token_auth)
```

### OAuth 1.0 Authentication

```python
# Note: OAuth requires additional libraries like requests-oauthlib
from requests_oauthlib import OAuth1

# OAuth 1.0 authentication
oauth = OAuth1('client_key', 'client_secret', 'resource_owner_key', 'resource_owner_secret')
response = requests.get('https://api.twitter.com/1.1/account/verify_credentials.json', auth=oauth)
```

### Bearer Token Authentication

```python
import requests

# Simple bearer token authentication
headers = {'Authorization': 'Bearer your-access-token'}
response = requests.get('https://api.example.com/data', headers=headers)

# Or create a custom auth class
class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    
    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r

# Use the custom auth
bearer_auth = BearerAuth('your-access-token')
response = requests.get('https://api.example.com/data', auth=bearer_auth)
```

### Multiple Authentication Methods

```python
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

# Try different auth methods
def authenticate_with_fallback(url, username, password):
    # Try Digest first (more secure)
    try:
        response = requests.get(url, auth=HTTPDigestAuth(username, password))
        if response.status_code == 200:
            return response
    except requests.exceptions.RequestException:
        pass
    
    # Fall back to Basic auth
    try:
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        return response
    except requests.exceptions.RequestException:
        pass
    
    # Try without auth
    return requests.get(url)

response = authenticate_with_fallback('https://api.example.com/data', 'user', 'pass')
```

### Session-based Authentication

```python
import requests

# Login to get session cookie
session = requests.Session()
login_data = {'username': 'user', 'password': 'pass'}
session.post('https://example.com/login', data=login_data)

# Subsequent requests use the session cookie
response = session.get('https://example.com/protected-data')

# Or combine with other auth methods
session.auth = ('api_user', 'api_pass')
response = session.get('https://api.example.com/data')
```

## Authentication with Different Request Types

### GET with Authentication

```python
import requests

# Simple GET with auth
response = requests.get('https://api.example.com/users', auth=('user', 'pass'))
users = response.json()
```

### POST with Authentication

```python
import requests

# POST data with authentication
data = {'name': 'John Doe', 'email': 'john@example.com'}
response = requests.post('https://api.example.com/users', 
                        json=data, 
                        auth=('admin', 'password'))
```

### File Upload with Authentication

```python
import requests

# Upload file with authentication
files = {'file': open('document.pdf', 'rb')}
response = requests.post('https://api.example.com/upload', 
                        files=files, 
                        auth=('user', 'pass'))
```

## Security Considerations

### HTTPS Requirement

Always use HTTPS when sending authentication credentials:

```python
import requests

# Good - HTTPS protects credentials
response = requests.get('https://api.example.com/data', auth=('user', 'pass'))

# Bad - HTTP exposes credentials
# response = requests.get('http://api.example.com/data', auth=('user', 'pass'))
```

### Environment Variables

Store credentials in environment variables instead of hardcoding:

```python
import os
import requests

username = os.environ.get('API_USERNAME')
password = os.environ.get('API_PASSWORD')

if username and password:
    response = requests.get('https://api.example.com/data', auth=(username, password))
else:
    raise ValueError("Missing authentication credentials")
```

### Certificate Verification

Always verify SSL certificates in production:

```python
import requests

# Default behavior - verify SSL certificates
response = requests.get('https://api.example.com/data', 
                       auth=('user', 'pass'),
                       verify=True)  # This is the default

# Only disable verification for testing
# response = requests.get('https://api.example.com/data', 
#                        auth=('user', 'pass'),
#                        verify=False)  # Only for testing!
```

## Authentication Utility Function

```python { .api }
def _basic_auth_str(username: str, password: str) -> str:
    """
    Generate a Basic Auth string.
    
    Parameters:
    - username: Username for authentication
    - password: Password for authentication
    
    Returns:
    Basic authentication header value
    """
```

This utility function is used internally by HTTPBasicAuth but can be useful for custom authentication implementations.