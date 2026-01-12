"""
Logger for RLM iterations.

Writes RLMIteration data to JSON-lines files for analysis and debugging.
"""

import json
import os
import uuid
from datetime import datetime

from rlm.core.types import RLMIteration, RLMMetadata


class RLMLogger:
    """Logger that writes RLMIteration data to a JSON-lines file."""

    def __init__(self, log_dir: str, file_name: str = "rlm"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_id = str(uuid.uuid4())[:8]
        self.log_file_path = os.path.join(log_dir, f"{file_name}_{timestamp}_{run_id}.jsonl")

        self._iteration_count = 0
        self._metadata_logged = False

    def log_metadata(self, metadata: RLMMetadata):
        """Log RLM metadata as the first entry in the file."""
        if self._metadata_logged:
            return

        entry = {
            "type": "metadata",
            "timestamp": datetime.now().isoformat(),
            **metadata.to_dict(),
        }

        with open(self.log_file_path, "a") as f:
            json.dump(entry, f)
            f.write("\n")

        self._metadata_logged = True

    def log_run_context(
        self,
        prompt,
        root_prompt: str | None = None,
        environment_type: str | None = None,
        environment_kwargs: dict | None = None,
        session_mode: bool | None = None,
    ) -> dict:
        """Log the prompt payload and optional root prompt for a single run."""
        entry = {
            "type": "run_context",
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "root_prompt": root_prompt,
            "environment_type": environment_type,
            "environment_kwargs": environment_kwargs or {},
            "session_mode": session_mode,
        }

        with open(self.log_file_path, "a") as f:
            json.dump(entry, f)
            f.write("\n")

        return entry

    def log(self, iteration: RLMIteration):
        """Log an RLMIteration to the file."""
        self._iteration_count += 1

        entry = {
            "type": "iteration",
            "iteration": self._iteration_count,
            "timestamp": datetime.now().isoformat(),
            **iteration.to_dict(),
        }

        with open(self.log_file_path, "a") as f:
            json.dump(entry, f)
            f.write("\n")

    @property
    def iteration_count(self) -> int:
        return self._iteration_count
