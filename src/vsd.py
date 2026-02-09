import pandas as pd
from datetime import datetime

class VSDManager:
    def __init__(self, vsd_path, measurement_year=2026):
        self.vsd_path = vsd_path
        self.measurement_year = measurement_year
        print(f"Loading VSD from {vsd_path}...")
        
        # Try to smart-load the VSD
        self.df = self._smart_load_vsd()
        
        # Normalize column names
        self._normalize_columns()
        
        # Parse date columns if they exist
        self._parse_dates()
        
        print(f"VSD loaded with {len(self.df)} code entries.")
        
        # Filter for valid codes
        self.valid_codes_count = self._count_valid_codes()
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

        # 2. Try looking for sheet by name
        target_sheets = ['Value Set Directory', 'Value Sets', 'Codes', 'Measures']
        for target in target_sheets:
            for sheet in sheet_names:
                if target.lower() in sheet.lower():
                    try:
                        df = pd.read_excel(self.vsd_path, sheet_name=sheet)
                        if self._has_required_columns(df):
                            print(f"Discovered VSD in sheet: '{sheet}'")
                            return df
                    except:
                        continue

        # 3. Last scan: Check ALL sheets for a "Value Set Name" or similar column
        print("Scanning all sheets for VSD structure...")
        for sheet in sheet_names:
            try:
                df = pd.read_excel(self.vsd_path, sheet_name=sheet)
                if self._has_required_columns(df):
                    print(f"Structure matched in sheet: '{sheet}'")
                    return df
            except:
                continue
        
        raise ValueError("Could not locate a valid Value Set directory sheet in the provided Excel file.")

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
    
    def _count_valid_codes(self):
        """Count codes valid for the measurement year."""
        my_start = datetime(self.measurement_year, 1, 1)
        my_end = datetime(self.measurement_year, 12, 31)
        
        # Check if date columns exist
        has_effective = 'Effective Date' in self.df.columns or 'EffectiveDate' in self.df.columns
        has_expiration = 'Expiration Date' in self.df.columns or 'ExpirationDate' in self.df.columns
        
        if not (has_effective or has_expiration):
            return len(self.df)  # No date filtering possible
        
        # Filter valid codes
        valid_mask = pd.Series([True] * len(self.df))
        
        if has_effective:
            eff_col = 'Effective Date' if 'Effective Date' in self.df.columns else 'EffectiveDate'
            valid_mask &= (self.df[eff_col].isna() | (self.df[eff_col] <= my_end))
        
        if has_expiration:
            exp_col = 'Expiration Date' if 'Expiration Date' in self.df.columns else 'ExpirationDate'
            valid_mask &= (self.df[exp_col].isna() | (self.df[exp_col] >= my_start))
        
        return valid_mask.sum()
    
    def is_code_valid(self, code, value_set_name=None):
        """
        Check if a code is valid for the measurement year.
        
        Args:
            code: The code to check
            value_set_name: Optional value set name to filter by
        
        Returns:
            dict with 'valid', 'reason', 'effective_date', 'expiration_date'
        """
        my_start = datetime(self.measurement_year, 1, 1)
        my_end = datetime(self.measurement_year, 12, 31)
        
        # Find code in VSD
        code_mask = self.df['Code'].astype(str) == str(code)
        if value_set_name:
            code_mask &= self.df['Value Set Name'].str.lower() == value_set_name.lower()
        
        matches = self.df[code_mask]
        
        if matches.empty:
            return {
                'valid': False,
                'reason': 'Code not found in VSD',
                'effective_date': None,
                'expiration_date': None
            }
        
        row = matches.iloc[0]
        
        # Check dates
        eff_col = 'Effective Date' if 'Effective Date' in self.df.columns else 'EffectiveDate'
        exp_col = 'Expiration Date' if 'Expiration Date' in self.df.columns else 'ExpirationDate'
        
        effective_date = row.get(eff_col) if eff_col in row else None
        expiration_date = row.get(exp_col) if exp_col in row else None
        
        # Validate
        if pd.notna(effective_date) and effective_date > my_end:
            return {
                'valid': False,
                'reason': f'Not yet effective (starts {effective_date.date()})',
                'effective_date': effective_date,
                'expiration_date': expiration_date
            }
        
        if pd.notna(expiration_date) and expiration_date < my_start:
            return {
                'valid': False,
                'reason': f'Expired (ended {expiration_date.date()})',
                'effective_date': effective_date,
                'expiration_date': expiration_date
            }
        
        return {
            'valid': True,
            'reason': 'Valid for measurement year',
            'effective_date': effective_date,
            'expiration_date': expiration_date
        }

    def get_codes(self, value_set_name, validate_dates=True):
        """
        Returns a list of codes for a given value set name.
        
        Args:
            value_set_name: Name of the value set
            validate_dates: If True, only return codes valid for measurement year
        """
        matches = self.df[self.df['Value Set Name'].str.lower() == value_set_name.lower()]
        
        if validate_dates:
            my_start = datetime(self.measurement_year, 1, 1)
            my_end = datetime(self.measurement_year, 12, 31)
            
            # Filter by dates if columns exist
            eff_col = 'Effective Date' if 'Effective Date' in self.df.columns else 'EffectiveDate'
            exp_col = 'Expiration Date' if 'Expiration Date' in self.df.columns else 'ExpirationDate'
            
            if eff_col in matches.columns:
                matches = matches[matches[eff_col].isna() | (matches[eff_col] <= my_end)]
            
            if exp_col in matches.columns:
                matches = matches[matches[exp_col].isna() | (matches[exp_col] >= my_start)]
        
        return matches['Code'].tolist()

    def get_random_code(self, value_set_name, validate_dates=True):
        """
        Returns a single code (first one found) for a value set.
        
        Args:
            value_set_name: Name of the value set
            validate_dates: If True, only return valid codes
        """
        codes = self.get_codes(value_set_name, validate_dates=validate_dates)
        if not codes:
            # Try without date validation as fallback
            if validate_dates:
                print(f"⚠️ No valid codes for '{value_set_name}' in MY {self.measurement_year}, using any available code")
                codes = self.get_codes(value_set_name, validate_dates=False)
        
        return str(codes[0]) if codes else None
    
    def find_value_sets(self, pattern, filter_empty=True):
        """
        Find value set names that match a pattern.
        
        Args:
            pattern: String or regex pattern to search for in Value Set Names
            filter_empty: If True, only return value sets that have valid codes
            
        Returns:
            list: Matching value set names
        """
        from re import search
        
        all_names = self.df['Value Set Name'].unique()
        matches = [name for name in all_names if search(pattern, name, flags=2)] # Case-insensitive
        
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
