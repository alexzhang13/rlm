# Cloudflare Workers Sandbox for RLM

This guide explains how to set up and use the `CloudflareREPL` environment, which runs Python code in Cloudflare Workers Sandbox containers.

## Prerequisites

1. **Cloudflare Account** with Workers Paid plan ($5/month)
2. **Wrangler CLI** installed and authenticated:
   ```bash
   npm install -g wrangler
   wrangler login
   ```
3. **Docker** running locally (for development)

## Architecture

```
┌─────────────────┐     HTTP      ┌──────────────────┐
│  CloudflareREPL │ ────────────► │  rlm-sandbox     │
│  (Python SDK)   │               │  (CF Worker)     │
└─────────────────┘               └────────┬─────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │  Sandbox Container│
                                  │  (Python 3.10)   │
                                  └──────────────────┘
```

## Deploying the Worker

### 1. Navigate to Worker Directory

```bash
cd workers/rlm-sandbox
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Deploy to Cloudflare

```bash
npm run deploy
# or: npx wrangler deploy
```

This will:
- Build the Docker image with Python 3.10, numpy, sympy, requests
- Upload the image to Cloudflare's container registry
- Deploy the Worker

Output will show your Worker URL:
```
Deployed rlm-sandbox triggers
  https://rlm-sandbox.<your-subdomain>.workers.dev
```

### 4. (Optional) Configure Authentication

For production, set an auth token:
```bash
npx wrangler secret put AUTH_TOKEN
# Enter your secret token when prompted
```

## Local Development

Run the Worker locally with Docker:
```bash
npm run dev
# Worker available at http://localhost:8787
```

First run takes 2-3 minutes to build the container; subsequent runs are faster.

## Using CloudflareREPL

### Environment Variables

CloudflareREPL supports configuration via environment variables:

| Variable | Description |
|----------|-------------|
| `RLM_CF_WORKER_URL` | Default worker URL (if not passed to constructor) |
| `RLM_CF_AUTH_TOKEN` | Default auth token (if not passed to constructor) |

```bash
# Set env vars for easy usage
export RLM_CF_WORKER_URL=https://rlm-sandbox.example.workers.dev
export RLM_CF_AUTH_TOKEN=your-auth-token
```

### Basic Usage

```python
from rlm.environments import get_environment

# With env vars set, minimal config needed:
env = get_environment("cloudflare", {})

# Or explicitly pass URL:
env = get_environment("cloudflare", {
    "worker_url": "https://rlm-sandbox.example.workers.dev",
    "auth_token": "your-auth-token",  # Optional if not configured
    "sandbox_id": "my-session",       # Optional, auto-generated if omitted
})

# Execute code
result = env.execute_code("x = 2 + 2\nprint(x)")
print(result.stdout)  # "4\n"
print(result.locals)  # {"x": "4"}

# Variables persist across executions
result2 = env.execute_code("y = x * 10\nprint(y)")
print(result2.stdout)  # "40\n"

# Cleanup when done
env.cleanup()
```

### With Context Manager

```python
from rlm.environments.cloudflare_repl import CloudflareREPL

# Uses RLM_CF_WORKER_URL and RLM_CF_AUTH_TOKEN env vars
with CloudflareREPL() as repl:
    result = repl.execute_code("import numpy as np\nprint(np.sum([1,2,3]))")
    print(result.stdout)  # "6\n"

# Or with explicit URL
with CloudflareREPL(worker_url="https://rlm-sandbox.example.workers.dev") as repl:
    result = repl.execute_code("print('hello')")
```

### Loading Context

```python
# String context
env = get_environment("cloudflare", {
    "worker_url": "https://...",
    "context_payload": "This is my context data",
})
# Access via: context variable in sandbox

# Dict/List context
env = get_environment("cloudflare", {
    "worker_url": "https://...",
    "context_payload": {"key": "value", "items": [1, 2, 3]},
})
```

## Worker API Reference

The Worker exposes these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/sandbox/exec` | Execute shell command |
| POST | `/sandbox/write` | Write file to sandbox |
| GET | `/sandbox/read` | Read file from sandbox |
| GET | `/sandbox/health` | Check Python availability |

### POST /sandbox/exec

Execute a command in the sandbox.

```bash
curl -X POST https://your-worker.workers.dev/sandbox/exec \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"sandbox_id": "my-session", "command": "python3 -c \"print(42)\""}'
```

Response:
```json
{
  "stdout": "42\n",
  "stderr": "",
  "exitCode": 0,
  "success": true
}
```

### POST /sandbox/write

Write a file to the sandbox filesystem.

```bash
curl -X POST https://your-worker.workers.dev/sandbox/write \
  -H "Content-Type: application/json" \
  -d '{"sandbox_id": "my-session", "path": "/workspace/script.py", "content": "print(\"hello\")"}'
```

### GET /sandbox/read

Read a file from the sandbox.

```bash
curl "https://your-worker.workers.dev/sandbox/read?sandbox_id=my-session&path=/workspace/script.py"
```

## Pre-installed Packages

The sandbox container includes:
- Python 3.10
- numpy
- sympy
- requests

To add more packages, edit `workers/rlm-sandbox/Dockerfile`:
```dockerfile
RUN pip3 install --no-cache-dir \
    numpy \
    sympy \
    requests \
    your-package-here
```

Then redeploy: `npm run deploy`

## Pricing

Cloudflare Workers Sandbox pricing (as of 2025):
- **Base**: Workers Paid plan ($5/month)
- **CPU**: $0.000020/vCPU-second (375 vCPU-min/month included)
- **Memory**: $0.0000025/GiB-second (25 GiB-hours/month included)
- **Disk**: $0.00000007/GB-second (200 GB-hours/month included)

Instance type "basic" (default): 1/4 vCPU, 1 GiB RAM, 5 GB disk.

## Troubleshooting

### "Sandbox binding not configured"
Ensure your `wrangler.toml` has the container and Durable Object bindings configured correctly.

### Container build fails
- Check Docker is running: `docker info`
- Verify the base image version matches the SDK: `npm list @cloudflare/sandbox`
- Use matching versions in Dockerfile: `FROM cloudflare/sandbox:X.Y.Z`

### Slow cold starts
First request to a new sandbox takes 2-3 seconds to initialize the container. Subsequent requests to the same `sandbox_id` are fast.

### State not persisting
Ensure you're using the same `sandbox_id` across requests. Each unique ID gets its own container.
