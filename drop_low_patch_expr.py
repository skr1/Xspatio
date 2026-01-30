#!/usr/bin/env python3
import argparse
import re
import sys
import pandas as pd

def norm_roi(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    if not s:
        return None
    s = s.replace("-", "_")
    s = re.sub(r"\s+", "", s)
    s = s.upper()
    # if it's just digits, prefix ROI_
    if re.fullmatch(r"\d+", s):
        s = f"ROI_{s}"
    # if it's like ROI100, make ROI_100
    m = re.fullmatch(r"ROI_?(\d+)", s)
    if m:
        s = f"ROI_{m.group(1)}"
    return s

def guess_roi_col(df):
    candidates = ["ROI", "roi", "Roi", "roi_id", "ROI_ID", "case_id", "Case_ID", "case"]
    for c in candidates:
        if c in df.columns:
            return c
    # fallback: first column containing 'roi'
    for c in df.columns:
        if "roi" in c.lower():
            return c
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expr_csv", required=True)
    ap.add_argument("--patch_counts_csv", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--drop_le", type=int, required=True, help="Drop ROIs with patch_count <= this value")
    ap.add_argument("--roi_col_expr", default=None, help="ROI column name in expression CSV (optional)")
    ap.add_argument("--roi_col_counts", default=None, help="ROI column name in patch counts CSV (optional)")
    args = ap.parse_args()

    expr = pd.read_csv(args.expr_csv, dtype=str, keep_default_na=False)
    counts = pd.read_csv(args.patch_counts_csv)

    roi_col_expr = args.roi_col_expr or guess_roi_col(expr)
    roi_col_counts = args.roi_col_counts or guess_roi_col(counts)

    if roi_col_expr is None:
        print("ERROR: Could not find ROI column in expression CSV. Use --roi_col_expr.", file=sys.stderr)
        print("Expression columns:", list(expr.columns), file=sys.stderr)
        sys.exit(2)
    if roi_col_counts is None:
        print("ERROR: Could not find ROI column in patch counts CSV. Use --roi_col_counts.", file=sys.stderr)
        print("Patch-count columns:", list(counts.columns), file=sys.stderr)
        sys.exit(2)

    # Normalize ROI ids
    expr["_ROI_NORM"] = expr[roi_col_expr].map(norm_roi)
    counts["_ROI_NORM"] = counts[roi_col_counts].map(norm_roi)

    # patch_count column
    if "patch_count" not in counts.columns:
        # try common variants
        for c in ["patches", "count", "n_patches", "num_patches"]:
            if c in counts.columns:
                counts = counts.rename(columns={c: "patch_count"})
                break
    if "patch_count" not in counts.columns:
        print("ERROR: patch_counts_csv must have a patch_count column (or a recognizable variant).", file=sys.stderr)
        print("Patch-count columns:", list(counts.columns), file=sys.stderr)
        sys.exit(2)

    counts["patch_count"] = pd.to_numeric(counts["patch_count"], errors="coerce")

    drop_set = set(
        counts.loc[counts["patch_count"] <= args.drop_le, "_ROI_NORM"]
        .dropna()
        .astype(str)
        .tolist()
    )

    in_rows = len(expr)
    dropped_mask = expr["_ROI_NORM"].isin(drop_set)
    dropped = expr.loc[dropped_mask, [roi_col_expr, "_ROI_NORM"]].copy()

    out = expr.loc[~dropped_mask].drop(columns=["_ROI_NORM"])
    out.to_csv(args.out_csv, index=False)

    dropped_list_path = f"dropped_rois_patch_le{args.drop_le}.csv"
    dropped.to_csv(dropped_list_path, index=False)

    print("✅ Done")
    print("• Expression rows in: ", in_rows)
    print(f"• Dropped (<= {args.drop_le} patches):", int(dropped_mask.sum()))
    print("• Expression rows out:", len(out))
    print("• Wrote filtered expr:", args.out_csv)
    print("• Wrote dropped list:", dropped_list_path)
    print("• ROI column used (expr):", roi_col_expr)
    print("• ROI column used (counts):", roi_col_counts)

if __name__ == "__main__":
    main()
