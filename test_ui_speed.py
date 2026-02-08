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
import os
from dotenv import load_dotenv
load_dotenv()
vsd_path = os.getenv('VSD_PATH', 'data/VSD_MY2026.xlsx')
result = run_measure_gen_custom(
    'PSA',
    'data/PSA_MY2026_TestCase.xlsx',
    vsd_path,
    skip_quality_check=True,
    disable_ai=True
)
print(f"✓ Full generation: {time.time() - start:.2f}s")
print(f"✓ Output: {result}")
