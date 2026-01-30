#!/usr/bin/env python3
import pandas as pd
import os
import glob
import shutil
import argparse
import re

def norm_key(x) -> str:
    """
    Normalize ROI/ID keys so they match filenames like ROI_1_tma1.h5/.pt
    Examples:
      " 1_tma1 "        -> "1_tma1"
      "ROI_1_tma1"      -> "1_tma1"
      "ROI-1-tma1"      -> "1_tma1"
    """
    s = str(x).strip()
    s = s.replace("-", "_")
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^ROI_", "", s, flags=re.IGNORECASE)
    return s

def main(args):
    # Load the DataFrame
    df = pd.read_csv(args.csv_file, delimiter=",", header=0)
    column_name = args.column_name

    # Check if expression column exists
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in the DataFrame.")

    # Use ROI if present; otherwise ID
    if "ROI" in df.columns:
        key_col = "ROI"
    elif "ID" in df.columns:
        key_col = "ID"
    else:
        raise ValueError("Neither 'ROI' nor 'ID' column found in the DataFrame.")
    print(f"Using key column: {key_col}")

    # Normalize keys into a single KEY column
    df["KEY"] = df[key_col].apply(norm_key)

    # Ensure expression is numeric before median
    df[column_name] = pd.to_numeric(df[column_name], errors="coerce")

    # Compute median & binarize
    median_value = df[column_name].median(skipna=True)
    df["binarized"] = (df[column_name] > median_value).astype(int)

    # Fast lookup: KEY -> binarized
    key_to_bin = dict(zip(df["KEY"], df["binarized"]))

    # Create subfolders if they don't exist
    os.makedirs(args.low_h5_folder, exist_ok=True)
    os.makedirs(args.low_pt_folder, exist_ok=True)
    os.makedirs(args.high_h5_folder, exist_ok=True)
    os.makedirs(args.high_pt_folder, exist_ok=True)

    # Get all files in the source folders
    all_h5_files = glob.glob(os.path.join(args.h5_source_folder, "*.h5"))
    all_pt_files = glob.glob(os.path.join(args.pt_source_folder, "*.pt"))
    all_files = all_h5_files + all_pt_files

    matched = 0
    unmatched = 0

    # Copy files to respective folders based on binarized values
    for file_path in all_files:
        filename = os.path.basename(file_path)
        stem = os.path.splitext(filename)[0]  # e.g., ROI_1_tma1
        file_key = norm_key(stem)             # -> 1_tma1

        binarized_value = key_to_bin.get(file_key, None)
        if binarized_value is None:
            unmatched += 1
            print(f"Key {file_key} not found in DataFrame (file: {filename})")
            continue

        matched += 1
        if binarized_value == 0:
            # low expression
            if filename.endswith(".h5"):
                destination = os.path.join(args.low_h5_folder, filename)
            else:
                destination = os.path.join(args.low_pt_folder, filename)
            shutil.copy(file_path, destination)
            print(f"Copied {filename} -> LOW")
        else:
            # high expression
            if filename.endswith(".h5"):
                destination = os.path.join(args.high_h5_folder, filename)
            else:
                destination = os.path.join(args.high_pt_folder, filename)
            shutil.copy(file_path, destination)
            print(f"Copied {filename} -> HIGH")

    print("\n✅ Done")
    print(f"• median({column_name}) = {median_value}")
    print(f"• matched files:   {matched}")
    print(f"• unmatched files: {unmatched}")
    print("Files copied successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Binarize expression column by median and split .h5/.pt files into low/high folders."
    )

    parser.add_argument("--csv_file", type=str, required=True,
                        help="Path to the CSV file containing expression data (must contain ROI or ID column).")
    parser.add_argument("--column_name", type=str, required=True,
                        help="Name of the column to binarize.")
    parser.add_argument("--h5_source_folder", type=str, required=True,
                        help="Source folder containing .h5 files.")
    parser.add_argument("--pt_source_folder", type=str, required=True,
                        help="Source folder containing .pt files.")
    parser.add_argument("--low_h5_folder", type=str, required=True,
                        help="Destination folder for low expression .h5 files.")
    parser.add_argument("--low_pt_folder", type=str, required=True,
                        help="Destination folder for low expression .pt files.")
    parser.add_argument("--high_h5_folder", type=str, required=True,
                        help="Destination folder for high expression .h5 files.")
    parser.add_argument("--high_pt_folder", type=str, required=True,
                        help="Destination folder for high expression .pt files.")

    args = parser.parse_args()
    main(args)
