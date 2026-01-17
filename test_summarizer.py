"""
Test Script for Summarizer

Tests the RLM-based summarizer.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set")
        return 1

    # Import after setting up path
    from src.rlm_summarizer_batched import AdmissionSummarizer

    print("=" * 70)
    print("Testing Summarizer")
    print("=" * 70)
    print("\nSchema: diagnoses, key_events, open_issues, complications, disposition")

    # Load dev subset
    dev_path = Path("data/processed/dev_subset_50_patients.parquet")
    print(f"\nLoading {dev_path}...")
    df = pd.read_parquet(dev_path)

    # Get first record
    record = df.iloc[0]
    print(f"\nTesting on: Subject {record['subject_id']}, Admission {record['hadm_id']}")

    # Create summarizer
    summarizer = AdmissionSummarizer(api_key=api_key, verbose=False)

    # Run extraction
    print("\nRunning extraction...")
    import time

    t0 = time.time()

    result = summarizer.summarize(discharge_text=record["input"])

    elapsed = time.time() - t0
    print(f"Completed in {elapsed:.2f}s")

    # Display results
    print("\n" + "=" * 70)
    print("EXTRACTED SUMMARY")
    print("=" * 70)

    summary = result

    print(f"\nDIAGNOSES ({len(summary.get('diagnoses', []))}):")
    for d in summary.get("diagnoses", [])[:5]:
        print(f"   - {d}")

    print(f"\nKEY EVENTS ({len(summary.get('key_events', []))}):")
    for e in summary.get("key_events", [])[:5]:
        print(f"   - {e}")

    print(f"\nOPEN ISSUES ({len(summary.get('open_issues', []))}):")
    for o in summary.get("open_issues", [])[:5]:
        print(f"   - {o}")

    print(f"\nCOMPLICATIONS ({len(summary.get('complications', []))}):")
    for c in summary.get("complications", [])[:3]:
        print(f"   - {c}")

    print(f"\nDISPOSITION: {summary.get('disposition', 'N/A')}")

    # Save sample output
    output_path = Path("data/processed/sample_summary.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull result saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
