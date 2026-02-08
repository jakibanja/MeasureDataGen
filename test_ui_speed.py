"""
Quick diagnostic to check what's slow in the UI
"""
import time

print("Testing UI generation speed...")

# Test 1: Import speed
start = time.time()
from main import run_measure_gen_custom
print(f"✓ Import time: {time.time() - start:.2f}s")

# Test 2: Format detection speed
start = time.time()
from main import _is_standard_format
is_standard = _is_standard_format('data/PSA_MY2026_TestCase.xlsx')
print(f"✓ Format detection: {time.time() - start:.2f}s (Standard: {is_standard})")

# Test 3: VSD loading (cached)
start = time.time()
vsd_path = r"C:\Users\sushi\Downloads\RAG-Tutorials-main\data\HEDIS MY 2026 Volume 2 Value Set Directory_2025-08-01.xlsx"
result = run_measure_gen_custom(
    'PSA',
    'data/PSA_MY2026_TestCase.xlsx',
    vsd_path,
    skip_quality_check=True,
    disable_ai=True
)
print(f"✓ Full generation: {time.time() - start:.2f}s")
print(f"✓ Output: {result}")
