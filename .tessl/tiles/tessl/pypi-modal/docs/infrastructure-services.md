# Infrastructure Services

Modal provides essential infrastructure services for networking, security, and resource management. These services enable secure communication, secret management, network connectivity, and fine-grained control over where functions execute.

## Capabilities

### Secret - Secure Environment Variable Management

Secure storage and injection of environment variables, API keys, database credentials, and other sensitive data into Modal functions.

```python { .api }
class Secret:
    @classmethod
    def from_name(cls, label: str, *, environment_name: Optional[str] = None) -> "Secret":
        """Load a Secret by its unique name"""
    
    @classmethod
    def from_dict(
        cls, 
        env_dict: dict[str, Optional[str]], 
        *, 
        name: Optional[str] = None
    ) -> "Secret":
        """Create a Secret from a dictionary of environment variables"""
    
    @classmethod
    def from_dotenv(cls, path: Optional[str] = None) -> "Secret":
        """Create a Secret from a .env file"""

class SecretInfo:
    """Information about a Secret object"""
    name: Optional[str]
    created_at: datetime
    created_by: Optional[str]
```

#### Usage Examples

```python
import modal

app = modal.App()

# Create secret from dictionary
db_secret = modal.Secret.from_dict({
    "DATABASE_URL": "postgresql://user:pass@host:5432/db",
    "DATABASE_PASSWORD": "secure_password",
    "API_KEY": "your_api_key_here"
})

# Load existing secret by name
api_secret = modal.Secret.from_name("openai-api-key")

@app.function(secrets=[db_secret, api_secret])
def database_operation():
    import os
    
    # Access secret values as environment variables
    db_url = os.environ["DATABASE_URL"]
    api_key = os.environ["API_KEY"]
    
    # Use secrets in your code
    connection = create_database_connection(db_url)
    client = APIClient(api_key)
    
    return process_data(connection, client)

# Create secret from .env file
@app.local_entrypoint()
def main():
    # Load secrets from local .env file
    local_secrets = modal.Secret.from_dotenv(".env")
    
    # Deploy function with secrets
    result = database_operation.remote()
    print(result)
```

### Proxy - Static Outbound IP Address

Proxy objects provide Modal containers with static outbound IP addresses for connecting to services that require IP whitelisting.

```python { .api }
class Proxy:
    @classmethod
    def from_name(cls, name: str, *, environment_name: Optional[str] = None) -> "Proxy":
        """Reference a Proxy by its name (must be provisioned via Dashboard)"""
```

#### Usage Examples

```python
import modal

app = modal.App()

# Reference proxy created in Modal Dashboard
proxy = modal.Proxy.from_name("production-proxy")

@app.function(proxy=proxy)
def connect_to_whitelisted_service():
    import requests
    
    # This request will come from the proxy's static IP
    response = requests.get("https://api.partner.com/data")
    
    # The partner service sees requests from the proxy's static IP
    # which can be added to their IP whitelist
    return response.json()

# Multiple functions can share the same proxy
@app.function(proxy=proxy)
def another_whitelisted_operation():
    # Also uses the same static IP
    return make_api_call()
```

### Tunnel - Network Tunnel for Remote Services

Network tunnels enable secure connections between Modal functions and remote services, useful for development and accessing services behind firewalls.

```python { .api }
class Tunnel:
    @classmethod
    def create(
        cls,
        *,
        host: str = "0.0.0.0",
        port: int = 8000,
        timeout: Optional[int] = None
    ) -> "Tunnel":
        """Create a network tunnel"""

def forward(port: int, *, host: str = "localhost") -> str:
    """Forward network traffic through tunnel (utility function)"""
```

#### Usage Examples

```python
import modal

app = modal.App()

@app.function()
def create_development_tunnel():
    # Create tunnel for development access
    tunnel = modal.Tunnel.create(port=8000)
    
    # Start a simple web server
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    
    server = HTTPServer(("0.0.0.0", 8000), SimpleHTTPRequestHandler)
    print(f"Server accessible via tunnel: {tunnel.url}")
    
    # Server runs and is accessible through tunnel
    server.serve_forever()

@app.function()
def connect_through_tunnel():
    # Forward local service through tunnel
    tunnel_url = modal.forward(5432, host="database.internal")
    
    # Connect to database through tunnel
    connection = create_connection(tunnel_url)
    return query_database(connection)
```

### SchedulerPlacement - Control Function Placement

Control where functions are scheduled to run, enabling optimization for latency, compliance, or resource availability.

```python { .api }
class SchedulerPlacement:
    @classmethod
    def zone(cls, zone: str) -> "SchedulerPlacement":
        """Set preferred zone/region for function execution"""
```

#### Usage Examples

```python
import modal

app = modal.App()

# Place functions in specific zones for latency optimization
us_east_placement = modal.SchedulerPlacement.zone("us-east-1")
eu_placement = modal.SchedulerPlacement.zone("eu-west-1")

@app.function(scheduler_placement=us_east_placement)
def process_us_data():
    # This function will preferentially run in us-east-1
    # for low latency to US-based services
    return fetch_and_process_us_data()

@app.function(scheduler_placement=eu_placement)
def process_eu_data():
    # This function will preferentially run in eu-west-1
    # for GDPR compliance and low latency to EU services
    return fetch_and_process_eu_data()

@app.function()
def coordinator():
    # Start processing in appropriate regions
    us_result = process_us_data.spawn()
    eu_result = process_eu_data.spawn()
    
    # Collect results
    return {
        "us": us_result.get(),
        "eu": eu_result.get()
    }
```

## Infrastructure Patterns

### Multi-Environment Secret Management

```python
import modal

app = modal.App()

# Different secrets for different environments
dev_secrets = modal.Secret.from_dict({
    "DATABASE_URL": "postgresql://localhost:5432/dev_db",
    "API_ENDPOINT": "https://api-dev.example.com",
    "DEBUG": "true"
})

prod_secrets = modal.Secret.from_name("production-secrets")

# Environment-specific function deployment
@app.function(secrets=[dev_secrets])
def dev_function():
    return process_with_dev_config()

@app.function(secrets=[prod_secrets])
def prod_function():
    return process_with_prod_config()
```

### Secure Multi-Service Integration

```python
import modal

app = modal.App()

# Multiple secrets for different services
database_secret = modal.Secret.from_name("postgres-credentials")
api_secret = modal.Secret.from_name("external-api-keys")
cloud_secret = modal.Secret.from_name("aws-credentials")

# Static IP for whitelisted services
proxy = modal.Proxy.from_name("main-proxy")

@app.function(
    secrets=[database_secret, api_secret, cloud_secret],
    proxy=proxy
)
def integrated_data_pipeline():
    import os
    import boto3
    import psycopg2
    import requests
    
    # Database connection using secret
    db_conn = psycopg2.connect(os.environ["DATABASE_URL"])
    
    # AWS client using secret
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
    )
    
    # API call using secret and proxy (for static IP)
    headers = {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}
    response = requests.get("https://api.partner.com/data", headers=headers)
    
    # Process data across all services
    data = response.json()
    processed = transform_data(data)
    
    # Store in database
    store_in_database(db_conn, processed)
    
    # Backup to S3
    backup_to_s3(s3_client, processed)
    
    return {"status": "success", "records": len(processed)}
```

### Geographically Distributed Processing

```python
import modal

app = modal.App()

# Regional placement for compliance and latency
us_placement = modal.SchedulerPlacement.zone("us-east-1")
eu_placement = modal.SchedulerPlacement.zone("eu-west-1")
asia_placement = modal.SchedulerPlacement.zone("ap-southeast-1")

# Regional secrets for compliance
us_secrets = modal.Secret.from_name("us-compliance-keys")
eu_secrets = modal.Secret.from_name("eu-gdpr-keys")
asia_secrets = modal.Secret.from_name("asia-keys")

@app.function(
    scheduler_placement=us_placement,
    secrets=[us_secrets]
)
def process_us_customer_data(customer_ids: list[str]):
    # Process US customer data in US region for compliance
    return [process_customer(id) for id in customer_ids]

@app.function(
    scheduler_placement=eu_placement,
    secrets=[eu_secrets]
)
def process_eu_customer_data(customer_ids: list[str]):
    # Process EU customer data in EU region for GDPR compliance
    return [process_customer_gdpr(id) for id in customer_ids]

@app.function()
def global_customer_processing():
    # Route customers to appropriate regional processors
    us_customers = get_us_customers()
    eu_customers = get_eu_customers()
    
    # Process in appropriate regions simultaneously
    us_task = process_us_customer_data.spawn(us_customers)
    eu_task = process_eu_customer_data.spawn(eu_customers)
    
    # Collect results
    us_results = us_task.get()
    eu_results = eu_task.get()
    
    return combine_regional_results(us_results, eu_results)
```

### Development to Production Pipeline

```python
import modal

# Development setup
dev_app = modal.App("data-pipeline-dev")
dev_secrets = modal.Secret.from_dict({
    "DATABASE_URL": "postgresql://localhost:5432/dev",
    "API_KEY": "dev_key_123",
    "S3_BUCKET": "dev-data-bucket"
})

# Production setup
prod_app = modal.App("data-pipeline-prod")
prod_secrets = modal.Secret.from_name("production-secrets")
prod_proxy = modal.Proxy.from_name("production-proxy")

# Shared function logic with environment-specific configuration
def create_pipeline_function(app, secrets, proxy=None):
    @app.function(secrets=secrets, proxy=proxy)
    def data_pipeline():
        import os
        
        # Environment variables automatically injected based on secrets
        db_url = os.environ["DATABASE_URL"]
        api_key = os.environ["API_KEY"]
        bucket = os.environ["S3_BUCKET"]
        
        # Same processing logic, different configurations
        return process_data(db_url, api_key, bucket)
    
    return data_pipeline

# Create environment-specific functions
dev_pipeline = create_pipeline_function(dev_app, [dev_secrets])
prod_pipeline = create_pipeline_function(prod_app, [prod_secrets], prod_proxy)

# Deploy based on environment
if os.getenv("ENVIRONMENT") == "production":
    prod_pipeline.remote()
else:
    dev_pipeline.remote()
```