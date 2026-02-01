# Data Structures

Data structure classes that provide enhanced dictionary interfaces with special behaviors for HTTP-related operations. These structures are used throughout the requests library for headers, status codes, and general data handling.

## Capabilities

### CaseInsensitiveDict Class

Dictionary with case-insensitive key lookup, primarily used for HTTP headers.

```python { .api }
class CaseInsensitiveDict(dict):
    """
    A case-insensitive dictionary implementation.
    
    Used for HTTP headers where keys should be treated case-insensitively
    according to HTTP specification.
    """

    def __init__(self, data=None, **kwargs):
        """
        Initialize CaseInsensitiveDict.
        
        Parameters:
        - data: Initial data (dict, list of tuples, or another CaseInsensitiveDict)
        - **kwargs: Additional key-value pairs
        """

    def __setitem__(self, key, value):
        """Set value with case-insensitive key."""

    def __getitem__(self, key):
        """Get value with case-insensitive key lookup."""

    def __delitem__(self, key):
        """Delete item with case-insensitive key lookup."""

    def __iter__(self):
        """Iterate over original-case keys."""

    def __len__(self) -> int:
        """Get number of items."""

    def __eq__(self, other) -> bool:
        """Compare with another mapping (case-insensitive)."""

    def __repr__(self) -> str:
        """String representation."""

    def lower_items(self):
        """
        Iterate over (lowercase_key, value) pairs.
        
        Yields:
        Tuples of (lowercase_key, value)
        """

    def copy(self) -> 'CaseInsensitiveDict':
        """Create a copy of the dictionary."""
```

### LookupDict Class

Dictionary subclass with attribute-style access, used for status codes.

```python { .api }
class LookupDict(dict):
    """
    A dictionary that supports both item and attribute access.
    
    Used for status codes to enable both codes['ok'] and codes.ok syntax.
    """

    def __init__(self, name=None):
        """
        Initialize LookupDict.
        
        Parameters:
        - name: Optional name for the lookup dict
        """

    def __getitem__(self, key):
        """Get item with fallback to __dict__ lookup."""

    def get(self, key, default=None):
        """
        Get value with default.
        
        Parameters:
        - key: Key to look up
        - default: Default value if key not found
        
        Returns:
        Value or default
        """

    def __repr__(self) -> str:
        """String representation."""
```

## Usage Examples

### CaseInsensitiveDict Usage

```python
import requests
from requests.structures import CaseInsensitiveDict

# CaseInsensitiveDict is used for response headers
response = requests.get('https://httpbin.org/get')
headers = response.headers

# All these access the same header (case-insensitive)
print(headers['Content-Type'])      # Works
print(headers['content-type'])      # Works  
print(headers['CONTENT-TYPE'])      # Works
print(headers['Content-type'])      # Works

# Check header existence (case-insensitive)
print('content-type' in headers)    # True
print('Content-Type' in headers)    # True

# Iterate over headers (preserves original case)
for name, value in headers.items():
    print(f"{name}: {value}")
```

### Manual CaseInsensitiveDict Creation

```python
from requests.structures import CaseInsensitiveDict

# Create from dict
headers = CaseInsensitiveDict({
    'Content-Type': 'application/json',
    'Authorization': 'Bearer token123',
    'User-Agent': 'MyApp/1.0'
})

# Access with any case
print(headers['content-type'])        # 'application/json'
print(headers['AUTHORIZATION'])       # 'Bearer token123'
print(headers['user-agent'])          # 'MyApp/1.0'

# Set with any case
headers['accept'] = 'application/json'
headers['CACHE-CONTROL'] = 'no-cache'

# Check existence (case-insensitive)
print('Accept' in headers)            # True
print('cache-control' in headers)     # True

# Delete with any case
del headers['USER-AGENT']
print('user-agent' in headers)        # False
```

### CaseInsensitiveDict Operations

```python
from requests.structures import CaseInsensitiveDict

# Create from various sources
headers1 = CaseInsensitiveDict([
    ('Content-Type', 'application/json'),
    ('Accept', 'application/json')
])

headers2 = CaseInsensitiveDict(
    authorization='Bearer token',
    user_agent='MyApp/1.0'
)

# Copy dictionary
headers_copy = headers1.copy()
headers_copy['X-Custom'] = 'custom-value'

# Compare dictionaries (case-insensitive)
h1 = CaseInsensitiveDict({'Content-Type': 'application/json'})
h2 = CaseInsensitiveDict({'content-type': 'application/json'})
print(h1 == h2)  # True (case-insensitive comparison)

# Get lowercase items for processing
headers = CaseInsensitiveDict({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer token'
})

for lower_key, value in headers.lower_items():
    print(f"{lower_key}: {value}")
# content-type: application/json
# accept: application/json  
# authorization: Bearer token
```

### LookupDict Usage

```python
import requests

# LookupDict is used for status codes
codes = requests.codes

# Attribute access
print(codes.ok)                    # 200
print(codes.not_found)             # 404
print(codes.internal_server_error) # 500

# Dictionary access  
print(codes['ok'])                 # 200
print(codes['not_found'])          # 404
print(codes['server_error'])       # 500

# Both work the same way
status_code = 404
if status_code == codes.not_found:
    print("Resource not found")

if status_code == codes['not_found']:
    print("Resource not found")
```

### Custom LookupDict

```python
from requests.structures import LookupDict

# Create custom lookup dict
http_methods = LookupDict('HTTP Methods')
http_methods.update({
    'get': 'GET',
    'post': 'POST', 
    'put': 'PUT',
    'delete': 'DELETE',
    'head': 'HEAD',
    'options': 'OPTIONS',
    'patch': 'PATCH'
})

# Use both access methods
print(http_methods.get)        # 'GET'
print(http_methods['post'])    # 'POST'
print(http_methods.delete)     # 'DELETE'

# Get with default
print(http_methods.get('trace', 'TRACE'))  # 'TRACE'
print(http_methods.get('connect'))         # None
```

### Practical Header Management

```python
import requests
from requests.structures import CaseInsensitiveDict

def build_headers(content_type=None, auth_token=None, custom_headers=None):
    """Build headers with case-insensitive handling."""
    headers = CaseInsensitiveDict()
    
    # Set standard headers
    headers['User-Agent'] = 'MyApp/2.0'
    
    if content_type:
        headers['Content-Type'] = content_type
    
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    # Merge custom headers (case-insensitive)
    if custom_headers:
        for key, value in custom_headers.items():
            headers[key] = value
    
    return headers

# Build headers
headers = build_headers(
    content_type='application/json',
    auth_token='abc123',
    custom_headers={
        'x-api-version': '2.0',
        'X-CUSTOM-HEADER': 'custom-value'
    }
)

# Use with request
response = requests.post('https://httpbin.org/post', 
                        headers=headers,
                        json={'key': 'value'})

# Examine sent headers (case preserved)
sent_headers = response.request.headers
for name, value in sent_headers.items():
    print(f"{name}: {value}")
```

### Header Manipulation

```python
import requests
from requests.structures import CaseInsensitiveDict

# Start with response headers
response = requests.get('https://httpbin.org/response-headers?foo=bar')
headers = response.headers

print(f"Original headers: {len(headers)} items")

# Modify headers (case-insensitive)
modified_headers = headers.copy()
modified_headers['cache-control'] = 'no-cache'        # Might overwrite Cache-Control
modified_headers['X-Custom'] = 'custom-value'         # Add new header
del modified_headers['date']                          # Remove Date header

# Use modified headers in new request
new_response = requests.get('https://httpbin.org/headers', 
                           headers=modified_headers)

# Check what was sent
request_headers = new_response.json()['headers']
for name, value in request_headers.items():
    print(f"{name}: {value}")
```

### Session Header Management

```python
import requests
from requests.structures import CaseInsensitiveDict

# Session headers are CaseInsensitiveDict
session = requests.Session()
print(type(session.headers))  # <class 'requests.structures.CaseInsensitiveDict'>

# Set session headers (case-insensitive)
session.headers.update({
    'User-Agent': 'MyApp/1.0',
    'accept': 'application/json',
    'AUTHORIZATION': 'Bearer token123'
})

# Check headers with different cases
print('user-agent' in session.headers)     # True
print(session.headers['Accept'])            # 'application/json'
print(session.headers['authorization'])     # 'Bearer token123'

# Headers persist across requests
response1 = session.get('https://httpbin.org/headers')
response2 = session.post('https://httpbin.org/post', json={'data': 'test'})

# Both requests include the session headers
print("Request 1 headers:", response1.json()['headers'])
print("Request 2 headers:", response2.json()['headers'])
```

### Status Code Management

```python
import requests
from requests.structures import LookupDict

# The codes object is a LookupDict
print(type(requests.codes))  # <class 'requests.structures.LookupDict'>

# Create custom status mappings
api_codes = LookupDict('API Status Codes')
api_codes.update({
    'success': 200,
    'created': 201,
    'accepted': 202,
    'bad_request': 400,
    'unauthorized': 401,
    'forbidden': 403,
    'not_found': 404,
    'server_error': 500
})

# Use in response handling
def handle_api_response(response):
    status = response.status_code
    
    if status == api_codes.success:
        return response.json()
    elif status == api_codes.created:
        print("Resource created")
        return response.json()
    elif status == api_codes.not_found:
        print("Resource not found")
        return None
    elif status == api_codes.server_error:
        print("Server error occurred")
        return None
    else:
        print(f"Unexpected status: {status}")
        return None

# Test with different responses
responses = [
    requests.get('https://httpbin.org/status/200'),
    requests.get('https://httpbin.org/status/404'),
    requests.get('https://httpbin.org/status/500')
]

for resp in responses:
    result = handle_api_response(resp)
    print(f"Status {resp.status_code}: {result}")
```

## Structure Comparison

### Standard Dict vs CaseInsensitiveDict

```python
from requests.structures import CaseInsensitiveDict

# Standard dict - case-sensitive
standard = {'Content-Type': 'application/json'}
print('content-type' in standard)        # False
print('Content-Type' in standard)        # True

# CaseInsensitiveDict - case-insensitive
case_insensitive = CaseInsensitiveDict({'Content-Type': 'application/json'})
print('content-type' in case_insensitive)    # True
print('Content-Type' in case_insensitive)    # True
print('CONTENT-TYPE' in case_insensitive)    # True

# Key preservation
print(list(standard.keys()))              # ['Content-Type']
print(list(case_insensitive.keys()))      # ['Content-Type'] (original case preserved)

# Lowercase iteration
for key, value in case_insensitive.lower_items():
    print(f"Lowercase: {key} -> {value}")  # content-type -> application/json
```

### Standard Dict vs LookupDict

```python
from requests.structures import LookupDict

# Standard dict - item access only
standard = {'ok': 200, 'not_found': 404}
print(standard['ok'])          # 200
# print(standard.ok)           # AttributeError

# LookupDict - both item and attribute access
lookup = LookupDict()
lookup.update({'ok': 200, 'not_found': 404})
print(lookup['ok'])            # 200
print(lookup.ok)               # 200 (attribute access)
print(lookup.not_found)        # 404

# Graceful handling of missing keys
print(lookup.get('missing'))   # None
print(lookup.get('missing', 'default'))  # 'default'
```