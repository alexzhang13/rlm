"""FastAPI server for RLM playground."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rlm import RLM
from rlm.logger import RLMLogger

from playground.models import RunRequest, RunResponse

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="RLM Playground API",
    description="API for running RLM completions via web interface",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative Next.js port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "RLM Playground API"}


@app.post("/api/run", response_model=RunResponse)
def run_rlm(request: RunRequest) -> RunResponse:
    """
    Run an RLM completion with the provided configuration.

    This endpoint creates an RLM instance, runs a completion, and returns the result.
    """
    try:
        # Setup logger if enabled
        logger = None
        if request.enable_logging:
            log_dir = os.getenv("RLM_LOG_DIR", "./logs")
            logger = RLMLogger(log_dir=log_dir)

        # Create RLM instance
        rlm = RLM(
            backend=request.backend,
            backend_kwargs=request.backend_kwargs or {},
            environment=request.environment,
            environment_kwargs=request.environment_kwargs or {},
            max_depth=request.max_depth,
            max_iterations=request.max_iterations,
            other_backends=request.other_backends,
            other_backend_kwargs=request.other_backend_kwargs,
            logger=logger,
            verbose=False,  # Disable console output in API
        )

        # Run completion
        result = rlm.completion(
            prompt=request.prompt,
            root_prompt=request.root_prompt,
        )

        # Extract response - handle both string and tuple (type, content) formats
        response_text = result.response
        if isinstance(response_text, tuple):
            # If it's a tuple from find_final_answer, extract the content
            # Format: (type, content) where type is "FINAL" or "FINAL_VAR"
            answer_type, answer_content = response_text
            if answer_type == "FINAL":
                # For FINAL, use the content directly
                response_text = answer_content.strip().strip('"').strip("'")
            elif answer_type == "FINAL_VAR":
                # For FINAL_VAR, the content is the variable name
                # We can't look it up here since we don't have access to the environment
                # So we'll return a message indicating the variable name
                variable_name = answer_content.strip().strip('"').strip("'")
                response_text = f"[FINAL_VAR: {variable_name}]"
            else:
                # Fallback: just use the content
                response_text = (
                    answer_content if isinstance(answer_content, str) else str(answer_content)
                )

        # Convert result to response
        return RunResponse(
            success=True,
            response=str(response_text) if response_text else None,
            root_model=result.root_model,
            execution_time=result.execution_time,
            usage_summary=result.usage_summary.to_dict(),
            error=None,
        )

    except Exception as e:
        # Return error response
        return RunResponse(
            success=False,
            response=None,
            root_model=None,
            execution_time=None,
            usage_summary=None,
            error=str(e),
        )
