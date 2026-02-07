from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
from main import run_measure_gen_custom
from src.reformatter import TestCaseReformatter

app = Flask(__name__)
app.secret_key = 'supersecretkey_hedis_2026'

# Config
UPLOAD_FOLDER = 'data_uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Default VSD Path
DEFAULT_VSD = r"C:\Users\sushi\Downloads\RAG-Tutorials-main\data\HEDIS MY 2026 Volume 2 Value Set Directory_2025-08-01.xlsx"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Get measure selection
        measure = request.form.get('measure', 'PSA')
        
        # 2. Handle Test Case Upload
        tc_path = None
        if 'testcase_file' in request.files and request.files['testcase_file'].filename:
            tc_file = request.files['testcase_file']
            tc_path = os.path.join(UPLOAD_FOLDER, f"{measure}_TestCase.xlsx")
            tc_file.save(tc_path)
            flash(f"Test case file uploaded: {tc_file.filename}", "success")
        else:
            # Try default locations
            tc_path = os.path.join('data', f"{measure}_MY2026_TestCase.xlsx")
            if not os.path.exists(tc_path):
                tc_path = os.path.join(UPLOAD_FOLDER, f"{measure}_TestCase.xlsx")
                if not os.path.exists(tc_path):
                    flash(f"No test case file found for {measure}. Please upload one.", "error")
                    return redirect(url_for('index'))
        
        # 3. Handle VSD Upload
        vsd_path = DEFAULT_VSD
        if 'vsd_file' in request.files and request.files['vsd_file'].filename:
            vsd_file = request.files['vsd_file']
            vsd_path = os.path.join(UPLOAD_FOLDER, "VSD_Current.xlsx")
            vsd_file.save(vsd_path)
            flash(f"VSD file uploaded: {vsd_file.filename}", "success")

        # 3.5. Handle NCQA PDF Upload (Auto-generate config)
        if 'ncqa_pdf' in request.files and request.files['ncqa_pdf'].filename:
            ncqa_file = request.files['ncqa_pdf']
            ncqa_path = os.path.join(UPLOAD_FOLDER, f"{measure}_NCQA_Spec.pdf")
            ncqa_file.save(ncqa_path)
            flash(f"📄 NCQA PDF uploaded: {ncqa_file.filename}", "info")
            
            try:
                from src.ncqa_parser import NCQASpecParser
                flash(f"🤖 Parsing NCQA specification...", "info")
                
                parser = NCQASpecParser(ncqa_path)
                config = parser.generate_config()
                
                flash(f"✅ Config auto-generated for {measure}! Please review config/{measure}.yaml", "success")
            except Exception as e:
                flash(f"⚠️ NCQA parsing failed: {str(e)}", "error")

        # 3.6. Handle Auto-Reformat (if checkbox is checked and file was uploaded)
        auto_reformat = request.form.get('auto_reformat')
        if auto_reformat and 'testcase_file' in request.files and request.files['testcase_file'].filename:
            flash(f"🔄 Auto-reformatting {measure} test case...", "info")
            try:
                reformatter = TestCaseReformatter()
                clean_path = reformatter.reformat_file(tc_path)
                tc_path = clean_path  # Use cleaned version
                flash(f"✅ Auto-reformat complete!", "success")
            except Exception as e:
                flash(f"⚠️ Auto-reformat failed: {str(e)}. Continuing with original file.", "error")

        # 4. Handle Actions
        action = request.form.get('action')
        
        if action == 'reformat':
            flash(f"🔄 Starting reformat for {measure}...", "info")
            try:
                reformatter = TestCaseReformatter()
                clean_path = reformatter.reformat_file(tc_path)
                flash(f"✅ Reformat successful! Cleaned file saved to: {os.path.basename(clean_path)}", "success")
                # Update tc_path to use cleaned version for future operations
                tc_path = clean_path
            except Exception as e:
                flash(f"❌ Reformat failed: {str(e)}", "error")
                return redirect(url_for('index'))

        elif action == 'generate':
            flash(f"🚀 Generating mockup for {measure}...", "info")
            try:
                # Check if config exists
                config_path = f'config/{measure}.yaml'
                if not os.path.exists(config_path):
                    flash(f"❌ Configuration file not found: {config_path}. Please create it first or use the measure automator.", "error")
                    return redirect(url_for('index'))
                
                # Run generation
                output_file = run_measure_gen_custom(measure, tc_path, vsd_path)
                
                if output_file and os.path.exists(output_file):
                    flash(f"✅ Mockup generated successfully!", "success")
                    return send_file(output_file, as_attachment=True, download_name=os.path.basename(output_file))
                else:
                    flash(f"❌ Generation failed. Check console for details.", "error")
                    
            except Exception as e:
                flash(f"❌ Generation error: {str(e)}", "error")
                import traceback
                print(traceback.format_exc())

        elif action == 'validate':
            flash(f"✅ Validating mockup for {measure}...", "info")
            try:
                from src.validator import HEDISValidator
                from src.parser import TestCaseParser
                
                # Check if mockup exists
                mockup_path = f'output/{measure}_MY2026_Mockup_v15.xlsx'
                if not os.path.exists(mockup_path):
                    flash(f"❌ Mockup file not found. Please generate first.", "error")
                    return redirect(url_for('index'))
                
                # Load test cases to get expected results
                parser = TestCaseParser(tc_path)
                config_path = f'config/{measure}.yaml'
                
                # Load measure config to get scenarios
                import yaml
                with open(config_path) as f:
                    measure_config = yaml.safe_load(f)
                
                scenarios = parser.parse_scenarios(measure_config)
                
                # Build test cases list
                test_cases = []
                for sc in scenarios:
                    expected = 'Compliant' if sc.get('compliant') else 'Non-Compliant'
                    if sc.get('excluded'):
                        expected = 'Excluded'
                    test_cases.append({
                        'id': sc['id'],
                        'expected': expected
                    })
                
                # Run validation
                validator = HEDISValidator(config_path, mockup_path)
                summary = validator.validate_all(test_cases)
                
                # Export report
                report_path = f'output/{measure}_Validation_Report.xlsx'
                validator.export_report(report_path)
                
                # Show results
                flash(f"✅ Validation complete! Pass rate: {summary['pass_rate']:.1f}%", "success")
                flash(f"📊 {summary['passed']}/{summary['total']} test cases passed", "info")
                
                if summary['failed'] > 0:
                    flash(f"⚠️ {summary['failed']} test cases failed. See report for details.", "error")
                
                return send_file(report_path, as_attachment=True, download_name=os.path.basename(report_path))
                
            except Exception as e:
                flash(f"❌ Validation error: {str(e)}", "error")
                import traceback
                print(traceback.format_exc())

    return render_template('index.html')

if __name__ == '__main__':
    print("🌐 Starting HEDIS Mockup Generator UI...")
    print("📍 Navigate to: http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
