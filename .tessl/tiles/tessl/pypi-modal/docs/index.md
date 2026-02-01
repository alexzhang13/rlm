# Modal

Modal is a Python client library for Modal, a serverless cloud computing platform that enables developers to run Python code in the cloud with on-demand access to compute resources. The library provides a comprehensive toolkit for building, deploying, and managing serverless applications including functions, classes, containers, volumes, secrets, and file systems. It features a rich API for defining cloud resources declaratively, supports parallel execution and distributed computing patterns, includes built-in monitoring and logging capabilities, and provides seamless integration with popular Python frameworks and libraries.

## Package Information

- **Package Name**: modal
- **Language**: Python
- **Installation**: `pip install modal`
- **Python Requirements**: >= 3.9, < 3.14

## Core Imports

```python
import modal
```

Common pattern for accessing main classes:

```python
from modal import App, Image, Secret, Volume
```

Alternative import all public APIs:

```python
from modal import *
```

## Basic Usage

```python
import modal

# Define an application
app = modal.App("my-app")

# Define a custom container image with dependencies
image = modal.Image.debian_slim().pip_install("requests", "beautifulsoup4")

# Define a serverless function
@app.function(image=image)
def scrape_url(url: str) -> str:
    import requests
    from bs4 import BeautifulSoup
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()

# Local entrypoint to run the function
@app.local_entrypoint()
def main():
    result = scrape_url.remote("https://example.com")
    print(result)

# Deploy the app
if __name__ == "__main__":
    app.run()
```

## Architecture

Modal follows a declarative resource model where applications are composed of:

- **App**: Main container that groups functions, classes, and resources
- **Compute Resources**: Functions and Classes that execute in the cloud
- **Infrastructure**: Storage (Volumes, NetworkFileSystem), networking (Proxy, Tunnel), and security (Secret)
- **Images**: Container definitions that specify the runtime environment
- **Scheduling**: Cron jobs and periodic tasks for automated execution

The library uses the synchronicity pattern to provide both synchronous and asynchronous APIs from a single codebase, enabling flexible usage patterns while maintaining type safety.

## Capabilities

### Core Application & Client

Primary interfaces for defining applications and managing authentication with Modal's cloud platform.

```python { .api }
class App:
    def __init__(self, name: str): ...
    def function(self, **kwargs): ...  # Decorator
    def cls(self, **kwargs): ...  # Decorator  
    def local_entrypoint(self): ...  # Decorator
    def deploy(self): ...
    def run(self): ...

class Client:
    @classmethod
    def from_env(cls): ...
    def lookup(self, label: str): ...
```

[Core Application & Client](./core-application-client.md)

### Compute Resources

Functions and classes that execute serverless workloads in Modal's cloud infrastructure.

```python { .api }
class Function:
    def remote(self, *args, **kwargs): ...
    def local(self, *args, **kwargs): ...
    def map(self, inputs): ...
    def spawn(self, *args, **kwargs): ...

class FunctionCall:
    def get(self): ...
    def cancel(self): ...

class Cls:
    @classmethod
    def from_name(cls, label: str): ...
    def lookup(self, name: str): ...

class Sandbox:
    @classmethod
    def create(cls, **kwargs): ...
    def exec(self, command: str): ...
    def terminate(self): ...
```

[Compute Resources](./compute-resources.md)

### Container Images

Container image definitions that specify the runtime environment for functions and classes.

```python { .api }
class Image:
    @classmethod
    def debian_slim(cls, python_version: str = None): ...
    @classmethod
    def from_registry(cls, tag: str): ...
    def pip_install(self, *packages: str): ...
    def run_commands(self, *commands: str): ...
    def copy_local_file(self, local_path: str, remote_path: str): ...
```

[Container Images](./container-images.md)

### Storage & Data

Persistent storage solutions including volumes, network file systems, key-value stores, and cloud bucket mounts.

```python { .api }
class Volume:
    @classmethod
    def from_name(cls, label: str): ...
    @classmethod
    def persist(cls, label: str): ...

class NetworkFileSystem:
    @classmethod  
    def from_name(cls, label: str): ...
    @classmethod
    def persist(cls, label: str): ...

class Dict:
    @classmethod
    def from_name(cls, label: str): ...
    def get(self, key: str): ...
    def put(self, key: str, value): ...
    def pop(self, key: str): ...

class Queue:
    @classmethod
    def from_name(cls, label: str): ...
    def put(self, item): ...
    def get(self): ...
```

[Storage & Data](./storage-data.md)

### Infrastructure Services

Networking, security, and infrastructure services for cloud applications.

```python { .api }
class Secret:
    @classmethod
    def from_name(cls, label: str): ...
    @classmethod
    def from_dict(cls, mapping: dict): ...

class Proxy:
    @classmethod
    def from_name(cls, label: str): ...

class Tunnel:
    @classmethod
    def create(cls, **kwargs): ...

class SchedulerPlacement:
    @classmethod
    def zone(cls, zone: str): ...
```

[Infrastructure Services](./infrastructure-services.md)

### Function Decorators & Helpers

Decorators and helper functions for enhancing function behavior and defining lifecycle methods.

```python { .api }
def method(func): ...
def parameter(name: str, default=None): ...
def enter(func): ...
def exit(func): ...
def batched(max_batch_size: int): ...
def concurrent(func): ...
```

[Function Decorators & Helpers](./function-decorators-helpers.md)

### Web & API Integration

Web application serving capabilities including ASGI, WSGI, and HTTP endpoint support.

```python { .api }
def asgi_app(func): ...
def wsgi_app(func): ...
def web_endpoint(func): ...  
def fastapi_endpoint(func): ...
def web_server(func): ...
```

[Web & API Integration](./web-api-integration.md)

### Scheduling & Reliability

Task scheduling and retry policies for automated and resilient execution.

```python { .api }
class Cron:
    def __init__(self, cron_string: str): ...

class Period:
    @classmethod
    def days(cls, n: int): ...
    @classmethod
    def hours(cls, n: int): ...
    @classmethod
    def minutes(cls, n: int): ...
    @classmethod
    def seconds(cls, n: int): ...

class Retries:
    def __init__(
        self, 
        max_retries: int = 3,
        backoff: float = 2.0,
        initial_delay: float = 1.0
    ): ...
```

[Scheduling & Reliability](./scheduling-reliability.md)

### Runtime Utilities

Utilities for runtime context, debugging, and execution control within Modal functions.

```python { .api }
def current_function_call_id() -> str: ...
def current_input_id() -> str: ...
def is_local() -> bool: ...
def interact(): ...
def enable_output(): ...
def forward(**kwargs): ...
```

[Runtime Utilities](./runtime-utilities.md)

### Utility Classes

General utility classes for error handling, file pattern matching, and package information.

```python { .api }
__version__: str  # Package version

class Error(Exception): ...

class FilePatternMatcher:
    def __init__(self, patterns: list): ...
    def matches(self, path: str) -> bool: ...
```

[Utility Classes](./utility-classes.md)

## Common Patterns

### Function with Custom Environment

```python
import modal

app = modal.App()

@app.function(
    image=modal.Image.debian_slim().pip_install("numpy", "pandas"),
    secrets=[modal.Secret.from_name("my-secret")],
    volumes={"/data": modal.Volume.from_name("my-volume")}
)
def process_data(filename: str):
    import pandas as pd
    df = pd.read_csv(f"/data/{filename}")
    return df.describe().to_dict()
```

### Scheduled Function

```python
from modal import App, Cron

app = App()

@app.function(schedule=Cron("0 0 * * *"))  # Daily at midnight
def daily_report():
    # Generate and send daily report
    print("Running daily report...")
```

### Class with Lifecycle Methods

```python
from modal import App, enter, exit, method

app = App()

@app.cls()
class MyService:
    @enter()
    def setup(self):
        # Initialize resources
        self.client = create_client()
    
    @exit()
    def cleanup(self):
        # Clean up resources
        self.client.close()
    
    @method()
    def process(self, data):
        return self.client.process(data)
```