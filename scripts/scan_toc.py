import PyPDF2
import re
import json

def scan_toc(pdf_path, start_page=4, end_page=12):
    print(f"Scanning TOC from {pdf_path} (Pages {start_page+1}-{end_page+1})...")
    measures = []
    
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for i in range(start_page, min(end_page, len(reader.pages))):
            text = reader.pages[i].extract_text()
            # Improved pattern to capture more complex titles
            # Example: Weight Assessment ... (WCC) ....... 45
            matches = re.finditer(r'([A-Z][A-Za-z\s\/\,]+)\(([A-Z]{3,4})\)\s*\.{3,}', text)
            for m in matches:
                title = m.group(1).strip()
                abbr = m.group(2).strip()
                # Clean up title (remove trailing 'and' or 'for' if it was cut off)
                title = re.sub(r'\s+(and|for|of|with)$', '', title, flags=re.I)
                measures.append({"abbr": abbr, "title": f"{title} ({abbr})"})
                
    return measures

if __name__ == "__main__":
    pdf = 'docs/ncqa_specs/HEDIS MY 2026 Volume 2 Publication_2025-08-01.pdf'
    measures = scan_toc(pdf)
    print(f"Found {len(measures)} measures:")
    for m in measures:
        print(f"- {m['abbr']}: {m['title']}")
    
    with open('data/measure_index.json', 'w') as f:
        json.dump(measures, f, indent=2)
    print("\nSaved to data/measure_index.json")
