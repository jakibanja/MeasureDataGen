## CLI Reference Guide

This document explains the command-line arguments available in `main.py` for fine-tuning your data generation.

### 1. Basic Usage
```bash
python main.py <Measure Name> [Ref Options]
```

### 2. New Toggles (v2.0)

| Flag | Choices | Default | Description |
| :--- | :--- | :--- | :--- |
| `--depth` | `population`<br>`scenario` | `population` | **Controls Row Generation**.<br>- **Population**: Generates comprehensive member history, including default visits (e.g., annual checkup) if none are specified.<br>- **Scenario**: Generates *only* the events explicitly defined in the Excel test case. Ideal for strict logic testing. |
| `--scope` | `all`<br>`mandatory` | `all` | **Controls Column Population**.<br>- **All**: Populates rich metadata (Claim IDs, NPIs, Tax IDs, Product IDs).<br>- **Mandatory**: Populates only the minimum fields required for compliance logic (Date, Code, Value). |

### 3. Examples

#### A. Full Mockup (Default)
**Best for:** Client delivery, UAT, Integration Testing.
```bash
python main.py PSA --depth population --scope all
```
*   **Result:** A realistic file with a full member history, standard visits, and complete claim metadata.

#### B. Logic Testing
**Best for:** Verifying if a specific scenario triggers the numerator.
```bash
python main.py PSA --depth scenario --scope mandatory
```
*   **Result:** A clean file containing *only* the events you wrote in Excel. No random visits to confuse the results.

#### C. Performance Load Test
**Best for:** Generating massive volumes of valid data quickly.
```bash
python main.py PSA --depth population --scope mandatory
```
*   **Result:** fast generation of compliant data without the overhead of rich metadata lookups.
