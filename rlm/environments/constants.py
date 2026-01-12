# Default packages for isolated REPL environments (Modal, Prime, etc.)

APT_PACKAGES = [
    "build-essential",
    "git",
    "curl",
    "wget",
    "libopenblas-dev",
    "liblapack-dev",
]

PIP_PACKAGES = [
    # Data science essentials
    "numpy>=1.26.0",
    "pandas>=2.1.0",
    "scipy>=1.11.0",
    # Math & symbolic computation
    "sympy>=1.12",
    # HTTP & APIs
    "requests>=2.31.0",
    "httpx>=0.25.0",
    "flask>=3.0.0",
    # Data formats
    "pyyaml>=6.0",
    "toml>=0.10.2",
    # Utilities
    "tqdm>=4.66.0",
    "python-dateutil>=2.8.2",
    "regex>=2023.0.0",
    # For state serialization
    "dill>=0.3.7",
]
