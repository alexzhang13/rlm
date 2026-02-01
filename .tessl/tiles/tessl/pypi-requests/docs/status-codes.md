# Status Codes

Convenient access to HTTP status codes through named constants and lookup functionality. The requests library provides a `codes` object that maps common status code names to their numerical values.

## Capabilities

### Status Code Lookup

The `codes` object provides multiple ways to access status codes by name.

```python { .api }
codes: LookupDict
# A lookup dictionary that maps status code names to their numerical values
# Supports both attribute and dictionary-style access
# Multiple names can map to the same status code
# Both upper and lowercase names are supported
```

## Usage Examples

### Basic Status Code Access

```python
import requests

# Access status codes by name
print(requests.codes.ok)                    # 200
print(requests.codes.not_found)             # 404
print(requests.codes.internal_server_error) # 500

# Dictionary-style access
print(requests.codes['ok'])                 # 200
print(requests.codes['not_found'])          # 404
print(requests.codes['server_error'])       # 500

# Case-insensitive access
print(requests.codes.OK)                    # 200
print(requests.codes.Ok)                    # 200
print(requests.codes.okay)                  # 200
```

### Status Code Checking

```python
import requests

response = requests.get('https://httpbin.org/status/200')

# Check specific status codes
if response.status_code == requests.codes.ok:
    print("Request successful")

if response.status_code == requests.codes.not_found:
    print("Resource not found")

# Check for success range
if 200 <= response.status_code < 300:
    print("Success")

# Using response.ok property (shorthand for status < 400)
if response.ok:
    print("Request successful")
```

### Status Code Categories

```python
import requests

def categorize_status(status_code):
    """Categorize HTTP status codes."""
    if 100 <= status_code < 200:
        return "Informational"
    elif 200 <= status_code < 300:
        return "Success"
    elif 300 <= status_code < 400:
        return "Redirection"
    elif 400 <= status_code < 500:
        return "Client Error"
    elif 500 <= status_code < 600:
        return "Server Error"
    else:
        return "Unknown"

response = requests.get('https://httpbin.org/status/404')
category = categorize_status(response.status_code)
print(f"Status {response.status_code} is a {category}")
```

### Common Status Code Names

```python
import requests

# Informational (1xx)
codes.continue_                  # 100
codes.switching_protocols        # 101
codes.processing                 # 102

# Success (2xx)
codes.ok                        # 200
codes.okay                      # 200 (alias)
codes.all_ok                    # 200 (alias)
codes.all_good                  # 200 (alias)
codes['\\o/']                   # 200 (fun alias)
codes['✓']                      # 200 (checkmark alias)
codes.created                   # 201
codes.accepted                  # 202
codes.no_content               # 204

# Redirection (3xx)
codes.multiple_choices         # 300
codes.moved_permanently        # 301
codes.moved                    # 301 (alias)
codes.found                    # 302
codes.see_other                # 303
codes.not_modified             # 304
codes.temporary_redirect       # 307
codes.permanent_redirect       # 308

# Client Error (4xx)
codes.bad_request              # 400
codes.unauthorized             # 401
codes.forbidden                # 403
codes.not_found                # 404
codes.method_not_allowed       # 405
codes.not_acceptable           # 406
codes.request_timeout          # 408
codes.conflict                 # 409
codes.gone                     # 410
codes.precondition_failed      # 412
codes.request_entity_too_large # 413
codes.unsupported_media_type   # 415
codes.too_many_requests        # 429

# Server Error (5xx)
codes.internal_server_error    # 500
codes.server_error             # 500 (alias)
codes.not_implemented          # 501
codes.bad_gateway              # 502
codes.service_unavailable      # 503
codes.gateway_timeout          # 504
```

### Response Status Checking with Codes

```python
import requests

def handle_response(response):
    """Handle response based on status code."""
    
    if response.status_code == requests.codes.ok:
        return response.json()
    
    elif response.status_code == requests.codes.created:
        print("Resource created successfully")
        return response.json()
    
    elif response.status_code == requests.codes.no_content:
        print("Operation successful, no content returned")
        return None
    
    elif response.status_code == requests.codes.not_modified:
        print("Resource not modified, using cached version")
        return None
    
    elif response.status_code == requests.codes.bad_request:
        print("Bad request - check your parameters")
        return None
    
    elif response.status_code == requests.codes.unauthorized:
        print("Authentication required")
        return None
    
    elif response.status_code == requests.codes.forbidden:
        print("Access forbidden")
        return None
    
    elif response.status_code == requests.codes.not_found:
        print("Resource not found")
        return None
    
    elif response.status_code == requests.codes.too_many_requests:
        print("Rate limit exceeded")
        return None
    
    elif response.status_code == requests.codes.internal_server_error:
        print("Internal server error")
        return None
    
    elif response.status_code == requests.codes.service_unavailable:
        print("Service temporarily unavailable")
        return None
    
    else:
        print(f"Unexpected status code: {response.status_code}")
        return None

# Usage
response = requests.get('https://api.example.com/data')
data = handle_response(response)
```

### Status Code Comparison

```python
import requests

response = requests.get('https://httpbin.org/status/200')

# Multiple ways to check for success
if response.status_code == 200:
    print("Success (numeric)")

if response.status_code == requests.codes.ok:
    print("Success (using codes)")

if response.ok:
    print("Success (using ok property)")

# Check for specific error conditions
if response.status_code in [requests.codes.unauthorized, requests.codes.forbidden]:
    print("Authentication or authorization error")

# Check ranges
if 400 <= response.status_code < 500:
    print("Client error")
elif 500 <= response.status_code < 600:
    print("Server error")
```

### Custom Status Code Handling

```python
import requests

class StatusHandler:
    """Custom status code handler."""
    
    @staticmethod
    def is_success(status_code):
        """Check if status code indicates success."""
        return 200 <= status_code < 300
    
    @staticmethod
    def is_redirect(status_code):
        """Check if status code indicates redirect."""
        return status_code in [
            requests.codes.moved_permanently,
            requests.codes.found,
            requests.codes.see_other,
            requests.codes.temporary_redirect,
            requests.codes.permanent_redirect
        ]
    
    @staticmethod
    def is_client_error(status_code):
        """Check if status code indicates client error."""
        return 400 <= status_code < 500
    
    @staticmethod
    def is_server_error(status_code):
        """Check if status code indicates server error."""
        return 500 <= status_code < 600
    
    @staticmethod
    def should_retry(status_code):
        """Determine if request should be retried based on status."""
        retry_codes = [
            requests.codes.request_timeout,
            requests.codes.too_many_requests,
            requests.codes.internal_server_error,
            requests.codes.bad_gateway,
            requests.codes.service_unavailable,
            requests.codes.gateway_timeout
        ]
        return status_code in retry_codes

# Usage
response = requests.get('https://api.example.com/data')
handler = StatusHandler()

if handler.is_success(response.status_code):
    data = response.json()
elif handler.should_retry(response.status_code):
    print("Should retry this request")
elif handler.is_client_error(response.status_code):
    print("Client error - check request")
else:
    print("Unexpected status code")
```

### Status Code Logging

```python
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def logged_request(url):
    """Make request with detailed status logging."""
    try:
        response = requests.get(url)
        
        # Log status information
        if response.status_code == requests.codes.ok:
            logger.info(f"Request successful: {response.status_code}")
        elif 300 <= response.status_code < 400:
            logger.info(f"Redirect: {response.status_code} -> {response.headers.get('Location', 'Unknown')}")
        elif 400 <= response.status_code < 500:
            logger.warning(f"Client error: {response.status_code} - {response.reason}")
        elif 500 <= response.status_code < 600:
            logger.error(f"Server error: {response.status_code} - {response.reason}")
        else:
            logger.info(f"Unexpected status: {response.status_code}")
        
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

# Usage
response = logged_request('https://httpbin.org/status/404')
```

## Complete Status Code Reference

The `codes` object includes mappings for all standard HTTP status codes with multiple name variations:

### Informational (1xx)
- `continue` (100)
- `switching_protocols` (101)
- `processing` (102)

### Success (2xx)
- `ok`, `okay`, `all_ok`, `all_good`, `\\o/`, `✓` (200)
- `created` (201)
- `accepted` (202)
- `no_content` (204)
- `partial_content` (206)

### Redirection (3xx)
- `moved_permanently`, `moved` (301)
- `found` (302)
- `see_other`, `other` (303)
- `not_modified` (304)
- `temporary_redirect` (307)
- `permanent_redirect` (308)

### Client Error (4xx)
- `bad_request` (400)
- `unauthorized` (401)
- `forbidden` (403)
- `not_found` (404)
- `method_not_allowed` (405)
- `request_timeout` (408)
- `conflict` (409)
- `gone` (410)
- `too_many_requests` (429)

### Server Error (5xx)
- `internal_server_error`, `server_error` (500)
- `not_implemented` (501)
- `bad_gateway` (502)
- `service_unavailable` (503)
- `gateway_timeout` (504)

Many codes have multiple aliases - both the formal name and common variations are supported.