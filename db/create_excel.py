
import pandas as pd
import os

# Create the db directory if it doesn't exist
if not os.path.exists('db'):
    os.makedirs('db')

# Create a Pandas Excel writer using openpyxl as the engine.
writer = pd.ExcelWriter('db/seed_data.xlsx', engine='openpyxl')

# Create dataframes for each sheet
field_contexts_df = pd.DataFrame({
    'name': ['Global Health', 'Climate Change'],
    'geographic_coverage': ['Worldwide', 'Global'],
    'category': ['Health', 'Environment']
})
field_contexts_df.to_excel(writer, sheet_name='field_contexts', index=False)

donor_df = pd.DataFrame({
    'name': ['Bill & Melinda Gates Foundation', 'USAID'],
    'account_id': ['BMGF', 'USAID'],
    'country': ['USA', 'USA'],
    'donor_group': ['Private Foundation', 'Government']
})
donor_df.to_excel(writer, sheet_name='donor', index=False)

outcome_df = pd.DataFrame({
    'name': ['Improved access to education', 'Reduced carbon emissions']
})
outcome_df.to_excel(writer, sheet_name='outcome', index=False)

reference_df = pd.DataFrame({
    "type": ["field_contexts", "donor", "outcome"],
    "name": ["Global Health", "USAID", "Reduced carbon emissions"],
    "url": ["http://example.com/health", "http://example.com/usaid", "http://example.com/climate"],
    "reference_type": ["Report", "Website", "Publication"],
    "summary": ["A report on global health initiatives.", "The official website of USAID.", "A publication on reducing carbon emissions."]
})
reference_df.to_excel(writer, sheet_name='reference', index=False)

# Close the Pandas Excel writer and output the Excel file.
writer.close()
