"""FastAPI server for RLM playground."""

import asyncio
import io
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from playground.models import RunRequest, RunResponse
from rlm import RLM
from rlm.logger import RLMLogger

# Load environment variables
load_dotenv()

# Thread pool for running RLM in the background
executor = ThreadPoolExecutor(max_workers=10)

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
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "RLM Playground API"}


def serialize_result(result):
    """Serialize RLMChatCompletion to a dict."""
    response_text = result.response
    if isinstance(response_text, tuple):
        answer_type, answer_content = response_text
        if answer_type == "FINAL":
            response_text = answer_content.strip().strip('"').strip("'")
        elif answer_type == "FINAL_VAR":
            variable_name = answer_content.strip().strip('"').strip("'")
            response_text = f"[FINAL_VAR: {variable_name}]"
        else:
            response_text = (
                answer_content if isinstance(answer_content, str) else str(answer_content)
            )

    return {
        "success": True,
        "response": str(response_text) if response_text else None,
        "root_model": result.root_model,
        "execution_time": result.execution_time,
        "usage_summary": result.usage_summary.to_dict(),
        "error": None,
    }


@app.post("/api/run/stream")
async def run_rlm_stream(request_body: RunRequest, request: Request):
    """Stream RLM execution via Server-Sent Events."""

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_log_callback(entry: dict):
            loop.call_soon_threadsafe(queue.put_nowait, entry)

        def run_rlm_sync():
            try:
                # Setup logger
                log_dir = os.getenv("RLM_LOG_DIR", "./logs")
                logger = RLMLogger(log_dir=log_dir, on_log=on_log_callback)

                # Create RLM instance
                rlm = RLM(
                    backend=request_body.backend,  # type: ignore
                    backend_kwargs=request_body.backend_kwargs or {},
                    environment=request_body.environment,  # type: ignore
                    environment_kwargs=request_body.environment_kwargs or {},
                    max_depth=request_body.max_depth,
                    max_iterations=request_body.max_iterations,
                    other_backends=request_body.other_backends,  # type: ignore
                    other_backend_kwargs=request_body.other_backend_kwargs,
                    custom_system_prompt=request_body.custom_system_prompt,
                    logger=logger,
                    verbose=False,  # Verbose output is messy in streaming
                )

                # Run completion
                result = rlm.completion(
                    prompt=request_body.prompt,
                    root_prompt=request_body.root_prompt,
                )

                # Signal completion
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "complete", "result": result})
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "error": str(e)})

        # Start RLM in background thread
        _ = executor.submit(run_rlm_sync)

        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    # Wait for an event with timeout to check for disconnect
                    entry = await asyncio.wait_for(queue.get(), timeout=1.0)
                except TimeoutError:
                    continue

                if entry["type"] == "metadata":
                    yield f"event: metadata\ndata: {json.dumps(entry)}\n\n"
                elif entry["type"] == "iteration":
                    yield f"event: iteration\ndata: {json.dumps(entry)}\n\n"
                elif entry["type"] == "complete":
                    yield f"event: complete\ndata: {json.dumps(serialize_result(entry['result']))}\n\n"
                    break
                elif entry["type"] == "error":
                    yield f"event: error\ndata: {json.dumps({'error': entry['error']})}\n\n"
                    break
        finally:
            # We don't explicitly cancel the thread as it's not easily possible in Python,
            # but we stop yielding and let it finish or hit its own timeout.
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


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

        # Capture verbose output if enabled
        verbose_output = None
        if request.verbose:
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr

        try:
            if request.verbose:
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture

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
                custom_system_prompt=request.custom_system_prompt,
                logger=logger,
                verbose=request.verbose,
            )

            # Run completion
            result = rlm.completion(
                prompt=request.prompt,
                root_prompt=request.root_prompt,
            )
        finally:
            # Restore stdout/stderr and capture output
            if request.verbose:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                stdout_text = stdout_capture.getvalue()
                stderr_text = stderr_capture.getvalue()
                verbose_output = stdout_text + stderr_text if stderr_text else stdout_text

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
            verbose_output=verbose_output,
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
            verbose_output=None,
            error=str(e),
        )
