#!/usr/bin/env python3
import argparse
import sys
import pandas as pd

def read_list_file(path: str) -> list[str]:
    vals = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                vals.append(s)
    return vals

def parse_threshold_pairs(pairs: list[str]) -> dict[str, float]:
    """
    Parse ["FOXC1=9", "CD11c=2500"] -> {"FOXC1": 9.0, "CD11c": 2500.0}
    """
    out = {}
    for p in pairs:
        if "=" not in p:
            raise ValueError(f"Bad threshold '{p}'. Use COL=NUMBER (e.g., FOXC1=9).")
        k, v = p.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            raise ValueError(f"Bad threshold '{p}': empty column name.")
        try:
            out[k] = float(v)
        except ValueError:
            raise ValueError(f"Bad threshold '{p}': '{v}' is not a number.")
    return out

def load_thresholds_file(path: str) -> dict[str, float]:
    """
    Accepts a CSV/TSV with columns: column,threshold
    Example:
      column,threshold
      FOXC1,9
      CD11c,2500
    """
    df = pd.read_csv(path)
    if not {"column", "threshold"}.issubset(df.columns):
        raise ValueError("Thresholds file must contain columns: column, threshold")
    out = {}
    for _, r in df.iterrows():
        out[str(r["column"]).strip()] = float(r["threshold"])
    return out

def main():
    ap = argparse.ArgumentParser(
        description="Binarize expression columns using median or per-column custom thresholds."
    )
    ap.add_argument("--in_csv", required=True, help="Input transposed expression CSV.")
    ap.add_argument("--out_csv", required=True, help="Output binarized CSV.")
    ap.add_argument("--keep_first_n", type=int, default=3,
                    help="Keep first N columns as metadata (not binarized). Default=3. Set 0 if none.")

    # Column selection (optional)
    ap.add_argument("--columns", nargs="*", default=None,
                    help="Optional: column names to binarize/output (space-separated). "
                         "Output will contain ONLY metadata + these columns.")
    ap.add_argument("--columns_file", default=None,
                    help="Optional: text file with column names (one per line) to binarize/output. "
                         "Output will contain ONLY metadata + these columns.")

    # Threshold behavior
    ap.add_argument("--ge", action="store_true",
                    help="Use >= threshold as 1 (default is > threshold).")
    ap.add_argument("--na_value", default="",
                    help="Value to write for missing/non-numeric entries. Default empty. Use 0 if desired.")

    # Custom thresholds
    ap.add_argument("--threshold", nargs="*", default=[],
                    help="Override thresholds for specific columns using COL=NUMBER "
                         "(e.g., --threshold FOXC1=9 CD11c=2500).")
    ap.add_argument("--thresholds_file", default=None,
                    help="CSV with columns: column,threshold to override specific columns.")

    args = ap.parse_args()

    if args.columns and args.columns_file:
        print("ERROR: Use only one of --columns or --columns_file.", file=sys.stderr)
        sys.exit(2)

    # Load overrides
    overrides = {}
    try:
        if args.threshold:
            overrides.update(parse_threshold_pairs(args.threshold))
        if args.thresholds_file:
            overrides.update(load_thresholds_file(args.thresholds_file))
    except Exception as e:
        print(f"ERROR parsing thresholds: {e}", file=sys.stderr)
        sys.exit(2)

    df = pd.read_csv(args.in_csv, dtype=str, keep_default_na=False)

    # metadata + expression split
    meta = df.iloc[:, :args.keep_first_n] if args.keep_first_n > 0 else pd.DataFrame(index=df.index)
    expr_full = df.iloc[:, args.keep_first_n:] if args.keep_first_n > 0 else df.copy()

    # Determine columns to binarize/output
    selected = None
    if args.columns_file:
        selected = read_list_file(args.columns_file)
    elif args.columns is not None and len(args.columns) > 0:
        selected = args.columns

    if selected is None:
        use_cols = list(expr_full.columns)  # Mode: all expression cols
    else:
        missing = [c for c in selected if c not in expr_full.columns]
        use_cols = [c for c in selected if c in expr_full.columns]
        if len(use_cols) == 0:
            print("ERROR: None of the requested columns were found among expression columns.", file=sys.stderr)
            if missing:
                print("Missing (examples):", ", ".join(missing[:20]), file=sys.stderr)
            sys.exit(2)
        if missing:
            print(f"⚠️ Warning: {len(missing)} requested columns not found (showing up to 20): "
                  + ", ".join(missing[:20]))

    expr = expr_full[use_cols].apply(pd.to_numeric, errors="coerce")

    # Compute medians for columns not overridden
    medians = expr.median(axis=0, skipna=True)

    # Build final thresholds per column
    thresholds = {}
    for c in expr.columns:
        thresholds[c] = overrides.get(c, float(medians[c]))

    # Binarize using per-column thresholds
    if args.ge:
        bin_df = pd.DataFrame({c: (expr[c] >= thresholds[c]).astype("Int64") for c in expr.columns})
        rule = "1 if >= threshold else 0"
    else:
        bin_df = pd.DataFrame({c: (expr[c] > thresholds[c]).astype("Int64") for c in expr.columns})
        rule = "1 if > threshold else 0"

    # NA handling
    if args.na_value != "":
        try:
            na_fill = int(args.na_value)
        except ValueError:
            na_fill = args.na_value
        bin_df = bin_df.fillna(na_fill)

    out = pd.concat([meta, bin_df], axis=1)
    out.to_csv(args.out_csv, index=False)

    # Small report
    print("✅ Wrote:", args.out_csv)
    print("• rows:", out.shape[0], "cols:", out.shape[1])
    print("• binarized cols:", bin_df.shape[1])
    print("• rule:", rule)
    if overrides:
        shown = ", ".join([f"{k}={v}" for k, v in list(overrides.items())[:10]])
        print(f"• overrides: {len(overrides)} (showing up to 10): {shown}")

if __name__ == "__main__":
    main()
