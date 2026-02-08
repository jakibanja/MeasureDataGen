# 📂 Project Folder Structure & Configuration

This guide explains the data organization and configuration of the HEDIS Mockup Generator.

## 🏗️ Folder Structure

The project uses a clean, separated structure for data and uploads:

### **1. `data/` Folder** 
*   **Purpose:** Permanent storage for reference files and test cases.
*   **Contents:**
    *   `PSA_MY2026_TestCase.xlsx` - Standard test case file.
    *   `VSD_MY2026.xlsx` - (Optional) Local copy of Value Set Directory.
*   **Git:** Tracked (except large VSD files).

### **2. `uploads/` Folder** 
*   **Purpose:** Temporary storage for files uploaded via the Web UI.
*   **Contents:** User-uploaded Excel/PDF files.
*   **Git:** **Ignored** (via `.gitignore`) to keep the repo clean.
*   **Note:** This replaces the old `data_uploads/` folder.

### **3. `output/` Folder**
*   **Purpose:** Destination for generated mockup files and reports.
*   **Contents:** `.xlsx` mockups, `.txt` compliance reports.
*   **Git:** **Ignored**.

### **4. `config/` Folder**
*   **Purpose:** YAML configuration files.
*   **Contents:**
    *   `{MEASURE}.yaml` - Measure logic (e.g., PSA.yaml).
    *   `ncqa/{MEASURE}_NCQA.yaml` - NCQA compliance rules.
    *   `schema_map.yaml` - Database schema definitions.

---

## 🔧 Configuration (No Hardcoded Paths!)

The system is designed to be portable. Instead of hardcoding paths like `C:\Users\sushi...`, we use **Environment Variables**.

### **Setting up VSD Path**
To use the Value Set Directory (VSD), you must configure its path in the `.env` file:

1.  Open (or create) the `.env` file in the project root.
2.  Add the `VSD_PATH` variable pointing to your VSD file:

```ini
# .env file
VSD_PATH=C:\Path\To\Your\HEDIS_VSD_File.xlsx
```

### **Why this helps:**
*   ✅ **Portable:** Works on any machine (Window/Mac/Linux).
*   ✅ **Secure:** Absolute paths aren't committed to Git.
*   ✅ **Flexible:** Each developer can save their VSD file wherever they want.

---

## 🧹 Maintenance

To clean up temporary files:
*   **Uploads:** Safe to delete files in `uploads/` at any time.
*   **Output:** Safe to delete files in `output/` at any time.
*   **PyCache:** Run `rm -r __pycache__` to clear Python cache.
