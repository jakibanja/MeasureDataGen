# HEDIS Mockup Generator - Deployment & Setup Guide

Follow these steps to set up and run the HEDIS Mockup Generator on a new Windows system.

## 1. Prerequisites
Ensure the following are installed:
*   **Python 3.10+** (Add to PATH during installation)
*   **Git**
*   **Ollama** (Required for AI Scenario Extraction)
    *   Download from: [ollama.com](https://ollama.com/)
    *   Open terminal and run: `ollama pull qwen2:0.5b` (or your preferred small model)

## 2. Clone and Setup Environment
```powershell
# Clone the repository
git clone <repository-url>
cd MeasureDataGen

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Preparation
The generator requires the **Value Set Directory (VSD)** to assign clinical codes.
*   Place your `VSD_MY2026.xlsx` file in the `data/` folder.
*   The system defaults to `data/VSD_MY2026.xlsx` but you can specify a different path in the UI.

## 4. Running the Application

### Option A: Web Interface (Recommended)
This provides the best experience with the **Live Progress Dashboard**.
```powershell
python app.py
```
*   Open your browser to: `http://localhost:5000`

### Option B: Command Line (For Batch Processing)
```powershell
# For a single measure
python main.py PSA

# For multiple measures
python main.py PSA,WCC,COL
```

## 5. Key Features Overview
*   **Universal Format**: For new measures, use the `templates/Standard_TestCase_Template.xlsx`.
*   **NCQA Parser**: Upload an official NCQA PDF in the UI to auto-generate measure configurations.
*   **Smart Validator**: After generation, use the "Validate Results" button to verify compliance against test case expectations.
*   **AI Extractor**: If your test cases have messy scenario text, ensure Ollama is running to enable AI-powered parsing.

## 6. Troubleshooting
*   **Ollama Connection Error**: Ensure the Ollama service is running in your system tray.
*   **Missing Sheet Error**: Ensure your VSD file has the standard NCQA sheets (Sheet index 3 is used for the primary directory).
*   **Performance**: If generation is slow, check the "Disable AI Extractor" box in the UI for 10x faster (regex-only) processing.
