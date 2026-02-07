# Test Case Document Requirements

## Overview
This document describes the format requirements for test case Excel files to work with the MeasMockD parser.

## File Structure

### Required Elements
1. **Excel Format** (.xlsx)
2. **Multiple Sheets** - One or more sheets containing test scenarios
3. **Header Row** - Must contain identifiable column headers

### Sheet Structure

#### Excluded Sheets (automatically skipped)
- `Revision_History`
- `DST`
- `Fileid_Summary`
- `Fileid_Detail`

#### Scenario Sheets
Each sheet should have:
- A header row containing column identifiers
- Rows with test case data
- **Multi-line support**: If a Member ID is empty, the parser treats the row as a continuation of the previous scenario.

### Column Requirements

The parser **dynamically detects** columns, but looks for these patterns:

#### ID Column (Required)
Must contain one of these in the header:
- `#TC`
- `mem_nbr`
- `member number`
- `testcase id`
- `#` (fallback)
- `s.n` (serial number)

#### Scenario/Description Column (Optional but recommended)
Header contains:
- `scenario`
- `test objective`

#### Objective Column (Optional)
Header contains:
- `objective`

#### Expected Result Column (Optional)
Header contains: `expected`

#### Date/Period Column (Optional)
Header contains: `period` or `enr_period`
*Specially scanned for enrollment ranges.*

## Data Format

### Test Case IDs
- **Valid**: `PSA_CE_02`, `WCC_BMI_01`
- **Continuation**: Empty field (inherits ID from previous row)
- **Invalid**: 
  - IDs > 60 chars
  - Rows containing "verify if", "member has" (likely headers)

### Enrollment Spans

The parser recognizes enrollment periods from scenario text using these patterns:

#### Keywords
- `enrollment`
- `enr`
- `member`
- `CE:` (Continuous Enrollment)

#### Date Formats
Supported formats:
- `1/1/MY` - January 1st of measurement year
- `12/31/MY-1` - December 31st of prior year
- `1/1/MY+1` - January 1st of next year
- `2026-01-01` - Absolute dates
- `1-1-2026` - Alternative separators

#### Range Format
```
<start_date> TO <end_date>
<start_date> - <end_date>
```

#### Example Enrollment Notation
```
CE:
1/1/MY-1 TO 10/1/MY
11/14/MY TO 12/31/MY
```

Or within scenario text:
```
Verify, if a member is enrolled in the measurement year. 44 days gap
Enrollment: 1/1/MY-1 TO 10/1/MY
Enrollment: 11/14/MY TO 12/31/MY
```

### Product Line Detection

Mentioned anywhere in ID, scenario, or expected result:
- `Commercial`
- `Medicaid`
- `Medicare`
- `Exchange`

Default: `Medicare`

### Product ID Detection

In enrollment span lines:
- `prod id: 11`
- `Product_ID=2`
- `product 92`
- `PL-1`

## Example Test Case Row

| # member number/TestCase ID | Scenario | Expected Result |
|-----|----------|-----------------|
| PSA_CE_02 | Verify, if a member is enrolled in the measurement year. 44 days\nCE:\n1/1/MY-1 TO 10/1/MY\n11/14/MY TO 12/31/MY | CE=1 |

## Testing Your Document

Use the validation script:
```bash
python test_new_tc.py your_testcase.xlsx MEASURE_NAME
```

This will:
1. Parse your document
2. Show sample scenarios
3. Report any issues
4. Display statistics

## Common Issues & Solutions

### Issue 1: No scenarios found
**Possible causes:**
- Wrong sheet names (all excluded)
- No valid header row
- IDs don't pass validation (too long, contain "verify", etc.)

**Solution:**
- Check sheet names
- Ensure header row has recognizable column names
- Ensure IDs are short and alphanumeric

### Issue 2: Enrollment spans not detected
**Possible causes:**
- Date format not recognized
- Missing keywords (CE:, enrollment, etc.)
- Dates on same line as visit/claim keywords

**Solution:**
- Use "CE:" or "enrollment" keyword before date ranges
- Put enrollment spans on separate lines from visit descriptions
- Use standard date formats (M/D/MY)

### Issue 3: Wrong product line
**Possible causes:**
- Product line not mentioned in text
- Conflicting product line keywords

**Solution:**
- Include product line name in scenario or ID
- Use standard names: Commercial, Medicaid, Medicare, Exchange

## Need Help?

If your document doesn't parse correctly:
1. Run `python test_new_tc.py your_file.xlsx`
2. Review the error messages
3. Check this document for format requirements
4. Adjust your test case file OR contact support to enhance the parser
