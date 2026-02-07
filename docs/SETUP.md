# Project Setup Guide

This guide will help you set up the MeasureDataGen project on your local machine.

## Prerequisites

- Python 3.11 or higher
- Git
- pip (Python package manager)

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jakibanja/MeasureDataGen.git
cd MeasureDataGen
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import flask; print('Flask installed successfully')"
```

## Running the Application

### Web Application (Flask)

```bash
python app.py
```

Then open your browser to: `http://localhost:5000`

### Command Line Interface

```bash
python main.py --help
```

## Project Structure

```
MeasureDataGen/
├── src/              Core application modules
├── config/           Measure configurations (PSA, WCC, IMA)
├── data/             Input data files
├── templates/        HTML templates
├── docs/             Documentation
├── output/           Generated mockups (created at runtime)
├── app.py            Flask web application
├── main.py           CLI entry point
└── requirements.txt  Python dependencies
```

## Important Notes

### Virtual Environment

⚠️ **The `venv/` directory is NOT tracked in git** (and shouldn't be). Each developer must create their own virtual environment locally.

### Output Files

The `output/` directory is where generated mockups are saved. This directory is empty in the repository but will be populated when you run the application.

### Data Files

Sample data files are included in the `data/` directory. You can add your own test case files here.

## Troubleshooting

### Issue: "Module not found" errors

**Solution:** Make sure your virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Port 5000 already in use

**Solution:** Either stop the process using port 5000, or modify `app.py` to use a different port:
```python
app.run(debug=True, port=5001)
```

### Issue: Permission errors on Windows

**Solution:** Run PowerShell as Administrator or adjust execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Development Workflow

1. **Always activate the virtual environment** before working
2. **Install new dependencies** via pip and update `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```
3. **Never commit** the `venv/` directory
4. **Test your changes** before committing

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- See `docs/` folder for project-specific documentation

## Getting Help

If you encounter issues not covered here, please:
1. Check the documentation in the `docs/` folder
2. Review existing GitHub issues
3. Create a new issue with details about your problem
