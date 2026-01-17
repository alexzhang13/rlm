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
        model_name: str = "gemini-2.5-flash",
        max_iterations: int = 8,
        max_depth: int = 1,
        verbose: bool = False
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set")
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

# Parse each result
def safe_parse_list(s):
    s = s.strip()
    try:
        # Try direct JSON parse
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return parsed
        return []
    except:
        # Try to find JSON list in response
        import re
        match = re.search(r'\\[.*?\\]', s, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return []

def safe_parse_string(s):
    s = s.strip()
    # Remove quotes if present
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    # Take first line, remove common prefixes
    first_line = s.split('\\n')[0].strip()
    for prefix in ['Disposition:', 'The disposition is', 'Patient discharged to']:
        if first_line.lower().startswith(prefix.lower()):
            first_line = first_line[len(prefix):].strip()
    return first_line[:100]  # Limit length

result = {
    "diagnoses": safe_parse_list(results[0]),
    "key_events": safe_parse_list(results[1]),
    "open_issues": safe_parse_list(results[2]),
    "complications": safe_parse_list(results[3]),
    "disposition": safe_parse_string(results[4])
}

print(f"Extracted: {len(result['diagnoses'])} diagnoses, {len(result['key_events'])} events, disposition: {result['disposition']}")
```

FINAL_VAR(result)"""
        
        try:
            result = rlm.completion(
                prompt=discharge_text,  # Pass text directly, not as dict
                root_prompt=root_prompt
            )
            
            logger.info(f"RLM V3 response type: {type(result.response) if hasattr(result, 'response') else type(result)}")
            
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
                # Try fallback parsing
                if hasattr(result, 'response') and isinstance(result.response, str):
                    return self._parse_fallback_response(result.response)
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
                parsed = ast.literal_eval(text)
                if isinstance(parsed, dict):
                    return parsed
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
    
    def _parse_fallback_response(self, text: str) -> Dict[str, Any]:
        """Parse a fallback string response that may contain JSON."""
        if not text:
            return self._empty_summary()
            
        text = text.strip()
        
        # Try direct JSON parse
        try:
            result = json.loads(text)
            if isinstance(result, dict) and 'diagnoses' in result:
                return result
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from code blocks or raw text
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[^{}]*"diagnoses"[^{}]*\}',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match.strip() if isinstance(match, str) else match)
                    if isinstance(result, dict) and 'diagnoses' in result:
                        return result
                except:
                    pass
        
        return self._empty_summary()
    
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
    model_name: str = "gemini-2.5-flash",
    max_iterations: int = 8,
    verbose: bool = False
) -> AdmissionSummarizerV3:
    """Factory function to create V3 summarizer."""
    return AdmissionSummarizerV3(
        api_key=api_key,
        model_name=model_name,
        max_iterations=max_iterations,
        verbose=verbose
    )
