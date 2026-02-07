import PyPDF2
import re
import yaml
import os

class NCQASpecParser:
    """
    Parses NCQA HEDIS specification PDFs to extract measure rules.
    Auto-generates config YAML files for the MockupEngine.
    """
    
    def __init__(self, pdf_path, ai_extractor=None):
        self.pdf_path = pdf_path
        self.ai_extractor = ai_extractor
        self.text = ""
        self.measure_name = ""
        
    def extract_text(self):
        """Extract all text from PDF."""
        print(f"Reading PDF: {self.pdf_path}")
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"Total pages: {len(reader.pages)}")
            
            for page_num, page in enumerate(reader.pages):
                self.text += page.extract_text() + "\n"
                
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
                
        print("⚠️ Could not identify measure name")
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
        
        print("⚠️ Could not extract age range")
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
        """Extract numerator components using AI if available."""
        if not self.ai_extractor:
            print("⚠️ No AI extractor available for numerator extraction")
            return []
        
        # Find numerator section
        numerator_match = re.search(
            r'Numerator(.*?)(?:Exclusions|Denominator|$)',
            self.text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not numerator_match:
            print("⚠️ Could not find Numerator section")
            return []
        
        numerator_text = numerator_match.group(1)[:2000]  # Limit to 2000 chars
        
        # Use AI to extract components
        print("Using AI to extract numerator components...")
        prompt = f"""
        Extract the numerator components from this HEDIS measure specification.
        Return a JSON list of components with 'name' and 'description'.
        
        Text:
        {numerator_text}
        
        Example output:
        [
          {{"name": "PSA Test", "description": "PSA lab test performed"}},
          {{"name": "Digital Rectal Exam", "description": "DRE procedure"}}
        ]
        """
        
        # For now, return placeholder (AI integration would go here)
        return [
            {
                'name': f'{self.measure_name} Test',
                'value_set_names': [f'{self.measure_name} Lab Test'],
                'table': f'{self.measure_name}_LAB_IN'
            }
        ]
    
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
    
    def generate_config(self, output_path=None):
        """Generate complete config YAML from PDF."""
        print("\n🔍 Parsing NCQA Specification PDF...")
        
        # Extract text
        self.extract_text()
        
        # Identify measure
        measure_name = self.identify_measure()
        if not measure_name:
            measure_name = input("Enter measure name (e.g., PSA): ").upper()
            self.measure_name = measure_name
        
        # Extract components
        age_range = self.extract_age_range()
        enrollment = self.extract_continuous_enrollment()
        numerator = self.extract_numerator_components()
        exclusions = self.extract_exclusions()
        
        # Build config
        config = {
            'measure_name': measure_name,
            'description': f'{measure_name} HEDIS Measure (Auto-generated from PDF)',
            'rules': {
                'age_range': age_range,
                'age_as_of': 'December 31',
                'anchor_date_type': 'calendar_end',
                'continuous_enrollment': enrollment,
                'initial_population': [
                    {
                        'event': 'Outpatient Visit',
                        'value_set_names': ['Outpatient'],
                        'table': f'{measure_name}_VISIT_IN'
                    }
                ],
                'exclusions': exclusions,
                'clinical_events': {
                    'numerator_components': numerator
                }
            }
        }
        
        # Save to file
        if not output_path:
            output_path = f'config/{measure_name}.yaml'
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
        
        print(f"\n✅ Config generated: {output_path}")
        print(f"📝 Please review and edit the file to refine the rules!")
        
        return config

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python src/ncqa_parser.py <PDF_PATH>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    parser = NCQASpecParser(pdf_path)
    parser.generate_config()
