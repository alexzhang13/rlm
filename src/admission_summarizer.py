#!/usr/bin/env python3
"""
Admission Summarizer Module

Uses Gemini 3 Pro to extract structured summaries from MIMIC-IV discharge notes.
"""

import json
import os
import time
from typing import Optional, Dict, Any, List
from dataclasses import asdict
from pathlib import Path
import logging

try:
    from google import genai
    from google.genai import types
    USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_SDK = False

from .prompts import SYSTEM_PROMPT, EXTRACTION_PROMPT, VALIDATION_PROMPT
from .schema import AdmissionSummaryV2 as AdmissionSummary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdmissionSummarizer:
    """
    Extracts structured admission summaries from discharge notes using Gemini 3 Pro.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.1,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        Initialize the summarizer.
        
        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.
            model_name: Gemini model to use.
            temperature: Sampling temperature (lower = more deterministic).
            max_retries: Maximum retry attempts for API calls.
            retry_delay: Delay between retries in seconds.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set or provided")
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize client based on SDK version
        if USE_NEW_SDK:
            self.client = genai.Client(api_key=self.api_key)
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    response_mime_type="application/json"
                )
            )
        
        logger.info(f"Initialized AdmissionSummarizer with model: {model_name} (new SDK: {USE_NEW_SDK})")
    
    def summarize(
        self,
        discharge_text: str,
        metadata: Dict[str, Any],
        validate: bool = False
    ) -> Dict[str, Any]:
        """
        Extract structured summary from a discharge note.
        
        Args:
            discharge_text: The discharge summary text (input field).
            metadata: Dictionary with subject_id, hadm_id, note_id, etc.
            validate: Whether to run validation pass.
            
        Returns:
            Dictionary containing the structured admission summary.
        """
        # Build the prompt
        prompt = EXTRACTION_PROMPT.format(
            discharge_text=discharge_text,
            subject_id=metadata.get('subject_id'),
            hadm_id=metadata.get('hadm_id'),
            note_id=metadata.get('note_id'),
            admittime=metadata.get('admittime'),
            dischtime=metadata.get('dischtime'),
            deathtime=metadata.get('deathtime'),
            admission_type=metadata.get('admission_type'),
            race=metadata.get('race'),
            marital_status=metadata.get('marital_status')
        )
        
        # Call API with retries
        summary = self._call_api_with_retry(prompt)
        
        if summary and validate:
            validation_result = self._validate_summary(discharge_text, summary)
            summary['_validation'] = validation_result
        
        return summary
    
    def _call_api_with_retry(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Gemini API with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                if USE_NEW_SDK:
                    # New SDK (google-genai)
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=self.temperature,
                            response_mime_type="application/json",
                            system_instruction=SYSTEM_PROMPT
                        )
                    )
                    result = json.loads(response.text)
                else:
                    # Old SDK (google-generativeai)
                    response = self.model.generate_content(prompt)
                    result = json.loads(response.text)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                last_error = e
                
            except Exception as e:
                logger.warning(f"API error on attempt {attempt + 1}: {e}")
                last_error = e
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        logger.error(f"Failed after {self.max_retries} attempts: {last_error}")
        return None
    
    def _validate_summary(
        self,
        discharge_text: str,
        extracted_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run validation pass on extracted summary."""
        prompt = VALIDATION_PROMPT.format(
            discharge_text=discharge_text,
            extracted_summary=json.dumps(extracted_summary, indent=2)
        )
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.warning(f"Validation failed: {e}")
            return {"error": str(e)}
    
    def summarize_batch(
        self,
        records: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple discharge notes.
        
        Args:
            records: List of dictionaries with 'input' and metadata fields.
            output_path: Optional path to save results incrementally.
            progress_callback: Optional callback(current, total) for progress.
            
        Returns:
            List of extracted summaries.
        """
        results = []
        total = len(records)
        
        for i, record in enumerate(records):
            logger.info(f"Processing {i + 1}/{total}: hadm_id={record.get('hadm_id')}")
            
            metadata = {
                'subject_id': record.get('subject_id'),
                'hadm_id': record.get('hadm_id'),
                'note_id': record.get('note_id'),
                'admittime': record.get('admittime'),
                'dischtime': record.get('dischtime'),
                'deathtime': record.get('deathtime'),
                'admission_type': record.get('admission_type'),
                'race': record.get('race'),
                'marital_status': record.get('marital_status')
            }
            
            summary = self.summarize(
                discharge_text=record.get('input', ''),
                metadata=metadata
            )
            
            if summary:
                summary['_source'] = {
                    'subject_id': metadata['subject_id'],
                    'hadm_id': metadata['hadm_id'],
                    'note_id': metadata['note_id']
                }
                results.append(summary)
                
                # Save incrementally
                if output_path:
                    with open(output_path, 'a') as f:
                        f.write(json.dumps(summary) + '\n')
            
            if progress_callback:
                progress_callback(i + 1, total)
            
            # Rate limiting
            time.sleep(0.5)
        
        return results


def create_summarizer(api_key: Optional[str] = None) -> AdmissionSummarizer:
    """Factory function to create a summarizer instance."""
    return AdmissionSummarizer(api_key=api_key)
