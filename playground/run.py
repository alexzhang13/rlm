"""CLI entry point for running the RLM playground FastAPI server."""

import sys
from pathlib import Path

import uvicorn

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


if __name__ == "__main__":
    uvicorn.run(
        "playground.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
