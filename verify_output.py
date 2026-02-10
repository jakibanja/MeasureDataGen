import pandas as pd
import sys

file_path = 'output/PSA_MY2026_Mockup_v20.xlsx'
df_enr = pd.read_excel(file_path, sheet_name='PSA_ENROLLMENT_IN')

print("Sample Enrollment Records:")
print(df_enr[['MEM_NBR', 'BEN_MEDICAL', 'BEN_RX', 'BEN_MH_INP', 'BEN_CD_INP']].head(10))

df_monthly = pd.read_excel(file_path, sheet_name='PSA_MONTHLY_MBR_IN')
print("\nSample Monthly Membership Records:")
print(df_monthly.head(10))
