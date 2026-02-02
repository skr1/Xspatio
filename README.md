# XSPATIO

XSPATIO is an explanatory computational pathology pipeline that directly links **H&E morphology** with **spatially resolved molecular expression** using **ROI-aware segmentation**, **foundation-model feature extraction**, and **spatially constrained multiple-instance learning (MIL)**.

The framework is designed for datasets with **region-level molecular ground truth**, such as **NanoString GeoMx DSP**, enabling biologically grounded prediction and interpretation of gene and protein expression from routine histology.

## Overview

XSPATIO consists of five modular stages:

1. **ROI-aware segmentation (XSPATIO-SEG)**  
2. **Patch-level feature extraction (XSPATIO-FEAT)**  
3. **Spatially constrained MIL modeling (XSPATIO-MIL)**  
4. **Model evaluation and cross-validation**  
5. **Attention-based spatial visualization (XSPATIO-Heatmaps)** 

### XSPATIO-SEG
## Input Slides

ORIGINAL_ROI_FOLDER/
├── ROI_1.jpg
├── ROI_2.jpg
└── ...

Once we have the ROIs, we proceed with segmenting regions of interest using dsp coordinates available in the presets folder under XSPATIO-SEG.

```bash
python3 create_patches_fp.py \
  --source /home/ubuntu/CLAM/ORIGINAL_ROI_FOLDER \
  --save_dir SEG_patches \
  --patch_size 256 \
  --preset dsp.csv \
  --seg --patch --stitch \
  > tma_segmentation.log 2>&1 &
```

### XSPATIO-FEAT
Once we have the segmented patches, we proceed with extracting features using the UNI model.
```bash
python3 extract_features_fp.py \
  --data_h5_dir SEG_patches \
  --data_slide_dir ORIGINAL_ROI_FOLDER \
  --csv_path ORIGINAL_ROI_FOLDER/process_list_autogen.csv \
  --model_name uni_v1 \
  --feat_dir tma_extracted_features \
  --batch_size 512 \
  --slide_ext .jpg \
  > tma_feature_extraction.log 2>&1 &
```

tma_extracted_features/
├── h5_files/
├── pt_files/
└── feature.txt

### XSPATIO-MIL
Gene or protein expression values are binarized into **low-** and **high-expression** groups using their **respective thresholds** across ROIs.

```bash
python3 gene_file_creater_clam.py \
  --csv_file combined_expression_tma1+2_gene_selected.csv \
  --column_name BIOMARKER_NAME \
  --h5_source_folder tma_extracted_features/h5_files \
  --pt_source_folder tma_extracted_features/pt_files \
  --low_h5_folder GENE_EXP/low_expression_genes/h5_files \
  --low_pt_folder GENE_EXP/low_expression_genes/pt_files \
  --high_h5_folder GENE_EXP/high_expression_genes/h5_files \
  --high_pt_folder GENE_EXP/high_expression_genes/pt_files
```

## CSV Generation for MIL Training
We create CSV files with patient_id, ROI_id, and labels before training using the script below.

```bash
python3 clam_csv_generator.py
```
Make necessary changes in the script before running it.

```bash
low_expression_genes_folder = "GENE_EXP_CLAM/low_expression_genes"
high_expression_genes_folder = "GENE_EXP_CLAM/high_expression_genes"

output_csv_path = "GENE_EXP_FILE.csv"
```

The GENE_EXP_FILE.csv file should look like:
```bash
patient_id,slide_id,label
patient_0,slide_1,low_expression_genes
patient_1,slide_2,high_expression_genes
```







