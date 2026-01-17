#!/usr/bin/env python3
"""
Compare RLM V2 (single llm_query) vs V3 (batched field-by-field)

V2: One llm_query() call for all 5 fields
V3: llm_query_batched() with 5 parallel calls, one per field
"""

import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rlm_summarizer import AdmissionSummarizerWeek2  # noqa: E402
from src.rlm_summarizer_batched import AdmissionSummarizer as AdmissionSummarizerV3  # noqa: E402

CONFIG = {
    "model_name": "gemini-2.5-pro",
    "max_iterations": 8,
    "n_samples": 1,
    "verbose": True,  # Disable verbose to avoid Rich console encoding on Windows
}


def run_comparison():
    # Check API key first
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not set")
        print("   Set with: set GEMINI_API_KEY=your-key")
        return 1

    print("=" * 70)
    print("Comparison: RLM V2 (single query) vs V3 (batched field-by-field)")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Model: {CONFIG['model_name']}")
    print(f"  Max iterations: {CONFIG['max_iterations']}")
    print(f"  Samples: {CONFIG['n_samples']}")

    # Load data
    data_path = Path("data/dev_subset_50_patients.parquet")
    print(f"\n[LOADING] {data_path}...")
    df = pd.read_parquet(data_path)

    # Get first note per patient
    first_notes = df.groupby("subject_id").first().reset_index()
    samples = first_notes.head(CONFIG["n_samples"])
    print(f"   Selected: {len(samples)} patient(s)")

    # Initialize summarizers
    v2_summarizer = AdmissionSummarizerWeek2(
        api_key=api_key,
        model_name=CONFIG["model_name"],
        max_iterations=CONFIG["max_iterations"],
        verbose=CONFIG["verbose"],
    )

    v3_summarizer = AdmissionSummarizerV3(
        api_key=api_key,
        model_name=CONFIG["model_name"],
        max_iterations=CONFIG["max_iterations"],
        verbose=CONFIG["verbose"],
    )

    results = []

    for _idx, row in samples.iterrows():
        subject_id = row["subject_id"]
        hadm_id = row["hadm_id"]
        discharge_text = row["input"]

        print(f"\n{'=' * 70}")
        print(f"Sample: Subject {subject_id}, Admission {hadm_id}")
        print(f"Input length: {len(discharge_text)} chars")
        print("=" * 70)

        # Run V2
        print("\n[1/2] Running V2 (single llm_query)...")
        start = time.time()
        v2_result = v2_summarizer.summarize_all_at_once(discharge_text)
        v2_time = time.time() - start
        print(f"   [OK] V2 completed in {v2_time:.2f}s")
        print(f"   Diagnoses: {len(v2_result.get('diagnoses', []))}")
        print(f"   Key events: {len(v2_result.get('key_events', []))}")

        # Run V3
        print("\n[2/2] Running V3 (batched field-by-field)...")
        start = time.time()
        v3_result = v3_summarizer.summarize(discharge_text)
        v3_time = time.time() - start
        print(f"   [OK] V3 completed in {v3_time:.2f}s")
        print(f"   Diagnoses: {len(v3_result.get('diagnoses', []))}")
        print(f"   Key events: {len(v3_result.get('key_events', []))}")

        results.append(
            {
                "subject_id": subject_id,
                "hadm_id": hadm_id,
                "v2_time": v2_time,
                "v3_time": v3_time,
                "v2_result": v2_result,
                "v3_result": v3_result,
            }
        )

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    avg_v2 = sum(r["v2_time"] for r in results) / len(results)
    avg_v3 = sum(r["v3_time"] for r in results) / len(results)

    print("\n[TIME] Average Time:")
    print(f"   V2 (single query):  {avg_v2:.2f}s")
    print(f"   V3 (batched):       {avg_v3:.2f}s")
    print(f"   Ratio:              {avg_v3 / avg_v2:.2f}x")

    # Save results
    output_path = Path("data/processed/v2_v3_comparison.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[SAVED] Results saved to: {output_path}")

    # Show detailed comparison for first sample
    if results:
        r = results[0]
        print("\n" + "=" * 70)
        print("DETAILED COMPARISON (First Sample)")
        print("=" * 70)

        for field in ["diagnoses", "key_events", "open_issues", "complications", "disposition"]:
            v2_val = r["v2_result"].get(field, [])
            v3_val = r["v3_result"].get(field, [])

            if isinstance(v2_val, list):
                print(f"\n[FIELD] {field.upper()}")
                print(f"   V2 ({len(v2_val)} items): {v2_val}")
                print(f"   V3 ({len(v3_val)} items): {v3_val}")
            else:
                print(f"\n[FIELD] {field.upper()}")
                print(f"   V2: {v2_val}")
                print(f"   V3: {v3_val}")

    print("\n" + "=" * 70)
    print("[DONE] Comparison complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(run_comparison())
