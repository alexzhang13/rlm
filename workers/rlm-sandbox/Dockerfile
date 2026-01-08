# RLM Sandbox - Python execution environment for CloudflareREPL
# Must match @cloudflare/sandbox npm package version
FROM docker.io/cloudflare/sandbox:0.6.7

# Install Python 3 and common dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages for data science / math
RUN pip3 install --no-cache-dir \
    numpy \
    sympy \
    requests

# Create workspace directory
RUN mkdir -p /workspace /tmp

# Required during local development to access exposed ports
EXPOSE 8080
