# 🏥 HEDIS Mockup Generator

AI-powered data generation system for NCQA-compliant HEDIS test data.

## 🚀 Quick Start

```bash
# 1. Start the web interface
python app.py

# 2. Open browser
http://localhost:5000

# 3. Upload test case, click Generate!
```

## ✨ Features

- 🤖 **Hybrid AI + Regex Parser** - Fast and intelligent
- 🔄 **Auto-Reformat** - Clean messy test cases with one click
- 📊 **Multi-Measure Support** - PSA, WCC, IMA (extensible)
- 🎨 **Beautiful UI** - Modern gradient design with progress tracking
- 📁 **VSD Integration** - Dynamic clinical code pulling
- ⚡ **Automation Tools** - Auto-generate configs for new measures

## 📖 Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete system documentation
- **[REMAINING_TASKS.md](REMAINING_TASKS.md)** - Roadmap and future enhancements

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Ollama (for AI features)

### Setup

```bash
# Install dependencies
pip install pandas openpyxl pyyaml ollama flask

# Install Ollama model
ollama pull tinyllama

# Run the app
python app.py
```

## 📂 Project Structure

```
MeasMockD/
├── app.py                    # Web server
├── main.py                   # CLI entry point
├── src/
│   ├── parser.py            # Test case parser
│   ├── engine.py            # Mockup generator
│   ├── vsd.py               # VSD manager
│   ├── ai_extractor.py      # AI fallback
│   ├── measure_automator.py # Measure automation
│   └── reformatter.py       # Test case cleaner
├── config/                   # Measure configurations
├── data/                     # Test cases and schemas
├── templates/                # Web UI
└── output/                   # Generated mockups
```

## 🎯 Usage

### Web Interface (Recommended)

1. Select measure (PSA/WCC/IMA)
2. Upload test case Excel file
3. ✅ Check "Auto-reformat" for messy data
4. Click "Generate Mockup"
5. Download result

### Command Line (v2.0)

```bash
# Generate PSA mockup (Default)
python main.py

# Generate multiple measures with no-AI speed optimization
python main.py PSA,WCC --no-ai --skip-quality-check

# Run with full NCQA Validation and specific model
python main.py PSA --validate-ncqa --model llama3
```

## 🔧 Configuration

### Add New Measure

```bash
# 1. Auto-generate schema
python src/measure_automator.py <MEASURE_NAME>

# 2. Edit config/<MEASURE_NAME>.yaml

# 3. Add test case to data/

# 4. Run generation
```

## ✍️ Tester Syntax (Shorthand)

Testers can now use standardized shortcuts in the **Scenario Description** field to gain surgical control over data generation WITHOUT changing Excel columns.

| Shortcut | Description | Example |
| :--- | :--- | :--- |
| `PL: [Line]`| **Product Line** | `PL: Medicare` |
| `AG: [Age]` | **Member Age** | `AG: 45` |
| `ED: [Date]` | **Event Date** (Global) | `ED: 6/1/MY` |
| `ED1: [Date]`| **Event Date** (Sequential) | `ED1: 1/1/MY` |
| `CE: [Name]` | **Compliance Event** | `CE: PSA Test` |
| `NE: [Name]` | **Numerator Exclusion**| `NE: Hospice` |

**Full Guide:** See [docs/TESTER_SYNTAX.md](docs/TESTER_SYNTAX.md)

## 📊 Performance & Optimization

- **Regex Mode (`--no-ai`):** High speed (~0.05s / case). Best for well-structured data or using Tester Syntax.
- **AI Mode:** Full reasoning for messy/paragraph scenarios. 
- **Recommendation:** Use **Tester Syntax** + **Regex Mode** for the best balance of speed and control.

## 🚧 Roadmap

### Priority 0 (Next)
- [ ] NCQA PDF Parser - Auto-extract rules from specs
- [ ] Expected Results Validator - Verify data quality

### Priority 1
- [ ] VSD Date Validation
- [ ] Data Quality Checks
- [ ] Real-time Progress Updates

See [REMAINING_TASKS.md](REMAINING_TASKS.md) for full roadmap.

## 🐛 Troubleshooting

### AI Extractor Failed
```bash
# Ensure Ollama is running
ollama serve

# Pull model
ollama pull tinyllama
```

### VSD File Not Found
Update `DEFAULT_VSD` path in `app.py` or upload via UI.

### Config Not Found
```bash
python src/measure_automator.py <MEASURE_NAME>
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📧 Support

For issues or questions, please open a GitHub issue.

---

**Version:** 1.0  
**Last Updated:** 2026-02-07  
**Status:** Production Ready (Core Features)
