#!/usr/bin/env python3
"""
Prompt templates for admission summarization.

Contains system prompts, extraction prompts, and validation prompts
used by AdmissionSummarizer.
"""

SYSTEM_PROMPT = """You are a medical information extraction specialist.
Your task is to extract structured admission summaries from hospital discharge notes.

RULES (CRITICAL):
- Extract ONLY facts explicitly stated in the text
- Do NOT infer, interpret, or generalize
- Do NOT add severity unless explicitly stated
- Do NOT include medications, labs, vitals, or social history unless relevant to diagnoses
- Use short phrases copied or lightly normalized from the text
- If a field is not mentioned, return an empty list or empty string
"""

EXTRACTION_PROMPT = """Extract a structured admission summary from the following discharge note.

Return ONLY a valid JSON object with exactly these fields:
{
  "diagnoses": [],
  "key_events": [],
  "open_issues": [],
  "complications": [],
  "disposition": ""
}

FIELD DEFINITIONS:
- diagnoses: List all diagnoses explicitly stated in the discharge summary
- key_events: List major clinical events that occurred during this admission
- open_issues: List unresolved or ongoing clinical issues at discharge
- complications: List any complications explicitly mentioned
- disposition: State the discharge disposition (e.g., home, SNF, expired)

RULES:
- Extract ONLY facts explicitly stated in the text
- Do NOT infer or interpret
- Use short phrases from the text
- If a field is not mentioned, return empty list or empty string

Discharge Note:
{discharge_text}

Return ONLY valid JSON, nothing else."""

VALIDATION_PROMPT = """Validate and correct the following extracted admission summary.

Original discharge note excerpt (first 2000 chars):
{note_excerpt}

Extracted summary:
{extracted_summary}

Check that:
1. All diagnoses are explicitly stated in the note
2. Key events actually occurred during this admission
3. Open issues are truly unresolved at discharge
4. Complications are explicitly mentioned
5. Disposition matches what's stated

If corrections are needed, return the corrected JSON.
If the extraction is accurate, return it unchanged.
Return ONLY valid JSON."""
