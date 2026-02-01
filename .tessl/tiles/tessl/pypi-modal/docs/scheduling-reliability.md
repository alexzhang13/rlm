# Scheduling & Reliability

Modal provides comprehensive scheduling and reliability features for automated task execution and resilient function behavior. These capabilities enable building robust serverless applications with automatic retry policies and flexible scheduling patterns.

## Capabilities

### Cron Scheduling

Schedule functions to run at specific times using Unix cron syntax, supporting timezone-aware scheduling for automated tasks.

```python { .api }
class Cron:
    def __init__(self, cron_string: str, timezone: str = "UTC") -> None:
        """Create a cron schedule from cron expression string"""
```

#### Usage Examples

```python
import modal

app = modal.App("scheduled-tasks")

# Run every minute
@app.function(schedule=modal.Cron("* * * * *"))
def check_system_health():
    """Monitor system health every minute"""
    health_status = check_all_services()
    if not health_status["healthy"]:
        send_alert(health_status["issues"])
    return health_status

# Run daily at 4:05 AM UTC
@app.function(schedule=modal.Cron("5 4 * * *"))
def daily_backup():
    """Perform daily database backup"""
    print("Starting daily backup...")
    backup_result = create_database_backup()
    upload_to_cloud_storage(backup_result)
    cleanup_old_backups()
    print("Daily backup completed")

# Run every Thursday at 9 AM UTC
@app.function(schedule=modal.Cron("0 9 * * 4"))
def weekly_report():
    """Generate weekly analytics report"""
    report_data = generate_weekly_analytics()
    send_report_email(report_data)
    store_report(report_data)

# Run daily at 6 AM New York time (timezone-aware)
@app.function(schedule=modal.Cron("0 6 * * *", timezone="America/New_York"))
def business_hours_task():
    """Task that runs at business hours in New York"""
    # Automatically adjusts for daylight saving time
    process_business_data()

# Complex cron expressions
@app.function(schedule=modal.Cron("15 2 * * 1-5"))  # Weekdays at 2:15 AM
def weekday_maintenance():
    """Maintenance tasks during weekdays"""
    perform_system_maintenance()

@app.function(schedule=modal.Cron("0 12 1 * *"))  # First day of month at noon
def monthly_billing():
    """Process monthly billing on first day of month"""
    process_monthly_invoices()
    send_billing_notifications()
```

### Period Scheduling

Schedule functions to run at regular intervals using natural time periods, supporting precise timing for recurring tasks.

```python { .api }
class Period:
    def __init__(
        self,
        *,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: float = 0
    ) -> None:
        """Create a periodic schedule with specified intervals"""
```

#### Usage Examples

```python
import modal

app = modal.App("periodic-tasks")

# Run every day
@app.function(schedule=modal.Period(days=1))
def daily_data_sync():
    """Synchronize data daily"""
    sync_external_apis()
    update_local_cache()
    print("Daily sync completed")

# Run every 4 hours
@app.function(schedule=modal.Period(hours=4))
def frequent_health_check():
    """Check system health every 4 hours"""
    status = perform_detailed_health_check()
    log_health_metrics(status)

# Run every 15 minutes
@app.function(schedule=modal.Period(minutes=15))
def cache_refresh():
    """Refresh application cache every 15 minutes"""
    refresh_application_cache()
    update_cache_metrics()

# Run every 30 seconds
@app.function(schedule=modal.Period(seconds=30))
def high_frequency_monitor():
    """High-frequency monitoring task"""
    collect_realtime_metrics()
    check_alert_conditions()

# Complex periods
@app.function(schedule=modal.Period(weeks=2, days=3))  # Every 17 days
def bi_weekly_plus_task():
    """Task that runs every 2 weeks + 3 days"""
    perform_special_analysis()

@app.function(schedule=modal.Period(months=1))  # Monthly (same day each month)  
def monthly_report():
    """Generate monthly report on same day each month"""
    # Handles varying month lengths correctly
    generate_monthly_analytics()
    archive_old_data()

# High precision timing
@app.function(schedule=modal.Period(seconds=3.14159))  # Every π seconds
def precise_timing_task():
    """Task with precise timing requirements"""
    collect_high_precision_measurements()
```

### Retry Policies

Configure automatic retry behavior for functions to handle transient failures and improve reliability.

```python { .api }
class Retries:
    def __init__(
        self,
        *,
        max_retries: int,
        backoff_coefficient: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0
    ) -> None:
        """Configure retry policy with exponential or fixed backoff"""
```

#### Usage Examples

```python
import modal

app = modal.App("reliable-functions") 

# Simple retry configuration
@app.function(retries=4)  # Retry up to 4 times with default settings
def simple_retry_task():
    """Task with basic retry policy"""
    result = call_external_api()
    return result

# Fixed-interval retries
@app.function(
    retries=modal.Retries(
        max_retries=3,
        backoff_coefficient=1.0,  # Fixed delay
        initial_delay=5.0,        # 5 seconds between retries
    )
)
def fixed_retry_task():
    """Task with fixed 5-second delay between retries"""
    try:
        return process_critical_data()
    except Exception as e:
        print(f"Attempt failed: {e}")
        raise  # Will trigger retry

# Exponential backoff
@app.function(
    retries=modal.Retries(
        max_retries=5,
        backoff_coefficient=2.0,  # Double delay each retry
        initial_delay=1.0,        # Start with 1 second
        max_delay=30.0           # Cap at 30 seconds
    )
)
def exponential_backoff_task():
    """Task with exponential backoff: 1s, 2s, 4s, 8s, 16s delays"""
    return call_rate_limited_service()

# Custom backoff configuration
@app.function(
    retries=modal.Retries(
        max_retries=6,
        backoff_coefficient=1.5,  # 50% increase each retry
        initial_delay=2.0,        # Start with 2 seconds
        max_delay=60.0           # Cap at 1 minute
    )
)
def custom_backoff_task():
    """Custom retry pattern: 2s, 3s, 4.5s, 6.75s, 10.125s, 15.1875s"""
    return perform_database_operation()

# Retry with error handling
@app.function(
    retries=modal.Retries(
        max_retries=3,
        initial_delay=1.0,
        backoff_coefficient=2.0
    )
)
def resilient_task():
    """Task with retry and comprehensive error handling"""
    attempt = 0
    try:
        # Simulate getting current attempt (in real usage, this would be tracked differently)
        result = unreliable_external_service()
        print(f"Success on attempt {attempt + 1}")
        return result
    except TemporaryError as e:
        print(f"Temporary error on attempt {attempt + 1}: {e}")
        raise  # Retry
    except PermanentError as e:
        print(f"Permanent error, not retrying: {e}")
        return {"error": "permanent_failure", "message": str(e)}
```

## Advanced Scheduling Patterns

### Multi-Timezone Scheduling

```python
import modal

app = modal.App("global-scheduling")

# Different tasks in different timezones
@app.function(schedule=modal.Cron("0 9 * * *", timezone="America/New_York"))
def us_business_hours():
    """Run at 9 AM Eastern Time"""
    process_us_customer_data()

@app.function(schedule=modal.Cron("0 9 * * *", timezone="Europe/London"))
def uk_business_hours():
    """Run at 9 AM London Time"""
    process_uk_customer_data()

@app.function(schedule=modal.Cron("0 9 * * *", timezone="Asia/Tokyo"))
def japan_business_hours():
    """Run at 9 AM Japan Time"""
    process_japan_customer_data()

@app.function(schedule=modal.Cron("0 0 * * *", timezone="UTC"))
def global_midnight_task():
    """Run at midnight UTC (global coordination)"""
    consolidate_global_reports()
```

### Cascading Scheduled Tasks

```python
import modal

app = modal.App("cascading-tasks")

# Shared queue for task coordination
task_queue = modal.Queue.persist("cascade-queue")

@app.function(schedule=modal.Cron("0 2 * * *"))  # 2 AM daily
def stage_1_data_extraction():
    """First stage: Extract data"""
    print("Stage 1: Starting data extraction...")
    raw_data = extract_raw_data()
    
    # Queue next stage
    task_queue.put({
        "stage": "transform",
        "data_id": raw_data["id"],
        "timestamp": time.time()
    })
    
    print("Stage 1: Data extraction completed")

@app.function(schedule=modal.Period(minutes=5))  # Check every 5 minutes
def stage_2_data_transformation():
    """Second stage: Transform data when available"""
    try:
        task = task_queue.get(timeout=1)  # Non-blocking check
        if task and task["stage"] == "transform":
            print(f"Stage 2: Transforming data {task['data_id']}")
            transformed_data = transform_data(task["data_id"])
            
            # Queue final stage
            task_queue.put({
                "stage": "load",
                "data_id": transformed_data["id"],
                "timestamp": time.time()
            })
            
            print("Stage 2: Data transformation completed")
    except:
        # No tasks available, continue
        pass

@app.function(schedule=modal.Period(minutes=10))  # Check every 10 minutes
def stage_3_data_loading():
    """Final stage: Load data when ready"""
    try:
        task = task_queue.get(timeout=1)
        if task and task["stage"] == "load":
            print(f"Stage 3: Loading data {task['data_id']}")
            load_data_to_warehouse(task["data_id"])
            send_completion_notification(task["data_id"])
            print("Stage 3: Data loading completed")
    except:
        pass
```

### Conditional Scheduling with Circuit Breaker

```python
import modal

app = modal.App("reliable-scheduling")

# Shared state for circuit breaker
circuit_state = modal.Dict.persist("circuit-breaker")

@app.function(
    schedule=modal.Period(minutes=10),
    retries=modal.Retries(max_retries=2, initial_delay=30.0)
)
def monitored_task():
    """Task with circuit breaker pattern"""
    # Check circuit breaker state
    is_open = circuit_state.get("circuit_open", False)
    failure_count = circuit_state.get("failure_count", 0)
    last_failure = circuit_state.get("last_failure_time", 0)
    
    # Circuit breaker logic
    if is_open:
        # Check if enough time has passed to try again
        if time.time() - last_failure > 300:  # 5 minutes
            print("Circuit breaker: Attempting to close circuit")
            circuit_state["circuit_open"] = False
        else:
            print("Circuit breaker: Circuit is open, skipping execution")
            return {"status": "circuit_open"}
    
    try:
        # Attempt the operation
        result = potentially_failing_operation()
        
        # Success - reset failure count
        circuit_state["failure_count"] = 0
        circuit_state["circuit_open"] = False
        
        print("Task completed successfully")
        return {"status": "success", "result": result}
        
    except Exception as e:
        # Handle failure
        new_failure_count = failure_count + 1
        circuit_state["failure_count"] = new_failure_count
        circuit_state["last_failure_time"] = time.time()
        
        # Open circuit if too many failures
        if new_failure_count >= 3:
            circuit_state["circuit_open"] = True
            print("Circuit breaker: Opening circuit due to repeated failures")
        
        print(f"Task failed (attempt {new_failure_count}): {e}")
        raise  # Will trigger retry policy
```

### Dynamic Scheduling Based on Load

```python
import modal

app = modal.App("adaptive-scheduling")

# Shared metrics storage
metrics = modal.Dict.persist("system-metrics")

@app.function(schedule=modal.Period(seconds=30))
def collect_system_metrics():
    """Collect system metrics every 30 seconds"""
    current_load = get_system_load()
    queue_depth = get_queue_depth()
    error_rate = get_error_rate()
    
    metrics.update({
        "load": current_load,
        "queue_depth": queue_depth,
        "error_rate": error_rate,
        "timestamp": time.time()
    })

@app.function(schedule=modal.Period(minutes=1))
def adaptive_processor():
    """Process tasks with adaptive frequency based on load"""
    current_metrics = metrics.get("load", 0)
    queue_depth = metrics.get("queue_depth", 0)
    
    # Adapt processing based on system state
    if current_metrics < 0.5 and queue_depth > 100:
        # Low load, high queue - process more aggressively
        batch_size = 50
        process_batch_tasks(batch_size)
        print(f"High throughput mode: processed {batch_size} tasks")
        
    elif current_metrics > 0.8:
        # High load - reduce processing
        batch_size = 10
        process_batch_tasks(batch_size)
        print(f"Conservative mode: processed {batch_size} tasks")
        
    else:
        # Normal processing
        batch_size = 25
        process_batch_tasks(batch_size)
        print(f"Normal mode: processed {batch_size} tasks")

@app.function(
    schedule=modal.Period(minutes=5),
    retries=modal.Retries(max_retries=3, initial_delay=60.0)
)
def health_based_processing():
    """Processing task that adapts based on system health"""
    error_rate = metrics.get("error_rate", 0)
    
    if error_rate > 0.1:  # More than 10% error rate
        print("High error rate detected, running diagnostic tasks")
        run_system_diagnostics()
        return {"status": "diagnostics"}
    else:
        print("System healthy, running normal processing")
        return process_normal_workload()
```