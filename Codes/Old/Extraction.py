#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import zipfile
from tqdm import tqdm
import shutil
import chardet
import subprocess
import concurrent
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from multiprocessing import Pool
import pandas as pd
import numpy as np
from datetime import datetime

x  = datetime.now()
print(x.strftime("%D   %H:%M:%S"))


# In[ ]:


num_cores = multiprocessing.cpu_count()


# In[ ]:

source_folder_path = "/data/"
target_folder = "/data/2023 Unzipped from Satish" 

#source_folder_path = input("Source Folder Path: ")
#target_folder = input("Target Folder Path: ")


# In[ ]:


def extract_zip_file(zip_file_path, extract_to):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        extracted_files = []
        for file in tqdm(file_list, desc="Extracting files: ", leave=False):
            zip_ref.extract(file, extract_to)
            extracted_files.append(file)
        return extracted_files

def extract_7z(file_path, target_folder):
    subprocess.run(['7z2301-linux-x64/7zzs', 'x', file_path, f'-o{target_folder}'])


# In[ ]:


def process_zip_file(zip_file):
    zip_file_path = os.path.join(source_folder_path, zip_file)
    extract_zip_file(zip_file_path, target_folder)
    
# Process zip files in parallel
with ThreadPoolExecutor(max_workers=num_cores) as executor:
    futures = []
    zip_files = sorted(file for file in os.listdir(source_folder_path) if file.endswith('.zip'))
    for zip_file in zip_files:
        future = executor.submit(process_zip_file, zip_file)
        futures.append(future)
    
    # Wait for all futures to complete
    concurrent.futures.wait(futures)


# In[ ]:


zip_folders = (zips for zips in os.listdir(source_folder_path) if zips.startswith('Blunted CP Angle'))

for zip_folder in zip_folders:
    file_path = os.path.join(source_folder_path, zip_folder)
    extract_7z(file_path, target_folder)

print("Extraction complete.")

y  = datetime.now()
print(y.strftime("%D   %H:%M:%S"))

