import os
import shutil
from tqdm.auto import tqdm

def move_patient_folders(main_folder_path, destination_folder_path):
    # Iterate through each date folder
#    for date_folder in tqdm(os.listdir(main_folder_path), leave=False):
#        date_folder_path = os.path.join(main_folder_path, date_folder)

        # Check if it's a directory
#        if os.path.isdir(date_folder_path):
            # Iterate through CR folders within each date folder
            for cr_folder in os.listdir(main_folder_path):
                cr_folder_path = os.path.join(main_folder_path, cr_folder)

                # Check if it's a directory
                if os.path.isdir(cr_folder_path):
                    # Move patient folders to the destination folder
                    destination_path = os.path.join(destination_folder_path, cr_folder)
                    shutil.move(cr_folder_path, destination_path)

# Example usage:
main_folder = '/data/2021 Months/CT 2021/21-25'
destination_folder = '/data/2021 Months/CT 2021'
move_patient_folders(main_folder, destination_folder)
