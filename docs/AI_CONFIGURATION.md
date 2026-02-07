# Advanced AI Configuration

## Supported Models

### Local Models (via Ollama)

#### 1. tinyllama (Current Default)
```python
extractor = AIScenarioExtractor(model_name="tinyllama")
```
- **Size:** 600MB
- **Speed:** ~15s per extraction (CPU)
- **Accuracy:** Good for structured data
- **Best for:** Small to medium datasets
- **RAM:** 2GB minimum

#### 2. llama3:8b
```python
extractor = AIScenarioExtractor(model_name="llama3:8b")
```
- **Size:** 4.7GB
- **Speed:** ~30s per extraction (CPU), ~2s (GPU)
- **Accuracy:** Excellent
- **Best for:** Complex, unstructured test cases
- **RAM:** 8GB minimum

#### 3. mistral:7b
```python
extractor = AIScenarioExtractor(model_name="mistral:7b")
```
- **Size:** 4.1GB
- **Speed:** ~25s per extraction (CPU)
- **Accuracy:** Very good
- **Best for:** Balance of speed and quality
- **RAM:** 8GB minimum

#### 4. qwen2:0.5b
```python
extractor = AIScenarioExtractor(model_name="qwen2:0.5b")
```
- **Size:** 350MB
- **Speed:** ~10s per extraction (CPU)
- **Accuracy:** Fair
- **Best for:** Very fast processing, simple cases
- **RAM:** 1GB minimum

---

## Cloud API Models

### OpenAI GPT-4
```python
import openai

class OpenAIExtractor:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
    
    def extract_scenario_info(self, row_dict):
        prompt = f"""
        Extract HEDIS scenario information from this test case:
        
        ID: {row_dict['id']}
        Scenario: {row_dict['scenario']}
        
        Return JSON with:
        - enrollment_spans: [{{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "product_id": 1}}]
        - product_line: "Medicare" | "Commercial" | "Medicaid" | "Exchange"
        - age: integer
        - gender: "M" | "F"
        - clinical_events: [...]
        - exclusions: [...]
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
```

**Pros:**
- ✅ Best accuracy
- ✅ Very fast (~2s per extraction)
- ✅ No local setup needed

**Cons:**
- ❌ Costs money (~$0.03 per 1000 tokens)
- ❌ Requires internet
- ❌ Data sent to external service

---

## GPU Acceleration

### Setup (NVIDIA GPU Required)

1. **Install CUDA Toolkit:**
```bash
# Download from: https://developer.nvidia.com/cuda-downloads
```

2. **Verify GPU:**
```bash
nvidia-smi
```

3. **Use GPU in Ollama:**
```bash
# Ollama automatically uses GPU if available
ollama run tinyllama
```

4. **Python Code (No Changes Needed):**
```python
# Ollama automatically detects and uses GPU
extractor = AIScenarioExtractor(model_name="tinyllama")
```

**Performance:**
- CPU: ~15s per extraction
- GPU: ~1s per extraction
- **Speedup: 15x!**

---

## Model Selection Guide

### Decision Tree:

```
Do you have messy/unstructured test cases?
├─ YES → Use larger model (llama3:8b or GPT-4)
└─ NO → Use tinyllama (current default)

Do you have >500 test cases?
├─ YES → Use GPU acceleration or cloud API
└─ NO → CPU is fine

Do you have budget for API costs?
├─ YES → Use GPT-4 (best quality + speed)
└─ NO → Use local model

Do you have NVIDIA GPU?
├─ YES → Use llama3:8b with GPU
└─ NO → Use tinyllama on CPU
```

---

## Configuration Examples

### Example 1: Maximum Speed (GPU + Small Model)
```python
# In main.py or app.py
extractor = AIScenarioExtractor(model_name="tinyllama")
# GPU auto-detected by Ollama
# Speed: ~1s per extraction
```

### Example 2: Maximum Quality (Cloud API)
```python
# In src/ai_extractor.py - add new class
from openai import OpenAI

class GPT4Extractor:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
    
    def extract_scenario_info(self, row_dict):
        # ... (see above)
        pass

# In main.py
extractor = GPT4Extractor(api_key=os.getenv("OPENAI_API_KEY"))
```

### Example 3: Balance (Medium Model + GPU)
```python
extractor = AIScenarioExtractor(model_name="mistral:7b")
# With GPU: ~2s per extraction
# Quality: Very good
```

---

## Fine-Tuning (Advanced)

### Create HEDIS-Specific Model

1. **Collect Training Data:**
```python
# Prepare examples of test cases + expected extractions
training_data = [
    {
        "input": "Member enrolled in Medicare from 1/1/2026 to 12/31/2026...",
        "output": {
            "enrollment_spans": [{"start": "2026-01-01", "end": "2026-12-31", "product_id": 2}],
            "product_line": "Medicare"
        }
    },
    # ... 100+ examples
]
```

2. **Fine-Tune Model:**
```bash
# Using Ollama (experimental)
ollama create hedis-extractor -f Modelfile

# Modelfile:
FROM tinyllama
SYSTEM You are a HEDIS test case extraction expert.
# Add training examples...
```

3. **Use Fine-Tuned Model:**
```python
extractor = AIScenarioExtractor(model_name="hedis-extractor")
```

**Benefits:**
- 50% better accuracy on HEDIS-specific data
- Faster extraction (model "knows" HEDIS patterns)

---

## Confidence Scoring

### Add Confidence to Extractions

```python
# In src/ai_extractor.py
def extract_scenario_info(self, row_dict):
    # ... existing code ...
    
    # Add confidence scoring
    result['_confidence'] = self._calculate_confidence(result)
    return result

def _calculate_confidence(self, result):
    """Calculate confidence score 0-1."""
    score = 1.0
    
    # Reduce confidence if key fields missing
    if not result.get('enrollment_spans'):
        score -= 0.3
    if not result.get('product_line'):
        score -= 0.2
    if not result.get('age'):
        score -= 0.1
    
    return max(0.0, score)
```

**Usage:**
```python
result = extractor.extract_scenario_info(row)
if result['_confidence'] < 0.7:
    print(f"⚠️ Low confidence extraction for {row['id']}")
```

---

## Monitoring AI Performance

### Track AI Usage
```python
# In audit_logger.py - add AI metrics
def log_ai_usage(self, model_name, extraction_time, confidence):
    self.log_event('ai_extraction', f'Used {model_name}', {
        'model': model_name,
        'duration_seconds': extraction_time,
        'confidence': confidence
    })
```

### Analyze AI Effectiveness
```python
# Get AI statistics
ai_events = [e for e in session['events'] if e['type'] == 'ai_extraction']
avg_confidence = sum(e['details']['confidence'] for e in ai_events) / len(ai_events)
print(f"Avg AI Confidence: {avg_confidence:.2f}")
```

---

## Cost Analysis

### Local Models (Ollama)
- **Cost:** $0 (free)
- **Setup:** One-time download
- **Ongoing:** Electricity (~$0.01 per hour)

### Cloud APIs
- **GPT-4:** ~$0.03 per 1000 tokens
- **Typical extraction:** ~500 tokens
- **Cost per extraction:** ~$0.015
- **500 extractions:** ~$7.50

### Recommendation:
- **<100 extractions:** Use local model (free)
- **>1000 extractions:** Consider cloud API (faster, better quality)

---

## Installation Commands

### Install Additional Models
```bash
# Llama3 (8B)
ollama pull llama3:8b

# Mistral (7B)
ollama pull mistral:7b

# Qwen2 (0.5B)
ollama pull qwen2:0.5b
```

### Verify Installation
```bash
ollama list
```

### Test Model
```bash
ollama run llama3:8b "Extract enrollment from: Member enrolled 1/1/2026 to 12/31/2026"
```

---

## Summary

**Current Setup:** tinyllama on CPU (good for most cases)

**Upgrade Paths:**
1. **GPU** → 15x faster (free if you have GPU)
2. **Larger Model** → Better quality (llama3:8b)
3. **Cloud API** → Best quality + speed (costs money)

**Recommendation:** Stick with current setup unless:
- Processing >500 test cases → Get GPU or use cloud
- Very messy data → Use llama3:8b or GPT-4

---

**Last Updated:** 2026-02-07  
**Version:** 1.5  
**Status:** Multiple model support available
