"""
Script to batch convert NCQA PDF specifications to YAML configuration files.

Usage:
    # Convert all PDFs in docs/ncqa_specs
    python scripts/convert_ncqa_pdfs.py --all
    
    # Convert single measure
    python scripts/convert_ncqa_pdfs.py --measure PSA
    
    # Convert specific file
    python scripts/convert_ncqa_pdfs.py --pdf docs/ncqa_specs/PSA.pdf --output config/ncqa/PSA_NCQA.yaml
"""

import argparse
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ncqa_parser import NCQASpecParser

def convert_all_pdfs(pdf_dir=None, output_dir=None):
    """Convert all NCQA PDFs in directory to YAML configs."""
    if pdf_dir is None: pdf_dir = os.getenv('NCQA_SPEC_DIR', 'docs/ncqa_specs')
    if output_dir is None: output_dir = os.getenv('NCQA_CONFIG_DIR', 'config/ncqa')
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(pdf_dir):
        print(f"Directory not found: {pdf_dir}")
        os.makedirs(pdf_dir, exist_ok=True)
        print(f"Created {pdf_dir}. Please place NCQA PDFs there.")
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return
        
    print(f"📚 Found {len(pdf_files)} NCQA PDFs")
    
    for pdf_file in pdf_files:
        # Extract measure name logic (assuming format like PSA_MY2026_Spec.pdf)
        # Fallback to first part of filename
        measure = pdf_file.split('_')[0]
        
        pdf_path = os.path.join(pdf_dir, pdf_file)
        output_path = os.path.join(output_dir, f'{measure}_NCQA.yaml')
        
        print(f"\n🔄 Converting {measure}...")
        print(f"   PDF: {pdf_path}")
        print(f"   Output: {output_path}")
        
        try:
            parser = NCQASpecParser(pdf_path)
            # We override the generate_config logic slightly to just save it
            # The original generates and returns and saves if output_path is provided
            parser.measure_name = measure # Force measure name from filename if extraction fails
            parser.generate_config(output_path)
        except Exception as e:
            print(f"   ❌ Failed: {e}")

def convert_single_measure(measure, pdf_dir=None, output_dir=None):
    """Convert a single measure's PDF."""
    if pdf_dir is None: pdf_dir = os.getenv('NCQA_SPEC_DIR', 'docs/ncqa_specs')
    if output_dir is None: output_dir = os.getenv('NCQA_CONFIG_DIR', 'config/ncqa')
    os.makedirs(output_dir, exist_ok=True)
    
    # Try finding the file roughly matching the measure
    if not os.path.exists(pdf_dir):
        print(f"Directory not found: {pdf_dir}")
        return

    candidates = [f for f in os.listdir(pdf_dir) if f.startswith(measure) and f.lower().endswith('.pdf')]
    
    if not candidates:
        print(f"❌ No PDF found for measure {measure} in {pdf_dir}")
        return
        
    # Use first match
    pdf_path = os.path.join(pdf_dir, candidates[0])
    output_path = os.path.join(output_dir, f'{measure}_NCQA.yaml')
    
    print(f"\n🔄 Converting {measure}...")
    print(f"   PDF: {pdf_path}")
    
    try:
        parser = NCQASpecParser(pdf_path)
        parser.measure_name = measure
        parser.generate_config(output_path)
    except Exception as e:
        print(f"   ❌ Failed: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert NCQA PDFs to YAML')
    parser.add_argument('--all', action='store_true', help='Convert all PDFs in docs/ncqa_specs')
    parser.add_argument('--measure', help='Convert single measure (e.g., PSA)')
    parser.add_argument('--pdf', help='Custom PDF path')
    parser.add_argument('--output', help='Custom output path')
    
    args = parser.parse_args()
    
    if args.all:
        convert_all_pdfs()
    elif args.measure:
        convert_single_measure(args.measure)
    elif args.pdf and args.output:
        try:
            p = NCQASpecParser(args.pdf)
            p.generate_config(args.output)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Default behavior: help
        parser.print_help()
