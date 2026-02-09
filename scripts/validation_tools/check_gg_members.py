import pandas as pd

# Read visit data
vis = pd.read_excel('output/PSA_MY2026_Mockup_v15.xlsx', sheet_name='PSA_VISIT_IN')

print("Total visit records:", len(vis))
print("Unique members with visits:", vis['MEM_NBR'].nunique())

# Check for GG_PROD_SWTICH members
gg_members = vis[vis['MEM_NBR'].str.contains('GG_PROD', na=False)]
print(f"\nGG_PROD members found: {len(gg_members['MEM_NBR'].unique())}")
print("Members:")
for mem in sorted(gg_members['MEM_NBR'].unique()):
    count = len(gg_members[gg_members['MEM_NBR'] == mem])
    print(f"  {mem}: {count} visit(s)")
