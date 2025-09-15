import os

text_file_path = input("Text File Path: ")
source_folder = input("Source Folder: ")
output_file_name = input("Output File Name: ")

not_matched = 0

# Step 1: Read instance IDs from the text file and store them in a set for faster lookup
with open(text_file_path, 'r') as file:
    instance_ids = {line.strip() for line in file}

# Step 2: Collect all file names in the source folder
all_files = set()
for root, dirs, files in os.walk(source_folder):
    for file in files:
        all_files.add(file)

# Step 3: Compare instance IDs with file names and write unmatched instances to the output file
with open(output_file_name, 'w') as file:
    for instance in instance_ids:
        if instance not in all_files:
            file.write(f"{instance}\n")
            not_matched += 1

print(f"Total matching instances: {len(instance_ids)}")
print(f"Total unmatched instances: {not_matched}")
