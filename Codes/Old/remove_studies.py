import os
import shutil
from tqdm.auto import tqdm

def count_folders_with_names(main_folder_path, notepad_path):
    with open(notepad_path, 'r') as file:
        folder_names = [line.strip() for line in file.readlines()]

    counter = 0
    for folder_name in tqdm(os.listdir(main_folder_path)):
        if folder_name in folder_names:
            folder_path = os.path.join(main_folder_path, folder_name)
            try:
                shutil.move(folder_path, dest_path)
                counter += 1
            except Exception as e:
                print(f"Failed to delete folder {folder_name}: {e}")

    return counter

# Replace these paths with your actual paths
main_folder_path = "/data/2023 Data/Feb_2023_Pneumothorax"
dest_path = "/data/2023 Data/Feb pneumo without age"
notepad_path = "/data/2023 Data/Feb 2023 Pneumothorax Blanks.txt"

result = count_folders_with_names(main_folder_path, notepad_path)
print("Moved folders:", result)