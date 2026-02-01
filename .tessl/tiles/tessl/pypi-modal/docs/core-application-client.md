# Core Application & Client

Primary interfaces for defining applications and managing authentication and object lookup with Modal's cloud platform.

## Capabilities

### App Class

Main application container for defining and deploying Modal functions and resources. All serverless functions, classes, and resources are defined within the context of an App.

```python { .api }
class App:
    def __init__(self, name: str = None):
        """
        Create a new Modal application.
        
        Parameters:
        - name: Optional name for the app. If not provided, a name will be generated.
        """

    def function(
        self,
        image: Optional["Image"] = None,
        schedule: Optional[Union["Cron", "Period"]] = None,
        secrets: Optional[list["Secret"]] = None,
        volumes: Optional[dict[str, "Volume"]] = None,
        network_file_systems: Optional[dict[str, "NetworkFileSystem"]] = None,
        cloud_bucket_mounts: Optional[dict[str, "CloudBucketMount"]] = None,
        memory: Optional[int] = None,
        cpu: Optional[float] = None,
        gpu: Optional[str] = None,
        timeout: Optional[int] = None,
        retries: Optional[Union[int, "Retries"]] = None,
        concurrency_limit: Optional[int] = None,
        allow_concurrent_inputs: Optional[int] = None,
        container_idle_timeout: Optional[int] = None,
        keep_warm: Optional[int] = None,
        **kwargs
    ):
        """
        Decorator to define a serverless function within the app.
        
        Parameters:
        - image: Container image to run the function in
        - schedule: Schedule for automatic execution (Cron or Period)
        - secrets: List of secrets to inject as environment variables
        - volumes: Dictionary mapping mount paths to Volume objects
        - network_file_systems: Dictionary mapping mount paths to NetworkFileSystem objects
        - cloud_bucket_mounts: Dictionary mapping mount paths to CloudBucketMount objects
        - memory: Memory limit in MB
        - cpu: CPU allocation (fractional values supported)
        - gpu: GPU specification string (e.g., "any", "a10g", "h100")
        - timeout: Function timeout in seconds
        - retries: Retry policy for failed executions
        - concurrency_limit: Maximum concurrent executions
        - allow_concurrent_inputs: Allow concurrent inputs per container
        - container_idle_timeout: How long to keep containers warm
        - keep_warm: Number of containers to keep warm
        
        Returns:
        Function decorator
        """

    def cls(
        self,
        image: Image = None,
        secrets: list[Secret] = None,
        volumes: dict[str, Volume] = None,
        mounts: list[Mount] = None,
        memory: int = None,
        cpu: float = None,
        gpu: GPU_T = None,
        timeout: int = None,
        retries: Retries = None,
        concurrency_limit: int = None,
        container_idle_timeout: int = None,
        keep_warm: int = None,
        **kwargs
    ):
        """
        Decorator to define a serverless class within the app.
        
        Parameters:
        - image: Container image to run the class in
        - secrets: List of secrets to inject as environment variables
        - volumes: Dictionary mapping mount paths to Volume objects
        - mounts: List of mount objects for code and data
        - memory: Memory limit in MB
        - cpu: CPU allocation
        - gpu: GPU configuration
        - timeout: Method timeout in seconds
        - retries: Retry policy for failed method calls
        - concurrency_limit: Maximum concurrent class instances
        - container_idle_timeout: How long to keep containers warm
        - keep_warm: Number of containers to keep warm
        
        Returns:
        Class decorator
        """

    def local_entrypoint(self):
        """
        Decorator to define a local entry point that can call remote functions.
        
        The decorated function will run locally and can invoke remote functions
        defined in the same app.
        
        Returns:
        Function decorator
        """

    def deploy(self, name: str = None):
        """
        Deploy the app to Modal cloud.
        
        Parameters:
        - name: Optional deployment name
        
        Returns:
        Deployed app handle
        """

    def run(self, detach: bool = False):
        """
        Run the app, executing the local entrypoint if defined.
        
        Parameters:
        - detach: Run in detached mode
        """

    def stop(self):
        """
        Stop a running app.
        """

    def list_objects(self):
        """
        List all objects (functions, classes, etc.) defined in the app.
        
        Returns:
        List of app objects
        """
```

### Client Class

Client for interacting with Modal's API, managing authentication, and looking up deployed objects.

```python { .api }
class Client:
    @classmethod
    def from_env(
        cls,
        profile: str = None,
        token_id: str = None,
        token_secret: str = None
    ):
        """
        Create a client from environment variables or profile.
        
        Parameters:
        - profile: Named profile to use for authentication
        - token_id: Override token ID from environment
        - token_secret: Override token secret from environment
        
        Returns:
        Authenticated Client instance
        """

    def lookup(
        self,
        label: str,
        namespace: str = None,
        create_if_missing: bool = False
    ):
        """
        Look up a deployed object by label.
        
        Parameters:
        - label: Label of the object to look up
        - namespace: Namespace to search in
        - create_if_missing: Create the object if it doesn't exist
        
        Returns:
        The deployed object
        """

    def list(self, namespace: str = None):
        """
        List objects in the account.
        
        Parameters:
        - namespace: Optional namespace to filter by
        
        Returns:
        List of deployed objects
        """
```

## Usage Examples

### Basic App Definition

```python
import modal

# Create an app
app = modal.App("my-application")

# Define a simple function
@app.function()
def hello(name: str) -> str:
    return f"Hello, {name}!"

# Local entrypoint to test the function
@app.local_entrypoint()
def main():
    result = hello.remote("World")
    print(result)  # "Hello, World!"
```

### App with Custom Configuration

```python
import modal

app = modal.App("data-processor")

# Custom image with dependencies
image = modal.Image.debian_slim().pip_install("pandas", "numpy")

# Function with resource configuration
@app.function(
    image=image,
    memory=2048,  # 2GB memory
    timeout=600,  # 10 minute timeout
    secrets=[modal.Secret.from_name("api-key")],
    volumes={"/data": modal.Volume.from_name("dataset")}
)
def process_data(filename: str):
    import pandas as pd
    df = pd.read_csv(f"/data/{filename}")
    return df.groupby('category').sum().to_dict()

@app.local_entrypoint()
def main():
    result = process_data.remote("sales_data.csv")
    print(result)
```

### Client Usage

```python
import modal

# Create client from environment
client = modal.Client.from_env()

# Look up a deployed function
my_function = client.lookup("my-function")

# Call the remote function
result = my_function.remote("input_data")
```

### Deployment

```python
import modal

app = modal.App("production-app")

@app.function()
def my_function():
    return "Hello from production!"

# Deploy to Modal cloud
if __name__ == "__main__":
    # Deploy the app
    app.deploy("v1.0")
    
    # Or run locally for development
    # app.run()
```