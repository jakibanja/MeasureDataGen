from flask import Flask, request, render_template, send_file, redirect, url_for, flash, Response, stream_with_context
import os
import json
import time
from main import run_measure_gen_custom
from src.reformatter import TestCaseReformatter
from src.progress import progress_tracker

app = Flask(__name__)
app.secret_key = 'hedis_mockup_secret_key_2026'

@app.route('/progress')
def progress():
    def generate():
        while True:
            # Yield progress data as SSE
            data = json.dumps(progress_tracker.progress)
            yield f"data: {data}\n\n"
            time.sleep(0.5)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# Folder Configuration
UPLOAD_FOLDER = 'uploads'      # Temporary uploads
DATA_FOLDER = 'data'            # Processed test cases
OUTPUT_FOLDER = 'output'        # Generated mockups

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# VSD Configuration - Use environment variable
DEFAULT_VSD = os.getenv('VSD_PATH', 'data/VSD_MY2026.xlsx')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Get measure selection & model preference
        measure = request.form.get('measure', 'PSA')
        model_name = request.form.get('model_name', 'qwen2:0.5b')
        
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
            flash(f"🔄 Auto-reformatting {measure} test case using {model_name}...", "info")
            try:
                reformatter = TestCaseReformatter(model_name=model_name)
                clean_path = reformatter.reformat_file(tc_path)
                tc_path = clean_path  # Use cleaned version
                flash(f"✅ Auto-reformat complete!", "success")
            except Exception as e:
                flash(f"⚠️ Auto-reformat failed: {str(e)}. Continuing with original file.", "error")

        # 4. Handle Actions
        action = request.form.get('action')
        
        if action == 'reformat':
            flash(f"🔄 Starting reformat for {measure} using {model_name}...", "info")
            try:
                reformatter = TestCaseReformatter(model_name=model_name)
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
                
                # Get performance options from form
                disable_ai = request.form.get('disable_ai') == 'on'
                skip_quality_check = request.form.get('skip_quality_check') == 'on'
                validate_ncqa = request.form.get('validate_ncqa') == 'on'
                
                # Show what options are enabled
                if disable_ai:
                    flash(f"⚡ AI Extractor disabled (regex-only mode for faster generation)", "info")
                else:
                    flash(f"🤖 AI Extractor enabled using model: {model_name}", "info")
                
                if skip_quality_check:
                    flash(f"⚡ Quality checks skipped (faster generation)", "info")
                if validate_ncqa:
                    flash(f"🔍 Validating against NCQA specification...", "info")
                
                # Run generation with options
                output_file = run_measure_gen_custom(
                    measure, 
                    tc_path, 
                    vsd_path,
                    skip_quality_check=skip_quality_check,
                    disable_ai=disable_ai,
                    validate_ncqa=validate_ncqa,
                    model_name=model_name
                )
                
                if output_file and os.path.exists(output_file):
                    flash(f"✅ Mockup generated successfully!", "success")
                    return send_file(output_file, as_attachment=True, download_name=os.path.basename(output_file))
                else:
                    flash(f"❌ Generation failed. Check console for details.", "error")
                    
            except Exception as e:
                flash(f"❌ Generation error: {str(e)}", "error")
                import traceback
                print(traceback.format_exc())
                return redirect(url_for('index'))




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


@app.route('/download_template')
def download_template():
    """Download the standard test case template."""
    template_path = 'templates/Standard_TestCase_Template.xlsx'
    if os.path.exists(template_path):
        return send_file(template_path, as_attachment=True, download_name='Standard_TestCase_Template.xlsx')
    else:
        flash("❌ Template file not found.", "error")
        return redirect(url_for('index'))
def convert_ncqa():
    """Convert uploaded NCQA PDF to YAML"""
    if 'ncqa_pdf' not in request.files:
        flash('No PDF uploaded', 'error')
        return redirect(url_for('index'))
    
    file = request.files['ncqa_pdf']
    measure = request.form.get('measure', 'PSA')
    
    if not file.filename:
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    # Save PDF temporarily
    pdf_path = os.path.join(UPLOAD_FOLDER, f'{measure}_NCQA_Spec.pdf')
    file.save(pdf_path)
    
    # Convert to YAML
    output_path = f'config/ncqa/{measure}_NCQA.yaml'
    os.makedirs('config/ncqa', exist_ok=True)
    
    try:
        from src.ncqa_parser import NCQASpecParser
        parser = NCQASpecParser(pdf_path)
        # We need to ensure generate_config can take an output path or we modify it
        # The existing generate_config takes output_path
        parser.measure_name = measure
        parser.generate_config(output_path)
        
        flash(f'✅ NCQA spec converted to {output_path}', 'success')
        flash('📝 Please review and edit the YAML file if needed', 'info')
    except Exception as e:
        flash(f'❌ Conversion failed: {e}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🌐 Starting HEDIS Mockup Generator UI...")
    print("📍 Navigate to: http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
