## Summary Table of Shortcuts

| Prefix | Description | Example |
| :--- | :--- | :--- |
| `PL:` | **Product Line** | `PL: Medicare` |
| `BE:` | **Benefit Profile** | `BE: Medical` |
| `ED:` | **Event Date** | `ED: 6/15/MY` |
| `ED1:`, `ED2:`| **Sequential Dates** | `ED1: 1/1/MY ED2: 3/1/MY` |
| `AD:` | **Anchor Date** | `AD: 12/31/MY` |
| `CE:` | **Compliance Event** | `CE: PSA Test` or `CE: 1/1/MY-12/31/MY` |
| `AG:` | **Age** | `AG: 65` |
| `NE:` | **Numerator Exclusion**| `NE: Hospice` |

---

## 1. Enrollment & Coverage (`CE:`, `PL:`)
*   **CE:** Use `CE:` prefix to define coverage periods.
    *   *Example:* `CE: 1/1/MY-1 - 12/31/MY`
*   **PL:** Use `PL:` to specify the product line explicitly.
    *   *Example:* `PL: Commercial`

## 2. Benefit Profiles (`BE:`)
Instead of checking 10 individual columns, use the `BE:` shortcut.
*   **Shortcut:** `BE: Medical`
    *   *Effect:* Automatically enables Mental Health (Inp/Int/Amb), Chemical Dependency (Inp/Int/Amb), and Hospital benefits.
*   **Shortcut:** `BE: Rx`
    *   *Effect:* Enables Pharmacy/Drug coverage.

## 3. Clinical & Exclusion Flags (`CE:`, `NE:`, `ED:`)
*   **Compliance:** Use `CE:` to force a clinical event.
    *   *Example:* `CE: PSA Test`
*   **Exclusion:** Use `NE:` to force an exclusion.
    *   *Example:* `NE: Hospice`
*   **Multiple Event Dates:**
    *   **Global:** `ED: 6/1/MY` (Sets date for ALL events in scenario)
    *   **Sequential:** `ED1: 1/1/MY ED2: 2/1/MY` (Maps to 1st and 2nd events)
    *   **Named Override:** `ED: PSA Test=6/1/MY` (Pins date to specific component)

## 4. Demographics (`AG:`, `AD:`)
*   **Age:** Use `AG:` to set member age.
    *   *Example:* `AG: 55`
*   **Anchor Date:** Use `AD:` to set the measurement year end or anchor point.
    *   *Example:* `AD: 12/31/MY`

---

## 5. Monthly Flags (Run-Date Specific)
If a flag (like Hospice) changes during the year, specify the `Rundate`.
*   **Syntax:** `[Flag]=[Y/N] ... Rundate=[Date]`
*   **Example:** `Hospice=Y with Rundate=12/31/MY-1`

**Note:** The system still supports checking individual columns (like `BEN_DENT`), but using this syntax in the Description field is faster and more reliable.
