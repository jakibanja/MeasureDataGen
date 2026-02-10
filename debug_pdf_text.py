import PyPDF2
import os

pdf_path = "docs/ncqa_specs/HEDIS MY 2026 Volume 2 Publication_2025-08-01.pdf"
target = "Diabetes Monitoring for People With Diabetes and Schizophrenia (SMD)"

with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for p_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if target.lower() in text.lower():
            print(f"Found on page {p_num + 1}")
            # Grab 10 pages
            import sys
            sys.stdout.reconfigure(encoding='utf-8')
            for i in range(p_num, p_num + 10):
                print(f"--- PAGE {i+1} ---")
                print(reader.pages[i].extract_text())
            break
