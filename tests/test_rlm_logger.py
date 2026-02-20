"""Tests for RLMLogger."""

import json
import os
import tempfile
from pathlib import Path

from rlm.core.types import CodeBlock, REPLResult, RLMIteration, RLMMetadata
from rlm.logger.rlm_logger import RLMLogger


class TestRLMLoggerInitialization:
    """Tests for RLMLogger initialization and file creation."""

    def test_creates_log_directory(self):
        """Logger should create the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = os.path.join(temp_dir, "nested", "logs")
            logger = RLMLogger(log_dir)

            assert os.path.isdir(log_dir)
            assert logger.log_dir == log_dir

    def test_log_file_path_format(self):
        """Log file path should contain filename, timestamp, and run_id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir, file_name="test_rlm")
            log_path = Path(logger.log_file_path)

            assert log_path.suffix == ".jsonl"
            assert log_path.name.startswith("test_rlm_")
            # Format: test_rlm_YYYY-MM-DD_HH-MM-SS_xxxxxxxx.jsonl
            parts = log_path.stem.split("_")
            assert len(parts) >= 4  # file_name + date + time + run_id

    def test_default_file_name(self):
        """Default file name should be 'rlm'."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            log_path = Path(logger.log_file_path)

            assert log_path.name.startswith("rlm_")

    def test_initial_iteration_count(self):
        """Initial iteration count should be zero."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)

            assert logger.iteration_count == 0


class TestRLMLoggerMetadata:
    """Tests for logging metadata."""

    def test_log_metadata_creates_entry(self):
        """log_metadata should write metadata as first entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            metadata = RLMMetadata(
                root_model="gpt-4",
                max_depth=3,
                max_iterations=10,
                backend="openai",
                backend_kwargs={"api_key": "test"},
                environment_type="local",
                environment_kwargs={},
            )

            logger.log_metadata(metadata)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert entry["type"] == "metadata"
            assert entry["root_model"] == "gpt-4"
            assert entry["max_depth"] == 3
            assert entry["max_iterations"] == 10
            assert entry["backend"] == "openai"
            assert entry["environment_type"] == "local"
            assert "timestamp" in entry

    def test_log_metadata_only_once(self):
        """log_metadata should only write once even if called multiple times."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            metadata = RLMMetadata(
                root_model="gpt-4",
                max_depth=3,
                max_iterations=10,
                backend="openai",
                backend_kwargs={},
                environment_type="local",
                environment_kwargs={},
            )

            logger.log_metadata(metadata)
            logger.log_metadata(metadata)
            logger.log_metadata(metadata)

            with open(logger.log_file_path) as f:
                lines = f.readlines()

            assert len(lines) == 1

    def test_metadata_with_other_backends(self):
        """Metadata should include other_backends if provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            metadata = RLMMetadata(
                root_model="claude-3",
                max_depth=2,
                max_iterations=5,
                backend="anthropic",
                backend_kwargs={},
                environment_type="docker",
                environment_kwargs={"image": "python:3.11"},
                other_backends=["openai", "gemini"],
            )

            logger.log_metadata(metadata)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert entry["other_backends"] == ["openai", "gemini"]


class TestRLMLoggerIteration:
    """Tests for logging iterations."""

    def test_log_iteration_increments_count(self):
        """Each log call should increment iteration count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            iteration = RLMIteration(
                prompt="Test prompt",
                response="Test response",
                code_blocks=[],
            )

            assert logger.iteration_count == 0

            logger.log(iteration)
            assert logger.iteration_count == 1

            logger.log(iteration)
            assert logger.iteration_count == 2

            logger.log(iteration)
            assert logger.iteration_count == 3

    def test_log_iteration_writes_entry(self):
        """log should write iteration data to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            iteration = RLMIteration(
                prompt="Calculate 1+1",
                response="Let me compute that.",
                code_blocks=[],
                final_answer="2",
            )

            logger.log(iteration)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert entry["type"] == "iteration"
            assert entry["iteration"] == 1
            assert entry["prompt"] == "Calculate 1+1"
            assert entry["response"] == "Let me compute that."
            assert entry["final_answer"] == "2"
            assert "timestamp" in entry

    def test_log_iteration_with_code_blocks(self):
        """Iteration with code blocks should serialize correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            code_result = REPLResult(stdout="42", stderr="", locals={"x": 42})
            iteration = RLMIteration(
                prompt="Compute something",
                response="Running code...",
                code_blocks=[
                    CodeBlock(code="x = 6 * 7\nprint(x)", result=code_result),
                ],
            )

            logger.log(iteration)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert len(entry["code_blocks"]) == 1
            code_block = entry["code_blocks"][0]
            assert code_block["code"] == "x = 6 * 7\nprint(x)"
            assert code_block["result"]["stdout"] == "42"
            assert code_block["result"]["stderr"] == ""

    def test_log_multiple_iterations(self):
        """Multiple iterations should be logged with correct iteration numbers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)

            for i in range(3):
                iteration = RLMIteration(
                    prompt=f"Prompt {i + 1}",
                    response=f"Response {i + 1}",
                    code_blocks=[],
                )
                logger.log(iteration)

            with open(logger.log_file_path) as f:
                lines = f.readlines()

            assert len(lines) == 3

            for i, line in enumerate(lines):
                entry = json.loads(line)
                assert entry["iteration"] == i + 1
                assert entry["prompt"] == f"Prompt {i + 1}"


class TestRLMLoggerJSONLFormat:
    """Tests for JSONL format validation."""

    def test_each_line_is_valid_json(self):
        """Each line in the log file should be valid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            metadata = RLMMetadata(
                root_model="test-model",
                max_depth=1,
                max_iterations=5,
                backend="openai",
                backend_kwargs={},
                environment_type="local",
                environment_kwargs={},
            )
            logger.log_metadata(metadata)

            for i in range(5):
                iteration = RLMIteration(
                    prompt=f"Prompt {i}",
                    response=f"Response {i}",
                    code_blocks=[],
                )
                logger.log(iteration)

            with open(logger.log_file_path) as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as e:
                        raise AssertionError(f"Line {line_num} is not valid JSON: {e}") from e

    def test_entries_end_with_newline(self):
        """Each entry should end with a newline character."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            iteration = RLMIteration(
                prompt="Test",
                response="Response",
                code_blocks=[],
            )
            logger.log(iteration)
            logger.log(iteration)

            with open(logger.log_file_path, "rb") as f:
                content = f.read()

            # Count newlines - should match number of entries
            newline_count = content.count(b"\n")
            assert newline_count == 2

    def test_metadata_and_iterations_in_order(self):
        """Metadata should come first, followed by iterations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            metadata = RLMMetadata(
                root_model="gpt-4",
                max_depth=2,
                max_iterations=3,
                backend="openai",
                backend_kwargs={},
                environment_type="local",
                environment_kwargs={},
            )
            logger.log_metadata(metadata)

            for _ in range(3):
                iteration = RLMIteration(
                    prompt="Test",
                    response="Response",
                    code_blocks=[],
                )
                logger.log(iteration)

            with open(logger.log_file_path) as f:
                lines = f.readlines()

            assert len(lines) == 4

            first_entry = json.loads(lines[0])
            assert first_entry["type"] == "metadata"

            for i, line in enumerate(lines[1:], 1):
                entry = json.loads(line)
                assert entry["type"] == "iteration"
                assert entry["iteration"] == i


class TestRLMLoggerComplexData:
    """Tests for logging complex data structures."""

    def test_iteration_with_dict_prompt(self):
        """Iteration with dict prompt should serialize correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            iteration = RLMIteration(
                prompt={"role": "user", "content": "Hello"},
                response="Hi there!",
                code_blocks=[],
            )

            logger.log(iteration)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert entry["prompt"] == {"role": "user", "content": "Hello"}

    def test_iteration_with_multiple_code_blocks(self):
        """Iteration with multiple code blocks should log all blocks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            iteration = RLMIteration(
                prompt="Multi-step computation",
                response="Running multiple blocks...",
                code_blocks=[
                    CodeBlock(
                        code="x = 10",
                        result=REPLResult(stdout="", stderr="", locals={"x": 10}),
                    ),
                    CodeBlock(
                        code="y = x * 2",
                        result=REPLResult(stdout="", stderr="", locals={"x": 10, "y": 20}),
                    ),
                    CodeBlock(
                        code="print(y)",
                        result=REPLResult(stdout="20", stderr="", locals={"x": 10, "y": 20}),
                    ),
                ],
            )

            logger.log(iteration)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert len(entry["code_blocks"]) == 3
            assert entry["code_blocks"][0]["code"] == "x = 10"
            assert entry["code_blocks"][1]["code"] == "y = x * 2"
            assert entry["code_blocks"][2]["code"] == "print(y)"
            assert entry["code_blocks"][2]["result"]["stdout"] == "20"

    def test_code_block_with_stderr(self):
        """Code block with stderr should be logged correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            iteration = RLMIteration(
                prompt="Error test",
                response="This will fail",
                code_blocks=[
                    CodeBlock(
                        code="1 / 0",
                        result=REPLResult(
                            stdout="",
                            stderr="ZeroDivisionError: division by zero",
                            locals={},
                        ),
                    ),
                ],
            )

            logger.log(iteration)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert entry["code_blocks"][0]["result"]["stderr"] == (
                "ZeroDivisionError: division by zero"
            )

    def test_metadata_with_complex_kwargs(self):
        """Metadata with complex backend/environment kwargs should serialize."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RLMLogger(temp_dir)
            metadata = RLMMetadata(
                root_model="gpt-4-turbo",
                max_depth=5,
                max_iterations=20,
                backend="azure_openai",
                backend_kwargs={
                    "api_key": "sk-xxx",
                    "api_version": "2024-01-01",
                    "azure_endpoint": "https://example.openai.azure.com",
                    "timeout": 30,
                    "max_retries": 3,
                },
                environment_type="docker",
                environment_kwargs={
                    "image": "python:3.11-slim",
                    "memory_limit": "2g",
                    "cpu_limit": 2,
                    "volumes": ["/data:/data:ro"],
                },
            )

            logger.log_metadata(metadata)

            with open(logger.log_file_path) as f:
                entry = json.loads(f.readline())

            assert entry["backend_kwargs"]["api_version"] == "2024-01-01"
            assert entry["environment_kwargs"]["memory_limit"] == "2g"
            assert entry["environment_kwargs"]["volumes"] == ["/data:/data:ro"]
