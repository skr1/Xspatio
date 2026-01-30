#!/usr/bin/env python3
import argparse
import pandas as pd

# Map "file2 column name" -> "file1 column name"
RENAME_2_TO_1 = {
    "ROI_Name": "ID",  # ROI key
    "Oct_2": "2_Oct",
    "PAK1_PAK2_PAK3_phospho_S141_S144_S154": "PAK1_2_3_p_S141_4_154",
    "Rb_phospho_T780": "Rb_p_T780",
    "SMAD1_SMAD5_SMAD9_phospho_S463_S465_S467": "SMAD1_5_9_S463_5_7",
    "VEGF_Receptor_2": "VEGF_R_2",
}

DROP_COLS_FILE2 = {"Core", "Nuclei_count"}  # you said you don't need these

def main():
    ap = argparse.ArgumentParser(description="Rename file2 cols to match file1, drop extra cols, then row-concat.")
    ap.add_argument("--file1", required=True)
    ap.add_argument("--file2", required=True)
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args()

    df1 = pd.read_csv(args.file1)
    df2 = pd.read_csv(args.file2)

    # Drop unwanted columns in file2 (if present)
    df2 = df2.drop(columns=[c for c in df2.columns if c in DROP_COLS_FILE2], errors="ignore")

    # Rename file2 columns to match file1 naming
    df2 = df2.rename(columns=RENAME_2_TO_1)

    # Sanity: both must have the same ID column name after rename
    if "ID" not in df1.columns:
        raise ValueError("File1 must have an 'ID' column.")
    if "ID" not in df2.columns:
        raise ValueError("File2 must have an 'ID' column after renaming (ROI_Name -> ID).")

    # Now check column-name sets
    c1 = set(df1.columns)
    c2 = set(df2.columns)

    only1 = sorted(c1 - c2)
    only2 = sorted(c2 - c1)

    if only1 or only2:
        print("❌ Still mismatched after renaming/dropping.")
        print("• Only in file1 (up to 30):", only1[:30])
        print("• Only in file2 (up to 30):", only2[:30])
        print("\nWriting union output instead (safe fallback).")

        # Fallback: union columns and concat
        all_cols = ["ID"] + sorted([c for c in (c1 | c2) if c != "ID"])
        out_union = args.out_csv.replace(".csv", "_UNION.csv")
        combined = pd.concat(
            [df1.reindex(columns=all_cols), df2.reindex(columns=all_cols)],
            ignore_index=True,
            sort=False
        )
        combined.to_csv(out_union, index=False)
        print("✅ Wrote union:", out_union)
        print("• rows:", combined.shape[0], "cols:", combined.shape[1])
        return

    # If sets match, reorder df2 to df1 column order and concat rows
    df2 = df2[df1.columns]
    combined = pd.concat([df1, df2], ignore_index=True)

    # Optional: also create a standardized ROI column (keeps ID too)
    # combined.insert(0, "ROI", combined["ID"].astype(str))

    combined.to_csv(args.out_csv, index=False)
    print("✅ Wrote:", args.out_csv)
    print("• rows:", combined.shape[0], "cols:", combined.shape[1])

if __name__ == "__main__":
    main()
