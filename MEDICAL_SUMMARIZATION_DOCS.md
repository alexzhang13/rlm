# Medical Discharge Note Summarization with RLM

## Overview

This project demonstrates the application of **Recursive Language Models (RLMs)** to extract structured summaries from hospital discharge notes using the MIMIC-IV dataset. We compare different approaches to understand the trade-offs between traditional LLM calls and RLM-based recursive extraction.

## Problem Statement

Hospital discharge notes contain critical medical information but are often long, unstructured text documents. Extracting key information consistently and accurately is challenging for several reasons:

- **Long Context**: Discharge notes can be 10,000+ characters
- **Medical Complexity**: Requires understanding medical terminology and relationships
- **Structured Output**: Need consistent JSON schema for downstream use
- **Accuracy**: Must extract ONLY explicitly stated facts (no hallucination)

## Our Approach: 5-Field Simplified Schema

We extract exactly 5 essential fields from each discharge note:

```json
{
  "diagnoses": ["list of diagnoses"],
  "key_events": ["major clinical events during admission"],
  "open_issues": ["unresolved issues at discharge"],
  "complications": ["complications that occurred"],
  "disposition": "where patient was discharged to (e.g., home, SNF)"
}
```

### Design Principles
- ✅ **Explicit Facts Only** - Extract only what is clearly stated
- ✅ **No Inference** - Don't interpret or generalize
- ✅ **Short Phrases** - Use concise text from the original note
- ✅ **Immutable Records** - One summary per admission

---

## Project Structure

```
rlm/
├── src/                                    # Source code for summarizers
│   ├── __init__.py                        # Package exports
│   ├── schema.py                          # Data schemas (AdmissionSummaryV2, ImmutableAdmissionRecord)
│   ├── prompts.py                         # Prompt templates for traditional LLM approach
│   ├── admission_summarizer.py            # Traditional single-pass LLM summarizer
│   ├── rlm_summarizer.py                  # RLM V2: Single llm_query() call
│   └── rlm_summarizer_batched.py          # RLM V3: Batched llm_query_batched() calls
│
├── data/                                   # Data storage
│   ├── dev_subset_50_patients.parquet     # Sample dataset (50 patients)
│   └── processed/                         # Output directory for results
│       ├── comparison_results.json        # Single-pass vs RLM V2 results
│       └── v2_v3_comparison.json          # RLM V2 vs V3 results
│
├── compare_summarizers.py                  # Experiment 1: Single-pass vs RLM
└── compare_rlm_single_vs_batched.py       # Experiment 2: RLM V2 vs V3
```

---

## Comparison Experiments

### Experiment 1: `compare_summarizers.py`
**Single-Pass LLM vs RLM Recursive Summarizer**

#### Approaches Compared

**Method 1: Single-Pass LLM (Baseline)**
- Direct LLM call with full discharge note
- One API call per patient
- Model: `gemini-2.5-flash`
- Prompt: "Extract JSON with these 5 fields..."

```python
def run_single_pass(discharge_text: str) -> dict:
    """Direct LLM call - no RLM, just extract JSON"""
    prompt = f"Extract summary from:\n{discharge_text}"
    response = client.generate_content(prompt)
    return json.loads(response.text)
```

**Method 2: RLM Recursive (V2)**
- Uses RLM pattern with REPL environment
- Model can write Python code to process context
- Can make recursive `llm_query()` calls
- Model: `gemini-2.5-flash`
- Max iterations: 8
- Max recursion depth: 1

```python
def run_rlm(discharge_text: str) -> dict:
    """RLM-based extraction with REPL"""
    summarizer = AdmissionSummarizerWeek2(
        model_name="gemini-2.5-flash",
        max_iterations=8
    )
    return summarizer.summarize_all_at_once(discharge_text)
```

#### How RLM V2 Works

The RLM has access to a Python REPL environment where:
1. `context` variable contains the discharge note
2. `llm_query(prompt)` function calls a sub-LLM
3. `FINAL_VAR(result)` returns the final answer

**Typical RLM V2 Execution Flow:**
```python
# Step 1: RLM analyzes the task
# Step 2: RLM writes code in REPL
import json

# Build extraction prompt
extraction_prompt = "Extract JSON: {...} from:\n" + context[:50000]

# Call sub-LLM
response = llm_query(extraction_prompt)

# Parse and validate JSON
try:
    result = json.loads(response)
except:
    # Fallback: extract JSON with regex
    result = extract_json_from_text(response)

# Step 3: Return result
FINAL_VAR(result)
```

#### Key Differences

| Aspect | Single-Pass LLM | RLM V2 |
|--------|-----------------|--------|
| **API Calls** | 1 per patient | 2-8 per patient |
| **Processing** | Direct extraction | Code generation → Execution → Sub-LLM call |
| **Context Handling** | Full context in prompt | Context in REPL environment |
| **Error Handling** | None (fails if JSON invalid) | Can retry/fallback in code |
| **Flexibility** | Fixed prompt | Can adapt strategy per note |

#### Results

Run with:
```bash
uv run compare_summarizers.py
```

Output saved to: `data/processed/comparison_results.json`

**Expected Findings:**
- Single-pass is **faster** (~5-10s per patient)
- RLM V2 is **slower** (~15-30s per patient, 2-3x slower)
- RLM V2 may be **more robust** (handles edge cases better)
- Both produce similar quality for straightforward notes

---

### Experiment 2: `compare_rlm_single_vs_batched.py`
**RLM V2 (Single Query) vs V3 (Batched Field-by-Field)**

#### Approaches Compared

**Method V2: RLM with Single llm_query()**
- One `llm_query()` call extracts all 5 fields at once
- Sub-LLM receives full context
- Returns complete JSON object

```python
# RLM V2 REPL code
extraction_prompt = "Extract all 5 fields:\n" + context
response = llm_query(extraction_prompt)
result = json.loads(response)
FINAL_VAR(result)
```

**Method V3: RLM with llm_query_batched()**
- Five **parallel** `llm_query_batched()` calls (one per field)
- Each sub-LLM focuses on extracting ONE field
- Results combined into final JSON

```python
# RLM V3 REPL code
fields = ["diagnoses", "key_events", "open_issues", "complications", "disposition"]
prompts = [f"Extract ONLY {field} from:\n{context}" for field in fields]

# Parallel execution!
responses = llm_query_batched(prompts)

# Combine results
result = {
    "diagnoses": parse_list(responses[0]),
    "key_events": parse_list(responses[1]),
    "open_issues": parse_list(responses[2]),
    "complications": parse_list(responses[3]),
    "disposition": responses[4].strip()
}
FINAL_VAR(result)
```

#### Key Differences

| Aspect | RLM V2 (Single) | RLM V3 (Batched) |
|--------|-----------------|------------------|
| **Sub-LLM Calls** | 1 call | 5 parallel calls |
| **Each Sub-LLM Task** | Extract all fields | Extract ONE field |
| **Context per Call** | Full context | Full context (5 times) |
| **Parallelization** | N/A | Yes (concurrent execution) |
| **Cost** | Lower (1 call) | Higher (5 calls) |
| **Expected Time** | Faster | ~Same (parallel execution) |
| **Quality** | Good | Potentially better (focused tasks) |

#### Why V3 Might Be Better

1. **Task Decomposition**: Each sub-LLM has a simpler, more focused task
2. **Attention**: Full context + single field = better extraction quality
3. **Parallelization**: `llm_query_batched()` runs concurrently, not 5x slower
4. **Error Isolation**: If one field fails, others still work

#### Results

Run with:
```bash
uv run compare_rlm_single_vs_batched.py
```

Output saved to: `data/processed/v2_v3_comparison.json`

**Expected Findings:**
- V3 should be **only slightly slower** than V2 (parallel execution)
- V3 may have **higher quality** for complex fields
- V3 costs **5x more** in API usage
- Trade-off: Cost vs Quality

---

## Source Files Explained

### `src/schema.py`
Defines the data structures for admission summaries.

**Key Classes:**
- `AdmissionSummaryV2`: 5-field summary schema
- `ImmutableAdmissionRecord`: Complete record with patient IDs + summary
- `SCHEMA_JSON`: JSON template for documentation

**Usage:**
```python
from src.schema import AdmissionSummaryV2

summary = AdmissionSummaryV2(
    diagnoses=["Acute MI", "CHF"],
    key_events=["PCI performed"],
    open_issues=[],
    complications=["Bleeding"],
    disposition="home"
)
```

### `src/prompts.py`
Prompt templates for traditional (non-RLM) LLM summarization.

**Exports:**
- `SYSTEM_PROMPT`: System instructions for LLM
- `EXTRACTION_PROMPT`: Main extraction prompt template
- `VALIDATION_PROMPT`: Optional validation step

### `src/admission_summarizer.py`
Traditional single-pass LLM summarizer using Gemini API.

**Class:** `AdmissionSummarizer`
- Uses `google.genai` client
- Direct API call with JSON mode
- No RLM, no REPL, no recursion

**Usage:**
```python
from src.admission_summarizer import AdmissionSummarizer

summarizer = AdmissionSummarizer(model_name="gemini-2.5-flash")
summary = summarizer.summarize(discharge_text)
```

### `src/rlm_summarizer.py` (RLM V2)
RLM-based summarizer using single `llm_query()` call.

**Class:** `AdmissionSummarizerWeek2`
- Uses RLM framework
- REPL environment with `context` variable
- One sub-LLM call extracts all 5 fields
- Robust JSON parsing with fallbacks

**Key Methods:**
- `summarize_all_at_once()`: Main extraction method
- `_safe_parse()`: Robust JSON parsing
- `_parse_fallback_response()`: Extract JSON from malformed responses

**Usage:**
```python
from src.rlm_summarizer import AdmissionSummarizerWeek2

summarizer = AdmissionSummarizerWeek2(
    model_name="gemini-2.5-flash",
    max_iterations=8,
    max_depth=1
)
result = summarizer.summarize_all_at_once(discharge_text)
```

### `src/rlm_summarizer_batched.py` (RLM V3)
RLM-based summarizer using batched field-by-field extraction.

**Class:** `AdmissionSummarizerV3`
- Uses RLM framework
- REPL environment with `llm_query_batched()`
- Five parallel sub-LLM calls (one per field)
- Each sub-LLM focuses on single field

**Key Features:**
- Parallel execution reduces wall-clock time
- Each field gets dedicated attention
- Robust parsing per field
- Graceful degradation if one field fails

**Usage:**
```python
from src.rlm_summarizer_batched import AdmissionSummarizerV3

summarizer = AdmissionSummarizerV3(
    model_name="gemini-2.5-pro",
    max_iterations=8
)
result = summarizer.summarize(discharge_text)
```

---

## Configuration

### Environment Variables

Create a `.env` file:
```bash
GEMINI_API_KEY=your-api-key-here
```

### Model Settings

Both comparison scripts use configuration dicts:

```python
CONFIG = {
    "model_name": "gemini-2.5-flash",  # or "gemini-2.5-pro"
    "max_iterations": 8,               # Max REPL iterations
    "max_depth": 1,                    # Max sub-LM recursion depth
    "n_samples": 1,                    # Number of patients to test
    "verbose": True                    # Show REPL execution details
}
```

**Model Recommendations:**
- `gemini-2.5-flash`: Faster, cheaper, good for most cases
- `gemini-2.5-pro`: Slower, more expensive, better for complex notes

---

## Data Format

### Input: `data/dev_subset_50_patients.parquet`

Parquet file with columns:
- `subject_id`: Patient ID
- `hadm_id`: Hospital admission ID
- `note_id`: Discharge note ID
- `input`: Full discharge note text
- `input_tokens`: Token count (for analysis)

### Output: `data/processed/comparison_results.json`

```json
[
  {
    "subject_id": 10000032,
    "hadm_id": 29079034,
    "single_pass_time": 8.23,
    "rlm_time": 24.56,
    "single_pass_result": {
      "diagnoses": ["Acute myocardial infarction", "Congestive heart failure"],
      "key_events": ["PCI with stent placement", "Developed pulmonary edema"],
      "open_issues": ["Blood pressure control"],
      "complications": ["Post-procedure bleeding"],
      "disposition": "home with services"
    },
    "rlm_result": {
      "diagnoses": ["Acute MI", "CHF"],
      "key_events": ["PCI", "Pulmonary edema"],
      "open_issues": ["BP management"],
      "complications": ["Bleeding"],
      "disposition": "home with services"
    }
  }
]
```

---

## How to Run

### Install Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv pip install -e .

# Install additional dependencies
uv pip install pandas pyarrow python-dotenv
```

### Run Experiments

**Experiment 1: Single-Pass vs RLM**
```bash
uv run compare_summarizers.py
```

**Experiment 2: RLM V2 vs V3**
```bash
uv run compare_rlm_single_vs_batched.py
```

### View Results

Results are saved as JSON files in `data/processed/`:
```bash
# View comparison results
cat data/processed/comparison_results.json

# View V2 vs V3 results
cat data/processed/v2_v3_comparison.json
```

---

## Key Insights

### When to Use Single-Pass LLM
✅ Fast results needed  
✅ Simple, well-structured notes  
✅ Cost-sensitive application  
✅ Sufficient context window  

### When to Use RLM V2 (Single Query)
✅ Long documents (>100K chars)  
✅ Need robust error handling  
✅ Want adaptive processing  
✅ Quality > Speed  

### When to Use RLM V3 (Batched)
✅ Complex, nuanced extraction  
✅ Each field requires deep analysis  
✅ Budget allows 5x API calls  
✅ Maximum quality needed  

---

## Technical Details

### RLM Architecture

The RLM framework provides:
1. **REPL Environment**: Execute Python code interactively
2. **Context Loading**: `context` variable holds the input
3. **Sub-LM Calls**: `llm_query()` and `llm_query_batched()` functions
4. **Final Answer**: `FINAL_VAR(variable_name)` to return results

### Error Handling

All summarizers include:
- **JSON Parsing**: Multiple fallback strategies
- **Regex Extraction**: Extract JSON from markdown/text
- **Balanced Braces**: Smart JSON object extraction
- **Default Values**: Return empty schema on failure

### Performance Considerations

**Token Usage:**
- Single-pass: ~10K input + 500 output per patient
- RLM V2: ~10K input + 10K output + 10K sub-LM per patient
- RLM V3: ~10K input + 50K output + 50K sub-LM per patient (5x)

**Wall-Clock Time:**
- Single-pass: 5-10 seconds
- RLM V2: 15-30 seconds
- RLM V3: 20-35 seconds (parallel execution helps!)

---

## Future Work

### Potential Improvements
1. **Field-Specific Prompts**: Tailor extraction prompts per field type
2. **Confidence Scores**: Track extraction confidence
3. **Multi-Turn Refinement**: Iteratively improve extraction quality
4. **Hierarchical Decomposition**: Break notes into sections first
5. **Validation Layer**: Cross-check extracted facts against source

### Evaluation Metrics
- **Accuracy**: Comparison with human-labeled ground truth
- **Completeness**: Are all relevant facts extracted?
- **Hallucination Rate**: Are there any fabricated facts?
- **Cost-Quality Trade-off**: ROC curves for different approaches

---

## References

- **RLM Paper**: [Recursive Language Models (arXiv)](https://arxiv.org/abs/2512.24601)
- **RLM Repository**: [github.com/alexzhang13/rlm](https://github.com/alexzhang13/rlm)
- **MIMIC-IV**: [PhysioNet MIMIC-IV Clinical Database](https://physionet.org/content/mimiciv/)

---

## Questions?

For questions or issues:
1. Check the RLM documentation: [alexzhang13.github.io/rlm](https://alexzhang13.github.io/rlm/)
2. Review the AGENTS.md guide for development guidelines
3. Open an issue on the RLM GitHub repository

---

**Last Updated**: January 17, 2026  
**Project**: Medical Discharge Note Summarization with RLM  
**Dataset**: MIMIC-IV Dev Subset (50 patients)
