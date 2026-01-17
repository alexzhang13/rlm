"""
RLM Summarizer V3 - Field-by-Field Extraction with llm_query_batched()

This version uses the RLM pattern with llm_query_batched() to extract 
each field in parallel, giving each sub-LLM full context and focused task.

Key differences from V2:
- V2: One llm_query() call for all 5 fields
- V3: llm_query_batched() with 5 parallel calls, one per field

Benefits:
- Each sub-LLM focuses on ONE extraction task
- Full context available for each field
- Parallel execution (not 5x slower)
- Potentially higher quality for nuanced fields
"""

import json
import logging
import os
import re
import ast
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from rlm import RLM

logger = logging.getLogger(__name__)


# =====================================================
# V3 QUERY - Field-by-Field Batched Extraction
# =====================================================

RLM_V3_QUERY = """Extract structured information from the discharge note in `context['context']`.

The note has headers like: <DISCHARGE DIAGNOSIS>, <DISCHARGE DISPOSITION>, <HISTORY OF PRESENT ILLNESS>, <PAST MEDICAL HISTORY>, <PHYSICAL EXAM>, etc.

TASK: Use llm_query_batched() to extract ALL 5 fields IN PARALLEL, then combine results and return immediately with FINAL_VAR().

Execute this code:
```repl
import json

text = context['context']

# Define 5 focused prompts - each extracts ONE field
prompts = [
    f'''From this discharge note, extract ONLY the DIAGNOSES.
Include: primary diagnosis, secondary diagnoses, active conditions.
Exclude: past medical history conditions unless actively addressed.
Return as a JSON list of short strings.

Text:
{text}

Return ONLY a JSON list like: ["diagnosis 1", "diagnosis 2"]''',

    f'''From this discharge note, extract ONLY the KEY CLINICAL EVENTS.
Include: procedures, surgeries, significant findings, treatments given.
Exclude: routine vitals, medications.
Return as a JSON list of short strings.

Text:
{text}

Return ONLY a JSON list like: ["event 1", "event 2"]''',

    f'''From this discharge note, extract ONLY the OPEN ISSUES at discharge.
Include: unresolved problems, pending tests, ongoing treatments, follow-up required.
Return as a JSON list of short strings.

Text:
{text}

Return ONLY a JSON list like: ["issue 1", "issue 2"]''',

    f'''From this discharge note, extract ONLY COMPLICATIONS during THIS admission.
Include: new problems that developed during hospital stay.
Exclude: historical complications from past surgeries.
Return as a JSON list of short strings. If none, return [].

Text:
{text}

Return ONLY a JSON list like: ["complication 1"] or []''',

    f'''From this discharge note, extract ONLY the DISPOSITION.
This is where the patient was discharged to.
Return as a single short string.

Text:
{text}

Return ONLY the disposition like: "Home" or "Home With Service" or "SNF"'''
]

# Run all 5 queries IN PARALLEL
results = llm_query_batched(prompts)

# Parse each result
def parse_list(s):
    try:
        return json.loads(s) if s.strip().startswith('[') else []
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

print(f"Extracted: {len(result['diagnoses'])} diagnoses, {len(result['key_events'])} events")
```

FINAL_VAR(result)
"""


@dataclass
class AdmissionSummaryV3:
    """Simplified 5-field admission summary - V3."""
    diagnoses: list
    key_events: list  
    open_issues: list
    complications: list
    disposition: str


class AdmissionSummarizerV3:
    """
    RLM-based summarizer using field-by-field batched extraction.
    
    Uses llm_query_batched() to run 5 parallel sub-LLM calls,
    each focused on extracting one specific field.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3-pro-preview",
        max_iterations: int = 5,  # Should complete in 2-3 iterations
        max_depth: int = 1,
        verbose: bool = False
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.verbose = verbose
        
        logger.info(f"Initialized AdmissionSummarizerV3: model={model_name}, max_iter={max_iterations}")
    
    def _create_rlm(self) -> RLM:
        """Create an RLM instance for extraction."""
        return RLM(
            backend="gemini",
            backend_kwargs={
                "api_key": self.api_key,
                "model_name": self.model_name
            },
            environment="local",
            max_iterations=self.max_iterations,
            max_depth=self.max_depth,
            verbose=self.verbose
        )
    
    def summarize(self, discharge_text: str) -> Dict[str, Any]:
        """
        Extract all 5 fields using batched parallel queries.
        
        Args:
            discharge_text: The discharge summary text
            
        Returns:
            Dict with diagnoses, key_events, open_issues, complications, disposition
        """
        rlm = self._create_rlm()
        
        try:
            result = rlm.completion(
                prompt={"context": discharge_text, "query": RLM_V3_QUERY},
                root_prompt="Extract diagnoses, key_events, open_issues, complications, disposition using batched queries"
            )
            
            parsed = self._safe_parse(result)
            
            if isinstance(parsed, dict) and 'diagnoses' in parsed:
                return {
                    "diagnoses": parsed.get("diagnoses", []),
                    "key_events": parsed.get("key_events", []),
                    "open_issues": parsed.get("open_issues", []),
                    "complications": parsed.get("complications", []),
                    "disposition": parsed.get("disposition", "")
                }
            else:
                logger.warning(f"V3: Unexpected result type: {type(parsed)}")
                return self._empty_summary()
                
        except Exception as e:
            logger.error(f"Error in V3 summarize: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_summary()
    
    def _safe_parse(self, result: Any) -> Any:
        """Parse RLM result handling various formats."""
        try:
            if hasattr(result, 'response'):
                text = result.response
            else:
                text = result
            
            if text is None:
                return {}
            
            if isinstance(text, dict):
                return text
            
            if isinstance(text, list):
                return {}
            
            text = str(text)
            
            # Try JSON parse
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
            
            # Try Python literal eval
            try:
                result = ast.literal_eval(text)
                if isinstance(result, dict):
                    return result
            except (ValueError, SyntaxError):
                pass
            
            # Try to find JSON in text
            json_match = re.search(r'\{.*"diagnoses".*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {}
            
        except Exception as e:
            logger.warning(f"Parse error: {e}")
            return {}
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary dict."""
        return {
            "diagnoses": [],
            "key_events": [],
            "open_issues": [],
            "complications": [],
            "disposition": ""
        }


def create_summarizer_v3(
    api_key: Optional[str] = None,
    model_name: str = "gemini-3-pro-preview",
    max_iterations: int = 5,
    verbose: bool = False
) -> AdmissionSummarizerV3:
    """Factory function to create V3 summarizer."""
    return AdmissionSummarizerV3(
        api_key=api_key,
        model_name=model_name,
        max_iterations=max_iterations,
        verbose=verbose
    )
