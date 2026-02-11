import pandas as pd
from datetime import datetime
import re

class VSDManager:
    def __init__(self, vsd_path, measurement_year=2026):
        self.vsd_path = vsd_path
        self.measurement_year = measurement_year
        self.vsd_map = {}
        self.unique_names = []
        
        print(f"Loading VSD from {vsd_path}...")
        
        # Try to smart-load the VSD
        self.df = self._smart_load_vsd()
        
        # Normalize column names
        self._normalize_columns()
        
        # Parse date columns if they exist
        self._parse_dates()
        
        print(f"VSD loaded with {len(self.df)} code entries.")
        
        # ⚡ Optimization: Pre-compute lookups
        self._build_fast_lookup()
        
        # Filter for valid codes (count based on our optimized map)
        self.valid_codes_count = sum(len(codes) for codes in self.vsd_map.values())
        print(f"Valid codes for MY {measurement_year}: {self.valid_codes_count}")

    def _smart_load_vsd(self):
        """Attempts to find the correct sheet and columns."""
        xl = pd.ExcelFile(self.vsd_path)
        sheet_names = xl.sheet_names
        
        # 1. Try traditional integer index (Sheet 4 / Index 3)
        if len(sheet_names) > 3:
            try:
                df = pd.read_excel(self.vsd_path, sheet_name=3)
                if self._has_required_columns(df):
                    return df
            except:
                pass

        # 2. Try looking for sheet by name (like 'Value Sets to Codes')
        target_sheets = ['Value Set to Codes', 'Value Set Directory', 'Value Sets', 'Codes']
        for target in target_sheets:
            for sheet in sheet_names:
                if target.lower() in sheet.lower():
                    # print(f"Checking sheet: '{sheet}'...")
                    found_df = self._scan_sheet_for_headers(sheet)
                    if found_df is not None:
                        print(f"[OK] Discovered VSD in sheet: '{sheet}'")
                        return found_df

        # 3. Last scan: Check ALL sheets
        print("Scanning all sheets for VSD structure...")
        for sheet in sheet_names:
            found_df = self._scan_sheet_for_headers(sheet)
            if found_df is not None:
                print(f"[OK] Structure matched in sheet: '{sheet}'")
                return found_df
        
        raise ValueError(f"Could not locate a valid Value Set sheet in {self.vsd_path}. Checked sheets: {sheet_names}")

    def _scan_sheet_for_headers(self, sheet_name):
        """Scans the first 20 rows of a sheet to find the header row."""
        try:
            # Read first 20 rows without header
            preview = pd.read_excel(self.vsd_path, sheet_name=sheet_name, nrows=20, header=None)
            
            # Iterate through rows to find one with "Value Set Name" or similar
            for idx, row in preview.iterrows():
                row_str = row.astype(str).str.lower().tolist()
                
                # Check if this row looks like a header
                has_name = any('value set name' in s or 'value set' in s for s in row_str)
                has_code = any('code' in s for s in row_str)
                
                if has_name and has_code:
                    # Found the header at row `idx`
                    # Reload the sheet with this header row
                    print(f"   Found headers at row {idx+1}")
                    return pd.read_excel(self.vsd_path, sheet_name=sheet_name, header=idx)
            
            return None
        except Exception as e:
            return None
        
        return None

    def _has_required_columns(self, df):
        """Check if dataframe has something looking like a value set name and code."""
        cols = [c.lower() for c in df.columns]
        has_name = any('value set' in c or 'valueset' in c for c in cols)
        has_code = any('code' in c for c in cols)
        return has_name and has_code

    def _normalize_columns(self):
        """Normalize key columns to standard names."""
        col_map = {}
        for col in self.df.columns:
            l_col = col.lower().strip()
            if 'value set name' in l_col:
                col_map[col] = 'Value Set Name'
            elif 'value set' in l_col and 'name' not in l_col: # e.g. "Value Set"
                col_map[col] = 'Value Set Name'
            elif l_col == 'code':
                col_map[col] = 'Code'
            elif 'effective' in l_col:
                col_map[col] = 'Effective Date'
            elif 'expiration' in l_col:
                col_map[col] = 'Expiration Date'
        
        if col_map:
            self.df.rename(columns=col_map, inplace=True)

        # ⚡ CRITICAL FIX: Handle duplicate columns (e.g. if 'Value Set Name' appears twice)
        # This prevents "DataFrame object has no attribute 'str'" errors
        self.df = self.df.loc[:, ~self.df.columns.duplicated()]
            
        if 'Value Set Name' not in self.df.columns:
            raise KeyError("Could not normalize column headers. Expected 'Value Set Name' or similar found: " + str(self.df.columns))
            
        self.df['Value Set Name'] = self.df['Value Set Name'].astype(str).str.strip()
    
    def _parse_dates(self):
        """Parse effective and expiration date columns."""
        date_columns = ['Effective Date', 'Expiration Date', 'EffectiveDate', 'ExpirationDate']
        
        for col in date_columns:
            if col in self.df.columns:
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                except:
                    pass

    def _build_fast_lookup(self):
        """Build dictionary-based lookups for O(1) performance."""
        print("Building fast VSD lookup cache...")
        # 1. Filter valid codes for MY once
        my_start = datetime(self.measurement_year, 1, 1)
        my_end = datetime(self.measurement_year, 12, 31)
        
        # Make a copy to avoid SettingWithCopy and ensure we don't mutate original if needed elsewhere
        valid_df = self.df.copy()
        
        eff_col = 'Effective Date' if 'Effective Date' in self.df.columns else 'EffectiveDate'
        exp_col = 'Expiration Date' if 'Expiration Date' in self.df.columns else 'ExpirationDate'
        
        if eff_col in valid_df.columns:
            valid_df = valid_df[valid_df[eff_col].isna() | (valid_df[eff_col] <= my_end)]
        if exp_col in valid_df.columns:
            valid_df = valid_df[valid_df[exp_col].isna() | (valid_df[exp_col] >= my_start)]
            
        # 2. Group by Value Set Name (lowercase for case-insensitive lookup)
        # Store list of codes as strings to ensure consistency
        # Optimization: use aggregation for speed
        grouped = valid_df.groupby(valid_df['Value Set Name'].str.lower())
        self.vsd_map = grouped['Code'].apply(list).to_dict()
        
        # 3. Cache Code -> System for smart routing
        # Ensure codes are strings
        valid_df['Code'] = valid_df['Code'].astype(str).str.strip()
        # Drop duplicates to keep map size reasonable (assuming System is consistent for a Code)
        unique_codes = valid_df.drop_duplicates(subset=['Code'])
        # Handle case where Code System column might be missing or named differently
        sys_col = next((c for c in valid_df.columns if 'system' in c.lower() and 'oid' not in c.lower() and 'version' not in c.lower()), 'Code System')
        
        if sys_col in valid_df.columns:
            self.code_to_system = unique_codes.set_index('Code')[sys_col].to_dict()
        else:
            print(f"[WARN] 'Code System' column not found in VSD keys: {valid_df.columns.tolist()}")
            self.code_to_system = {}
        
        # 4. Cache unique names for regex search
        self.unique_names = list(self.vsd_map.keys())
        print(f"   [OK] Cached {len(self.unique_names)} value sets, {len(valid_df)} valid codes, {len(self.code_to_system)} system lookups")

    def get_code_system(self, code):
        """
        Get the Code System (e.g. CPT, ICD-10-CM) for a given code.
        Returns 'Unknown' if not found.
        """
        return self.code_to_system.get(str(code).strip(), 'Unknown')

    def get_codes(self, value_set_name, validate_dates=True):
        """
        Returns a list of codes for a given value set name.
        Uses fast O(1) lookup with fuzzy fallback.
        """
        key = value_set_name.lower().strip()
        
        # 1. Try Exact Match
        codes = self.vsd_map.get(key)
        
        # 2. ⚡ Fuzzy Fallback (Case-insensitive search in unique names)
        if codes is None:
            # Look for a name that contains the requested name, or vice versa
            matches = [n for n in self.unique_names if key in n or n in key]
            if matches:
                # Prioritize shortest match (usually the most generic one)
                matches.sort(key=len)
                key = matches[0]
                codes = self.vsd_map.get(key)
                # print(f"    ✨ Fuzzy-matched '{value_set_name}' to '{key}'")
        
        # 3. Final extraction
        if codes is not None:
            if validate_dates: return codes
            # Slow fallback for non-date-validated (rare)
            matches_df = self.df[self.df['Value Set Name'].str.lower() == key]
            return matches_df['Code'].tolist()
            
        return []

    def get_random_code(self, value_set_name, validate_dates=True):
        """
        Returns a single random code for a value set.
        """
        import random
        codes = self.get_codes(value_set_name, validate_dates=validate_dates)
        if not codes:
            # Try without date validation as fallback
            if validate_dates:
                codes = self.get_codes(value_set_name, validate_dates=False)
        
        return str(random.choice(codes)) if codes else None
    
    def find_value_sets(self, pattern, filter_empty=True):
        """
        Find value set names that match a pattern efficiently.
        """
        # Search in cached unique names instead of dataframe
        # This is much faster
        matches = [name for name in self.unique_names if re.search(pattern, name, flags=re.IGNORECASE)]
        
        if filter_empty:
            matches = [name for name in matches if self.get_codes(name)]
            
        return matches

    def get_random_code_from_pattern(self, pattern, validate_dates=True):
        """
        Search for a value set matching a pattern and return a random code from it.
        Useful for generic needs like 'Outpatient' or 'Diagnosis'.
        """
        matches = self.find_value_sets(pattern)
        if not matches:
            return None
            
        # Prioritize shorter names as they are often more 'generic'
        matches.sort(key=len)
        return self.get_random_code(matches[0], validate_dates=validate_dates)
