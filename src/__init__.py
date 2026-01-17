"""
Summarizer Module

Provides tools for extracting structured admission summaries from
MIMIC-IV discharge notes using RLM (Recursive Language Models).

Week 2 Simplified Schema:
{
    "diagnoses": [],
    "key_events": [],
    "open_issues": [],
    "complications": [],
    "disposition": ""
}
"""

# Original summarizer (comprehensive schema)
from .admission_summarizer import AdmissionSummarizer, create_summarizer
from .prompts import EXTRACTION_PROMPT, SYSTEM_PROMPT, VALIDATION_PROMPT

# Week 2 simplified summarizer (5 fields only)
try:
    from .rlm_summarizer import (
        EXTRACTION_USER_PROMPT,
        FIELD_PROMPTS,
        FIELDS,
        RLM_MEDICAL_SYSTEM_PROMPT,
        AdmissionSummarizerWeek2,
        create_summarizer_week2,
    )
    from .rlm_summarizer_batched import (
        AdmissionSummarizerV3,
        AdmissionSummaryV3,
        create_summarizer_v3,
    )
    from .schema import SCHEMA_JSON, AdmissionSummaryV2, ImmutableAdmissionRecord

    HAS_RLM = True
except ImportError:
    HAS_RLM = False

__all__ = [
    # Original summarizer
    "AdmissionSummarizer",
    "create_summarizer",
    "SYSTEM_PROMPT",
    "EXTRACTION_PROMPT",
    "VALIDATION_PROMPT",
    # Week 2 simplified (if RLM available)
    "AdmissionSummarizerWeek2",
    "create_summarizer_week2",
    "AdmissionSummaryV2",
    "ImmutableAdmissionRecord",
    "HAS_RLM",
    "SCHEMA_JSON",
    "RLM_MEDICAL_SYSTEM_PROMPT",
    "EXTRACTION_USER_PROMPT",
    "FIELDS",
    "FIELD_PROMPTS",
    # V3 batched summarizer
    "AdmissionSummarizerV3",
    "AdmissionSummaryV3",
    "create_summarizer_v3",
]
