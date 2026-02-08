# Performance Optimization Guide

## Current Performance Issues

### Identified Bottlenecks

1. **VSD Manager Loading** (~10-30 seconds)
   - Loads 50MB+ Excel file on every request
   - No caching mechanism

2. **AI Extractor Initialization** (~5-15 seconds)
   - Loads LLM model for every generation
   - Model not reused between requests

3. **Quality Checks** (~2-5 seconds)
   - Runs comprehensive validation every time
   - No option to skip for quick generation

4. **Excel Writing** (~1-3 seconds)
   - Synchronous write blocks response
   - No progress feedback

**Total Time:** 18-53 seconds per generation

## Quick Wins (Immediate Improvements)

### 1. Cache VSD Manager (Saves 10-30 seconds)

**Before:**
```python
def run_measure_gen_custom(measure_name, testcase_path, vsd_path):
    vsd_manager = VSDManager(vsd_path, measurement_year=2026)  # Loads every time!
```

**After:**
```python
# Global cache
_vsd_cache = {}

def run_measure_gen_custom(measure_name, testcase_path, vsd_path):
    # Use cached VSD if available
    if vsd_path not in _vsd_cache:
        print("Loading VSD (first time only)...")
        _vsd_cache[vsd_path] = VSDManager(vsd_path, measurement_year=2026)
    vsd_manager = _vsd_cache[vsd_path]
```

### 2. Cache AI Extractor (Saves 5-15 seconds)

**Before:**
```python
def run_measure_gen_custom(...):
    extractor = AIScenarioExtractor(model_name="tinyllama")  # Loads every time!
```

**After:**
```python
# Global cache
_ai_extractor_cache = None

def run_measure_gen_custom(...):
    global _ai_extractor_cache
    if _ai_extractor_cache is None:
        print("Initializing AI Extractor (first time only)...")
        _ai_extractor_cache = AIScenarioExtractor(model_name="tinyllama")
    extractor = _ai_extractor_cache
```

### 3. Make Quality Checks Optional (Saves 2-5 seconds)

**Add parameter:**
```python
def _process_measure(measure_name, parser, engine, output_path=None, 
                     audit_logger=None, skip_quality_check=False):
    
    if not skip_quality_check:
        # Run quality checks
        quality_checker = DataQualityChecker(data_store, full_schema)
        quality_report = quality_checker.check_all()
    else:
        print("⚡ Skipping quality checks for faster generation")
```

### 4. Add Progress Indicators

```python
def _process_measure(...):
    print(f"📊 Processing {len(scenarios)} scenarios...")
    
    for idx, sc in enumerate(scenarios, 1):
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{len(scenarios)} scenarios processed")
        # ... process scenario
```

## Expected Performance After Optimization

| Operation | Before | After (1st run) | After (cached) |
|-----------|--------|-----------------|----------------|
| VSD Loading | 10-30s | 10-30s | ~0s |
| AI Extractor | 5-15s | 5-15s | ~0s |
| Quality Checks | 2-5s | 2-5s | 0s (if skipped) |
| Data Generation | 1-3s | 1-3s | 1-3s |
| Excel Writing | 1-3s | 1-3s | 1-3s |
| **Total** | **19-56s** | **19-56s** | **2-6s** ⚡ |

## Advanced Optimizations

### 5. Async Processing with Progress Bar

Use background tasks to prevent blocking:

```python
from threading import Thread
import time

def generate_async(measure_name, testcase_path, vsd_path, callback):
    def worker():
        result = run_measure_gen_custom(measure_name, testcase_path, vsd_path)
        callback(result)
    
    thread = Thread(target=worker)
    thread.start()
    return thread
```

### 6. Lazy Loading

Only load components when needed:

```python
class LazyVSDManager:
    def __init__(self, vsd_path):
        self.vsd_path = vsd_path
        self._manager = None
    
    @property
    def manager(self):
        if self._manager is None:
            self._manager = VSDManager(self.vsd_path, measurement_year=2026)
        return self._manager
```

### 7. Parallel Processing

Process multiple scenarios in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_scenario, sc) for sc in scenarios]
    results = [f.result() for f in futures]
```

## Implementation Priority

1. ✅ **High Priority** - Cache VSD Manager (biggest impact)
2. ✅ **High Priority** - Cache AI Extractor (second biggest impact)
3. ✅ **Medium Priority** - Optional quality checks
4. ✅ **Medium Priority** - Progress indicators
5. ⏸️ **Low Priority** - Async processing (more complex)
6. ⏸️ **Low Priority** - Parallel processing (needs careful testing)

## Monitoring Performance

Add timing to track improvements:

```python
import time

def _process_measure(...):
    start_time = time.time()
    
    # ... processing ...
    
    elapsed = time.time() - start_time
    print(f"⏱️  Total generation time: {elapsed:.2f} seconds")
```

## Next Steps

1. Implement caching for VSD and AI Extractor
2. Add progress indicators
3. Make quality checks optional
4. Test and measure improvements
5. Consider async processing for web interface
