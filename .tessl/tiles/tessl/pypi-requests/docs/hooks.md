# Event Hooks

Event hook system that allows custom functions to be called at specific points during request processing. Hooks provide a way to modify requests and responses or implement custom logging and monitoring.

## Capabilities

### Hook System

The requests library provides a simple but powerful hook system for intercepting and modifying HTTP requests and responses.

```python { .api }
# Available hook events
HOOKS: list[str]  # ['response']

def default_hooks() -> dict:
    """
    Return the default hooks structure.
    
    Returns:
    Dict with default hook configuration
    """

def dispatch_hook(key: str, hooks: dict, hook_data, **kwargs):
    """
    Execute hooks for a given event.
    
    Parameters:
    - key: Hook event name
    - hooks: Hook configuration dict
    - hook_data: Data to pass to hook functions
    - **kwargs: Additional arguments for hooks
    
    Returns:
    Result from hook execution
    """
```

### Hook Events

Currently, requests supports one hook event:

- **response**: Called after receiving a response, allows modifying the Response object

## Usage Examples

### Basic Hook Usage

```python
import requests

def response_hook(response, *args, **kwargs):
    """Custom response hook function."""
    print(f"Received response: {response.status_code} from {response.url}")
    # Optionally modify the response
    response.custom_processed = True
    return response

# Add hook to single request
response = requests.get('https://httpbin.org/get', 
                       hooks={'response': response_hook})

print(hasattr(response, 'custom_processed'))  # True
```

### Multiple Hooks

```python
import requests

def log_hook(response, *args, **kwargs):
    """Log response details."""
    print(f"LOG: {response.request.method} {response.url} -> {response.status_code}")
    return response

def timing_hook(response, *args, **kwargs):
    """Add timing information."""
    print(f"TIMING: Request took {response.elapsed.total_seconds():.3f} seconds")
    return response

def validation_hook(response, *args, **kwargs):
    """Validate response."""
    if response.status_code >= 400:
        print(f"WARNING: Error response {response.status_code}")
    return response

# Multiple hooks for the same event
hooks = {
    'response': [log_hook, timing_hook, validation_hook]
}

response = requests.get('https://httpbin.org/status/404', hooks=hooks)
# Prints:
# LOG: GET https://httpbin.org/status/404 -> 404
# TIMING: Request took 0.123 seconds  
# WARNING: Error response 404
```

### Session-Level Hooks

```python
import requests

def session_response_hook(response, *args, **kwargs):
    """Hook applied to all session requests."""
    # Add custom header to all responses
    response.headers['X-Custom-Processed'] = 'true'
    
    # Log all requests
    print(f"Session request: {response.request.method} {response.url}")
    
    return response

# Add hook to session - applies to all requests
session = requests.Session()
session.hooks['response'].append(session_response_hook)

# All requests through this session will trigger the hook
response1 = session.get('https://httpbin.org/get')
response2 = session.post('https://httpbin.org/post', json={'key': 'value'})

print(response1.headers['X-Custom-Processed'])  # 'true'
print(response2.headers['X-Custom-Processed'])  # 'true'
```

### Authentication Hook

```python
import requests
import hashlib
import time

def custom_auth_hook(response, *args, **kwargs):
    """Custom authentication logic."""
    if response.status_code == 401:
        print("Authentication required - could trigger token refresh")
        # In real implementation, might refresh token and retry request
    return response

def rate_limit_hook(response, *args, **kwargs):
    """Handle rate limiting."""
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After', '60')
        print(f"Rate limited. Retry after {retry_after} seconds")
        # Could implement automatic retry with backoff
    return response

# Combine authentication and rate limiting hooks
auth_hooks = {
    'response': [custom_auth_hook, rate_limit_hook]
}

session = requests.Session()
session.hooks = auth_hooks

response = session.get('https://httpbin.org/status/429')
# Prints: Rate limited. Retry after 60 seconds
```

### Request Modification Hook

```python
import requests

def add_user_agent_hook(response, *args, **kwargs):
    """Add custom user agent information to response for logging."""
    original_ua = response.request.headers.get('User-Agent', 'Unknown')
    print(f"Request made with User-Agent: {original_ua}")
    
    # Add metadata to response for later use
    response.user_agent_info = {
        'original_ua': original_ua,
        'timestamp': time.time()
    }
    return response

# Apply hook
response = requests.get('https://httpbin.org/user-agent', 
                       hooks={'response': add_user_agent_hook})

print(response.user_agent_info)
```

### Error Handling Hook

```python
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def error_logging_hook(response, *args, **kwargs):
    """Log errors and add context."""
    if response.status_code >= 400:
        logger.error(f"HTTP Error {response.status_code}: {response.url}")
        logger.error(f"Response: {response.text[:200]}...")
        
        # Add error context to response
        response.error_logged = True
        response.error_timestamp = time.time()
    
    return response

def retry_header_hook(response, *args, **kwargs):
    """Extract retry information from headers."""
    if response.status_code in [429, 503]:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            response.retry_after_seconds = int(retry_after)
            logger.info(f"Server suggests retry after {retry_after} seconds")
    
    return response

# Error handling hook chain
error_hooks = {
    'response': [error_logging_hook, retry_header_hook]
}

response = requests.get('https://httpbin.org/status/503', hooks=error_hooks)
print(f"Error logged: {getattr(response, 'error_logged', False)}")
```

### Performance Monitoring Hook

```python
import requests
import time

class PerformanceMonitor:
    """Performance monitoring via hooks."""
    
    def __init__(self):
        self.stats = {}
    
    def response_hook(self, response, *args, **kwargs):
        """Monitor response performance."""
        url = response.url
        elapsed = response.elapsed.total_seconds()
        status = response.status_code
        size = len(response.content)
        
        # Track stats
        if url not in self.stats:
            self.stats[url] = []
        
        self.stats[url].append({
            'elapsed': elapsed,
            'status': status,
            'size': size,
            'timestamp': time.time()
        })
        
        print(f"PERF: {url} -> {status} ({elapsed:.3f}s, {size} bytes)")
        return response
    
    def get_stats(self):
        """Get performance statistics."""
        return self.stats

# Use performance monitor
monitor = PerformanceMonitor()

session = requests.Session()
session.hooks['response'].append(monitor.response_hook)

# Make several requests
urls = [
    'https://httpbin.org/get',
    'https://httpbin.org/json',
    'https://httpbin.org/html'
]

for url in urls:
    response = session.get(url)

# View stats
stats = monitor.get_stats()
for url, measurements in stats.items():
    avg_time = sum(m['elapsed'] for m in measurements) / len(measurements)
    print(f"Average time for {url}: {avg_time:.3f}s")
```

### Custom Response Processing Hook

```python
import requests
import json

def json_response_hook(response, *args, **kwargs):
    """Automatically parse JSON responses."""
    content_type = response.headers.get('content-type', '')
    
    if 'application/json' in content_type:
        try:
            response.parsed_json = response.json()
            response.json_parsed = True
        except ValueError:
            response.json_parsed = False
            response.parsed_json = None
    else:
        response.json_parsed = False
        response.parsed_json = None
    
    return response

def xml_response_hook(response, *args, **kwargs):
    """Handle XML responses."""
    content_type = response.headers.get('content-type', '')
    
    if 'xml' in content_type:
        response.is_xml = True
        # Could parse XML here with lxml or xml module
    else:
        response.is_xml = False
    
    return response

# Content processing hooks
content_hooks = {
    'response': [json_response_hook, xml_response_hook]
}

response = requests.get('https://httpbin.org/json', hooks=content_hooks)
print(f"JSON parsed: {response.json_parsed}")
print(f"Data: {response.parsed_json}")
```

### Hook Registration Patterns

```python
import requests

# Pattern 1: Direct function assignment
def my_hook(response, *args, **kwargs):
    return response

hooks = {'response': my_hook}

# Pattern 2: List of functions
hooks = {'response': [hook1, hook2, hook3]}

# Pattern 3: Adding to existing hooks
session = requests.Session()
session.hooks['response'].append(my_hook)

# Pattern 4: Replacing all hooks
session.hooks['response'] = [my_hook]

# Pattern 5: Using Request object
req = requests.Request('GET', 'https://httpbin.org/get', hooks=hooks)
prepared = req.prepare()

with requests.Session() as session:
    response = session.send(prepared)
```

## Hook Best Practices

### Hook Function Signature

```python
def my_hook(response, *args, **kwargs):
    """
    Standard hook function signature.
    
    Parameters:
    - response: Response object being processed
    - *args: Additional positional arguments
    - **kwargs: Additional keyword arguments
    
    Returns:
    Modified or original Response object
    """
    # Process response
    return response
```

### Error Handling in Hooks

```python
def safe_hook(response, *args, **kwargs):
    """Hook with proper error handling."""
    try:
        # Hook logic here
        response.custom_data = process_response(response)
    except Exception as e:
        # Log error but don't break the request
        print(f"Hook error: {e}")
        response.hook_error = str(e)
    
    return response
```

### Performance Considerations

```python
def efficient_hook(response, *args, **kwargs):
    """Efficient hook implementation."""
    # Only process if needed
    if should_process(response):
        # Minimal processing
        response.processed = True
    
    return response

def should_process(response):
    """Determine if processing is needed."""
    return response.headers.get('content-type') == 'application/json'
```

## Hook Limitations

1. **Limited Events**: Only 'response' hook is currently supported
2. **No Request Hooks**: Cannot modify requests before sending
3. **Exception Handling**: Hook exceptions can break request processing
4. **Performance Impact**: Hooks add processing overhead
5. **State Management**: Hooks are stateless - use closures or classes for state

## Advanced Hook Patterns

### Hook Factory

```python
def create_logging_hook(logger_name):
    """Factory function to create logging hooks."""
    import logging
    logger = logging.getLogger(logger_name)
    
    def logging_hook(response, *args, **kwargs):
        logger.info(f"{response.request.method} {response.url} -> {response.status_code}")
        return response
    
    return logging_hook

# Create specialized hooks
api_hook = create_logging_hook('api_client')
web_hook = create_logging_hook('web_scraper')

# Use different hooks for different purposes
api_session = requests.Session()
api_session.hooks['response'].append(api_hook)

web_session = requests.Session()  
web_session.hooks['response'].append(web_hook)
```

### Conditional Hooks

```python
def conditional_hook(condition_func):
    """Create a hook that only runs when condition is met."""
    def decorator(hook_func):
        def wrapper(response, *args, **kwargs):
            if condition_func(response):
                return hook_func(response, *args, **kwargs)
            return response
        return wrapper
    return decorator

# Conditional hook decorators
@conditional_hook(lambda r: r.status_code >= 400)
def error_only_hook(response, *args, **kwargs):
    print(f"Error response: {response.status_code}")
    return response

@conditional_hook(lambda r: 'json' in r.headers.get('content-type', ''))
def json_only_hook(response, *args, **kwargs):
    print("Processing JSON response")
    return response
```