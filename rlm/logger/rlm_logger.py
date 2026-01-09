"""
Logger for RLM iterations.

Writes RLMIteration data to JSON-lines files for analysis and debugging.
"""

import json
import os
import uuid
from collections.abc import Callable
from datetime import datetime

from rlm.core.types import RLMIteration, RLMMetadata


class RLMLogger:
    """Logger that writes RLMIteration data to a JSON-lines file."""

    def __init__(
        self, log_dir: str, file_name: str = "rlm", on_log: Callable[[dict], None] | None = None
    ):
        self.log_dir = log_dir
        self.on_log = on_log
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
        if self.on_log:
            self.on_log(entry)

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

        if self.on_log:
            self.on_log(entry)

    @property
    def iteration_count(self) -> int:
        return self._iteration_count
