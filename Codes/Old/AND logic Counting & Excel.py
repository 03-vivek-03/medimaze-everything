#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
from bs4 import BeautifulSoup
import chardet
from tqdm import tqdm
import itertools
import re
import csv
import pandas as pd



# In[ ]:


total = 0
found = 0


# In[ ]:


target_words1 = ["infective etiology", "infective etology"]
target_words2 = ["homogeneous opacit", "homogenous opacit"]


# In[ ]:


found_counts = {combo: 0 for combo in itertools.product(target_words1, target_words2)}


# In[ ]:


main_folder_path = "/data/Reports_Jan_2023/"
excel_path = "/data"
excel_name = "GGO Jan 2023"


# In[ ]:


# Create lists to store patient information
patient_ids = []
genders = []
ages = []

# Change in age_check function
def age_check(moving_path, text):
    index2 = text.find("name:")
    index3 = text.find("sex:")
    age = ""
    newstring = text[index2:index3]
    if bool(re.search(r'\d', newstring)) == False:
        age_path = os.path.join(moving_path, "No Age")
    else:
        for i in range(index2, index3):
            if text[i].isnumeric() == True and text[i+1].isnumeric() == True:
                age = text[i] + text[i+1]
                if int(age) >= 60:
                    age_path = os.path.join(moving_path, "Above 60")
                    break
                elif 30 < int(age) <= 60:
                    age_path = os.path.join(moving_path, "30 to 60")
                    break
                elif 18 <= int(age) <= 30:
                    age_path = os.path.join(moving_path, "18 to 30")
                    break
                else:
                    age_path = os.path.join(moving_path, "Below 18")
                    break
            elif text[i].isnumeric() == True and text[i+1].isnumeric() != True:
                # AGE LESS THAN 10
                age_path = os.path.join(moving_path, "Below 18")
                break
    return age

# Change in gender_check function
def gender_check(destination, text):
    moving_path = os.path.join(destination, "No Sex")
    if "sex:m" in text:
        moving_path = os.path.join(destination, "Male")
    elif "sex:f" in text:
        moving_path = os.path.join(destination, "Female")
    return os.path.basename(moving_path.split("/")[-1])  # Extract the gender from the path

main_folders = set(os.listdir(main_folder_path))


# In[ ]:


for folder in tqdm(main_folders):
    rep_folder_path = os.path.join(main_folder_path, folder)
    if os.path.isdir(rep_folder_path):
        for html_file in os.listdir(rep_folder_path):
            if html_file.startswith('Approved'):
                total += 1
                report_file_path = os.path.join(rep_folder_path, html_file)
                with open(report_file_path, 'rb') as f:
                    raw_data = f.read()
                    encoding_result = chardet.detect(raw_data)
                    file_encoding = encoding_result['encoding']
                with open(report_file_path, 'r', encoding=file_encoding) as f:
                    content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text().lower()

                # Check for each combination
                for combo in itertools.product(target_words1, target_words2):
                    word1, word2 = combo
                    if word1 in text and word2 in text:
                        found_counts[combo] += 1
                        found += 1
                        
                        # Extract patient information
                        patient_ids.append(folder)
                        genders.append(gender_check(rep_folder_path, text))
                        ages.append(age_check(rep_folder_path, text))


# In[ ]:


# Create a DataFrame with the extracted patient information and pathology counts
df = pd.DataFrame({'Patient_ID': patient_ids, 'Gender': genders, 'Age': ages})

# Save the DataFrame to an Excel file
excel_file_path = os.path.join(excel_path, f"{excel_name}.xlsx").replace("\\", "/")
df.to_excel(excel_file_path, index=False)

print(f"Excel file created at: {excel_file_path}")


# In[ ]:


print("Total Reports: ", total)
print("---------------------------")
print("Total Found: ", found)
print("---------------------------")
print("Combination-wise counts:")
for combo, count in found_counts.items():
    print(f"{combo}: {count}")

