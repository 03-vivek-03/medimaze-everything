import re

# Raw text as-is (copy and paste the exact text you gave into this variable)
raw_text = """
1 
. 
 ** 
Protocol 
:** 
 MRI 
 Brain 
 
 

 
2 
. 
 ** 
Patient 
 Positioning 
:** 
 Sup 
ine 
 position 
, 
 head 
 immobilized 
 in 
 a 
 head 
 coil 
.
 

 
3 
. 
 ** 
Planning 
:** 
 Axial 
, 
 coronal 
, 
 and 
 sagit 
tal 
 planes 
.
 

 
4 
. 
 ** 
Sequences 
:** 

 

 
     
* 
   
** 
T 
1 
- 
weighted 
:** 
 Axial 
 and 
 sagit 
tal 

 

 
     
* 
   
** 
T 
2 
- 
weighted 
:** 
 Axial 
 and 
 sagit 
tal 
 
 

 
     
* 
   
** 
FLA 
IR 
 ( 
Fluid 
 Atten 
uated 
 Inversion 
 Recovery 
): 
** 
 Axial 

 

 
     
* 
   
** 
D 
WI 
 ( 
Diffusion 
 Weighted 
 Imaging 
): 
** 
 Axial 
, 
 with 
 ADC 
 map 

 

 
5 
. 
 ** 
Image 
 Parameters 
:** 

 

 
     
* 
 ** 
Slice 
 Thickness 
:** 
  
3 
- 
5 
 mm 

 

 
     
* 
 ** 
Slice 
 Gap 
:** 
  
0 
. 
5 
 - 
  
1 
 mm 

 

 
     
* 
 ** 
Field 
 of 
 View 
:** 
 Appropriate 
 to 
 cover 
 the 
 entire 
 brain 

 

 
     
* 
 ** 
Matrix 
:** 
  
2 
5 
6 
 x 
  
2 
5 
6 
 or 
 higher 

 

 
6 
. 
 ** 
Contrast 
:** 
   
Not 
 routinely 
 required 
 for 
 basic 
 brain 
 MRI 
. 
 Gad 
ol 
inium 
- 
based 
 contrast 
 may 
 be 
 administered 
 intraven 
ously 
 if 
 evaluating 
 for 
 specific 
 pathologies 
 ( 
e 
. 
g 
., 
 tumors 
, 
 inflammation 
). 
 Dosage 
 will 
 depend 
 on 
 the 
 specific 
 contrast 
 agent 
 used 
 and 
 institutional 
 protocols 
.
 

 
7 
. 
 ** 
Additional 
 Information 
:** 
 
 

 
     
* 
 Patient 
 should 
 remove 
 any 
 metallic 
 objects 
.
 

 
     
* 
 Explain 
 the 
 procedure 
 to 
 the 
 patient 
 and 
 answer 
 any 
 questions 
 they 
 may 
 have 
. 
 
 

 
     
* 
 Monitor 
 the 
 patient 
 throughout 
 the 
 scan 
 for 
 comfort 
 and 
 safety 
. 




 
 

"""

# --- Cleaning functions ---

# Remove line breaks between words
def join_broken_words(text):
    # Collapse multiple spaces and newlines into a single space between words
    text = re.sub(r'(\S)\s*\n\s*(\S)', r'\1 \2', text)
    return text

# Clean multiple spaces
def clean_spaces(text):
    text = re.sub(r'\s{2,}', ' ', text)
    return text

# Re-introduce proper line breaks for headings and lists
def format_structure(text):
    # Add line breaks after section numbers
    text = re.sub(r'(\d)\s*\.\s*\*\*\s*(.*?)\s*\*\*\s*:\s*', r'\n\1. \2:\n', text)

    # Add line breaks before list items
    text = re.sub(r'\*\s+\*\*\s*(.*?)\s*\*\*\s*:\s*', r'\n* \1:', text)
    text = re.sub(r'\*\s+', r'\n* ', text)

    return text.strip()

# --- Pipeline ---

# Step 1: Fix broken words
clean_text = join_broken_words(raw_text)

# Step 2: Clean extra spaces
clean_text = clean_spaces(clean_text)

# Step 3: Apply structure formatting
clean_text = format_structure(clean_text)

# --- Final output ---
print(clean_text)
