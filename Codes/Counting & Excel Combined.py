#!/usr/bin/env python
# coding: utf-8

# In[9]:


import os
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import itertools
import chardet
import csv
import pandas as pd


# In[10]:


# Common setup
main_folder_path = "/data/Reports_Mar_2023/March_23"
excel_name = "March 2023 Final"
excel_file_path = os.path.join("/data", f"{excel_name}.xlsx").replace("\\", "/")
keywords_csv = os.path.join("/data", "feb24_keywords.csv").replace("\\", "/")


# In[11]:


# Read keywords from CSV
with open(keywords_csv, 'r') as file:
    reader = csv.reader(file)
    headers = next(reader)
    keywords = {}
    for row in reader:
        for header, value in zip(headers, row):
            if header not in keywords:
                keywords[header] = set()
            keywords[header] |= {v for v in value.split(',') if v}

# Create list of dictionaries for keywords
keyword_list = []
for header, values in keywords.items():
    keyword_dict = {
        'keyword': values,
        'findings': f'{header.capitalize()}'
    }
    keyword_list.append(keyword_dict)


# In[12]:


# Initialize variables
pathology_counts = {keyword_data['findings']: [] for keyword_data in keyword_list}
counts = {keyword_data['findings']: 0 for keyword_data in keyword_list}
Total_count = 0
patient_data = {}
found = 0
target_words1 = ["infective etiology", "infective etology"]
target_words2 = ["homogeneous opacit", "homogenous opacit"]
found_counts = {combo: 0 for combo in itertools.product(target_words1, target_words2)}


# In[13]:


# Define age and gender check functions
def age_check(text):
    index2 = text.find("name:")
    index3 = text.find("sex:")
    age = ""
    newstring = text[index2:index3]
    if not re.search(r'\d', newstring):
        age = "No Age"
    else:
        for i in range(index2, index3):
            if text[i].isnumeric() and text[i+1].isnumeric():
                age = text[i] + text[i+1]
                break
            elif text[i].isnumeric() and not text[i+1].isnumeric():
                age = text[i]
                break
    return age

def gender_check(text):
    gender = "No Sex"
    if "sex:m" in text:
        gender = "M"
    elif "sex:f" in text:
        gender = "F"
    return gender


# In[ ]:


main_folders = set(os.listdir(main_folder_path))

for folder in tqdm(main_folders):
    rep_folder_path = os.path.join(main_folder_path, folder)

    if os.path.isdir(rep_folder_path):
        for html_file in os.listdir(rep_folder_path):
            if html_file.startswith('Approved'):
                pathology_counts_instance = {keyword_data['findings']: 0 for keyword_data in keyword_list}
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
                    
                    for keyword_data in keyword_list:
                        for k in keyword_data['keyword']:
                            if all(keyword.lower() in text for keyword in ['modality:cr', 'study:chest', k.lower()]):
                                pathology_counts_instance[keyword_data['findings']] = 1
                                break
                                
                    # Extract patient information
                    patient_id = folder
                    gender = gender_check(text)
                    age = age_check(text)
  
                    if patient_id not in patient_data:
                        patient_data[patient_id] = {'Gender': gender, 'Age': age}
                        for pathology, count in pathology_counts_instance.items():
                            if count != 0:
                                patient_data[patient_id][pathology] = count
                                counts[pathology] += 1
  
                    for combo in itertools.product(target_words1, target_words2):
                        word1, word2 = combo
                        if word1 in text and word2 in text:
                            found_counts[combo] += 1
                            if 'Ggo' not in patient_data[patient_id]:
                                patient_data[patient_id]['Ggo'] = '1'
                                counts['Ggo'] += 1
  
                except UnicodeDecodeError:
                    continue


# In[ ]:


# Create a DataFrame from patient_data
df = pd.DataFrame.from_dict(patient_data, orient='index').reset_index()
df.rename(columns={'index': 'Patient_ID'}, inplace=True)

# Save the DataFrame to an Excel file
df.to_excel(excel_file_path, index=False)

print(f"Excel file created at: {excel_file_path}")


# In[ ]:


# Print summary    
print('Total Reports: ' + str(Total_count))
print("--"*20)

for findings, count in counts.items():
    print(findings + ': ' + str(count))

