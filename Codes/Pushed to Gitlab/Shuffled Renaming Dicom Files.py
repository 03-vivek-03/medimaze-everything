import os
import random

# Path to the folder containing DICOMs
folder_path = 'D:/Validation Data/New Validation/user7'

# List all DICOM files in the folder
dicom_files = [f for f in os.listdir(folder_path) if f.endswith('.dic')]

# Randomly shuffle the list
random.shuffle(dicom_files)

# Rename and move DICOM files
for i, filename in enumerate(dicom_files):
    # Generate new filename
    new_filename = f"{i+1:02}.{filename.split('_')[1]}"
    
    # Rename the file
    os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_filename))