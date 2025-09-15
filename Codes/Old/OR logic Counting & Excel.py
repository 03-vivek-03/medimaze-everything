#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
from bs4 import BeautifulSoup
import re
from tqdm.auto import tqdm
import chardet
import csv
import pandas as pd


# In[1]:

#main_folder_path = "/data/Reports_Jan_2023"
#excel_name = "New pathologies Jan 2023"

main_folder_path = input("Main Folder Name: ")
excel_name = input("Excel Name: ")

keywords_csv = os.path.join("/data", "new_pathologies.csv")
with open(keywords_csv, 'r') as file:
    reader = csv.reader(file)
    headers = next(reader)
    keywords = {}
    for row in reader:
        for header, value in zip(headers, row):
            if header not in keywords:
                keywords[header] = set()
            keywords[header] |= {v for v in value.split(',') if v}

keyword_list = []
for header, values in keywords.items():
    keyword_dict = {
        'keyword': values,
        'folder_name': f'{header.capitalize()}'
    }
    keyword_list.append(keyword_dict)

# Initialize pathology_counts
pathology_counts = {keyword_data['folder_name']: [] for keyword_data in keyword_list}
counts = {keyword_data['folder_name']: 0 for keyword_data in keyword_list}
Total_count = 0

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

for folder in tqdm(main_folders):
    rep_folder_path = os.path.join(main_folder_path, folder)

    if os.path.isdir(rep_folder_path):
        for html_file in os.listdir(rep_folder_path):
            if html_file.startswith('Approved'):
                # Initialize counts for each pathology
                pathology_counts_instance = {keyword_data['folder_name']: 0 for keyword_data in keyword_list}
                Total_count += 1
                report_file_path = os.path.join(rep_folder_path, html_file)

                try:
                    with open(report_file_path, 'rb') as f:
                        raw_data = f.read()
                        encoding_result = chardet.detect(raw_data)
                        file_encoding = encoding_result['encoding']

                    with open(report_file_path, 'r', encoding=file_encoding) as f:
                        content = f.read()

                    soup = BeautifulSoup(content, 'html.parser')

                    text = soup.get_text().lower()

                    keyword_match = False

                    for keyword_data in keyword_list:
                        for k in keyword_data['keyword']:
                            if all(keyword.lower() in text for keyword in ['modality:cr', 'study:chest', k.lower()]):
                                pathology_counts_instance[keyword_data['folder_name']] += 1
                                counts[keyword_data['folder_name']] += 1
                                keyword_match = True
                                break
                    

                    # Extract patient information
                    patient_ids.append(folder)
                    genders.append(gender_check(rep_folder_path, text))
                    ages.append(age_check(rep_folder_path, text))

                    # Append pathology counts for the instance
                    for pathology, count in pathology_counts_instance.items():
                        if count == 0:
                            pathology_counts[pathology].append("")
                        else:
                            pathology_counts[pathology].append(count)

                except UnicodeDecodeError:
                    continue

# Create a DataFrame with the extracted patient information and pathology counts
df = pd.DataFrame({'Patient_ID': patient_ids, 'Gender': genders, 'Age': ages})

# Add columns for each pathology and fill with counts
for pathology, counts_list in pathology_counts.items():
    df[pathology] = counts_list

# Save the DataFrame to an Excel file
excel_file_path = os.path.join("/data", f"{excel_name}.xlsx").replace("\\", "/")
df.to_excel(excel_file_path, index=False)

print(f"Excel file created at: {excel_file_path}")


# In[2]:


print('Total Reports: ' + str(Total_count))
print('--' * 20)

for folder_name, count in counts.items():
    print(folder_name + ': ' + str(count))


# In[ ]:




