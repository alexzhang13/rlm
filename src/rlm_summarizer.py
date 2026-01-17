#!/usr/bin/env python3
"""
Week 2 Admission Summarizer - Simplified Schema

Uses RLM (Recursive Language Model) pattern for field-by-field extraction.
Each admission produces ONE immutable summary file with only essential fields.

Schema:
{
  "diagnoses": [],
  "key_events": [],
  "open_issues": [],
  "complications": [],
  "disposition": ""
}
"""

import json
import os
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from rlm import RLM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =====================================================
# SIMPLIFIED SCHEMA - 5 Essential Fields Only
# =====================================================

FIELDS = [
    "diagnoses",
    "key_events", 
    "open_issues",
    "complications",
    "disposition"
]

FIELD_PROMPTS = {
    "diagnoses": "List all diagnoses explicitly stated in the discharge summary.",
    "key_events": "List major clinical events that occurred during this admission.",
    "open_issues": "List unresolved or ongoing clinical issues at discharge.",
    "complications": "List any complications explicitly mentioned.",
    "disposition": "State the discharge disposition (e.g., home, SNF, expired)."
}


# =====================================================
# RLM SYSTEM PROMPT - Strict Fact Extraction
# =====================================================

RLM_MEDICAL_SYSTEM_PROMPT = """
You are extracting STRUCTURED FACTS from a hospital discharge summary.

You must produce a JSON object with EXACTLY these fields:

{
  "diagnoses": [],
  "key_events": [],
  "open_issues": [],
  "complications": [],
  "disposition": ""
}

RULES (CRITICAL):
- Extract ONLY facts explicitly stated in the text
- Do NOT infer, interpret, or generalize
- Do NOT add severity unless explicitly stated
- Do NOT include medications, labs, vitals, or social history
- Do NOT include follow-up plans unless stated as unresolved issues
- Use short phrases copied or lightly normalized from the text
- If a field is not mentioned, return an empty list or empty string

You may use the REPL to:
- Parse sections
- Call llm_query() for narrow extraction tasks

Return the final JSON using FINAL_VAR().
"""


EXTRACTION_USER_PROMPT = """
Extract a structured admission summary from the discharge note.

Focus ONLY on:
- diagnoses
- key_events
- open_issues
- complications
- disposition

Do not infer or add information not explicitly stated.
Return ONLY valid JSON using FINAL_VAR().
"""


# =====================================================
# ADMISSION SUMMARIZER - Week 2 Version
# =====================================================

class AdmissionSummarizerWeek2:
    """
    RLM-based admission summarizer with simplified schema.
    
    Extracts each field separately for higher accuracy,
    then combines into a single immutable admission file.
    
    Key Parameters:
    - max_iterations: Max REPL iterations per RLM call (default: 8)
    - max_depth: Max recursion depth for sub-LM calls (default: 1)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3-pro-preview",
        max_iterations: int = 8,
        max_depth: int = 1,
        verbose: bool = False
    ):
        """
        Initialize the summarizer.
        
        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var)
            model_name: Model to use for extraction
            max_iterations: Max RLM iterations per extraction (default: 8)
            max_depth: Max recursion depth for sub-LM calls (default: 1)
            verbose: Enable verbose output
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set")
        
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.verbose = verbose
        
        logger.info(f"Initialized AdmissionSummarizerWeek2: model={model_name}, max_iter={max_iterations}, max_depth={max_depth}")
    
    def _create_rlm(self) -> RLM:
        """Create an RLM instance for extraction.
        
        Uses the default RLM system prompt which explains REPL, llm_query, FINAL_VAR.
        Our extraction instructions go in the query, not system prompt.
        """
        return RLM(
            backend="gemini",
            backend_kwargs={
                "api_key": self.api_key,
                "model_name": self.model_name
            },
            # NOTE: Do NOT set custom_system_prompt - we need the default RLM 
            # system prompt that explains how to use REPL, llm_query, FINAL_VAR
            environment="local",
            max_iterations=self.max_iterations,
            max_depth=self.max_depth,
            verbose=self.verbose
        )
    
    def summarize(self, discharge_text: str) -> Dict[str, Any]:
        """
        Extract structured summary from discharge text.
        
        Uses field-by-field extraction for higher accuracy.
        
        Args:
            discharge_text: The discharge summary text
            
        Returns:
            Dict with diagnoses, key_events, open_issues, complications, disposition
        """
        rlm = self._create_rlm()
        extracted = {}
        
        for field in FIELDS:
            logger.info(f"Extracting field: {field}")
            
            prompt = f"""
{FIELD_PROMPTS[field]}

Rules:
- Extract ONLY what is explicitly stated
- If none found, return empty list or empty string
Return JSON only.
"""
            try:
                result = rlm.completion(
                    prompt={"context": discharge_text, "query": prompt},
                    root_prompt=f"Extract {field}"
                )
                extracted[field] = self._safe_parse(result, field)
                
            except Exception as e:
                logger.warning(f"Error extracting {field}: {e}")
                extracted[field] = [] if field != "disposition" else ""
        
        return extracted
    
    def summarize_all_at_once(self, discharge_text: str) -> Dict[str, Any]:
        """
        Extract all fields using the RLM REPL pattern.
        
        Args:
            discharge_text: The discharge summary text
            
        Returns:
            Dict with all 5 fields
        """
        rlm = self._create_rlm()
        
        # Simpler, more robust prompt that handles JSON parsing errors
        root_prompt = """Extract a JSON summary from the discharge note in the `context` variable.

Execute this code to extract the summary:
```repl
import json

# Build the extraction prompt
extraction_prompt = "Extract from this discharge note and return ONLY valid JSON with these exact fields:\\n"
extraction_prompt += '{"diagnoses": [], "key_events": [], "open_issues": [], "complications": [], "disposition": ""}\\n'
extraction_prompt += "Rules: Extract ONLY explicit facts. Use short phrases. Return ONLY the JSON.\\n\\n"
extraction_prompt += "Discharge Note:\\n" + context[:50000]  # Limit context size

# Query sub-LLM
response = llm_query(extraction_prompt)
print("Sub-LLM response:", response[:500])

# Try to parse the JSON response
try:
    # Try direct parse first
    result = json.loads(response)
except json.JSONDecodeError:
    # Try to extract JSON from response
    import re
    json_match = re.search(r'\{[^{}]*"diagnoses"[^{}]*\}', response, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
    else:
        # Fallback: create empty result
        result = {"diagnoses": [], "key_events": [], "open_issues": [], "complications": [], "disposition": ""}

print("Parsed result:", result)
```

Now return the result:
FINAL_VAR(result)"""
        
        try:
            result = rlm.completion(
                prompt=discharge_text,
                root_prompt=root_prompt
            )
            
            logger.info(f"RLM response type: {type(result.response) if hasattr(result, 'response') else type(result)}")
            
            parsed = self._safe_parse(result, "all")
            
            # Ensure all fields present
            if isinstance(parsed, dict) and 'diagnoses' in parsed:
                summary = {
                    "diagnoses": parsed.get("diagnoses", []),
                    "key_events": parsed.get("key_events", []),
                    "open_issues": parsed.get("open_issues", []),
                    "complications": parsed.get("complications", []),
                    "disposition": parsed.get("disposition", "")
                }
                return summary
            else:
                logger.warning(f"RLM did not return expected structure, got: {type(parsed)}")
                # Try to extract from string if it's a fallback response
                if hasattr(result, 'response') and isinstance(result.response, str):
                    logger.info("Attempting to parse fallback string response")
                    return self._parse_fallback_response(result.response)
                return self._empty_summary()
            
        except Exception as e:
            logger.error(f"Error in summarize_all_at_once: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_summary()
    
    def _parse_fallback_response(self, text: str) -> Dict[str, Any]:
        """Parse a fallback string response that may contain JSON.
        
        Tries multiple strategies to extract JSON:
        1. Direct JSON parse
        2. Extract from markdown code blocks (closed or unclosed)
        3. Extract JSON after 'json' marker
        4. Balanced brace extraction for JSON with 'diagnoses'
        """
        if not text:
            return self._empty_summary()
            
        text = text.strip()
        
        # Strategy 1: Try direct JSON parse
        try:
            result = json.loads(text)
            if isinstance(result, dict) and 'diagnoses' in result:
                return result
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from markdown code blocks (```json ... ``` or ``` ... ```)
        # Try both closed and potentially unclosed blocks
        code_block_patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # Closed json block
            r'```\s*([\s\S]*?)\s*```',       # Closed block
            r'```json\s*([\s\S]+)',           # Unclosed json block (greedy)
            r'```\s*(\{[\s\S]+)',             # Unclosed block starting with {
        ]
        for pattern in code_block_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                json_str = match.strip()
                # Try to parse, extracting balanced JSON if needed
                extracted = self._extract_balanced_json(json_str)
                if extracted:
                    return extracted
        
        # Strategy 3: Look for JSON after 'json' marker (common in LLM responses)
        json_marker_idx = text.lower().find('json')
        if json_marker_idx != -1:
            remaining = text[json_marker_idx + 4:].strip()
            extracted = self._extract_balanced_json(remaining)
            if extracted:
                return extracted
        
        # Strategy 4: Find first { and try balanced brace extraction
        extracted = self._extract_balanced_json(text)
        if extracted:
            return extracted
        
        # Couldn't parse, return empty
        logger.warning(f"Could not extract JSON from fallback response: {text[:200]}...")
        return self._empty_summary()
    
    def _extract_balanced_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a balanced JSON object from text using brace matching."""
        start_idx = text.find('{')
        if start_idx == -1:
            return None
            
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text[start_idx:], start_idx):
            if escape_next:
                escape_next = False
                continue
            if char == '\\' and in_string:
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
                
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    potential_json = text[start_idx:i+1]
                    try:
                        result = json.loads(potential_json)
                        if isinstance(result, dict) and 'diagnoses' in result:
                            return result
                    except json.JSONDecodeError:
                        pass
                    # Try to find another JSON object
                    return self._extract_balanced_json(text[i+1:])
        
        return None
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return an empty summary dict."""
        return {
            "diagnoses": [],
            "key_events": [],
            "open_issues": [],
            "complications": [],
            "disposition": ""
        }
    
    def _safe_parse(self, result: Any, field: str) -> Any:
        """Safely parse RLM result to JSON or return directly if already parsed."""
        try:
            # Handle RLMChatCompletion object from RLM
            if hasattr(result, 'response'):
                text = result.response
            else:
                text = result
            
            # Handle None response (RLM didn't produce FINAL_VAR)
            if text is None:
                logger.warning(f"RLM returned None for {field}, using default")
                if field == "disposition":
                    return ""
                if field == "all":
                    return {}
                return []
            
            # If it's already a dict, return it directly (FINAL_VAR returns Python objects)
            if isinstance(text, dict):
                return text
            
            # If it's a list, return it directly
            if isinstance(text, list):
                # For 'all' field, we expect a dict, not list
                if field == "all":
                    logger.warning(f"RLM returned list instead of dict for {field}")
                    return {}
                return text
            
            # Convert to string if needed
            text = str(text)
            
            # Try direct JSON parse first
            try:
                parsed = json.loads(text)
                if field == "all" and isinstance(parsed, dict) and 'diagnoses' in parsed:
                    return parsed
                elif field != "all":
                    return parsed
            except json.JSONDecodeError:
                pass
            
            # Try Python literal eval (for dict strings from FINAL_VAR)
            import ast
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, dict):
                    if field == "all" and 'diagnoses' in parsed:
                        return parsed
                    elif field != "all":
                        return parsed
            except (ValueError, SyntaxError):
                pass
            
            # For 'all' field, use robust fallback extraction
            if field == "all":
                return self._parse_fallback_response(text)
            
            # For other fields, try simpler extraction
            extracted = self._extract_balanced_json(text)
            if extracted is not None:
                return extracted
            
            # Return default based on field type
            if field == "disposition":
                return text.strip()[:100] if text else ""
            return []
            
        except Exception as e:
            logger.warning(f"Error parsing RLM result for {field}: {e}")
            if field == "disposition":
                return ""
            if field == "all":
                return {}
            return []
    
    def create_admission_file(
        self,
        subject_id: int,
        hadm_id: int,
        note_id: str,
        discharge_text: str,
        output_dir: Optional[Path] = None,
        method: str = "all_at_once"
    ) -> Dict[str, Any]:
        """
        Create an immutable admission summary file.
        
        Args:
            subject_id: Patient subject ID
            hadm_id: Hospital admission ID
            note_id: Discharge note ID (for traceability)
            discharge_text: The discharge summary text
            output_dir: Directory to save the file (optional)
            method: "all_at_once" or "field_by_field"
            
        Returns:
            Complete admission record dict
        """
        # Extract summary
        if method == "field_by_field":
            summary = self.summarize(discharge_text)
        else:
            summary = self.summarize_all_at_once(discharge_text)
        
        # Create immutable record with note_id for traceability
        record = {
            "subject_id": subject_id,
            "hadm_id": hadm_id,
            "note_id": note_id,
            "admission_summary": summary
        }
        
        # Save to file if output_dir provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{subject_id}_{hadm_id}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(record, f, indent=2)
            
            logger.info(f"Saved admission file: {filepath}")
        
        return record


# =====================================================
# FACTORY FUNCTION
# =====================================================

def create_summarizer_week2(
    api_key: Optional[str] = None,
    model_name: str = "gemini-3-pro-preview"
) -> AdmissionSummarizerWeek2:
    """Factory function to create the Week 2 summarizer."""
    return AdmissionSummarizerWeek2(api_key=api_key, model_name=model_name)
