"""
AI-Powered Scenario Extractor using Local LLM (Ollama) - Python API Version
Extracts structured information from HEDIS test case scenarios.
"""

import json
import re
from typing import Dict, List, Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: ollama package not installed. Run: pip install ollama")


class AIScenarioExtractor:
    def __init__(self, model_name: str = "qwen2:0.5b"):
        """
        Initialize AI extractor with Ollama model.
        
        Args:
            model_name: Ollama model to use (default: llama3)
        """
        if not OLLAMA_AVAILABLE:
            raise ImportError("ollama package required. Install with: pip install ollama")
        
        self.model_name = model_name
        self.client = ollama.Client()
        self._ensure_model_available()
    
    def _ensure_model_available(self):
        """Check if model is available, pull if not."""
        try:
            models = self.client.list()
            # Handle new API response format which might return an object with a 'models' attribute or a list
            if hasattr(models, 'models'):
                models_list = models.models
            elif isinstance(models, dict):
                models_list = models.get('models', [])
            else:
                models_list = models

            # Extract names robustly
            model_names = []
            for m in models_list:
                if hasattr(m, 'name'):
                    model_names.append(m.name)
                elif isinstance(m, dict):
                    model_names.append(m.get('name'))
                else:
                    model_names.append(str(m))
            
            # Check if our model exists (with or without :latest tag)
            model_exists = any(
                self.model_name in name or name.startswith(self.model_name + ':')
                for name in model_names
            )
            
            if not model_exists:
                print(f"Model {self.model_name} not found. Pulling...")
                self.client.pull(self.model_name)
                print(f"Model {self.model_name} pulled successfully!")
                
        except Exception as e:
            print(f"Warning: Could not verify Ollama model: {e}")
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API with a prompt using Python client.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Model response as string
        """
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.1,  # Low temperature for deterministic output
                    'num_predict': 500,  # Max tokens to generate
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            raise Exception(f"Failed to call Ollama: {e}")
    
    def _build_extraction_prompt(self, test_case_row: Dict) -> str:
        """
        Build prompt for extracting scenario information.
        
        Args:
            test_case_row: Dictionary with test case fields
            
        Returns:
            Formatted prompt string
        """
        tc_id = test_case_row.get('id', 'UNKNOWN')
        scenario = test_case_row.get('scenario', '')
        objective = test_case_row.get('objective', '')
        expected = test_case_row.get('expected', '')
        
        prompt = f"""Extract structured data from this HEDIS test case. Return ONLY valid JSON.

Test Case ID: {tc_id}
Scenario: {scenario}
Objective: {objective}
Expected: {expected}

Extract:
1. enrollment_spans: List of enrollment periods
   - Look for "CE:", "enrollment", or date ranges like "1/1/MY-1 TO 10/1/MY"
   - MY = 2026, MY-1 = 2025, MY+1 = 2027
   - Multiple spans = enrollment gaps
   
2. product_line: Commercial/Medicaid/Medicare/Exchange (default: Medicare)
3. age: Integer (default: 70)
4. gender: M/F/O (default: M)
5. gap_days: Days gap if mentioned (null if not)
6. expected_results: Flags like CE=1, AD=0, etc.
7. clinical_events: Events mentioned (PSA Test, BMI, etc.)
8. exclusions: Exclusions mentioned (Hospice, etc.)

Return ONLY this JSON (no other text):
{{
  "enrollment_spans": [{{"start": "1/1/MY-1", "end": "10/1/MY", "product_id": null}}],
  "product_line": "Medicare",
  "age": 70,
  "gender": "M",
  "gap_days": null,
  "expected_results": {{"CE": 1}},
  "clinical_events": [],
  "exclusions": []
}}"""

        return prompt
    
    def _parse_json_response(self, response: str) -> Dict:
        """
        Parse JSON from LLM response, handling common formatting issues.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed JSON dictionary
        """
        # Clean up response
        response = response.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        # Find first { and last }
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1:
            response = response[start:end+1]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Try to fix common issues
            response = response.replace("'", '"')  # Single to double quotes
            response = re.sub(r',(\s*[}\]])', r'\1', response)  # Trailing commas
            try:
                return json.loads(response)
            except:
                raise Exception(f"Could not parse JSON: {response[:200]}...")
    
    def extract_scenario_info(self, test_case_row: Dict) -> Dict:
        """
        Extract structured information from a test case using AI.
        
        Args:
            test_case_row: Dictionary with keys: id, scenario, objective, expected
            
        Returns:
            Dictionary with extracted structured data
        """
        try:
            # Build and send prompt
            prompt = self._build_extraction_prompt(test_case_row)
            response = self._call_ollama(prompt)
            
            # Parse response
            extracted = self._parse_json_response(response)
            
            # Add original ID and sheet
            extracted['id'] = test_case_row.get('id', 'UNKNOWN')
            extracted['sheet'] = test_case_row.get('sheet', 'Unknown')
            
            # Ensure all required fields exist
            extracted.setdefault('enrollment_spans', [])
            extracted.setdefault('product_line', 'Medicare')
            extracted.setdefault('age', 70)
            extracted.setdefault('gender', 'M')
            extracted.setdefault('gap_days', None)
            extracted.setdefault('expected_results', {})
            extracted.setdefault('clinical_events', [])
            extracted.setdefault('exclusions', [])
            
            return extracted
            
        except Exception as e:
            print(f"⚠️  AI extraction failed for {test_case_row.get('id', 'UNKNOWN')}: {e}")
            # Return minimal structure on failure
            return {
                'id': test_case_row.get('id', 'UNKNOWN'),
                'sheet': test_case_row.get('sheet', 'Unknown'),
                'enrollment_spans': [],
                'product_line': 'Medicare',
                'age': 70,
                'gender': 'M',
                'gap_days': None,
                'expected_results': {},
                'clinical_events': [],
                'exclusions': [],
                '_ai_failed': True,
                '_error': str(e)
            }


if __name__ == "__main__":
    # Test the extractor
    print("=" * 60)
    print("Testing AI Scenario Extractor")
    print("=" * 60)
    
    extractor = AIScenarioExtractor(model_name="qwen2:0.5b")
    
    # Test cases
    test_cases = [
        {
            'id': 'PSA_CE_02',
            'scenario': '''Verify, if a member is enrolled in the measurement year. 44 days
CE:
1/1/MY-1 TO 10/1/MY
11/14/MY TO 12/31/MY''',
            'objective': '',
            'expected': 'CE=1',
            'sheet': 'PSA_Measure'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['id']}")
        print("-" * 60)
        
        result = extractor.extract_scenario_info(test_case)
        
        if result.get('_ai_failed'):
            print("❌ AI extraction failed")
            print(f"Error: {result.get('_error', 'Unknown')}")
        else:
            print("✅ AI extraction successful")
            print(f"\nEnrollment spans: {len(result.get('enrollment_spans', []))}")
            for span in result.get('enrollment_spans', []):
                print(f"  - {span.get('start')} → {span.get('end')}")
            print(f"Product Line: {result.get('product_line')}")
            print(f"Expected CE: {result.get('expected_results', {}).get('CE', 'N/A')}")
        
        print()
    
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
