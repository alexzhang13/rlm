# Requests

Python HTTP for Humans - an elegant and simple HTTP library that abstracts the complexities of making HTTP requests behind a beautiful, simple API. Requests allows you to send HTTP/1.1 requests extremely easily with features like automatic content decoding, connection pooling, cookie persistence, authentication, and comprehensive SSL verification.

## Package Information

- **Package Name**: requests
- **Language**: Python
- **Installation**: `pip install requests`
- **Version**: 2.32.4

## Core Imports

```python
import requests
```

Individual components:

```python
from requests import Session, Request, PreparedRequest, Response, codes
from requests.auth import HTTPBasicAuth, HTTPDigestAuth, HTTPProxyAuth, AuthBase
from requests.exceptions import (
    RequestException, HTTPError, ConnectionError, Timeout, ConnectTimeout, 
    ReadTimeout, URLRequired, TooManyRedirects, SSLError, JSONDecodeError
)
from requests.adapters import HTTPAdapter, BaseAdapter
from requests.structures import CaseInsensitiveDict, LookupDict
from requests.cookies import RequestsCookieJar
```

## Basic Usage

```python
import requests

# Simple GET request
response = requests.get('https://api.github.com/user', auth=('user', 'pass'))
print(response.status_code)
print(response.json())

# POST request with JSON data
data = {'key': 'value'}
response = requests.post('https://httpbin.org/post', json=data)

# Using sessions for persistent settings
session = requests.Session()
session.auth = ('user', 'pass')
session.headers.update({'Custom-Header': 'value'})

response = session.get('https://api.example.com/data')
```

## Architecture

Requests is built around several key components:

- **HTTP Methods**: Simple functions (get, post, put, etc.) that create and send requests
- **Session**: Persistent configuration and connection pooling across requests
- **Request/PreparedRequest**: Request objects representing HTTP requests before sending
- **Response**: Response objects containing server responses with convenient access methods
- **Authentication**: Pluggable authentication handlers for various auth schemes
- **Adapters**: Transport adapters that handle the actual HTTP communication
- **Exceptions**: Comprehensive exception hierarchy for different error conditions

## Capabilities

### HTTP Methods

Core HTTP method functions for making requests with various verbs. These are the primary interface most users interact with.

```python { .api }
def request(method: str, url: str, **kwargs) -> Response: ...
def get(url: str, params=None, **kwargs) -> Response: ...
def post(url: str, data=None, json=None, **kwargs) -> Response: ...
def put(url: str, data=None, **kwargs) -> Response: ...
def patch(url: str, data=None, **kwargs) -> Response: ...
def delete(url: str, **kwargs) -> Response: ...
def head(url: str, **kwargs) -> Response: ...
def options(url: str, **kwargs) -> Response: ...
```

[HTTP Methods](./http-methods.md)

### Sessions

Session objects provide persistent configuration, connection pooling, and cookie persistence across multiple requests.

```python { .api }
class Session:
    def __init__(self): ...
    def request(self, method: str, url: str, **kwargs) -> Response: ...
    def get(self, url: str, **kwargs) -> Response: ...
    def post(self, url: str, **kwargs) -> Response: ...
    def close(self): ...

def session() -> Session: ...
```

[Sessions](./sessions.md)

### Request and Response Objects

Core objects representing HTTP requests and responses with full control over request preparation and response handling.

```python { .api }
class Request:
    def __init__(self, method=None, url=None, headers=None, files=None, 
                 data=None, params=None, auth=None, cookies=None, 
                 hooks=None, json=None): ...
    def prepare(self) -> PreparedRequest: ...

class Response:
    content: bytes
    text: str
    status_code: int
    headers: dict
    cookies: dict
    url: str
    def json(self, **kwargs) -> dict: ...
    def raise_for_status(self): ...
```

[Request and Response Objects](./models.md)

### Authentication

Authentication handlers for various HTTP authentication schemes including Basic, Digest, and custom authentication.

```python { .api }
class HTTPBasicAuth:
    def __init__(self, username: str, password: str): ...

class HTTPDigestAuth:
    def __init__(self, username: str, password: str): ...

class HTTPProxyAuth(HTTPBasicAuth): ...
```

[Authentication](./authentication.md)

### Exception Handling

Comprehensive exception hierarchy for handling various error conditions that can occur during HTTP requests.

```python { .api }
class RequestException(IOError): ...
class HTTPError(RequestException): ...
class ConnectionError(RequestException): ...
class Timeout(RequestException): ...
class ConnectTimeout(ConnectionError, Timeout): ...
class ReadTimeout(Timeout): ...
class URLRequired(RequestException): ...
class TooManyRedirects(RequestException): ...
class SSLError(ConnectionError): ...
```

[Exception Handling](./exceptions.md)

### Status Codes

Convenient access to HTTP status codes through named constants and lookup functionality.

```python { .api }
codes: dict  # Lookup dict for status codes
# Usage: codes.ok == 200, codes['not_found'] == 404
```

[Status Codes](./status-codes.md)

### Cookie Handling

Cookie management functionality providing a dict-like interface for handling HTTP cookies with compatibility for both client and server-side cookie operations.

```python { .api }
class RequestsCookieJar:
    def __init__(self, policy=None): ...
    def get(self, name: str, default=None, domain=None, path=None) -> str: ...
    def set(self, name: str, value: str, **kwargs): ...
    def __getitem__(self, name: str) -> str: ...
    def __setitem__(self, name: str, value: str): ...

def cookiejar_from_dict(cookie_dict: dict, cookiejar=None, overwrite=True): ...
def merge_cookies(cookiejar, cookies): ...
```

[Cookie Handling](./cookies.md)

### Transport Adapters

Transport adapters handle the actual HTTP communication, providing the interface between requests and underlying HTTP libraries.

```python { .api }
class BaseAdapter:
    def send(self, request, stream=False, timeout=None, verify=True, 
             cert=None, proxies=None) -> Response: ...
    def close(self): ...

class HTTPAdapter(BaseAdapter):
    def __init__(self, pool_connections=10, pool_maxsize=10, max_retries=0, 
                 pool_block=False): ...
    def send(self, request, **kwargs) -> Response: ...
    def mount(self, prefix: str, adapter): ...
```

[Transport Adapters](./adapters.md)

### Data Structures

Data structure classes that provide enhanced dictionary interfaces with special behaviors for HTTP-related operations.

```python { .api }
class CaseInsensitiveDict(dict):
    def __init__(self, data=None, **kwargs): ...
    def __getitem__(self, key): ...
    def __setitem__(self, key, value): ...
    def copy(self) -> 'CaseInsensitiveDict': ...

class LookupDict(dict):
    def __init__(self, name=None): ...
    def __getitem__(self, key): ...
    def get(self, key, default=None): ...
```

[Data Structures](./structures.md)

### Event Hooks

Event hook system that allows custom functions to be called at specific points during request processing.

```python { .api }
HOOKS: list[str]  # ['response']

def default_hooks() -> dict: ...
def dispatch_hook(key: str, hooks: dict, hook_data, **kwargs): ...
```

[Event Hooks](./hooks.md)

## Types

```python { .api }
from typing import Dict, Optional, Union, Any, List, Tuple, IO
from datetime import timedelta

# Common type aliases
JSONType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
AuthType = Union[Tuple[str, str], HTTPBasicAuth, HTTPDigestAuth, HTTPProxyAuth, AuthBase]
CookiesType = Union[Dict[str, str], RequestsCookieJar]
HeadersType = Union[Dict[str, str], CaseInsensitiveDict]
ParamsType = Union[Dict[str, str], List[Tuple[str, str]], bytes]
DataType = Union[Dict[str, Any], List[Tuple[str, str]], str, bytes, IO]
FilesType = Dict[str, Union[str, bytes, IO, Tuple[str, Union[str, bytes, IO]], 
                           Tuple[str, Union[str, bytes, IO], str], 
                           Tuple[str, Union[str, bytes, IO], str, Dict[str, str]]]]
ProxiesType = Dict[str, str]
TimeoutType = Union[float, Tuple[float, float]]
VerifyType = Union[bool, str]
CertType = Union[str, Tuple[str, str]]
HooksType = Dict[str, List[callable]]
AdapterType = BaseAdapter
```