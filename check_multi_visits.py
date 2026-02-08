import pandas as pd

# Read visit data
vis = pd.read_excel('output/PSA_MY2026_Mockup_v15.xlsx', sheet_name='PSA_VISIT_IN')

# Check the members you mentioned
members = [
    'PSA_CE_GG_PROD_SWTICH_02',
    'PSA_CE_GG_PROD_SWTICH_03', 
    'PSA_CE_GG_PROD_SWTICH_04',
    'PSA_CE_GG_PROD_SWTICH_05',
    'PSA_CE_GG_PROD_SWTICH_06'
]

print("=" * 80)
print("MULTI-VISIT SCENARIOS CHECK")
print("=" * 80)

for mem in members:
    mem_visits = vis[vis['MEM_NBR'] == mem]
    print(f"\n{mem}: {len(mem_visits)} visit(s)")
    
    if len(mem_visits) > 0:
        # Show key columns
        cols_to_show = ['MEM_NBR', 'SERV_DT', 'POS', 'CPT_1', 'HCPCS_1', 'DIAG_I_1']
        print(mem_visits[cols_to_show].to_string(index=False))
    else:
        print("  ❌ NO VISITS FOUND!")

# Also check visit count distribution
print("\n" + "=" * 80)
print("VISIT COUNT DISTRIBUTION")
print("=" * 80)
visit_counts = vis['MEM_NBR'].value_counts()
print(f"Members with 1 visit: {len(visit_counts[visit_counts == 1])}")
print(f"Members with 2 visits: {len(visit_counts[visit_counts == 2])}")
print(f"Members with 3+ visits: {len(visit_counts[visit_counts >= 3])}")

print("\nTop 10 members with most visits:")
print(visit_counts.head(10).to_string())
