"""
RLM Summarizer - Field-by-Field Extraction with llm_query_batched()

This version uses the RLM pattern with llm_query_batched() to extract
each field in parallel.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from rlm import RLM

logger = logging.getLogger(__name__)


@dataclass
class AdmissionSummary:
    """Admission summary schema."""

    diagnoses: list
    key_events: list
    open_issues: list
    complications: list
    disposition: str


class AdmissionSummarizer:
    """
    RLM-based summarizer using field-by-field batched extraction.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-flash",
        max_iterations: int = 8,
        max_depth: int = 1,
        verbose: bool = False,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set")
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.verbose = verbose

    def _create_rlm(self) -> RLM:
        return RLM(
            backend="gemini",
            backend_kwargs={"api_key": self.api_key, "model_name": self.model_name},
            environment="local",
            max_iterations=self.max_iterations,
            max_depth=self.max_depth,
            verbose=self.verbose,
        )

    def summarize(self, discharge_text: str) -> dict[str, Any]:
        """
        Extract all 5 fields using batched parallel queries.

        Args:
            discharge_text: The discharge summary text

        Returns:
            Dict with diagnoses, key_events, open_issues, complications, disposition
        """
        rlm = self._create_rlm()

        # Root prompt instructs the RLM to use batched queries
        root_prompt = """Extract 5 fields from the discharge note in `context` using parallel batched queries.

Execute this code:
```repl
import json

text = context  # context is the discharge note string

# Define 5 focused prompts - each extracts ONE field
prompt_diagnoses = "From this discharge note, extract ONLY the DIAGNOSES as a JSON list. Include primary and secondary diagnoses. Return ONLY a JSON list like [\\\"diagnosis 1\\\", \\\"diagnosis 2\\\"].\\n\\nText:\\n" + text[:40000]

prompt_events = "From this discharge note, extract ONLY the KEY CLINICAL EVENTS as a JSON list. Include procedures, surgeries, treatments. Return ONLY a JSON list.\\n\\nText:\\n" + text[:40000]

prompt_issues = "From this discharge note, extract ONLY the OPEN ISSUES at discharge as a JSON list. Include unresolved problems, pending tests. Return ONLY a JSON list.\\n\\nText:\\n" + text[:40000]

prompt_complications = "From this discharge note, extract ONLY COMPLICATIONS during this admission as a JSON list. If none, return [].\\n\\nText:\\n" + text[:40000]

prompt_disposition = "From this discharge note, extract ONLY the DISPOSITION (where discharged to) as a single string like Home or SNF.\\n\\nText:\\n" + text[:40000]

prompts = [prompt_diagnoses, prompt_events, prompt_issues, prompt_complications, prompt_disposition]

# Run all 5 queries IN PARALLEL
print("Running batched queries...")
results = llm_query_batched(prompts)
print(f"Got {len(results)} results")

def parse_list(s):
    try:
        parsed = json.loads(s)
        return parsed if isinstance(parsed, list) else []
    except:
        return []

def parse_string(s):
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s

result = {
    "diagnoses": parse_list(results[0]),
    "key_events": parse_list(results[1]),
    "open_issues": parse_list(results[2]),
    "complications": parse_list(results[3]),
    "disposition": parse_string(results[4])
}

print(f"Extracted: {len(result['diagnoses'])} diagnoses, {len(result['key_events'])} events, disposition: {result['disposition']}")
```

FINAL_VAR(result)"""

        result = rlm.completion(prompt=discharge_text, root_prompt=root_prompt)

        if isinstance(result, dict):
            return result
        return {
            "diagnoses": [],
            "key_events": [],
            "open_issues": [],
            "complications": [],
            "disposition": "",
        }


def create_summarizer(
    api_key: str | None = None,
    model_name: str = "gemini-2.5-flash",
    max_iterations: int = 8,
    verbose: bool = False,
) -> AdmissionSummarizer:
    return AdmissionSummarizer(
        api_key=api_key, model_name=model_name, max_iterations=max_iterations, verbose=verbose
    )
