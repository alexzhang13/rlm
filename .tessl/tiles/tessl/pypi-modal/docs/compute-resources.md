# Compute Resources

Functions and classes that execute serverless workloads in Modal's cloud infrastructure, including interactive sandboxes for development and debugging.

## Capabilities

### Function Class

Represents a deployed serverless function that can be called remotely, locally, or in parallel across multiple inputs.

```python { .api }
class Function:
    def remote(self, *args, **kwargs):
        """
        Call the function remotely in Modal's cloud.
        
        Parameters:
        - *args: Positional arguments to pass to the function
        - **kwargs: Keyword arguments to pass to the function
        
        Returns:
        Result of the function execution
        """

    def local(self, *args, **kwargs):
        """
        Call the function locally (useful for testing).
        
        Parameters:
        - *args: Positional arguments to pass to the function
        - **kwargs: Keyword arguments to pass to the function
        
        Returns:
        Result of the function execution
        """

    def map(
        self,
        inputs,
        order_outputs: bool = True,
        return_exceptions: bool = False
    ):
        """
        Map the function over a list of inputs in parallel.
        
        Parameters:
        - inputs: Iterable of inputs to map over
        - order_outputs: Whether to return outputs in input order
        - return_exceptions: Include exceptions in results instead of raising
        
        Returns:
        List of results
        """

    def spawn(self, *args, **kwargs):
        """
        Spawn the function asynchronously without waiting for result.
        
        Parameters:
        - *args: Positional arguments to pass to the function
        - **kwargs: Keyword arguments to pass to the function
        
        Returns:
        FunctionCall object for retrieving result later
        """

    @classmethod
    def from_name(
        cls,
        app_name: str,
        tag: str = None,
        namespace: str = None,
        environment_name: str = None
    ):
        """
        Look up a deployed function by name.
        
        Parameters:
        - app_name: Name of the app containing the function
        - tag: Optional deployment tag
        - namespace: Namespace to search in
        - environment_name: Environment name
        
        Returns:
        Function object
        """
```

### FunctionCall Class

Represents an executing or executed function call, providing methods to retrieve results and manage execution.

```python { .api }
class FunctionCall:
    def get(self, timeout: float = None):
        """
        Get the result of the function call, blocking until completion.
        
        Parameters:
        - timeout: Maximum time to wait for result in seconds
        
        Returns:
        Result of the function call
        
        Raises:
        TimeoutError: If timeout is exceeded
        """

    def cancel(self):
        """
        Cancel the running function call.
        
        Returns:
        True if cancellation was successful
        """

    def is_finished(self) -> bool:
        """
        Check if the function call has completed.
        
        Returns:
        True if finished, False otherwise
        """

    @property
    def object_id(self) -> str:
        """
        Get the unique ID of this function call.
        
        Returns:
        Function call ID string
        """
```

### Cls Class

Serverless class for stateful compute with lifecycle methods, enabling persistent state across method calls.

```python { .api }
class Cls:
    @classmethod
    def from_name(
        cls,
        app_name: str,
        tag: str = None,
        namespace: str = None,
        environment_name: str = None
    ):
        """
        Look up a deployed class by name.
        
        Parameters:
        - app_name: Name of the app containing the class
        - tag: Optional deployment tag
        - namespace: Namespace to search in
        - environment_name: Environment name
        
        Returns:
        Cls object
        """

    def lookup(self, method_name: str):
        """
        Look up a specific method of the class.
        
        Parameters:
        - method_name: Name of the method to look up
        
        Returns:
        Method object that can be called remotely
        """
```

### Sandbox Class

Interactive compute environment for development, debugging, and ad-hoc computation.

```python { .api }
class Sandbox:
    @classmethod
    def create(
        cls,
        image: Image = None,
        secrets: list[Secret] = None,
        volumes: dict[str, Volume] = None,
        mounts: list[Mount] = None,
        memory: int = None,
        cpu: float = None,
        gpu: GPU_T = None,
        timeout: int = None,
        workdir: str = "/root",
        **kwargs
    ):
        """
        Create a new interactive sandbox.
        
        Parameters:
        - image: Container image for the sandbox
        - secrets: List of secrets to inject
        - volumes: Dictionary mapping paths to volumes
        - mounts: List of mount objects
        - memory: Memory limit in MB
        - cpu: CPU allocation
        - gpu: GPU configuration
        - timeout: Sandbox timeout in seconds
        - workdir: Working directory
        
        Returns:
        Sandbox instance
        """

    def exec(
        self,
        command: str,
        workdir: str = None,
        secrets: list[Secret] = None,
        **kwargs
    ):
        """
        Execute a command in the sandbox.
        
        Parameters:
        - command: Shell command to execute
        - workdir: Working directory for command
        - secrets: Additional secrets for this command
        
        Returns:
        Command execution result
        """

    def terminate(self):
        """
        Terminate the sandbox, cleaning up all resources.
        """

    def tunnel(self, port: int):
        """
        Create a tunnel to a port in the sandbox.
        
        Parameters:
        - port: Port number to tunnel to
        
        Returns:
        Tunnel URL for accessing the port
        """

    @property
    def object_id(self) -> str:
        """
        Get the unique ID of this sandbox.
        
        Returns:
        Sandbox ID string
        """
```

### SandboxSnapshot Class

Snapshot of a sandbox environment that can be reused to create new sandboxes or deploy as container images.

```python { .api }
class SandboxSnapshot:
    @classmethod
    def create(
        cls,
        sandbox: Sandbox,
        label: str = None
    ):
        """
        Create a snapshot from an existing sandbox.
        
        Parameters:
        - sandbox: Source sandbox to snapshot
        - label: Optional label for the snapshot
        
        Returns:
        SandboxSnapshot instance
        """

    def deploy(self, name: str):
        """
        Deploy the snapshot as a container image.
        
        Parameters:
        - name: Name for the deployed image
        
        Returns:
        Deployed image reference
        """

    @classmethod
    def from_name(
        cls,
        label: str,
        namespace: str = None
    ):
        """
        Look up a snapshot by label.
        
        Parameters:
        - label: Snapshot label
        - namespace: Optional namespace
        
        Returns:
        SandboxSnapshot instance
        """
```

## Usage Examples

### Basic Function Usage

```python
import modal

app = modal.App("compute-example")

@app.function()
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

@app.local_entrypoint()
def main():
    # Call function remotely
    result = fibonacci.remote(10)
    print(f"Fibonacci(10) = {result}")
    
    # Map over multiple inputs
    results = fibonacci.map([1, 2, 3, 4, 5])
    print(f"Results: {results}")
    
    # Spawn async call
    call = fibonacci.spawn(15)
    # Do other work...
    result = call.get()
    print(f"Async result: {result}")
```

### Stateful Class Example

```python
import modal
from modal import enter, exit, method

app = modal.App("stateful-service")

@app.cls()
class DatabaseService:
    @enter()
    def setup(self):
        # Initialize database connection
        self.connection = create_db_connection()
        self.cache = {}
    
    @exit()
    def cleanup(self):
        # Clean up resources
        self.connection.close()
    
    @method()
    def query(self, sql: str):
        if sql in self.cache:
            return self.cache[sql]
        
        result = self.connection.execute(sql)
        self.cache[sql] = result
        return result
    
    @method()
    def insert(self, table: str, data: dict):
        return self.connection.insert(table, data)

@app.local_entrypoint()
def main():
    db = DatabaseService()
    
    # Insert data
    db.insert.remote("users", {"name": "Alice", "email": "alice@example.com"})
    
    # Query data (uses caching)
    users = db.query.remote("SELECT * FROM users")
    print(users)
```

### Interactive Sandbox

```python
import modal

# Create a sandbox with custom environment
sandbox = modal.Sandbox.create(
    image=modal.Image.debian_slim().pip_install("pandas", "matplotlib"),
    timeout=3600  # 1 hour
)

# Execute commands
result = sandbox.exec("python -c 'import pandas; print(pandas.__version__)'")
print(f"Pandas version: {result.stdout}")

# Run a data analysis script
analysis_code = """
import pandas as pd
import matplotlib.pyplot as plt

# Create sample data
data = {'x': range(10), 'y': [i**2 for i in range(10)]}
df = pd.DataFrame(data)

# Create plot
plt.figure(figsize=(8, 6))
plt.plot(df['x'], df['y'])
plt.savefig('/tmp/plot.png')
plt.close()

print("Analysis complete")
"""

result = sandbox.exec(f"python -c \"{analysis_code}\"")
print(result.stdout)

# Terminate when done
sandbox.terminate()
```

### Sandbox Snapshots

```python
import modal

# Create and configure a sandbox
sandbox = modal.Sandbox.create(
    image=modal.Image.debian_slim()
)

# Install custom software
sandbox.exec("apt-get update && apt-get install -y git curl")
sandbox.exec("pip install numpy scipy scikit-learn")

# Create a snapshot
snapshot = modal.SandboxSnapshot.create(sandbox, label="ml-environment")

# Use the snapshot to create new sandboxes
new_sandbox = modal.Sandbox.create(image=snapshot)

# Or deploy as an image for functions
app = modal.App("ml-app")

@app.function(image=snapshot)
def ml_computation(data):
    import numpy as np
    from sklearn.linear_model import LinearRegression
    
    # ML computation using pre-installed libraries
    model = LinearRegression()
    return model.fit(data['X'], data['y']).predict(data['X_test'])
```

### Parallel Processing

```python
import modal

app = modal.App("parallel-processing")

@app.function()
def process_batch(batch_data: list) -> dict:
    # Process a batch of data
    results = {}
    for item in batch_data:
        results[item['id']] = expensive_computation(item['data'])
    return results

@app.local_entrypoint()
def main():
    # Prepare data batches
    all_data = [{'id': i, 'data': f"data_{i}"} for i in range(1000)]
    batches = [all_data[i:i+100] for i in range(0, len(all_data), 100)]
    
    # Process batches in parallel
    batch_results = process_batch.map(batches)
    
    # Combine results
    final_results = {}
    for batch_result in batch_results:
        final_results.update(batch_result)
    
    print(f"Processed {len(final_results)} items")
```