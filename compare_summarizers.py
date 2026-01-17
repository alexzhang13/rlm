#!/usr/bin/env python3
"""
Comparison: Single-Pass LLM vs RLM Recursive Summarizer

This script compares:
1. Single-pass: Direct LLM call with full context
2. RLM: Recursive Language Model with REPL-based extraction

Both use the simplified 5-field schema:
- diagnoses, key_events, open_issues, complications, disposition
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load .env file

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd  # noqa: E402

CONFIG = {
    # Model settings
    "model_name": "gemini-2.5-flash",
    # RLM parameters
    "max_iterations": 8,  # Constrained to 8 iterations max
    "max_depth": 1,  # Max recursion depth for sub-LM calls
    # Test settings
    "n_samples": 1,  # Compare 1 patient
    "verbose": True,  # Disable verbose to avoid Rich console encoding on Windows
}


def run_single_pass(discharge_text: str, api_key: str, model_name: str) -> dict:
    """Run single-pass LLM extraction (no RLM, just direct call)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    prompt = f"""Extract a structured admission summary from this discharge note.

Return ONLY a valid JSON object with exactly these fields:
{{
  "diagnoses": [],
  "key_events": [],
  "open_issues": [],
  "complications": [],
  "disposition": ""
}}

RULES:
- Extract ONLY facts explicitly stated in the text
- Do NOT infer or interpret
- Use short phrases from the text
- If a field is not mentioned, return empty list or empty string

Discharge Note:
{discharge_text}

Return ONLY valid JSON, nothing else."""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json"),
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"error": "JSON parse failed", "raw": response.text[:500]}


def run_rlm(discharge_text: str, api_key: str, config: dict) -> dict:
    """Run RLM-based extraction."""
    from src.rlm_summarizer import AdmissionSummarizerWeek2

    summarizer = AdmissionSummarizerWeek2(
        api_key=api_key,
        model_name=config["model_name"],
        max_iterations=config["max_iterations"],
        max_depth=config["max_depth"],
        verbose=config["verbose"],
    )

    return summarizer.summarize_all_at_once(discharge_text)


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not set")
        print("   Set with: export GEMINI_API_KEY='your-key'")
        return 1

    print("=" * 70)
    print("Comparison: Single-Pass LLM vs RLM Recursive Summarizer")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Model: {CONFIG['model_name']}")
    print(f"  RLM max_iterations: {CONFIG['max_iterations']}")
    print(f"  RLM max_depth: {CONFIG['max_depth']}")
    print(f"  Samples: {CONFIG['n_samples']}")

    # Load dev subset
    dev_path = Path("data/dev_subset_50_patients.parquet")
    print(f"\n[LOADING] {dev_path}...")
    df = pd.read_parquet(dev_path)

    # Select N unique patients, take first note for each
    unique_patients = df["subject_id"].unique()[: CONFIG["n_samples"]]
    samples = df[df["subject_id"].isin(unique_patients)].groupby("subject_id").first().reset_index()

    print(f"   Total records: {len(df)}")
    print(f"   Unique patients: {len(df['subject_id'].unique())}")
    print(f"   Selected: {len(samples)} patients (first note each)")

    results = []

    for i, (_, row) in enumerate(samples.iterrows()):
        print(f"\n{'=' * 70}")
        print(
            f"Sample {i + 1}/{CONFIG['n_samples']}: Subject {row['subject_id']}, Admission {row['hadm_id']}"
        )
        print(f"{'=' * 70}")
        print(f"Input tokens: {row['input_tokens']}")

        # Single-pass
        print("\n[1/2] Running Single-Pass LLM...")
        t0 = time.time()
        sp_result = run_single_pass(row["input"], api_key, CONFIG["model_name"])
        sp_time = time.time() - t0
        print(f"   [OK] Completed in {sp_time:.2f}s")

        if "error" not in sp_result:
            print(f"   Diagnoses: {len(sp_result.get('diagnoses', []))}")
            print(f"   Key events: {len(sp_result.get('key_events', []))}")
            print(f"   Disposition: {sp_result.get('disposition', 'N/A')}")

        # RLM
        print("\n[2/2] Running RLM Recursive...")
        t0 = time.time()
        rlm_result = run_rlm(row["input"], api_key, CONFIG)
        rlm_time = time.time() - t0
        print(f"   [OK] Completed in {rlm_time:.2f}s")

        if isinstance(rlm_result, dict) and "error" not in rlm_result:
            print(f"   Diagnoses: {len(rlm_result.get('diagnoses', []))}")
            print(f"   Key events: {len(rlm_result.get('key_events', []))}")
            print(f"   Disposition: {rlm_result.get('disposition', 'N/A')}")

        results.append(
            {
                "subject_id": int(row["subject_id"]),
                "hadm_id": int(row["hadm_id"]),
                "single_pass_time": sp_time,
                "rlm_time": rlm_time,
                "single_pass_result": sp_result,
                "rlm_result": rlm_result,
            }
        )

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    avg_sp = sum(r["single_pass_time"] for r in results) / len(results)
    avg_rlm = sum(r["rlm_time"] for r in results) / len(results)

    print("\n[TIME] Average Time:")
    print(f"   Single-Pass: {avg_sp:.2f}s")
    print(f"   RLM:         {avg_rlm:.2f}s")
    print(f"   Ratio:       {avg_rlm / avg_sp:.1f}x slower")

    # Save results
    output_path = Path("data/processed/comparison_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[SAVED] Results saved to: {output_path}")

    print("\n" + "=" * 70)
    print("[DONE] Comparison complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
