#!/usr/bin/env python3
"""
Simplified Admission Summary Schema - Week 2

Each admission produces ONE immutable summary with just 5 essential fields.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


@dataclass
class AdmissionSummaryV2:
    """
    Simplified admission summary - 5 essential fields only.
    
    Designed for:
    - Minimal hallucination (only explicit facts)
    - Easy comparison across admissions
    - Efficient longitudinal tracking
    """
    diagnoses: List[str] = field(default_factory=list)
    key_events: List[str] = field(default_factory=list)
    open_issues: List[str] = field(default_factory=list)
    complications: List[str] = field(default_factory=list)
    disposition: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AdmissionSummaryV2":
        """Create from dictionary."""
        return cls(
            diagnoses=data.get("diagnoses", []),
            key_events=data.get("key_events", []),
            open_issues=data.get("open_issues", []),
            complications=data.get("complications", []),
            disposition=data.get("disposition", "")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "AdmissionSummaryV2":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class ImmutableAdmissionRecord:
    """
    Complete immutable admission record.
    
    Structure:
    {
        "subject_id": 123,
        "hadm_id": 456,
        "note_id": "123-DS-1",
        "admission_summary": {
            "diagnoses": [...],
            "key_events": [...],
            "open_issues": [...],
            "complications": [...],
            "disposition": "..."
        }
    }
    """
    subject_id: int
    hadm_id: int
    note_id: str
    admission_summary: AdmissionSummaryV2
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "subject_id": self.subject_id,
            "hadm_id": self.hadm_id,
            "note_id": self.note_id,
            "admission_summary": self.admission_summary.to_dict()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, filepath: str) -> None:
        """Save to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: dict) -> "ImmutableAdmissionRecord":
        """Create from dictionary."""
        return cls(
            subject_id=data["subject_id"],
            hadm_id=data["hadm_id"],
            note_id=data.get("note_id", ""),
            admission_summary=AdmissionSummaryV2.from_dict(data["admission_summary"])
        )
    
    @classmethod
    def load(cls, filepath: str) -> "ImmutableAdmissionRecord":
        """Load from file."""
        with open(filepath, 'r') as f:
            return cls.from_dict(json.load(f))


# Schema as JSON for documentation
SCHEMA_JSON = {
    "diagnoses": [],
    "key_events": [],
    "open_issues": [],
    "complications": [],
    "disposition": ""
}
