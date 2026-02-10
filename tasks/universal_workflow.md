# Task: Universal Measure Workflow Improvements

## Status
- **Phase**: Planning
- **Priority**: High
- **Owner**: Antigravity

## Context
The core "Logic Engine" (MockupEngine) has been successfully upgraded to support complex, multi-event HEDIS logic (e.g., SMD Step 1 vs Step 2) using "Smart Components".
Now, we need to ensure this power is accessible for **ALL** measures (not just SMD/PSA) and improve the user workflow for handling test cases across years (MY2025 vs MY2026).

## Objectives
1.  **AI Config Automation**:
    - Update `src/ncqa_parser.py` (or create new `src/ai_config_generator.py`) to automatically generate `denominator_components` from PDF text.
    - Goal: Eliminating manual YAML editing for new measures.
2.  **Test Case Comparison Mode**:
    - Implement UI/Backend logic to compare two uploaded test case files (Baseline vs Target).
    - Goal: Allow users to run mockup generation ONLY for new/changed scenarios (Delta Run).3.  **Universal Validation**:
    - Verify the "Universal Format" works for a Custom State Measure (non-NCQA) to prove flexibility.

## Dependencies
- `src/engine.py` (Completed - Logic Ready)
- `config/SMD.yaml` (Completed - Reference Config)
- `src/ncqa_parser.py` (Existing, needs upgrade)

## Proposed User Stories
- "As a user, I want to upload a new NCQA PDF and have the system automatically figure out the '2 visit' requirement without me writing YAML."
- "As a tester, I want to upload my old 2025 test cases and my new 2026 test cases, and only run the 5 new ones to save time."
