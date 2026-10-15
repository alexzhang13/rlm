"""Tests for RLMLogger in-memory and disk logging."""

import json
import tempfile
from pathlib import Path

from rlm.core.types import CodeBlock, REPLResult, RLMIteration, RLMMetadata
from rlm.logger.rlm_logger import RLMLogger


def _make_iteration(code: str = "print(42)", stdout: str = "42\n", final_answer: str | None = None) -> RLMIteration:
    """Helper to build an RLMIteration with sensible defaults."""
    repl_result = REPLResult(stdout=stdout, stderr="", locals={})
    return RLMIteration(
        prompt="do something",
        response=f"```python\n{code}\n```",
        code_blocks=[CodeBlock(code=code, result=repl_result)],
        final_answer=final_answer,
    )


def test_logger_in_memory_capture():
    """Logger captures metadata and iterations in memory correctly."""
    logger = RLMLogger(log_dir=None)
    assert logger.get_trajectory() is None
    assert logger.iteration_count == 0

    # Initialize metadata with all required fields
    metadata = RLMMetadata(
        root_model="mock-model",
        max_depth=2,
        max_iterations=5,
        backend="openai",
        backend_kwargs={},
        environment_type="local",
        environment_kwargs={},
    )
    logger.log_metadata(metadata)
    logger.log_metadata(metadata)  # Ignored by guard

    iteration = _make_iteration()
    logger.log(iteration)

    assert logger.iteration_count == 1
    trajectory = logger.get_trajectory()
    assert trajectory is not None
    assert "run_metadata" in trajectory
    assert len(trajectory["iterations"]) == 1
    assert trajectory["iterations"][0]["iteration"] == 1

    logger.clear_iterations()
    assert logger.iteration_count == 0
    assert len(logger.get_trajectory()["iterations"]) == 0


def test_logger_disk_persistence():
    """Logger correctly writes metadata and iterations to JSONL files on disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = RLMLogger(log_dir=tmpdir, file_name="test_run")
        assert logger.log_file_path is not None

        metadata = RLMMetadata(
            root_model="mock-model",
            max_depth=2,
            max_iterations=3,
            backend="openai",
            backend_kwargs={},
            environment_type="local",
            environment_kwargs={},
        )
        logger.log_metadata(metadata)

        assert Path(logger.log_file_path).exists()

        iteration = _make_iteration(code="x = 10", stdout="", final_answer="done")
        logger.log(iteration)

        lines = Path(logger.log_file_path).read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

        entry_meta = json.loads(lines[0])
        assert entry_meta["type"] == "metadata"

        entry_iter = json.loads(lines[1])
        assert entry_iter["type"] == "iteration"
        assert entry_iter["code_blocks"][0]["code"] == "x = 10"
