import os
import shutil
from tqdm.auto import tqdm

count = 0

# Path to the folder containing patient ID folders
main_folder_path = "/data/2023 Extracted Images/"

# Path to the notepad file containing patient IDs
notepad_path = "/data/2023 Extracted Images/Swine Flu MarAprMay.txt"

# Path to the folder where you want to copy the matching folders
destination_folder = "/data/Swine Flu MarAprMay"

# Read patient IDs from the notepad
with open(notepad_path, 'r') as file:
    patient_ids = [line.strip() for line in file]

# Iterate through the main folder
for state_folder in tqdm(os.listdir(main_folder_path), leave=False):
    state_path = os.path.join(main_folder_path, state_folder)
    if os.path.isdir(state_path):
      for folder_name in tqdm(os.listdir(state_path), leave=False):
          folder_path = os.path.join(state_path, folder_name)
          if os.path.isdir(folder_path) and folder_name in patient_ids:
              # Copy the folder to the destination folder
              shutil.move(folder_path, os.path.join(destination_folder, folder_name))
              count += 1

print("Moved Folders: ", count)