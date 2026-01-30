import os
import shutil

def combine_folders(src_folders, dest_folder):
    """
    Combine h5_files and pt_files from multiple source folders into a destination folder.
    """
    # Define sub-folder paths for low and high gene expression
    categories = ["low_expression_genes", "high_expression_genes"]
    sub_folders = ["h5_files", "pt_files"]

    # Create destination folder structure
    for category in categories:
        for sub in sub_folders:
            os.makedirs(os.path.join(dest_folder, category, sub), exist_ok=True)
    
    # Iterate through source folders and copy files
    for src in src_folders:
        for category in categories:
            for sub in sub_folders:
                src_path = os.path.join(src, category, sub)
                dest_path = os.path.join(dest_folder, category, sub)
                if os.path.exists(src_path):
                    for file in os.listdir(src_path):
                        src_file = os.path.join(src_path, file)
                        dest_file = os.path.join(dest_path, file)
                        if os.path.isfile(src_file):  # Ensure it's a file
                            shutil.copy2(src_file, dest_file)
                            print(f"Copied: {src_file} -> {dest_file}")

# Define source folders and destination folder
src_folders = ["/home/ubuntu/CLAM/dsp_ROIs_center_extracted_features", "/home/ubuntu/CLAM/tma2_extracted_features"]
dest_folder = "/home/ubuntu/CLAM/tma1+2_extracted_features"

# Combine the folders
combine_folders(src_folders, dest_folder)

print("Files have been successfully combined!")
