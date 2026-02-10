import os
import argparse
import sys
import glob
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ncqa_parser import NCQASpecParser
from src.schema_manager import SchemaManager
from src.template_generator import SmartTemplateGenerator

try:
    from src.ai_extractor import AIScenarioExtractor
    AI_AVAILABLE = True
except ImportError:
    print("⚠️ AI Extractor not available. Running in Regex Mode.")
    AI_AVAILABLE = False

class BatchNCQAConverter:
    """
    Automates the conversion of NCQA PDFs to:
    1. YAML Configurations (via NCQASpecParser)
    2. Universal Schema Definitions (via SchemaManager)
    3. Smart Test Case Templates (via TemplateGenerator)
    4. Comprehensive Extraction Report
    """
    
    def __init__(self, pdf_dir, output_dir='config/ncqa', model_name='qwen2:0.5b'):
        self.pdf_dir = pdf_dir
        self.output_dir = output_dir
        self.model_name = model_name
        self.report_log = []
        self.schema_manager = SchemaManager()
        
        # Initialize AI
        self.ai_extractor = None
        if AI_AVAILABLE:
            try:
                self.ai_extractor = AIScenarioExtractor(model_name=model_name)
                print(f"🤖 AI Initialized: {model_name}")
            except Exception as e:
                print(f"❌ AI Init Failed: {e}")

    def find_pdfs(self):
        """Find all PDFs in directory."""
        return glob.glob(os.path.join(self.pdf_dir, '*.pdf'))

    def run(self):
        """Execute the batch process."""
        pdfs = self.find_pdfs()
        print(f"🚀 Starting Batch Conversion for {len(pdfs)} PDFs...")
        
        # Ensure 'Universal' templates exist
        self.schema_manager.universalize_schema()
        
        for pdf_path in pdfs:
            self.process_single_pdf(pdf_path)
            
        self.generate_report()
        print("\n✨ Batch Processing Complete! ✨")

    def process_single_pdf(self, pdf_path):
        """Process a single PDF."""
        filename = os.path.basename(pdf_path)
        print(f"\n--------------------------------------------------")
        print(f"📄 Processing: {filename}")
        
        try:
            # 1. Parse PDF -> YAML
            parser = NCQASpecParser(pdf_path, ai_extractor=self.ai_extractor)
            
            # Auto-detect measure name from filename if possible (e.g. "PSA_Spec.pdf")
            measure_guess = filename.split('_')[0].split('.')[0].upper()
            if len(measure_guess) > 4: measure_guess = None # Probably not an abbr
            
            # We pass Title=None to let Parser auto-detect inside PDF
            config = parser.generate_config(target_measure_title=None) 
            
            measure_name = config.get('measure_name', 'UNKNOWN')
            if measure_name == 'UNKNOWN' and measure_guess:
                measure_name = measure_guess
                config['measure_name'] = measure_name
            
            # Save YAML
            yaml_path = os.path.join(self.output_dir, f"{measure_name}.yaml")
            parser.generate_config(output_path=yaml_path, target_measure_title=None) # Re-save with correct path
            
            # 2. Expand Schema
            self.schema_manager.expand_schema(measure_name)
            
            # 3. Generate Smart Template
            template_gen = SmartTemplateGenerator(measure_name, config_path=yaml_path)
            template_path = f"data/{measure_name}_TestCase_SMART.xlsx"
            template_gen.generate_template(output_path=template_path)
            
            # 4. Log Success
            age_range = config['rules'].get('age_range', 'N/A')
            num_components = len(config['rules'].get('clinical_events', {}).get('numerator_components', []))
            logic_pathways = len(config['rules'].get('clinical_events', {}).get('logic_pathways', []))
            
            self.report_log.append({
                'status': 'SUCCESS',
                'file': filename,
                'measure': measure_name,
                'details': f"Age: {age_range}, Numerators: {num_components}, Pathways: {logic_pathways}",
                'template': template_path
            })
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            self.report_log.append({
                'status': 'FAILED',
                'file': filename,
                'error': str(e)
            })

    def generate_report(self):
        """Generate Markdown and HTML Reports."""
        # 1. Markdown
        md_path = "NCQA_EXTRACTION_REPORT.md"
        with open(md_path, 'w') as f:
            f.write(f"# NCQA Batch Extraction Report\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Model:** {self.model_name}\n\n")
            
            f.write("| Status | PDF File | Measure | Details | Template |\n")
            f.write("|---|---|---|---|---|\n")
            
            for entry in self.report_log:
                if entry.get('status') == 'SUCCESS':
                    f.write(f"| ✅ | {entry['file']} | **{entry['measure']}** | {entry['details']} | [{entry['measure']} Template]({entry['template']}) |\n")
                else:
                    f.write(f"| ❌ | {entry['file']} | N/A | Error: {entry.get('error')} | N/A |\n")
        
        print(f"\n📄 Markdown Report: {md_path}")
        
        # 2. HTML (Professional Dashboard)
        html_path = "NCQA_EXTRACTION_REPORT.html"
        self.generate_html_report(html_path)
        print(f"🎨 HTML Dashboard: {html_path}")

    def generate_html_report(self, html_path):
        """Generate a sleek HTML dashboard."""
        
        success_count = sum(1 for e in self.report_log if e.get('status') == 'SUCCESS')
        total_count = len(self.report_log)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NCQA Extraction Report</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f6f9; }}
                h1 {{ color: #2c3e50; }}
                .summary {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; display: flex; gap: 40px; }}
                .stat {{ text-align: center; }}
                .stat-num {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                .stat-label {{ color: #7f8c8d; font-size: 14px; }}
                table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 12px; border-bottom: 1px solid #ecf0f1; }}
                tr:last-child td {{ border-bottom: none; }}
                .status-success {{ color: #27ae60; font-weight: bold; }}
                .status-failed {{ color: #c0392b; font-weight: bold; }}
                .btn {{ display: inline-block; padding: 6px 12px; background: #3498db; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; }}
                .btn:hover {{ background: #2980b9; }}
            </style>
        </head>
        <body>
            <h1>🏭 NCQA Automated Extraction Report</h1>
            
            <div class="summary">
                <div class="stat">
                    <div class="stat-num">{total_count}</div>
                    <div class="stat-label">Total PDFs</div>
                </div>
                <div class="stat">
                    <div class="stat-num">{success_count}</div>
                    <div class="stat-label">Successful</div>
                </div>
                <div class="stat">
                    <div class="stat-num">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                    <div class="stat-label">Run Time</div>
                </div>
                <div class="stat">
                    <div class="stat-num">{self.model_name}</div>
                    <div class="stat-label">AI Model</div>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>PDF File</th>
                        <th>Measure</th>
                        <th>Details</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for entry in self.report_log:
            if entry.get('status') == 'SUCCESS':
                row = f"""
                <tr>
                    <td class="status-success">SUCCESS</td>
                    <td>{entry['file']}</td>
                    <td><strong>{entry['measure']}</strong></td>
                    <td>{entry['details']}</td>
                    <td><a href="{entry['template']}" class="btn">Download Template</a></td>
                </tr>
                """
            else:
                row = f"""
                <tr>
                    <td class="status-failed">FAILED</td>
                    <td>{entry['file']}</td>
                    <td>N/A</td>
                    <td>{entry.get('error')}</td>
                    <td>-</td>
                </tr>
                """
            html_content += row
            
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        with open(html_path, 'w') as f:
            f.write(html_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Batch NCQA Converter')
    parser.add_argument('--input', default='data/pdfs', help='Input directory containing PDFs')
    parser.add_argument('--model', default='qwen2:0.5b', help='Ollama model name')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Creating input directory: {args.input}")
        os.makedirs(args.input, exist_ok=True)
        print("Please place your NCQA PDFs in this folder and run again.")
    else:
        converter = BatchNCQAConverter(args.input, model_name=args.model)
        converter.run()
