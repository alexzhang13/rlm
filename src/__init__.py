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
from .prompts import SYSTEM_PROMPT, EXTRACTION_PROMPT, VALIDATION_PROMPT

# Week 2 simplified summarizer (5 fields only)
try:
    from .rlm_summarizer import (
        AdmissionSummarizerWeek2,
        create_summarizer_week2,
        RLM_MEDICAL_SYSTEM_PROMPT,
        EXTRACTION_USER_PROMPT,
        FIELDS,
        FIELD_PROMPTS
    )
    from .schema import (
        AdmissionSummaryV2,
        ImmutableAdmissionRecord,
        SCHEMA_JSON
    )
    HAS_RLM = True
except ImportError:
    HAS_RLM = False

__all__ = [
    # Original summarizer
    'AdmissionSummarizer',
    'create_summarizer',
    'SYSTEM_PROMPT',
    'EXTRACTION_PROMPT',
    'VALIDATION_PROMPT',
    
    # Week 2 simplified (if RLM available)
    'AdmissionSummarizerWeek2',
    'create_summarizer_week2',
    'AdmissionSummaryV2',
    'ImmutableAdmissionRecord',
    'HAS_RLM',
    'SCHEMA_JSON',
    'RLM_MEDICAL_SYSTEM_PROMPT',
    'EXTRACTION_USER_PROMPT',
    'FIELDS',
    'FIELD_PROMPTS'
]
