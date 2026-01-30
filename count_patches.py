
import os, glob
import h5py
import numpy as np

# CHANGE THIS to patches h5 directory:
H5_DIR = "/home/ubuntu/CLAM/gene_exp_CLAM_TMA2_le2_vim/high_expression_genes/h5_files"


h5_files = sorted(glob.glob(os.path.join(H5_DIR, "*.h5")))

if not h5_files:
    raise SystemExit(f"No .h5 files found in: {H5_DIR}\nUpdate H5_DIR to the folder containing ROI_*.h5")

counts = []
missing_keys = 0

for fp in h5_files:
    roi = os.path.splitext(os.path.basename(fp))[0]
    with h5py.File(fp, "r") as f:
        # Common keys used by CLAM patching
        key = None
        for k in ["coords", "patch_coords", "coordinates"]:
            if k in f:
                key = k
                break
        if key is None:
            missing_keys += 1
            continue
        n = f[key].shape[0]
    counts.append((roi, int(n)))

if not counts:
    raise SystemExit("Found .h5 files but couldn't find a coords dataset. "
                     "Open one file with h5py to inspect keys.")

# Summary
vals = np.array([c for _, c in counts], dtype=int)
roi_min = [r for r,c in counts if c == vals.min()]
roi_max = [r for r,c in counts if c == vals.max()]

print(f"ROIs counted: {len(counts)} / {len(h5_files)}")
if missing_keys:
    print(f"⚠️ {missing_keys} files skipped (no coords dataset found)")

print(f"Min patches: {vals.min()}  (ROIs: {', '.join(roi_min[:10])}{' ...' if len(roi_min)>10 else ''})")
print(f"Max patches: {vals.max()}  (ROIs: {', '.join(roi_max[:10])}{' ...' if len(roi_max)>10 else ''})")
print(f"Mean patches: {vals.mean():.2f}")
print(f"Median patches: {np.median(vals):.0f}")

# Save full table
out = "tma2_new_roi_patch_counts.csv"
with open(out, "w") as w:
    w.write("roi,patch_count\n")
    for r,c in counts:
        w.write(f"{r},{c}\n")

print(f"✅ Wrote full per-ROI counts to {out}")

