import os
import struct
import re
from io import BytesIO
import base64
from PIL import Image, UnidentifiedImageError
from paddleocr import PaddleOCR
from tqdm.auto import tqdm
from bs4 import BeautifulSoup
import numpy as np
import shutil
import logging
import random
import pandas as pd
import warnings
import pydicom

dummy_patient_id = ""
dummy_patient_name = ""

# Set logging level for PaddleOCR
logging.getLogger("ppocr").setLevel(logging.ERROR)

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

warnings.filterwarnings("ignore", category=UserWarning, module="pydicom")

def modify_dicom_files(root_path, excel_path):
    # Load or initialize institution map
    if os.path.exists(excel_path):
        institution_df = pd.read_excel(excel_path)
        institution_map = dict(zip(institution_df['InstitutionName'], institution_df['Counter']))
    else:
        institution_df = pd.DataFrame(columns=["InstitutionName", "Counter"])
        institution_map = {}

    metadata_rows = []
    dummy_counter = random.randint(100, 999) # For generating ANON IDs

    for patient_folder in tqdm(os.listdir(root_path)):
        patient_folder_path = os.path.join(root_path, patient_folder)
        if os.path.isdir(patient_folder_path):
            for inside_folder in tqdm(os.listdir(patient_folder_path), leave=False):
                inside_folder_path = os.path.join(patient_folder_path, inside_folder)
                if os.path.isdir(inside_folder_path):
                    for file in tqdm(os.listdir(inside_folder_path), leave=False):
                        if file.endswith('.dic') or file.endswith('.dcm'):
                            dicom_path = os.path.join(inside_folder_path, file)
                            #dicom_image = pydicom.dcmread(dicom_path, force=True)
                            try:
                                dicom_image = pydicom.dcmread(dicom_path, force=True)
                            except (OSError, struct.error) as e:
                                print(f"Skipping corrupted file: {dicom_path} | Error: {e}")
                                return  # or continue


                            # Extract or anonymize PatientName and PatientID
                            original_patient_name = str(getattr(dicom_image, 'PatientName', ''))
                            original_patient_id = str(getattr(dicom_image, 'PatientID', ''))
                            patient_age = ''

                            # Extract age if embedded in name
                            if original_patient_name:
                                age_match = re.search(r'\^?(\d+)\s*(?:Y(?:rs?|ear)?)', original_patient_name, re.IGNORECASE)
                                if age_match:
                                    patient_age = age_match.group(1)
                                    dicom_image.PatientAge = f"{int(patient_age):03d}Y"

                            # Generate dummy name and ID
                            dummy_patient_id = f"ANON_{dummy_counter:03d}"
                            dummy_patient_name = f"PATIENT_{dummy_counter:03d}"

                            dicom_image.PatientID = dummy_patient_id
                            dicom_image.PatientName = dummy_patient_name 

                            # Remove additional sensitive tags
                            tag_numbers = [(0x0002, 0x0013), (0x0002, 0x0016), (0x0008, 0x1060), (0x0008, 0x1090),
                                        (0x0021, 0x0012), (0x0400, 0x0561), (0x0009, 0x0010), (0x0008, 0x1070),
                                        (0x0008, 0x0090), (0x0018,0x1030)]
                            
                            metadata = dicom_image.file_meta
                            for tag in [(0x0002, 0x0016), (0x0002, 0x0013)]:
                                if tag in metadata:
                                    metadata[tag].value = ''

                            # Replace InstitutionName with a mapped ID
                            institution_name = str(getattr(dicom_image, 'InstitutionName', 'Unknown'))
                            if institution_name not in institution_map:
                                institution_map[institution_name] = len(institution_map) + 1
                            institution_id = institution_map[institution_name]
                            dicom_image.InstitutionName = str(institution_id)

                            # Remove any specified tags
                            for tag_number in tag_numbers:
                                dicom_image.pop(tag_number, None)
                                dicom_image.file_meta.pop(tag_number, None)

                            # Handle transfer syntax (decompression + rewrite)
                            if dicom_image.file_meta.TransferSyntaxUID.name.startswith("JPEG"):
                                try:
                                    dicom_image.decompress()  # GDCM must be installed
                                    dicom_image.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
                                except Exception as e:
                                    print(f"Warning: Failed to decompress file {dicom_path}: {str(e)}")

                            # Save the modified DICOM image
                            try:
                                dicom_image.save_as(dicom_path)
                            except Exception as e:
                                print(f"Error saving DICOM file: {dicom_path}")
                                print(f"Error message: {str(e)}")

                            # Add metadata to full_df
                            metadata_rows.append({
                                "PatientFolder": patient_folder,
                                "OriginalPatientName": original_patient_name,
                                "OriginalPatientID": original_patient_id,
                                "AnonymizedPatientID": dummy_patient_id,
                                "AnonymizedPatientName": dummy_patient_name,
                                "PatientAge": patient_age,
                                "InstitutionName": institution_name,
                                "InstitutionID": institution_id
                            })

            new_patient_name_path = os.path.join(root_path, dummy_patient_name)
            os.rename(patient_folder_path, new_patient_name_path)
            dummy_counter += 1 

    # Save full_df
    full_df = pd.DataFrame(metadata_rows)
    full_df.to_excel(excel_path, index=False)

    # Save updated institution map
    institution_df = pd.DataFrame(list(institution_map.items()), columns=["InstitutionName", "Counter"])
    institution_df.to_excel("institution_mapping.xlsx", index=False)
    
def remove_img_tags(soup, reg_no):
    # Find all <img> tags and decompose them
    for img_tag in soup.find_all('img'):
        img_tag.replace_with(reg_no)

def extract_image_tags(soup):
    img_tags = soup.find_all('img')
    for img_tag in img_tags:
        base64str = img_tag['src']
        image = base64_to_image(base64str)
        if image is None:
            continue
        image = np.array(image)
        
        result = ocr.ocr(image, cls=True)
        extracted_text = ' '.join([element[1][0] for line in result if line for element in line if element])
        
        pattern = r"Reg(.*)"
        match = re.search(pattern, extracted_text, re.IGNORECASE)
        if match:
            return base64str, match, extracted_text
    return None, None, None

def base64_to_image(base64str):
    base64_string = base64str.split(",")[-1]
    
    # Fix padding issues in base64 string
    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += '=' * (4 - missing_padding)
    
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        return image
    except (UnidentifiedImageError, base64.binascii.Error) as e:
        logging.warning(f"Unidentified image file or invalid base64 string: {e}")
        return None

def replace_image_with_text(soup, original_base64str, text):
    img_tag = None
    for tag in soup.find_all('img'):
        if original_base64str in tag['src']:
            img_tag = tag
            break
    if img_tag:
        img_tag.replace_with(text)

def erase_and_save_details(input_folder, excel_path, no_report_path, error_folder):
    final_count = 0
    approved_count = 0
    no_report = 0

    reg_numbers = [
        "Reg.No. 2003/04/1779",
        "Reg.No.: 2014/11/4806",
        "Reg.No. 2005/03/1611"
    ]

    # Initialize an empty DataFrame to store the extracted data
    columns = ["Folder", "Patient ID", "Patient Name", "Age", "Gender", "Study", "Modality", "Study Date", "Accession", "Physician", "Extracted Text", "Reg No"]
    data_df = pd.DataFrame(columns=columns)
        
    # Ensure directories exist
    os.makedirs(excel_path, exist_ok=True)
    os.makedirs(no_report_path, exist_ok=True)
    os.makedirs(error_folder, exist_ok=True)
    
    # Iterate through each folder in the input folder
    for folder in tqdm(os.listdir(input_folder)):
        inside_folder = os.path.join(input_folder, folder)
        html_files = [f for f in os.listdir(inside_folder) if f.endswith('.html')]
        
        if not html_files:
            shutil.move(inside_folder, os.path.join(no_report_path, folder))
            no_report += 1
        else:
            for filename in os.listdir(inside_folder):
                if filename.startswith('Final'):
                    final_count +=1
                    # Read the HTML file
                    with open(os.path.join(inside_folder, filename), 'r', encoding='utf-16') as file:
                        html_content = file.read()
    
                    # Parse the HTML content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    td_tags = soup.find_all('td')
                    
                    if td_tags:
                        
                        patient_name_value = None
                        patient_id_value = None
                        age_value = None
                        sex_value = None
                        study_value = None
                        modality_value = None
                        study_date_value = None
                        accession_value = None
                        physician_value = None
                        
                        # Find and erase 'Patient Name' and 'Patient ID' values
                        for tag in soup.find_all('td'):
                            if tag.find('b') and 'Patient Name' in tag.find('b').text:
                                patient_name_value = tag.get_text().strip().replace('Patient Name:', '').strip()
                                age_match = re.search(r'\d+', patient_name_value)
                                if age_match:
                                    age_value = patient_name_value[age_match.start():].strip()
                                    # Remove the age part from patient_name_value
                                    patient_name_value = patient_name_value[:age_match.start()].strip()
                                # Replace text after 'Patient Name' with empty string
                                tag.contents[-1].replace_with('')
    
                            if tag.find('b') and 'Patient ID' in tag.find('b').text:
                                patient_id_value = tag.get_text().strip().replace('Patient ID:', '').strip()
                                tag.contents[-1].replace_with('')
    
                            if tag.find('b') and 'Sex' in tag.find('b').text:
                                sex_value = tag.get_text().strip().replace('Sex:', '').strip()
    
                            if tag.find('b') and 'Modality' in tag.find('b').text:
                                modality_value = tag.get_text().strip().replace('Modality:', '').strip()
    
                            if tag.find('b') and 'Study' in tag.find('b').text and not 'Study ' in tag.find('b').text:
                                study_value = tag.get_text().strip().replace('Study:', '').strip()
    
                            if tag.find('b') and 'Study Date' in tag.find('b').text:
                                study_date_value = tag.get_text().strip().replace('Study Date:', '').strip()
    
                            if tag.find('b') and 'Accession Number' in tag.find('b').text:
                                accession_value = tag.get_text().strip().replace('Accession Number:', '').strip()
                                tag.contents[-1].replace_with('')
    
                            if tag.find('b') and 'Referring Physician' in tag.find('b').text:
                                physician_value = tag.get_text().strip().replace('Referring Physician:', '').strip()
                                tag.contents[-1].replace_with('')
    
                        # Insert the age value into the <b>Age</b> tag if it exists
                        if age_value:
                            for tag in soup.find_all('td'):
                                if tag.find('b') and 'Age' in tag.find('b').text:
                                    # Replace ':' with ': ' + age_value
                                    tag.contents[-1].replace_with(f':{age_value}')
                        else:
                            for tag in soup.find_all('td'):
                                if tag.find('b') and 'Age' in tag.find('b').text:
                                    age_value = tag.get_text().strip().replace('Age:', '').strip()
                                    if not age_value:
                                        age_value = "0"

                        base64str, match, extracted_text = extract_image_tags(soup)

                        if match:                
                            reg_no = match.group(0).strip()
                            replace_image_with_text(soup, base64str, reg_no)
    
                            for img_tag in soup.find_all('img'):
                                img_tag.decompose()
                        else:        
                            reg_no = random.choice(reg_numbers)                            
                            
                            for img_tag in soup.find_all('img'):
                                img_tag.replace_with(reg_no)
                    else:
                        reg_no = random.choice(reg_numbers)
                            
                        remove_img_tags(soup, reg_no)
                    
                    # Write the modified HTML to the output folder
                    with open(os.path.join(inside_folder, filename), 'w', encoding='utf-16') as file:
                        file.write(str(soup))

                elif filename.startswith('Approved'):
                    approved_count += 1
                    # Read the HTML file
                    with open(os.path.join(inside_folder, filename), 'r', encoding='utf-16') as file:
                        html_content = file.read()
    
                    # Parse the HTML content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
    
                    base64str, match, extracted_text = extract_image_tags(soup)
    
                    td_tags = soup.find_all('td')
                    
                    if td_tags:
                        patient_name_value = None
                        patient_id_value = None
                        age_value = None
                        sex_value = None
                        study_value = None
                        modality_value = None
                        study_date_value = None
                        accession_value = None
                        physician_value = None
    
                        # Find and erase 'Patient Name' and 'Patient ID' values
                        for tag in soup.find_all('td'):
                            if tag.find('b') and 'Patient Name' in tag.find('b').text:
                                patient_name_value = tag.get_text().strip().replace('Patient Name:', '').strip()
                                age_match = re.search(r'\d+', patient_name_value)
                                if age_match:
                                    age_value = patient_name_value[age_match.start():].strip()
                                    # Remove the age part from patient_name_value
                                    patient_name_value = patient_name_value[:age_match.start()].strip()
                                # Replace text after 'Patient Name' with empty string
                                tag.contents[-1].replace_with('')
    
                            if tag.find('b') and 'Patient ID' in tag.find('b').text:
                                patient_id_value = tag.get_text().strip().replace('Patient ID:', '').strip()
                                tag.contents[-1].replace_with('')
    
                            if tag.find('b') and 'Sex' in tag.find('b').text:
                                sex_value = tag.get_text().strip().replace('Sex:', '').strip()
    
                            if tag.find('b') and 'Modality' in tag.find('b').text:
                                modality_value = tag.get_text().strip().replace('Modality:', '').strip()
    
                            if tag.find('b') and 'Study' in tag.find('b').text and not 'Study ' in tag.find('b').text:
                                study_value = tag.get_text().strip().replace('Study:', '').strip()
    
                            if tag.find('b') and 'Study Date' in tag.find('b').text:
                                study_date_value = tag.get_text().strip().replace('Study Date:', '').strip()
    
                            if tag.find('b') and 'Accession Number' in tag.find('b').text:
                                accession_value = tag.get_text().strip().replace('Accession Number:', '').strip()
                                tag.contents[-1].replace_with('')
    
                            if tag.find('b') and 'Referring Physician' in tag.find('b').text:
                                physician_value = tag.get_text().strip().replace('Referring Physician:', '').strip()
                                tag.contents[-1].replace_with('')
    
                        # Insert the age value into the <b>Age</b> tag if it exists
                        if age_value:
                            for tag in soup.find_all('td'):
                                if tag.find('b') and 'Age' in tag.find('b').text:
                                    # Replace ':' with ': ' + age_value
                                    tag.contents[-1].replace_with(f':{age_value}')
                        else:
                            for tag in soup.find_all('td'):
                                if tag.find('b') and 'Age' in tag.find('b').text:
                                    age_value = tag.get_text().strip().replace('Age:', '').strip()
                                    if not age_value:
                                        age_value = "0"
                        if match:                
                            reg_no = match.group(0).strip()
                            replace_image_with_text(soup, base64str, reg_no)
    
                            for img_tag in soup.find_all('img'):
                                img_tag.decompose()
                        else:        
                            reg_no = random.choice(reg_numbers)                            
                            
                            for img_tag in soup.find_all('img'):
                                img_tag.replace_with(reg_no)
                            
                        # Write the modified HTML to the output folder
                        with open(os.path.join(inside_folder, filename), 'w', encoding='utf-16') as file:
                            file.write(str(soup))

                        # Create a DataFrame row with the extracted data
                        data_row = {
                            "Folder": folder,
                            "Patient ID": patient_id_value,
                            "Patient Name": patient_name_value,
                            "Age": age_value,
                            "Gender": sex_value,
                            "Study": study_value,
                            "Modality": modality_value,
                            "Study Date": study_date_value,
                            "Accession": accession_value,
                            "Physician": physician_value,
                            "Extracted Text": extracted_text,
                            "Reg No": reg_no
                        }
                        
                        # Append the data row to the DataFrame
                        data_df = pd.concat([data_df, pd.DataFrame([data_row])], ignore_index=True)
    
    # Save the data DataFrame to an Excel file
    data_df.to_excel(os.path.join(excel_path, 'Pleural_Effusion_extracted_data.xlsx'), index=False)
    
    # Print the count after the main loop
    print(f"Total count of Final Reports: {final_count}")
    print(f"Total count of Approved Reports: {approved_count}")
    print(f"Total count of folders without report: {no_report}")

input_folder = "/data/Merai/25KPerPathology/Pleural_Effusion/"
error_folder = "/data/Merai/25KPerPathology/err"
no_report_path = "/data/Merai/25KPerPathology/err"
excel_path = "/data/Merai/25KPerPathology/"
dic_excel_path = "/data/Merai/25KPerPathology/Pleural_Effusion_Institution_names.xlsx"

# Run the main function
modify_dicom_files(input_folder, dic_excel_path)
erase_and_save_details(input_folder, excel_path, no_report_path, error_folder)