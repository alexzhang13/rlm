# Runtime Utilities

Modal provides essential runtime utilities for execution context awareness, debugging, output control, and network tunneling within Modal functions. These utilities enable functions to understand their execution environment and provide enhanced debugging and development capabilities.

## Capabilities

### Execution Context Functions

Functions for understanding the current execution context and accessing runtime information.

```python { .api }
def current_function_call_id() -> Optional[str]:
    """Get the ID of the currently executing function call"""

def current_input_id() -> Optional[str]:
    """Get the ID of the current function input"""

def is_local() -> bool:
    """Check if code is running locally vs in Modal cloud"""
```

#### Usage Examples

```python
import modal

app = modal.App("context-aware")

@app.function()
def context_aware_function(data: str):
    """Function that uses runtime context information"""
    
    # Check execution environment
    if modal.is_local():
        print("Running locally - using development configuration")
        debug_mode = True
        log_level = "DEBUG"
    else:
        print("Running in Modal cloud - using production configuration")
        debug_mode = False
        log_level = "INFO"
    
    # Get runtime identifiers
    call_id = modal.current_function_call_id()
    input_id = modal.current_input_id()
    
    print(f"Function call ID: {call_id}")
    print(f"Input ID: {input_id}")
    
    # Use context for logging and tracing
    log_entry = {
        "timestamp": time.time(),
        "function_call_id": call_id,
        "input_id": input_id,
        "environment": "local" if modal.is_local() else "cloud",
        "data": data,
        "debug_mode": debug_mode
    }
    
    # Process data with context-aware behavior
    if debug_mode:
        result = process_with_detailed_logging(data, log_entry)
    else:
        result = process_efficiently(data, log_entry)
    
    return {
        "result": result,
        "call_id": call_id,
        "input_id": input_id,
        "environment": "local" if modal.is_local() else "cloud"
    }

@app.local_entrypoint()
def main():
    # Test locally
    local_result = context_aware_function("local_test_data")
    print("Local result:", local_result)
    
    # Test in cloud
    cloud_result = context_aware_function.remote("cloud_test_data")
    print("Cloud result:", cloud_result)
```

### Interactive Debugging

Function for enabling interactive debugging sessions within Modal containers.

```python { .api }
def interact() -> None:
    """Start an interactive debugging session (only works in Modal containers)"""
```

#### Usage Examples

```python
import modal

app = modal.App("debugging")

@app.function()
def debug_function(data: dict):
    """Function with interactive debugging capabilities"""
    
    print("Starting data processing...")
    
    # Process first part
    intermediate_result = preprocess_data(data)
    
    # Interactive debugging point
    if should_debug(data):
        print("Entering interactive debugging mode...")
        print("Available variables: data, intermediate_result")
        print("Type 'continue' or Ctrl+D to exit debugging")
        
        # This opens an interactive Python shell inside the container
        modal.interact()
    
    # Continue processing after debugging
    final_result = postprocess_data(intermediate_result)
    
    return final_result

def should_debug(data: dict) -> bool:
    """Determine if debugging should be enabled"""
    # Enable debugging for specific conditions
    return (
        data.get("debug_flag", False) or
        data.get("complexity_score", 0) > 0.8 or
        "error_prone_input" in str(data)
    )

@app.local_entrypoint()
def main():
    # Normal execution
    result1 = debug_function.remote({"value": 42})
    print("Normal result:", result1)
    
    # Execution with debugging
    result2 = debug_function.remote({
        "value": 42,
        "debug_flag": True,
        "complex_data": [1, 2, 3, 4, 5]
    })
    print("Debug result:", result2)
```

### Output Control

Function for controlling output display and progress indicators during Modal function execution.

```python { .api }
def enable_output(show_progress: bool = True) -> None:
    """Enable output streaming for functions (context manager)"""
```

#### Usage Examples

```python
import modal

app = modal.App("output-control")

@app.function()
def processing_function(items: list[str]) -> list[str]:
    """Function that processes items with output"""
    results = []
    
    print("Starting batch processing...")
    
    for i, item in enumerate(items):
        # Print progress
        print(f"Processing item {i+1}/{len(items)}: {item}")
        
        # Simulate processing
        result = expensive_operation(item)
        results.append(result)
        
        # Periodic status updates
        if (i + 1) % 10 == 0:
            print(f"Completed {i+1} items, {len(items) - i - 1} remaining")
    
    print("Batch processing completed!")
    return results

@app.function()
def map_processing_function(item: str) -> str:
    """Function for use with map() that shows progress"""
    print(f"Processing: {item}")
    result = complex_processing(item)
    print(f"Completed: {item} -> {result}")
    return result

@app.local_entrypoint()
def main():
    # Enable output to see function logs and progress
    with modal.enable_output(show_progress=True):
        
        # Single function with output
        items = [f"item_{i}" for i in range(50)]
        batch_result = processing_function.remote(items)
        print(f"Batch processing completed: {len(batch_result)} results")
        
        # Map with progress tracking
        map_items = [f"map_item_{i}" for i in range(20)]
        map_results = list(map_processing_function.map(map_items))
        print(f"Map processing completed: {len(map_results)} results")

# Alternative: Enable output for specific operations
@app.local_entrypoint()
def selective_output():
    """Enable output only for specific operations"""
    
    # Normal execution (no output)
    quiet_result = processing_function.remote([f"quiet_{i}" for i in range(5)])
    
    # With output enabled
    with modal.enable_output():
        verbose_result = processing_function.remote([f"verbose_{i}" for i in range(5)])
    
    print("Selective output demo completed")
```

### Network Tunneling

Function for forwarding network traffic through tunnels, enabling secure connections to remote services.

```python { .api }
def forward(port: int, *, host: str = "localhost") -> str:
    """Forward network traffic through tunnel"""
```

#### Usage Examples

```python
import modal

app = modal.App("network-tunneling")

@app.function()
def tunnel_database_connection():
    """Connect to database through network tunnel"""
    
    # Forward database port through tunnel
    tunnel_url = modal.forward(5432, host="internal-database.company.com")
    
    print(f"Database tunnel established: {tunnel_url}")
    
    # Connect to database through tunnel
    import psycopg2
    connection = psycopg2.connect(
        host=tunnel_url.split("://")[1].split(":")[0],
        port=int(tunnel_url.split(":")[-1]),
        database="production_db",
        user="app_user",
        password=os.environ["DB_PASSWORD"]
    )
    
    # Use the connection
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    connection.close()
    return {"user_count": count, "tunnel_url": tunnel_url}

@app.function()
def tunnel_api_access():
    """Access internal API through tunnel"""
    
    # Forward API port
    api_tunnel = modal.forward(8080, host="internal-api.company.com")
    
    print(f"API tunnel established: {api_tunnel}")
    
    # Make requests through tunnel
    import requests
    response = requests.get(f"{api_tunnel}/api/v1/data")
    
    return {
        "api_response": response.json(),
        "status_code": response.status_code,
        "tunnel_url": api_tunnel
    }

@app.function()
def multi_service_tunneling():
    """Connect to multiple services through tunnels"""
    
    # Set up multiple tunnels
    database_tunnel = modal.forward(5432, host="db.internal")
    redis_tunnel = modal.forward(6379, host="redis.internal")
    elasticsearch_tunnel = modal.forward(9200, host="es.internal")
    
    services = {
        "database": database_tunnel,
        "redis": redis_tunnel,
        "elasticsearch": elasticsearch_tunnel
    }
    
    print("All tunnels established:")
    for service, url in services.items():
        print(f"  {service}: {url}")
    
    # Use services through tunnels
    results = {}
    
    # Database query
    db_result = query_database_through_tunnel(database_tunnel)
    results["database"] = db_result
    
    # Redis operation
    redis_result = access_redis_through_tunnel(redis_tunnel)
    results["redis"] = redis_result
    
    # Elasticsearch search
    es_result = search_elasticsearch_through_tunnel(elasticsearch_tunnel)
    results["elasticsearch"] = es_result
    
    return {
        "results": results,
        "tunnels": services
    }

def query_database_through_tunnel(tunnel_url: str) -> dict:
    """Helper function to query database through tunnel"""
    # Extract host and port from tunnel URL
    host = tunnel_url.split("://")[1].split(":")[0]
    port = int(tunnel_url.split(":")[-1])
    
    # Connect and query
    connection = create_db_connection(host, port)
    cursor = connection.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    connection.close()
    
    return {"version": version, "status": "connected"}

def access_redis_through_tunnel(tunnel_url: str) -> dict:
    """Helper function to access Redis through tunnel"""
    import redis
    
    host = tunnel_url.split("://")[1].split(":")[0]
    port = int(tunnel_url.split(":")[-1])
    
    client = redis.Redis(host=host, port=port)
    client.set("tunnel_test", "success")
    value = client.get("tunnel_test").decode()
    
    return {"test_value": value, "status": "connected"}

@app.local_entrypoint()
def main():
    # Test database tunnel
    db_result = tunnel_database_connection.remote()
    print("Database tunnel result:", db_result)
    
    # Test API tunnel
    api_result = tunnel_api_access.remote()
    print("API tunnel result:", api_result)
    
    # Test multiple tunnels
    multi_result = multi_service_tunneling.remote()
    print("Multi-service tunnel result:", multi_result)
```

## Advanced Runtime Patterns

### Context-Aware Error Handling

```python
import modal

app = modal.App("context-error-handling")

@app.function()
def robust_function(data: dict):
    """Function with context-aware error handling"""
    
    call_id = modal.current_function_call_id()
    input_id = modal.current_input_id()
    is_local_env = modal.is_local()
    
    error_context = {
        "call_id": call_id,
        "input_id": input_id,
        "environment": "local" if is_local_env else "cloud",
        "timestamp": time.time()
    }
    
    try:
        result = risky_operation(data)
        return {"success": True, "result": result, "context": error_context}
        
    except Exception as e:
        # Enhanced error information with runtime context
        error_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "context": error_context,
            "data_summary": {
                "size": len(str(data)),
                "keys": list(data.keys()) if isinstance(data, dict) else None
            }
        }
        
        # Different handling based on environment
        if is_local_env:
            print("Local error - entering debug mode")
            print(f"Error context: {error_info}")
            modal.interact()  # Interactive debugging in local mode
        else:
            print("Cloud error - logging and continuing")
            log_error_to_monitoring_system(error_info)
        
        return {"success": False, "error": error_info}
```

### Distributed Tracing with Context

```python
import modal

app = modal.App("distributed-tracing")

# Shared tracing storage
trace_store = modal.Dict.persist("trace-data")

@app.function()
def traced_function_a(data: str):
    """First function in trace chain"""
    
    call_id = modal.current_function_call_id()
    trace_id = f"trace_{int(time.time())}"
    
    # Start trace
    trace_entry = {
        "trace_id": trace_id,
        "function": "traced_function_a",
        "call_id": call_id,
        "start_time": time.time(),
        "input_data": data
    }
    
    print(f"Starting trace {trace_id} in function A")
    
    # Process data
    result_a = process_step_a(data)
    
    # Call next function with trace context
    result_b = traced_function_b.remote(result_a, trace_id)
    
    # Complete trace entry
    trace_entry.update({
        "end_time": time.time(),
        "result": "completed",
        "next_call": "traced_function_b"
    })
    
    # Store trace data
    trace_store[f"{trace_id}_function_a"] = trace_entry
    
    return {"result": result_b, "trace_id": trace_id}

@app.function()
def traced_function_b(data: str, trace_id: str):
    """Second function in trace chain"""
    
    call_id = modal.current_function_call_id()
    
    trace_entry = {
        "trace_id": trace_id,
        "function": "traced_function_b",
        "call_id": call_id,
        "start_time": time.time(),
        "input_data": data
    }
    
    print(f"Continuing trace {trace_id} in function B")
    
    # Process data
    result = process_step_b(data)
    
    # Complete trace
    trace_entry.update({
        "end_time": time.time(),
        "result": result
    })
    
    trace_store[f"{trace_id}_function_b"] = trace_entry
    
    return result

@app.function()
def get_trace_summary(trace_id: str):
    """Get complete trace summary"""
    
    # Collect all trace entries
    trace_entries = {}
    for key in trace_store.keys():
        if key.startswith(trace_id):
            trace_entries[key] = trace_store.get(key)
    
    # Calculate trace metrics
    start_times = [entry["start_time"] for entry in trace_entries.values()]
    end_times = [entry["end_time"] for entry in trace_entries.values()]
    
    total_duration = max(end_times) - min(start_times)
    
    return {
        "trace_id": trace_id,
        "total_duration": total_duration,
        "function_count": len(trace_entries),
        "entries": trace_entries
    }

@app.local_entrypoint()
def main():
    with modal.enable_output():
        # Execute traced function chain
        result = traced_function_a.remote("test_data")
        
        # Get trace summary
        trace_summary = get_trace_summary.remote(result["trace_id"])
        print("Trace summary:", trace_summary)
```

### Development vs Production Runtime

```python
import modal

app = modal.App("environment-aware")

@app.function()
def environment_aware_processing(data: dict):
    """Function that adapts behavior based on runtime environment"""
    
    is_local_env = modal.is_local()
    call_id = modal.current_function_call_id()
    
    # Environment-specific configuration
    if is_local_env:
        config = {
            "timeout": 30,
            "retries": 1,
            "logging_level": "DEBUG",
            "use_cache": False,
            "external_apis": "staging"
        }
        print("Using development configuration")
    else:
        config = {
            "timeout": 300,
            "retries": 3,
            "logging_level": "INFO", 
            "use_cache": True,
            "external_apis": "production"
        }
        print("Using production configuration")
    
    print(f"Processing with config: {config}")
    print(f"Call ID: {call_id}")
    
    # Adaptive processing based on environment
    try:
        if config["use_cache"]:
            # Check cache first in production
            cached_result = check_cache(data)
            if cached_result:
                return {"result": cached_result, "source": "cache", "config": config}
        
        # Process with environment-specific settings
        result = process_with_config(data, config)
        
        if config["use_cache"]:
            # Cache result in production
            store_in_cache(data, result)
        
        return {"result": result, "source": "computed", "config": config}
        
    except Exception as e:
        error_info = {
            "error": str(e),
            "environment": "local" if is_local_env else "production",
            "call_id": call_id,
            "config": config
        }
        
        if is_local_env:
            # More verbose error handling in development
            print(f"Development error: {error_info}")
            modal.interact()  # Debug interactively
            
        return {"error": error_info, "success": False}

def process_with_config(data: dict, config: dict):
    """Process data with environment-specific configuration"""
    
    # Simulate processing with different timeouts
    import time
    processing_time = min(config["timeout"] / 10, 5)  # Simulate work
    time.sleep(processing_time)
    
    # Different API endpoints based on environment
    api_base = f"https://api-{config['external_apis']}.example.com"
    
    return {
        "processed_data": f"processed_{data}",
        "api_used": api_base,
        "processing_time": processing_time
    }

@app.local_entrypoint()
def main():
    test_data = {"input": "test_value", "timestamp": time.time()}
    
    with modal.enable_output():
        # This will use development config when run locally
        local_result = environment_aware_processing(test_data)
        print("Local result:", local_result)
        
        # This will use production config when run in Modal cloud
        cloud_result = environment_aware_processing.remote(test_data)
        print("Cloud result:", cloud_result)
```