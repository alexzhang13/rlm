#!/usr/bin/env python3
"""
Test Script for Week 2 Simplified Summarizer

Tests the RLM-based summarizer with the simplified 5-field schema.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return 1
    
    # Import after setting up path
    from src.summarizer.rlm_summarizer import AdmissionSummarizerWeek2
    
    print("=" * 70)
    print("Testing Week 2 Simplified Summarizer")
    print("=" * 70)
    print("\nSchema: diagnoses, key_events, open_issues, complications, disposition")
    
    # Load dev subset
    dev_path = Path("data/processed/dev_subset_50_patients.parquet")
    print(f"\n📁 Loading {dev_path}...")
    df = pd.read_parquet(dev_path)
    
    # Get first record
    record = df.iloc[0]
    print(f"\n📋 Testing on: Subject {record['subject_id']}, Admission {record['hadm_id']}")
    print(f"   Input tokens: {record['input_tokens']}")
    
    # Create summarizer
    print("\n🤖 Initializing Week 2 summarizer...")
    summarizer = AdmissionSummarizerWeek2(api_key=api_key, verbose=False)
    
    # Test all-at-once method
    print("\n⏳ Running all-at-once extraction...")
    import time
    t0 = time.time()
    
    result = summarizer.create_admission_file(
        subject_id=int(record['subject_id']),
        hadm_id=int(record['hadm_id']),
        note_id=str(record['note_id']),
        discharge_text=record['input'],
        output_dir=Path("data/processed/admission_summaries"),
        method="all_at_once"
    )
    
    elapsed = time.time() - t0
    print(f"   ✅ Completed in {elapsed:.2f}s")
    
    # Display results
    print("\n" + "=" * 70)
    print("EXTRACTED SUMMARY")
    print("=" * 70)
    
    summary = result["admission_summary"]
    
    print(f"\n📌 DIAGNOSES ({len(summary.get('diagnoses', []))}):")
    for d in summary.get("diagnoses", [])[:5]:
        print(f"   - {d}")
    
    print(f"\n📋 KEY EVENTS ({len(summary.get('key_events', []))}):")
    for e in summary.get("key_events", [])[:5]:
        print(f"   - {e}")
    
    print(f"\n⚠️  OPEN ISSUES ({len(summary.get('open_issues', []))}):")
    for o in summary.get("open_issues", [])[:5]:
        print(f"   - {o}")
    
    print(f"\n❌ COMPLICATIONS ({len(summary.get('complications', []))}):")
    for c in summary.get("complications", [])[:3]:
        print(f"   - {c}")
    
    print(f"\n📤 DISPOSITION: {summary.get('disposition', 'N/A')}")
    
    # Save sample output
    output_path = Path("data/processed/sample_summary_v2.json")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Full result saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ Test completed!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
