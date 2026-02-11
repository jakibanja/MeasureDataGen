import PyPDF2
import re
import yaml
import os

class NCQASpecParser:
    """
    Parses NCQA HEDIS specification PDFs to extract measure rules.
    Auto-generates config YAML files for the MockupEngine.
    """
    
    def __init__(self, pdf_path, ai_extractor=None, reader=None):
        self.pdf_path = pdf_path
        self.ai_extractor = ai_extractor
        self.reader = reader
        self.text = ""
        self.measure_name = ""
        
    def extract_text(self, target_measure_title=None):
        """Extract text from PDF. If target_measure_title is provided, surgically extract relevant pages only."""
        print(f"Reading PDF: {self.pdf_path}")
        
        if self.reader:
            reader = self.reader
        else:
            file = open(self.pdf_path, 'rb')
            reader = PyPDF2.PdfReader(file)
            self.reader = reader # Cache it
            
        total_pages = len(reader.pages)
        print(f"Total pages: {total_pages}")
        
        if target_measure_title:
            print(f"[SEARCH] Searching for section: '{target_measure_title}'...")
            # Extract abbreviation from title if possible, e.g. "Prostate Cancer (PSA)" -> "PSA"
            abbr = None
            abbr_match = re.search(r'\(([A-Z]{3,4})\)', target_measure_title)
            if abbr_match:
                abbr = abbr_match.group(1)
            
            found = False
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                
                # Fuzzy match: Title or Abbreviation
                match_found = False
                if abbr and f"({abbr})" in page_text:
                    match_found = True
                elif target_measure_title.lower() in page_text.lower():
                    match_found = True
                
                if match_found:
                    # Ensure it's not a TOC entry (has many dots)
                    if re.search(r'\.{4,}\s*\d+', page_text):
                        continue
                        
                    print(f"[OK] Found measure start on page {page_num + 1}")
                    # HEDIS specs are usually 5-10 pages. Grabbing 20 for safety in grouped pubs.
                    self.text = ""
                    for i in range(page_num, min(page_num + 20, total_pages)):
                        self.text += reader.pages[i].extract_text() + "\n"
                    found = True
                    break
            
            if not found:
                print(f" Could not find '{target_measure_title}' in PDF. Falling back to full scan...")
                # Fallback to moderate scan (first 100 pages for speed) if title not found
                for page_num in range(min(100, total_pages)):
                    self.text += reader.pages[page_num].extract_text() + "\n"
        else:
            # Standard scan (first 50 pages if no title to avoid hanging on 700+ pages)
            for page_num in range(min(50, total_pages)):
                self.text += reader.pages[page_num].extract_text() + "\n"
                
        print(f"Extracted {len(self.text)} characters")
        return self.text
    
    def identify_measure(self):
        """Identify measure name from PDF."""
        # Look for common patterns like "PSA - Prostate Cancer Screening"
        patterns = [
            r'([A-Z]{3,4})\s*[-–]\s*([A-Za-z\s]+)',  # PSA - Prostate Cancer
            r'Measure:\s*([A-Z]{3,4})',
            r'([A-Z]{3,4})\s+Measure'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text[:2000])  # Check first 2000 chars
            if match:
                self.measure_name = match.group(1)
                print(f"Identified measure: {self.measure_name}")
                return self.measure_name
                
        print(" Could not identify measure name")
        return None
    
    def extract_age_range(self):
        """Extract age range from denominator criteria."""
        patterns = [
            r'age[sd]?\s+(\d+)[-–](\d+)',
            r'(\d+)[-–](\d+)\s+years?\s+of\s+age',
            r'Members?\s+(\d+)\s+to\s+(\d+)\s+years'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                age_min = int(match.group(1))
                age_max = int(match.group(2))
                print(f"Found age range: {age_min}-{age_max}")
                return [age_min, age_max]
        
        print(" Could not extract age range")
        return [18, 100]  # Default
    
    def extract_continuous_enrollment(self):
        """Extract continuous enrollment requirements."""
        # Look for patterns like "12 months" or "continuous enrollment"
        pattern = r'continuous(?:ly)?\s+enroll(?:ed|ment)\s+(?:for\s+)?(\d+)\s+months?'
        match = re.search(pattern, self.text, re.IGNORECASE)
        
        if match:
            months = int(match.group(1))
            print(f"Found enrollment requirement: {months} months")
            return {
                'period_months': months,
                'allowable_gap_days': 45,  # NCQA standard
                'no_gap_on_last_day': True
            }
        
        return {
            'period_months': 12,
            'allowable_gap_days': 45,
            'no_gap_on_last_day': True
        }
    
    def extract_value_sets(self):
        """Extract value set names mentioned in the spec."""
        # Look for value set references
        pattern = r'([A-Z][A-Za-z\s]+(?:Encounter|Procedure|Test|Lab|Diagnosis|Intervention)s?)'
        
        value_sets = set()
        for match in re.finditer(pattern, self.text):
            vs_name = match.group(1).strip()
            if len(vs_name) > 5 and len(vs_name) < 50:  # Reasonable length
                value_sets.add(vs_name)
        
        print(f"Found {len(value_sets)} potential value sets")
        return list(value_sets)[:10]  # Limit to top 10
    
    def extract_numerator_components(self):
        """Extract numerator components from the specification text."""
        # Find numerator section
        numerator_match = re.search(
            r'Numerator(.*?)(?:Exclusions|Denominator|Administrative|$)',
            self.text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not numerator_match:
            print(" Could not find Numerator section")
            return []
        
        numerator_text = numerator_match.group(1).strip()
        print(f"Numerator text found: {len(numerator_text)} characters")

        if self.ai_extractor:
            print("Using AI to extract components...")
            prompt = f"""
            Extract the numerator components from this HEDIS measure specification.
            Focus on identifying the specific tests, procedures, or pharmacy requirements.
            
            Text:
            {numerator_text[:3000]}
            
            Return a JSON list of objects:
            [
              {{"name": "Component Name", "table": "lab/visit/rx/emr", "description": "Short description"}}
            ]
            
            Return ONLY the JSON list.
            """
            try:
                # Reuse the AI extractor's call_ollama if possible, or direct call
                if hasattr(self.ai_extractor, '_call_ollama'):
                    response = self.ai_extractor._call_ollama(prompt)
                    # Use the AI extractor's parse logic
                    components = self.ai_extractor._parse_json_response(response)
                    if isinstance(components, list):
                        # Add prefixes if missing for measure specific tables
                        for c in components:
                            c['value_set_names'] = [c['name']] # Default to its own name as vs name
                        return components
            except Exception as e:
                print(f"AI extraction failed: {e}")

        # Fallback to keyword search if AI fails or not available
        components = []
        if "HbA1c" in numerator_text or "monitoring" in numerator_text.lower():
            components.append({'name': 'HbA1c Test', 'table': 'lab', 'value_set_names': ['HbA1c Tests']})
        if "LDL-C" in numerator_text or "lipid" in numerator_text.lower():
            components.append({'name': 'LDL-C Test', 'table': 'lab', 'value_set_names': ['LDL-C Tests']})
        
        if not components:
            # Absolute fallback
            components.append({
                'name': f'{self.measure_name} Screening',
                'table': 'visit',
                'value_set_names': [f'{self.measure_name} Value Set']
            })
            
        return components
    
    def extract_exclusions(self):
        """Extract exclusion criteria."""
        exclusions = []
        
        # Common HEDIS exclusions
        common_exclusions = [
            ('Hospice', ['Hospice Encounter', 'Hospice Intervention']),
            ('Death', None),
        ]
        
        # Check if mentioned in text
        for name, value_sets in common_exclusions:
            if name.lower() in self.text.lower():
                exclusion = {'name': name}
                if value_sets:
                    exclusion['value_set_names'] = value_sets
                else:
                    exclusion['criteria'] = f'{name} during measurement period'
                exclusions.append(exclusion)
        
        print(f"Found {len(exclusions)} exclusions")
        return exclusions

    def extract_logic_pathways(self):
        """
        Extract 'Logic Pathways' (Compliance options) using AI.
        E.g., "Pathway 1: HbA1c < 8", "Pathway 2: HbA1c > 8"
        """
        # Find Numerator / Compliance section
        num_match = re.search(
            r'(Numerator|Compliance)(.*?)(?:Exclusions|Denominator|Administrative|$)',
            self.text,
            re.IGNORECASE | re.DOTALL
        )

        if not num_match:
            return []
        
        num_text = num_match.group(2).strip()

        if self.ai_extractor:
            print(" Using AI to extract Compliance Logic Pathways...")
            prompt = f"""
            Analyze the HEDIS Specification below.
            Identify distinct "Compliance Pathways" (ways to pass the measure).
            
            Text:
            {num_text[:4000]}
            
            Return a JSON list of objects:
            [
              {{
                "name": "HbA1c Control",
                "description": "HbA1c < 8.0%",
                "criteria": {{ "event": "HbA1c Test", "value": "< 8.0" }}
              }}
            ]
            
            Return ONLY the valid JSON list.
            """
            try:
                # Reuse the AI extractor's call_ollama if possible
                if hasattr(self.ai_extractor, '_call_ollama'):
                    response = self.ai_extractor._call_ollama(prompt)
                    # Use the AI extractor's parse logic
                    pathways = self.ai_extractor._parse_json_response(response)
                    if isinstance(pathways, list):
                        print(f" AI Found {len(pathways)} logic pathways")
                        return pathways
            except Exception as e:
                print(f"AI Logic Pathway extraction failed: {e}")
        
        return []

    def extract_denominator_components(self):
        """
        Extract complex denominator logic (Step 1, Step 2, multi-visit requirements) using AI.
        Returns a list of component definitions for 'denominator_components'.
        """
        # Find Denominator / Event / Diagnosis section
        denom_match = re.search(
            r'(Denominator|Event/Diagnosis)(.*?)(?:Exclusions|Numerator|Administrative|$)',
            self.text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not denom_match:
            print(" Could not find Denominator section")
            return []
            
        denom_text = denom_match.group(2).strip()
        print(f"Denominator text found: {len(denom_text)} characters")

        if self.ai_extractor:
            print(" Using AI to extract complex denominator components...")
            prompt = f"""
            Analyze the HEDIS Denominator/Event criteria below.
            Identify distinct cohorts or steps (e.g., "Step 1: Schizophrenia", "Step 2: Diabetes").
            For each step, identify the requirements:
            - Visit counts (e.g., "Two outpatient visits") -> "count": 2
            - Time separation (e.g., "different dates of service", "14 days apart") -> "min_separation_days": 1 (or 14)
            - Diagnosis/Event (e.g., "Schizophrenia") -> "diagnosis_pattern": "Schizophrenia"
            - Inpatient vs Outpatient -> "table": "visit", "overrides": {{"POS": "21"}} (Inpatient) or {{"POS": "11"}} (Outpatient)
            
            Text:
            {denom_text[:4000]}
            
            Return a JSON list of objects matching this schema:
            [
              {{
                "name": "Schizophrenia_Inpatient",
                "count": 1,
                "table": "visit",
                "value_set_names": ["Schizophrenia", "Inpatient"],
                "diagnosis_pattern": "Schizophrenia",
                "overrides": {{"POS": "21"}}
              }},
              {{
                "name": "Schizophrenia_Outpatient_History",
                "count": 2,
                "min_separation_days": 1, 
                "table": "visit",
                "diagnosis_pattern": "Schizophrenia",
                "overrides": {{"POS": "11"}}
              }}
            ]
            
            Return ONLY the valid JSON list.
            """
            try:
                if hasattr(self.ai_extractor, '_call_ollama'):
                    response = self.ai_extractor._call_ollama(prompt)
                    components = self.ai_extractor._parse_json_response(response)
                    if isinstance(components, list):
                        print(f" AI Found {len(components)} denominator components")
                        return components
            except Exception as e:
                print(f"AI Denominator extraction failed: {e}")
        
        return [] # Return empty if AI fails or no section found
    
    def generate_config(self, output_path=None, target_measure_title=None):
        """Generate complete config YAML from PDF."""
        # Fix encoding issue for terminal output (silly Windows/cp1252)
        safe_title = target_measure_title if target_measure_title else self.measure_name if self.measure_name else 'Default'
        try:
            print(f"\n[SCAN] Parsing NCQA Specification PDF for '{safe_title}'...")
        except UnicodeEncodeError:
            print(f"\n[SCAN] Parsing NCQA Specification PDF for '{safe_title}'...")
        
        # ⚡ Use self.measure_name as fallback for target_measure_title
        if not target_measure_title and self.measure_name:
            target_measure_title = self.measure_name
            
        # Extract text
        self.extract_text(target_measure_title=target_measure_title)
        
        # Identify measure
        measure_name = None
        if target_measure_title:
            if "(" in target_measure_title:
                # Try to extract abbreviation from title like "Diabetes Monitoring (SMD)"
                abbr_match = re.search(r'\(([A-Z]{3,4})\)', target_measure_title)
                if abbr_match:
                    measure_name = abbr_match.group(1)
            elif len(target_measure_title) >= 3 and len(target_measure_title) <= 4 and target_measure_title.isupper():
                # It's likely already an abbreviation (e.g. "SMD")
                measure_name = target_measure_title

        if not measure_name:
            measure_name = self.identify_measure()
            
        if not measure_name or measure_name == "UNKNOWN":
            # If still not found, use a placeholder or the title slug
            if self.measure_name and self.measure_name != "UNKNOWN":
                 measure_name = self.measure_name
            elif target_measure_title:
                measure_name = target_measure_title.split(' ')[0].upper()
                # Clean up e.g. "DIABETES" -> "DM" if possible (simplified fallback)
                if measure_name == "DIABETES": measure_name = "DM"
            else:
                measure_name = "UNKNOWN"
        
        self.measure_name = measure_name
        
        # Extract components
        age_range = self.extract_age_range()
        enrollment = self.extract_continuous_enrollment()
        numerator = self.extract_numerator_components()
        exclusions = self.extract_exclusions()
        
        # ⚡ New AI Extraction for Complex Logic
        denominator_components = self.extract_denominator_components()
        logic_pathways = self.extract_logic_pathways()
        
        # Build config
        clinical_events = {
            'numerator_components': numerator,
            'logic_pathways': logic_pathways
        }
        
        # If we found complex denominator logic, add it and simplify initial population
        initial_pop = []
        if denominator_components:
            clinical_events['denominator_components'] = denominator_components
            # Minimal IP for engine compatibility
            initial_pop = [{
                'event': 'Outpatient Visit',
                'value_set_names': ['Outpatient'],
                'table': f'{measure_name}_VISIT_IN' 
            }]
        else:
            # Fallback to standard IP logic if no complex components found
            initial_pop = [{
                'event': 'Outpatient Visit',
                'value_set_names': ['Outpatient'],
                'table': f'{measure_name}_VISIT_IN'
            }]

        config = {
            'measure_name': measure_name,
            'description': f'{measure_name} HEDIS Measure (Auto-generated from PDF)',
            'rules': {
                'age_range': age_range,
                'age_as_of': 'December 31',
                'anchor_date_type': 'calendar_end',
                'continuous_enrollment': enrollment,
                'initial_population': initial_pop,
                'exclusions': exclusions,
                'clinical_events': clinical_events
            }
        }
        
        # Save to file
        if not output_path:
            output_path = f'config/{measure_name}.yaml'
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
        
        print(f"\n[OK] Config generated: {output_path}")
        print(f"[NOTE] Please review and edit the file to refine the rules!")
        
        return config

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert NCQA PDF to YAML')
    parser.add_argument('pdf', help='Path to NCQA PDF specification')
    parser.add_argument('--output', help='Output path for YAML config')
    parser.add_argument('--title', help='Target measure title to search for (e.g., "Diabetes Monitoring (SMD)")')
    
    args = parser.parse_args()
    
    # Try to initialize AI extractor
    extractor = None
    try:
        try:
            from ai_extractor import AIScenarioExtractor
        except ImportError:
            from src.ai_extractor import AIScenarioExtractor
        print(" Initializing AI Extractor for NCQA rules...")
        extractor = AIScenarioExtractor(model_name=os.getenv('OLLAMA_MODEL', 'qwen2:0.5b'))
    except Exception as e:
        import traceback
        print(f" AI Extractor not available: {e}")
        traceback.print_exc()
    
    parser_obj = NCQASpecParser(args.pdf, ai_extractor=extractor)
    parser_obj.generate_config(output_path=args.output, target_measure_title=args.title)
