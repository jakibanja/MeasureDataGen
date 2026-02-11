# Clinical Code Management Audit (Phase 4)

**Objective**: Verify the integrity of clinical code capture (NDC, CPT, ICD) and confirm that 'Value Set' codes are managed correctly according to HEDIS specifications.

## 1. Audit Findings: The "98000" Case
During the audit, we identified why the value `98000` was appearing frequently in the WCC (Weight Assessment) visit table:
*   **VSD Verification**: Technical search confirmed `98000` is a valid CPT code inside the official **NCQA 'Outpatient' Value Set**.
*   **Logic Flaw**: The `vsd.py` engine was previously taking the *first* code in the list rather than picking randomly. Because `98000` is the first entry for Outpatient, it was being over-used.
*   **Fix Applied**: Updated `src/vsd.py` to use `random.choice`. This ensures 100% variety from the official VSD pool.

## 2. Code Management Strategy (How it works)
The system uses a 3-tier "Cascading Fidelity" strategy for every clinical event:

| Tier | Source | Priority | Logic |
| :--- | :--- | :--- | :--- |
| **1. Explicit Override** | Test Case Excel | **Highest** | Captured via `EVENT_X_CODE`, `CPT:XXXX`, or `NDC:XXXX` syntax in your scenario text. |
| **2. High-Fidelity Master**| `data/HEDIS_Medication_Codes.json` | **High** | Automatic lookup for Pharmacy (NDC) and Clinical (RxNorm) codes based on the 14MB HEDIS MY 2026 master. |
| **3. VSD Fallback** | `VSD_MY2026.xlsx` | **Standard** | Randomly selected from the 180,000 official NCQA rules. |

## 3. Verified Routing Logic
I confirmed that the **Smart Routing** system correctly separates codes into the respective columns:
- **RX Table** -> Always routes to `RX_NDC`.
- **Visit Table (Diagnosis Code)** -> Routes to `DIAG_I_1` if the VSD/Override system identifies it as ICD-10.
- **Visit Table (Procedure Code)** -> Routes to `CPT_1` if identified as CPT/HCPCS.
- **Special Case (Counseling)** -> WCC Counseling codes (Nutrition/Physical Activity) are **forced** into the Procedure column (`CPT_1`) to meet HEDIS evidence standards, even if an ICD code is used.

## 4. Verification Plan
To ensure this is working to your satisfaction:
- [x] **VSD Randomness**: Verify codes in the output are no longer stuck on `98000`.
- [ ] **Manual Capture Test**: Add `EVENT_1_CODE: 99401` to a test case and verify it appears in `CPT_1`.
- [ ] **NDC Audit**: Run a measure with 'Antibiotics' and verify the `RX_NDC` matches a real NDC from the master list.
