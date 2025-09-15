#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import shutil
from tqdm import tqdm
from datetime import datetime

x  = datetime.now()
print(x.strftime("%D   %H:%M:%S"))


# In[ ]:


# Get the paths from the user
text_file_path = input("Text File Path: ")
source_folder = input("Source Folder: ")
result_folder = input("Result Folder: ")

matching_patient_count = 0


# In[ ]:


# Step 1: Read instance IDs from the text file and store them in a list
with open(text_file_path, 'r') as file:
    instance_ids = [line.strip() for line in file]
    
print("Total INSTANCES: ", len(instance_ids))


# In[ ]:


# Initialize tqdm progress bars
day_entries = os.scandir(source_folder)
for day_entry in day_entries:
    if day_entry.is_dir():
        modality_entries = os.scandir(day_entry.path)
        for modality_entry in modality_entries:
            if modality_entry.is_dir():
                patient_entries = os.scandir(modality_entry.path)
                for patient_entry in patient_entries:
                    if patient_entry.is_dir() and patient_entry.name in instance_ids:
                        matching_patient_count += 1
                        dest = os.path.join(result_folder, patient_entry.name)
                        if not os.path.exists(dest):
                            shutil.copytree(patient_entry.path, dest)
        print(modality_entry)
        
    print(day_entry)

# Close tqdm progress bars
day_entries.close()

print(f"Total matching patient folders: {matching_patient_count}")

y  = datetime.now()
print(y.strftime("%D   %H:%M:%S"))
