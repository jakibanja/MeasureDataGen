import pandas as pd
from datetime import datetime
from collections import defaultdict

class DataQualityChecker:
    """
    Pre-flight data quality validation before Excel export.
    Checks for common data issues and provides detailed reports.
    """
    
    def __init__(self, data_store, schema):
        """
        Args:
            data_store: Dict of {table_name: [row_dicts]}
            schema: Dict of {table_name: [column_names]}
        """
        self.data_store = data_store
        self.schema = schema
        self.issues = []
        self.warnings = []
        self.stats = defaultdict(int)
    
    def check_all(self):
        """Run all quality checks."""
        print("\n🔍 Running Data Quality Checks...")
        
        self.check_duplicate_members()
        self.check_date_logic()
        self.check_required_fields()
        self.check_orphaned_records()
        self.check_data_types()
        self.check_schema_compliance()
        
        return self._generate_report()
    
    def check_duplicate_members(self):
        """Check for duplicate member IDs across tables."""
        print("  Checking for duplicate member IDs...")
        
        for table_name, rows in self.data_store.items():
            # Duplicate check only makes sense for the master Member table
            if not rows or 'MEM_NBR' not in rows[0] or 'MEMBER_IN' not in table_name:
                continue
            
            df = pd.DataFrame(rows)
            duplicates = df[df.duplicated('MEM_NBR', keep=False)]
            
            if not duplicates.empty:
                dup_ids = duplicates['MEM_NBR'].unique().tolist()
                self.issues.append({
                    'severity': 'ERROR',
                    'table': table_name,
                    'check': 'Duplicate Members',
                    'message': f"Found {len(dup_ids)} duplicate member IDs",
                    'details': dup_ids[:5]  # Show first 5
                })
                self.stats['duplicate_members'] += len(dup_ids)
    
    def check_date_logic(self):
        """Validate date logic (e.g., end > start)."""
        print("  Checking date logic...")
        
        for table_name, rows in self.data_store.items():
            if not rows:
                continue
            
            df = pd.DataFrame(rows)
            
            # Check enrollment dates
            if 'ENR_START' in df.columns and 'ENR_END' in df.columns:
                df['ENR_START'] = pd.to_datetime(df['ENR_START'], errors='coerce')
                df['ENR_END'] = pd.to_datetime(df['ENR_END'], errors='coerce')
                
                invalid = df[df['ENR_START'] > df['ENR_END']]
                
                if not invalid.empty:
                    self.issues.append({
                        'severity': 'ERROR',
                        'table': table_name,
                        'check': 'Date Logic',
                        'message': f"{len(invalid)} records have ENR_START > ENR_END",
                        'details': invalid['MEM_NBR'].tolist()[:5] if 'MEM_NBR' in invalid.columns else []
                    })
                    self.stats['invalid_dates'] += len(invalid)
            
            # Check service dates
            svc_start_col = next((c for c in df.columns if c in ['SERV_DT', 'SVC_START', 'LAB_SCR_DT']), None)
            svc_end_col = next((c for c in df.columns if c in ['DISCH_DT', 'SVC_END']), None)
            
            if svc_start_col and svc_end_col:
                df[svc_start_col] = pd.to_datetime(df[svc_start_col], errors='coerce')
                df[svc_end_col] = pd.to_datetime(df[svc_end_col], errors='coerce')
                
                invalid = df[df[svc_start_col] > df[svc_end_col]].dropna(subset=[svc_start_col, svc_end_col])
                
                if not invalid.empty:
                    self.issues.append({
                        'severity': 'ERROR',
                        'table': table_name,
                        'check': 'Date Logic',
                        'message': f"{len(invalid)} records have {svc_start_col} > {svc_end_col}",
                        'details': invalid['MEM_NBR'].tolist()[:5] if 'MEM_NBR' in invalid.columns else []
                    })
                    self.stats['invalid_dates'] += len(invalid)
    
    def check_required_fields(self):
        """Check that required fields are populated."""
        print("  Checking required fields...")
        
        required_fields = {
            'MEMBER_IN': ['MEM_NBR', 'MEM_DOB', 'MEM_GENDER'],
            'ENROLLMENT_IN': ['MEM_NBR', 'ENR_START', 'ENR_END'],
            'VISIT_IN': ['MEM_NBR', 'SERV_DT'],
            'LAB_IN': ['MEM_NBR', 'LAB_SCR_DT']
        }
        
        for table_name, rows in self.data_store.items():
            if not rows:
                continue
            
            df = pd.DataFrame(rows)
            
            # Determine required fields for this table
            table_type = None
            for key in required_fields.keys():
                if key in table_name:
                    table_type = key
                    break
            
            if not table_type:
                continue
            
            for field in required_fields[table_type]:
                if field not in df.columns:
                    self.issues.append({
                        'severity': 'ERROR',
                        'table': table_name,
                        'check': 'Required Fields',
                        'message': f"Missing required column: {field}",
                        'details': []
                    })
                    continue
                
                null_count = df[field].isna().sum()
                if null_count > 0:
                    self.warnings.append({
                        'severity': 'WARNING',
                        'table': table_name,
                        'check': 'Required Fields',
                        'message': f"{null_count} null values in required field: {field}",
                        'details': []
                    })
                    self.stats['null_required_fields'] += null_count
    
    def check_orphaned_records(self):
        """Check for records without corresponding member records."""
        print("  Checking for orphaned records...")
        
        # Get all member IDs from MEMBER tables
        member_ids = set()
        for table_name, rows in self.data_store.items():
            if 'MEMBER_IN' in table_name and rows:
                df = pd.DataFrame(rows)
                if 'MEM_NBR' in df.columns:
                    member_ids.update(df['MEM_NBR'].unique())
        
        if not member_ids:
            self.warnings.append({
                'severity': 'WARNING',
                'table': 'ALL',
                'check': 'Orphaned Records',
                'message': "No member records found - cannot check for orphans",
                'details': []
            })
            return
        
        # Check other tables
        for table_name, rows in self.data_store.items():
            if 'MEMBER_IN' in table_name or not rows:
                continue
            
            df = pd.DataFrame(rows)
            if 'MEM_NBR' not in df.columns:
                continue
            
            orphans = df[~df['MEM_NBR'].isin(member_ids)]
            
            if not orphans.empty:
                self.issues.append({
                    'severity': 'ERROR',
                    'table': table_name,
                    'check': 'Orphaned Records',
                    'message': f"{len(orphans)} records without corresponding member",
                    'details': orphans['MEM_NBR'].unique().tolist()[:5]
                })
                self.stats['orphaned_records'] += len(orphans)
    
    def check_data_types(self):
        """Check for data type issues."""
        print("  Checking data types...")
        
        for table_name, rows in self.data_store.items():
            if not rows:
                continue
            
            df = pd.DataFrame(rows)
            
            # Check numeric fields
            numeric_patterns = ['_AMT', '_QTY', '_CNT', 'PRODUCT_ID']
            for col in df.columns:
                if any(pattern in col for pattern in numeric_patterns):
                    try:
                        pd.to_numeric(df[col], errors='raise')
                    except:
                        non_numeric = df[~df[col].apply(lambda x: pd.isna(x) or str(x).replace('.', '').replace('-', '').isdigit())]
                        if not non_numeric.empty:
                            self.warnings.append({
                                'severity': 'WARNING',
                                'table': table_name,
                                'check': 'Data Types',
                                'message': f"{len(non_numeric)} non-numeric values in {col}",
                                'details': non_numeric[col].unique().tolist()[:5]
                            })
    
    def check_schema_compliance(self):
        """Check that all tables match their schema."""
        print("  Checking schema compliance...")
        
        for table_name, rows in self.data_store.items():
            if table_name not in self.schema:
                self.warnings.append({
                    'severity': 'WARNING',
                    'table': table_name,
                    'check': 'Schema Compliance',
                    'message': f"Table not in schema definition",
                    'details': []
                })
                continue
            
            if not rows:
                continue
            
            df = pd.DataFrame(rows)
            expected_cols = set(self.schema[table_name])
            actual_cols = set(df.columns)
            
            missing = expected_cols - actual_cols
            extra = actual_cols - expected_cols
            
            if missing:
                self.warnings.append({
                    'severity': 'WARNING',
                    'table': table_name,
                    'check': 'Schema Compliance',
                    'message': f"{len(missing)} missing columns (will be added as null)",
                    'details': list(missing)[:5]
                })
            
            if extra:
                self.warnings.append({
                    'severity': 'WARNING',
                    'table': table_name,
                    'check': 'Schema Compliance',
                    'message': f"{len(extra)} extra columns (will be removed)",
                    'details': list(extra)[:5]
                })
    
    def _generate_report(self):
        """Generate quality check report."""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        
        print(f"\n📊 Data Quality Report:")
        print(f"   Errors: {total_issues}")
        print(f"   Warnings: {total_warnings}")
        
        if total_issues > 0:
            print(f"\n❌ Critical Issues Found:")
            for issue in self.issues[:5]:  # Show first 5
                print(f"   - [{issue['table']}] {issue['message']}")
        
        if total_warnings > 0:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"   - [{warning['table']}] {warning['message']}")
        
        if total_issues == 0 and total_warnings == 0:
            print(f"   ✅ All checks passed!")
        
        return {
            'passed': total_issues == 0,
            'total_issues': total_issues,
            'total_warnings': total_warnings,
            'issues': self.issues,
            'warnings': self.warnings,
            'stats': dict(self.stats)
        }
    
    def export_report(self, output_path):
        """Export quality report to Excel."""
        issues_df = pd.DataFrame(self.issues) if self.issues else pd.DataFrame()
        warnings_df = pd.DataFrame(self.warnings) if self.warnings else pd.DataFrame()
        stats_df = pd.DataFrame([self.stats])
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            if not issues_df.empty:
                issues_df.to_excel(writer, sheet_name='Issues', index=False)
            if not warnings_df.empty:
                warnings_df.to_excel(writer, sheet_name='Warnings', index=False)
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        print(f"\n📄 Quality report saved: {output_path}")
