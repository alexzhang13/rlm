# Cookie Handling

Cookie management functionality providing a dict-like interface for handling HTTP cookies with compatibility for both client and server-side cookie operations.

## Capabilities

### RequestsCookieJar Class

A CookieJar with dict-like interface that extends standard cookielib functionality.

```python { .api }
class RequestsCookieJar:
    """
    Compatibility class for http.cookiejar.CookieJar with dict-like interface.
    
    Provides convenient access to cookies while maintaining full CookieJar functionality.
    """

    def __init__(self, policy=None):
        """
        Initialize RequestsCookieJar.
        
        Parameters:
        - policy: CookiePolicy instance (optional)
        """

    # Dict-like interface
    def get(self, name: str, default=None, domain=None, path=None) -> str:
        """
        Get cookie value by name.
        
        Parameters:
        - name: Cookie name
        - default: Default value if cookie not found
        - domain: Specific domain to search (optional)
        - path: Specific path to search (optional)
        
        Returns:
        Cookie value or default
        """

    def set(self, name: str, value: str, **kwargs):
        """
        Set a cookie.
        
        Parameters:
        - name: Cookie name
        - value: Cookie value
        - **kwargs: Additional cookie attributes (domain, path, etc.)
        
        Returns:
        Cookie object
        """

    def __getitem__(self, name: str) -> str:
        """Get cookie value by name."""

    def __setitem__(self, name: str, value: str):
        """Set cookie value by name."""

    def __delitem__(self, name: str):
        """Delete cookie by name."""

    def __contains__(self, name: str) -> bool:
        """Check if cookie exists."""

    def update(self, other):
        """Update cookies from another cookie jar or dict."""

    def keys(self) -> list[str]:
        """Get list of cookie names."""

    def values(self) -> list[str]:
        """Get list of cookie values."""

    def items(self) -> list[tuple[str, str]]:
        """Get list of (name, value) tuples."""

    def iterkeys(self):
        """Iterate over cookie names."""

    def itervalues(self):
        """Iterate over cookie values."""

    def iteritems(self):
        """Iterate over (name, value) tuples."""

    # Cookie management methods
    def list_domains(self) -> list[str]:
        """Get list of domains with cookies."""

    def list_paths(self) -> list[str]:
        """Get list of paths with cookies."""

    def multiple_domains(self) -> bool:
        """Check if cookies exist for multiple domains."""

    def get_dict(self, domain=None, path=None) -> dict:
        """
        Get cookies as a plain dict.
        
        Parameters:
        - domain: Filter by domain (optional)
        - path: Filter by path (optional)
        
        Returns:
        Dict of cookie name -> value mappings
        """

    def copy(self) -> 'RequestsCookieJar':
        """Create a copy of the cookie jar."""

    def get_policy(self):
        """Get the cookie policy."""
```

### Cookie Utility Functions

Functions for cookie manipulation and conversion.

```python { .api }
def extract_cookies_to_jar(jar, request, response):
    """
    Extract cookies from response and add to jar.
    
    Parameters:
    - jar: RequestsCookieJar to add cookies to
    - request: Request object
    - response: Response object
    """

def get_cookie_header(jar, request) -> str | None:
    """
    Get Cookie header value from jar for request.
    
    Parameters:
    - jar: RequestsCookieJar containing cookies
    - request: Request object
    
    Returns:
    Cookie header value or None
    """

def remove_cookie_by_name(cookiejar, name: str, domain=None, path=None):
    """
    Remove cookie from jar by name.
    
    Parameters:
    - cookiejar: CookieJar to remove from
    - name: Cookie name to remove
    - domain: Domain filter (optional)
    - path: Path filter (optional)
    """

def create_cookie(name: str, value: str, **kwargs):
    """
    Create a Cookie object.
    
    Parameters:
    - name: Cookie name
    - value: Cookie value
    - **kwargs: Additional cookie attributes
    
    Returns:
    Cookie object
    """

def morsel_to_cookie(morsel):
    """
    Convert http.cookies.Morsel to Cookie object.
    
    Parameters:
    - morsel: Morsel object to convert
    
    Returns:
    Cookie object
    """

def cookiejar_from_dict(cookie_dict: dict, cookiejar=None, overwrite=True):
    """
    Create CookieJar from dictionary.
    
    Parameters:
    - cookie_dict: Dict of cookie name -> value mappings
    - cookiejar: Existing jar to add to (optional)
    - overwrite: Whether to overwrite existing cookies
    
    Returns:
    CookieJar containing the cookies
    """

def merge_cookies(cookiejar, cookies):
    """
    Merge cookies into an existing jar.
    
    Parameters:
    - cookiejar: Target CookieJar
    - cookies: Cookies to merge (dict or CookieJar)
    
    Returns:
    Updated CookieJar
    """
```

### Cookie Exceptions

```python { .api }
class CookieConflictError(RuntimeError):
    """Raised when multiple cookies match the same criteria."""
```

## Usage Examples

### Basic Cookie Operations

```python
import requests

# Cookies are automatically handled
response = requests.get('https://httpbin.org/cookies/set/sessionid/abc123')
print(response.cookies['sessionid'])  # 'abc123'

# Access cookie jar
jar = response.cookies
print(jar.get('sessionid'))  # 'abc123'
print('sessionid' in jar)    # True

# Send cookies with request
cookies = {'user': 'john', 'token': 'xyz789'}
response = requests.get('https://httpbin.org/cookies', cookies=cookies)
```

### Session Cookie Persistence

```python
import requests

# Cookies persist across requests in a session
session = requests.Session()
session.get('https://httpbin.org/cookies/set/sessionid/abc123')

# Cookie is automatically sent in subsequent requests
response = session.get('https://httpbin.org/cookies')
data = response.json()
print(data['cookies']['sessionid'])  # 'abc123'
```

### Manual Cookie Management

```python
import requests
from requests.cookies import RequestsCookieJar

# Create custom cookie jar
jar = RequestsCookieJar()
jar.set('custom_cookie', 'custom_value', domain='example.com')
jar.set('another_cookie', 'another_value')

# Use jar with request
response = requests.get('https://example.com', cookies=jar)

# Examine cookies
for name, value in jar.items():
    print(f"{name}: {value}")

# Get cookies for specific domain
domain_cookies = jar.get_dict(domain='example.com')
print(domain_cookies)
```

### Cookie Jar Operations

```python
import requests

# Get cookies from response
response = requests.get('https://httpbin.org/cookies/set/foo/bar')
jar = response.cookies

# Cookie jar behaves like a dict
print(jar['foo'])           # 'bar'
print(jar.get('foo'))       # 'bar'
print(list(jar.keys()))     # ['foo']
print(list(jar.values()))   # ['bar']
print(list(jar.items()))    # [('foo', 'bar')]

# Copy cookie jar
new_jar = jar.copy()

# Update from dict
jar.update({'baz': 'qux'})

# Check domains and paths
print(jar.list_domains())
print(jar.list_paths())
print(jar.multiple_domains())
```

### Cookie Utilities

```python
import requests
from requests.cookies import cookiejar_from_dict, merge_cookies

# Create jar from dict
cookie_dict = {'session': 'abc123', 'user': 'john'}
jar = cookiejar_from_dict(cookie_dict)

# Use with session
session = requests.Session()
session.cookies = jar

# Merge cookies
additional_cookies = {'theme': 'dark', 'lang': 'en'}
merge_cookies(jar, additional_cookies)

response = session.get('https://httpbin.org/cookies')
```

### Advanced Cookie Handling

```python
import requests
from requests.cookies import RequestsCookieJar

def manage_cookies():
    jar = RequestsCookieJar()
    
    # Set cookies with attributes
    jar.set('secure_cookie', 'secret_value', 
            domain='api.example.com', 
            path='/secure',
            secure=True)
    
    # Set session cookie (no expiry)
    jar.set('session_id', 'sess_123456')
    
    # Check cookie existence
    if 'session_id' in jar:
        print("Session cookie found")
    
    # Get cookie with domain/path filtering
    secure_value = jar.get('secure_cookie', 
                          domain='api.example.com', 
                          path='/secure')
    
    # Remove specific cookie
    if 'old_cookie' in jar:
        del jar['old_cookie']
    
    return jar

# Use custom jar
jar = manage_cookies()
response = requests.get('https://api.example.com/secure/data', cookies=jar)
```

## Cookie Security

### Secure Cookie Practices

```python
import requests
from requests.cookies import RequestsCookieJar

# Always use HTTPS for sensitive cookies
jar = RequestsCookieJar()
jar.set('auth_token', 'sensitive_token', 
        domain='secure-api.com',
        secure=True,      # Only send over HTTPS
        httponly=True)    # Not accessible via JavaScript

# Use with secure request
response = requests.get('https://secure-api.com/data', cookies=jar)
```

### Cookie Domain Validation

```python
import requests

def safe_cookie_handling(url, cookies):
    """Safely handle cookies with domain validation."""
    session = requests.Session()
    
    # Let requests handle cookie domain validation
    response = session.get(url, cookies=cookies)
    
    # Check which cookies were actually sent
    request_cookies = response.request.headers.get('Cookie', '')
    print(f"Cookies sent: {request_cookies}")
    
    return response

# Example usage
cookies = {'token': 'abc123'}
response = safe_cookie_handling('https://api.example.com', cookies)
```