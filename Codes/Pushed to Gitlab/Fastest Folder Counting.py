import os
from tqdm.auto import tqdm

# Define the path to your disease folder
main_folder = 'F:/Data Results/2020/2020 - Combined'

# Initialize an empty dictionary to store the counts
patient_counts = {}

# Define the gender and age groups
genders = ['Male', 'Female']
age_groups = ['18 to 30', '30 to 60', 'Above 60']

# Loop through gender and age groups
for pathology in tqdm(os.listdir(main_folder), leave=False):
    for gender in genders:
        patient_counts[gender] = {}
        for age_group in age_groups:
            age_folder = os.path.join(main_folder, pathology, gender, age_group).replace("\\","/")
            if os.path.exists(age_folder):
                patients = os.listdir(age_folder)
                patient_counts[gender][age_group] = len(patients)
    print(pathology)
    for gender, age_groups_dict in patient_counts.items():
        print(gender)
        for age_group, count in age_groups_dict.items():
            print(f'  {age_group}: {count}')
    print("---------------------")