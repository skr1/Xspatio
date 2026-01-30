import pandas as pd

# INPUT
in_csv = "tma2_rna_expression.csv"   
out_csv = "tma2_rna_expression_transposed.csv"

# Read CSV
# Assumes first column = gene names
df = pd.read_csv(in_csv, index_col=0)

# Transpose
df_t = df.T

# Optional: make ROI a column instead of index
df_t.insert(0, "ROI", df_t.index)

# Save
df_t.to_csv(out_csv, index=False)

print(f"Saved transposed file to {out_csv}")
