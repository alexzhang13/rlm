# Container Images

Container image definitions that specify the runtime environment for functions and classes. Images define the operating system, Python version, packages, and system dependencies needed for your code to run.

## Capabilities

### Image Class

Defines container environments with pre-installed dependencies, custom configurations, and optimized builds for serverless execution.

```python { .api }
class Image:
    @classmethod
    def debian_slim(
        cls,
        python_version: str = None,
        builder_version: str = None
    ):
        """
        Create a Debian slim base image with Python.
        
        Parameters:
        - python_version: Python version (e.g., "3.11", "3.12"). Defaults to local version.
        - builder_version: Image builder version for reproducible builds
        
        Returns:
        Image instance with Debian slim base
        """

    @classmethod
    def from_registry(
        cls,
        tag: str,
        secret: Secret = None,
        setup_dockerfile_commands: list[str] = None
    ):
        """
        Create an image from a container registry (Docker Hub, ECR, etc.).
        
        Parameters:
        - tag: Full image tag (e.g., "python:3.11-slim", "ubuntu:22.04")
        - secret: Secret for private registry authentication
        - setup_dockerfile_commands: Additional setup commands to run
        
        Returns:
        Image instance based on registry image
        """

    def pip_install(
        self,
        *packages: str,
        find_links: str = None,
        index_url: str = None,
        extra_index_url: str = None,
        pre: bool = False,
        force_build: bool = False
    ):
        """
        Install Python packages using pip.
        
        Parameters:
        - *packages: Package names, optionally with version specifiers
        - find_links: Additional URLs to search for packages
        - index_url: Base URL of package index
        - extra_index_url: Extra URLs of package indexes
        - pre: Include pre-release versions
        - force_build: Force rebuild even if cached
        
        Returns:
        New Image instance with packages installed
        """

    def poetry_install_from_file(
        self,
        poetry_pyproject_toml: str,
        poetry_lock_file: str = None,
        ignore_lockfile: bool = False
    ):
        """
        Install dependencies from Poetry configuration files.
        
        Parameters:
        - poetry_pyproject_toml: Path to pyproject.toml file
        - poetry_lock_file: Path to poetry.lock file
        - ignore_lockfile: Install without using lockfile
        
        Returns:
        New Image instance with Poetry dependencies
        """

    def run_commands(
        self,
        *commands: str,
        secrets: list[Secret] = None,
        gpu: str = None
    ):
        """
        Run shell commands during image build.
        
        Parameters:
        - *commands: Shell commands to execute
        - secrets: Secrets available during build
        - gpu: GPU type for build environment
        
        Returns:
        New Image instance with commands executed
        """

    def apt_install(
        self,
        *packages: str,
        force_build: bool = False
    ):
        """
        Install system packages using apt (Debian/Ubuntu).
        
        Parameters:
        - *packages: Package names to install
        - force_build: Force rebuild even if cached
        
        Returns:
        New Image instance with system packages
        """

    def copy_local_file(
        self,
        local_path: str,
        remote_path: str = None
    ):
        """
        Copy a local file into the image.
        
        Parameters:
        - local_path: Path to local file or directory
        - remote_path: Destination path in image. Defaults to same path.
        
        Returns:
        New Image instance with file copied
        """

    def copy_local_dir(
        self,
        local_path: str,
        remote_path: str = None,
        condition: callable = None
    ):
        """
        Copy a local directory into the image.
        
        Parameters:
        - local_path: Path to local directory
        - remote_path: Destination path in image
        - condition: Function to filter which files to copy
        
        Returns:
        New Image instance with directory copied
        """

    def add_python_packages(
        self,
        *python_packages: str,
        force_build: bool = False
    ):
        """
        Add Python packages from local wheel files or directories.
        
        Parameters:
        - *python_packages: Paths to wheel files or package directories
        - force_build: Force rebuild even if cached
        
        Returns:
        New Image instance with packages added
        """

    def dockerfile_commands(
        self,
        dockerfile_commands: list[str],
        secrets: list[Secret] = None,
        gpu: str = None,
        context_files: dict = None
    ):
        """
        Execute Dockerfile commands during build.
        
        Parameters:
        - dockerfile_commands: List of Dockerfile commands (RUN, COPY, etc.)
        - secrets: Build secrets
        - gpu: GPU type for build
        - context_files: Files to include in build context
        
        Returns:
        New Image instance with Dockerfile commands applied
        """

    def env(self, **env_vars: str):
        """
        Set environment variables in the image.
        
        Parameters:
        - **env_vars: Environment variables as keyword arguments
        
        Returns:
        New Image instance with environment variables set
        """

    def workdir(self, path: str):
        """
        Set the working directory for the image.
        
        Parameters:
        - path: Working directory path
        
        Returns:
        New Image instance with working directory set
        """
```

## Usage Examples

### Basic Python Environment

```python
import modal

# Simple Python environment
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "requests",
    "beautifulsoup4",
    "pandas==2.0.0"
)

app = modal.App("web-scraper")

@app.function(image=image)
def scrape_and_analyze(url: str):
    import requests
    import pandas as pd
    from bs4 import BeautifulSoup
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract and analyze data
    links = [a.get('href') for a in soup.find_all('a', href=True)]
    df = pd.DataFrame({'links': links})
    
    return {
        'total_links': len(links),
        'unique_domains': len(df['links'].apply(lambda x: x.split('/')[2] if x.startswith('http') else None).dropna().unique())
    }
```

### Data Science Environment

```python
import modal

# Comprehensive data science environment
ds_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "curl", "build-essential")
    .pip_install(
        "numpy",
        "pandas",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "jupyter",
        "plotly",
        "scipy"
    )
    .run_commands(
        "pip install --no-deps lightgbm",  # Custom installation
        "mkdir -p /opt/data"
    )
    .env(
        DATA_PATH="/opt/data",
        PYTHONPATH="/opt/models"
    )
)

app = modal.App("ml-pipeline")

@app.function(image=ds_image)
def train_model(dataset_path: str):
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    
    # Load and prepare data
    df = pd.read_csv(dataset_path)
    X = df.drop('target', axis=1)
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)
    
    # Evaluate
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    return {"accuracy": accuracy, "model_type": "RandomForest"}
```

### Custom Base Image

```python
import modal

# Using a custom base image from Docker Hub
custom_image = (
    modal.Image.from_registry("nvidia/cuda:11.8-devel-ubuntu22.04")
    .apt_install("python3", "python3-pip", "python3-dev")
    .run_commands(
        "ln -s /usr/bin/python3 /usr/bin/python",
        "pip install --upgrade pip"
    )
    .pip_install("torch", "torchvision", "transformers")
    .env(CUDA_VISIBLE_DEVICES="0")
)

app = modal.App("gpu-ml")

@app.function(
    image=custom_image,
    gpu="T4"  # GPU required for this function
)
def run_inference(model_name: str, input_text: str):
    import torch
    from transformers import AutoTokenizer, AutoModel
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    
    # Tokenize and run inference
    inputs = tokenizer(input_text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    
    return {
        "embeddings_shape": outputs.last_hidden_state.shape,
        "mean_embedding": outputs.last_hidden_state.mean().item()
    }
```

### Development Environment with Local Code

```python
import modal

# Development image with local code and dependencies
dev_image = (
    modal.Image.debian_slim()
    .pip_install("fastapi", "uvicorn", "sqlalchemy", "pytest")
    .copy_local_dir("./src", "/app/src")  # Copy local source code
    .copy_local_file("requirements.txt", "/app/requirements.txt")
    .run_commands("pip install -r /app/requirements.txt")
    .workdir("/app")
)

app = modal.App("development")

@app.function(image=dev_image)
def run_tests():
    import subprocess
    
    # Run tests using the copied code
    result = subprocess.run(
        ["python", "-m", "pytest", "src/tests/", "-v"],
        capture_output=True,
        text=True,
        cwd="/app"
    )
    
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }
```

### Poetry-based Project

```python
import modal

# Using Poetry for dependency management
poetry_image = (
    modal.Image.debian_slim()
    .apt_install("curl")
    .run_commands(
        "curl -sSL https://install.python-poetry.org | python3 -",
        "export PATH=\"/root/.local/bin:$PATH\""
    )
    .poetry_install_from_file(
        "pyproject.toml",
        "poetry.lock"
    )
    .copy_local_dir("./my_package", "/app/my_package")
    .workdir("/app")
)

app = modal.App("poetry-app")

@app.function(image=poetry_image)
def process_with_poetry_deps():
    # Use dependencies installed via Poetry
    from my_package import main_module
    return main_module.process_data()
```

### Multi-stage Build

```python
import modal

# Complex multi-stage build with custom compilation
build_image = (
    modal.Image.debian_slim()
    .apt_install(
        "build-essential",
        "cmake",
        "git",
        "pkg-config",
        "libssl-dev"
    )
    .run_commands(
        # Clone and build custom library
        "git clone https://github.com/example/custom-lib.git /tmp/custom-lib",
        "cd /tmp/custom-lib && mkdir build && cd build",
        "cmake .. && make -j$(nproc) && make install"
    )
    .pip_install("numpy", "cython")
    .copy_local_file("setup.py", "/app/setup.py")
    .copy_local_dir("./src", "/app/src")
    .run_commands(
        "cd /app && python setup.py build_ext --inplace",
        "pip install -e ."
    )
    .apt_install("--purge", "build-essential", "cmake")  # Clean up build tools
    .run_commands("apt-get autoremove -y && apt-get clean")
)

app = modal.App("optimized-build")

@app.function(image=build_image)
def run_optimized_computation(data):
    # Use the custom-built optimized library
    import my_optimized_package
    return my_optimized_package.fast_compute(data)
```

## Common Patterns

### Environment Variables and Configuration

```python
config_image = (
    modal.Image.debian_slim()
    .pip_install("python-dotenv", "pydantic")
    .env(
        ENVIRONMENT="production",
        LOG_LEVEL="INFO",
        API_TIMEOUT="30"
    )
    .copy_local_file(".env.production", "/app/.env")
)
```

### Caching for Faster Builds

```python
# Use force_build=False (default) to enable caching
cached_image = (
    modal.Image.debian_slim()
    .pip_install("numpy", "pandas", force_build=False)  # Will be cached
    .copy_local_file("requirements.txt")  # This will trigger rebuild if file changes
    .pip_install("-r", "requirements.txt")
)
```

### Secrets in Build Process

```python
build_secret = modal.Secret.from_dict({
    "GITHUB_TOKEN": "ghp_...",
    "PRIVATE_REGISTRY_TOKEN": "..."
})

secure_image = (
    modal.Image.debian_slim()
    .run_commands(
        "git clone https://${GITHUB_TOKEN}@github.com/private/repo.git /app",
        secrets=[build_secret]
    )
    .pip_install("--extra-index-url", "https://token:${PRIVATE_REGISTRY_TOKEN}@pypi.private.com/simple/", "private-package", secrets=[build_secret])
)
```