# RLM Playground

The RLM Playground provides a web interface to interactively run RLM completions, visualize recursive calls, and debug execution across different environments.

## Architecture

- **Backend**: FastAPI server (`playground/server.py`) that executes RLM logic.
- **Frontend**: Next.js visualizer (`visualizer/`) with a dedicated playground page.

## Getting Started

### 1. Prerequisites

Ensure you have installed the project dependencies with the `playground` extra:

```bash
uv pip install -e ".[playground]"
```

### 2. Environment Setup

The playground server uses a `.env` file for configuration. Create one in the root directory:

```bash
# API Keys for LLM providers
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Optional: Directory for RLM logs
RLM_LOG_DIR=./logs
```

### 3. Running the Backend Server

Start the FastAPI server. By default, it runs on `http://localhost:8000`.

```bash
uv run playground/run.py
```

The server includes:
- **CORS Middleware**: Pre-configured to allow requests from the visualizer (port 3000).
- **Auto-reload**: Enabled for development.

### 4. Running the Visualizer Frontend

Navigate to the visualizer directory and start the Next.js development server:

```bash
cd visualizer
bun install
bun run dev
```

Open [http://localhost:3000/playground](http://localhost:3000/playground) in your browser.

## Features

- **Configuration**: Toggle between different backends (OpenAI, Anthropic, Portkey, etc.) and environments (Local, Modal, Docker).
- **Iterative Execution**: Set `max_iterations` and `max_depth` to control the recursion.
- **Usage Tracking**: View real-time token usage and execution time for every model call.
