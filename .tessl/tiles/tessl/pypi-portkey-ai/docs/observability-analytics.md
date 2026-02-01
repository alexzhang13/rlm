# Observability & Analytics

Comprehensive logging, request tracing, analytics, and monitoring capabilities with custom metadata and performance metrics.

## Capabilities

### Request Logging

Track and analyze all API requests with detailed logging capabilities including request/response data, performance metrics, and custom metadata.

```python { .api }
class Logs:
    """Request logging and retrieval"""
    
    def list(
        self,
        *,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        order: Optional[str] = None,
        filters: Optional[dict] = None,
        **kwargs
    ) -> dict:
        """
        List request logs with filtering and pagination.
        
        Parameters:
        - limit: Maximum number of logs to retrieve
        - after: Cursor for pagination (logs after this ID)
        - before: Cursor for pagination (logs before this ID)
        - order: Sort order ('asc' or 'desc')
        - filters: Filter criteria (date range, model, provider, etc.)
        
        Returns:
        Dictionary containing log entries and pagination info
        """
    
    def retrieve(
        self,
        log_id: str,
        **kwargs
    ) -> dict:
        """
        Retrieve a specific log entry by ID.
        
        Parameters:
        - log_id: Unique identifier for the log entry
        
        Returns:
        Detailed log entry with request/response data
        """

class AsyncLogs:
    """Async request logging and retrieval"""
    
    async def list(self, **kwargs) -> dict: ...
    async def retrieve(self, log_id: str, **kwargs) -> dict: ...
```

### Response Analysis

Analyze API responses with detailed breakdowns of input/output tokens, performance metrics, and content analysis.

```python { .api }
class Responses:
    """Response analysis and metrics"""
    
    def list(
        self,
        *,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        filters: Optional[dict] = None,
        **kwargs
    ) -> dict:
        """List and analyze API responses"""
    
    def retrieve(
        self,
        response_id: str,
        **kwargs
    ) -> dict:
        """Retrieve detailed response analysis"""
    
    input_items: InputItems
    output_items: OutputItems

class InputItems:
    """Input content analysis"""
    
    def list(self, **kwargs) -> dict: ...
    def retrieve(self, item_id: str, **kwargs) -> dict: ...

class OutputItems:
    """Output content analysis"""
    
    def list(self, **kwargs) -> dict: ...
    def retrieve(self, item_id: str, **kwargs) -> dict: ...

class AsyncResponses:
    """Async response analysis"""
    
    async def list(self, **kwargs) -> dict: ...
    async def retrieve(self, response_id: str, **kwargs) -> dict: ...
    input_items: AsyncInputItems
    output_items: AsyncOutputItems
```

### Request Labeling

Categorize and tag API requests for better organization, analysis, and filtering.

```python { .api }
class Labels:
    """Request labeling and categorization"""
    
    def create(
        self,
        *,
        log_id: str,
        label: str,
        value: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create a label for a request log.
        
        Parameters:
        - log_id: ID of the log entry to label
        - label: Label name/category
        - value: Optional label value
        
        Returns:
        Created label object
        """
    
    def list(
        self,
        *,
        log_id: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs
    ) -> dict:
        """List labels with optional filtering"""
    
    def update(
        self,
        label_id: str,
        *,
        value: Optional[str] = None,
        **kwargs
    ) -> dict:
        """Update an existing label"""
    
    def delete(
        self,
        label_id: str,
        **kwargs
    ) -> dict:
        """Delete a label"""

class AsyncLabels:
    """Async request labeling"""
    
    async def create(self, **kwargs) -> dict: ...
    async def list(self, **kwargs) -> dict: ...
    async def update(self, label_id: str, **kwargs) -> dict: ...
    async def delete(self, label_id: str, **kwargs) -> dict: ...
```

## Usage Examples

### Basic Request Logging

```python
from portkey_ai import Portkey

# Initialize with observability enabled
portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY",
    debug=True,  # Enable detailed logging
    metadata={
        "environment": "production",
        "user_id": "user123",
        "session_id": "session456"
    }
)

# Make a request (automatically logged)
response = portkey.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4",
    metadata={
        "request_type": "greeting",
        "category": "customer_support"
    }
)

# Retrieve recent logs
logs = portkey.logs.list(limit=10, order="desc")
print(f"Found {len(logs['data'])} recent requests")

for log in logs['data']:
    print(f"Request {log['id']}: {log['model']} - {log['status']}")
    print(f"  Tokens: {log['usage']['total_tokens']}")
    print(f"  Duration: {log['duration_ms']}ms")
```

### Advanced Log Filtering

```python
from datetime import datetime, timedelta

# Filter logs by date range and criteria
yesterday = datetime.now() - timedelta(days=1)
logs = portkey.logs.list(
    filters={
        "date": {
            "gte": yesterday.isoformat(),
            "lte": datetime.now().isoformat()
        },
        "model": "gpt-4",
        "status": "success",
        "provider": "openai",
        "metadata.environment": "production"
    },
    limit=50
)

# Analyze request patterns
total_requests = len(logs['data'])
total_tokens = sum(log['usage']['total_tokens'] for log in logs['data'])
avg_latency = sum(log['duration_ms'] for log in logs['data']) / total_requests

print(f"Analysis for last 24 hours:")
print(f"  Total requests: {total_requests}")
print(f"  Total tokens: {total_tokens}")
print(f"  Average latency: {avg_latency:.2f}ms")
```

### Request Tracing

```python
import uuid

# Use trace IDs to track request flows
trace_id = str(uuid.uuid4())

# First request in trace
response1 = portkey.chat.completions.create(
    messages=[{"role": "user", "content": "What is Python?"}],
    model="gpt-4",
    trace_id=trace_id,
    metadata={"step": "initial_query"}
)

# Follow-up request in same trace
response2 = portkey.chat.completions.create(
    messages=[
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": response1.choices[0].message.content},
        {"role": "user", "content": "Give me a code example"}
    ],
    model="gpt-4", 
    trace_id=trace_id,
    metadata={"step": "follow_up"}
)

# Retrieve all logs for this trace
trace_logs = portkey.logs.list(
    filters={"trace_id": trace_id}
)

print(f"Trace {trace_id} has {len(trace_logs['data'])} requests")
```

### Response Analysis

```python
# Analyze response patterns and content
responses = portkey.responses.list(
    filters={
        "model": "gpt-4",
        "date": {"gte": "2024-01-01"}
    },
    limit=100
)

# Analyze input/output patterns
for response in responses['data']:
    response_detail = portkey.responses.retrieve(response['id'])
    
    print(f"Response {response['id']}:")
    print(f"  Input tokens: {response_detail['input_tokens']}")
    print(f"  Output tokens: {response_detail['output_tokens']}")
    print(f"  Cost: ${response_detail['cost']:.4f}")
    
    # Analyze input items
    input_items = portkey.responses.input_items.list(
        response_id=response['id']
    )
    
    # Analyze output items
    output_items = portkey.responses.output_items.list(
        response_id=response['id']
    )
```

### Request Labeling and Categorization

```python
# Create labels for request categorization
recent_logs = portkey.logs.list(limit=20)

for log in recent_logs['data']:
    # Auto-label based on content
    if 'translate' in log['request']['messages'][0]['content'].lower():
        portkey.labels.create(
            log_id=log['id'],
            label="category",
            value="translation"
        )
    elif 'code' in log['request']['messages'][0]['content'].lower():
        portkey.labels.create(
            log_id=log['id'],
            label="category", 
            value="coding"
        )
    
    # Label by performance
    if log['duration_ms'] > 5000:
        portkey.labels.create(
            log_id=log['id'],
            label="performance",
            value="slow"
        )

# Query logs by labels
coding_requests = portkey.logs.list(
    filters={"labels.category": "coding"}
)

slow_requests = portkey.logs.list(
    filters={"labels.performance": "slow"}
)

print(f"Found {len(coding_requests['data'])} coding requests")
print(f"Found {len(slow_requests['data'])} slow requests")
```

### Real-time Monitoring

```python
import time

def monitor_requests():
    """Monitor requests in real-time"""
    last_check = datetime.now()
    
    while True:
        # Get new logs since last check
        new_logs = portkey.logs.list(
            filters={
                "date": {"gte": last_check.isoformat()}
            },
            order="asc"
        )
        
        for log in new_logs['data']:
            print(f"New request: {log['id']}")
            print(f"  Model: {log['model']}")
            print(f"  Status: {log['status']}")
            print(f"  Duration: {log['duration_ms']}ms")
            print(f"  Tokens: {log['usage']['total_tokens']}")
            
            # Alert on errors
            if log['status'] == 'error':
                print(f"  ERROR: {log['error']['message']}")
            
            # Alert on slow requests
            if log['duration_ms'] > 10000:
                print(f"  WARNING: Slow request ({log['duration_ms']}ms)")
        
        last_check = datetime.now()
        time.sleep(30)  # Check every 30 seconds

# Run monitoring (in production, use proper async/threading)
# monitor_requests()
```

### Custom Analytics Dashboard

```python
from collections import defaultdict

def generate_analytics_report(days=7):
    """Generate comprehensive analytics report"""
    
    # Get logs for specified period
    start_date = datetime.now() - timedelta(days=days)
    logs = portkey.logs.list(
        filters={
            "date": {"gte": start_date.isoformat()}
        },
        limit=1000
    )
    
    # Aggregate metrics
    metrics = {
        'total_requests': len(logs['data']),
        'by_model': defaultdict(int),
        'by_provider': defaultdict(int),
        'by_status': defaultdict(int),
        'total_tokens': 0,
        'total_cost': 0,
        'avg_latency': 0,
        'error_rate': 0
    }
    
    latencies = []
    errors = 0
    
    for log in logs['data']:
        metrics['by_model'][log['model']] += 1
        metrics['by_provider'][log['provider']] += 1
        metrics['by_status'][log['status']] += 1
        metrics['total_tokens'] += log['usage']['total_tokens']
        metrics['total_cost'] += log['cost']
        latencies.append(log['duration_ms'])
        
        if log['status'] == 'error':
            errors += 1
    
    metrics['avg_latency'] = sum(latencies) / len(latencies) if latencies else 0
    metrics['error_rate'] = (errors / len(logs['data'])) * 100 if logs['data'] else 0
    
    # Print report
    print(f"Analytics Report ({days} days)")
    print("=" * 40)
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Total Tokens: {metrics['total_tokens']:,}")
    print(f"Total Cost: ${metrics['total_cost']:.2f}")
    print(f"Average Latency: {metrics['avg_latency']:.0f}ms")
    print(f"Error Rate: {metrics['error_rate']:.2f}%")
    
    print("\nTop Models:")
    for model, count in sorted(metrics['by_model'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {model}: {count} requests")
    
    print("\nProviders:")
    for provider, count in metrics['by_provider'].items():
        print(f"  {provider}: {count} requests")
    
    return metrics

# Generate report
analytics = generate_analytics_report(days=30)
```

### Async Observability Operations

```python
import asyncio
from portkey_ai import AsyncPortkey

async def async_observability_example():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    # Make async request with metadata
    response = await portkey.chat.completions.create(
        messages=[{"role": "user", "content": "Hello async world"}],
        model="gpt-4",
        metadata={"async": "true", "test": "observability"}
    )
    
    # Async log retrieval
    logs = await portkey.logs.list(limit=5)
    
    # Async labeling
    if logs['data']:
        await portkey.labels.create(
            log_id=logs['data'][0]['id'],
            label="async_test",
            value="true"
        )
    
    # Async response analysis
    responses = await portkey.responses.list(limit=5)
    for resp in responses['data']:
        detail = await portkey.responses.retrieve(resp['id'])
        print(f"Response {resp['id']}: {detail['input_tokens']} → {detail['output_tokens']} tokens")

asyncio.run(async_observability_example())
```

## Analytics Metrics

Portkey automatically tracks 40+ production-critical metrics including:

### Performance Metrics
- Request latency (p50, p95, p99)
- Throughput (requests per minute/hour)
- Error rates by provider/model
- Token usage and costs

### Usage Metrics
- Requests by model, provider, user
- Token consumption patterns
- Cost analysis and optimization
- Geographic distribution

### Quality Metrics
- Response quality scores
- User feedback integration
- A/B test results
- Conversion tracking

### Infrastructure Metrics
- Cache hit rates
- Fallback trigger frequency
- Load balancing distribution
- Provider availability