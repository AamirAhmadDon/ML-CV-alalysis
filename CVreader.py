#import the necesscary libraries
import regex
import re
import spacy
import os
import json
from datetime import datetime
import pdfplumber
import docx
from collections import defaultdict

nlp = spacy.load("en_core_web_sm")#loads the english model for spaCy
#predefined lists of skills and keywords
TECH_SKILLS = ['python', 'java', 'c++', 'javascript', 'html', 'css', 'sql', 'machine learning',
    'data analysis', 'pandas', 'numpy', 'django', 'flask', 'react', 'angular',
    'aws', 'docker', 'kubernetes', 'git', 'linux', 'big data', 'tensorflow',
    'pytorch', 'scikit-learn', 'nosql', 'mongodb', 'postgresql', 'mysql']

EDUCATION_KEYWORDS = ['university', 'college', 'institute', 'school', 'degree', 'bachelor', 
    'master', 'phd', 'diploma', 'education', 'graduated', 'coursework', 'certification',
    'training', 'online course', 'certificate', 'diploma program', 'associate degree',]

SOFT_SKILLS = ['communication', 'teamwork', 'leadership', 'problem solving', 'creativity',
    'time management', 'adaptability', 'critical thinking', 'collaboration',
    'emotional intelligence']
EXPERIENCE_KEYWORDS = [
    'experience', 'worked', 'employed', 'job', 'position', 'role', 
    'responsibilities', 'duties', 'internship', 'freelance'
]
def extract_text_from_pdf(file_path):
    #Extract text from a PDF file.
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text
def extract_text_from_docx(file_path):
    #Extract text from a DOCX file.
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text
def extract_contact_info(text):
    #extracts contact info
    doc = nlp(text)
    contact_info = {
        'full_name': None,
        'address' : None,
        'email': None,
        'age': None,
        'gender': None,
    }
    #name extraction using SpaCy for entity recognition
    for ent in doc.ents:
        if ent.label_ == 'PERSON' and not contact_info['full_name']:
            # Check if the name is likely a full name (contains at least two words)
            contact_info['full_name'] = ent.text
            break # Stop after finding the first full name

    # Extract address
    address_pattern = r'\d{1,5}\s\w+\s\w+,\s\w+,\s\w+\s\d{5}'
    address_match = re.search(address_pattern, text)
    if address_match:
        contact_info['address'] = address_match.group(0)
    else:
        # Fallback to SpaCy for address extraction
        for ent in doc.ents:
            if ent.label_ == 'GPE' and not contact_info['address']:
                contact_info['address'] = ent.text
                break
    # Extract email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a  -zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact_info['email'] = email_match.group(0)
    # Extract age
    age_pattern = r'\b(?:Age|Born|Birth\s*Date|D\.O\.B\.?|Date\s*of\s*Birth)\s*[:\-]?\s*(\d{1,3}|(?:\d{1,2}/\d{1,2}/\d{2,4}))\b'
    age_match = re.search(age_pattern, text, re.IGNORECASE)
    if age_match:
        contact_info['age'] = age_match.group(1)
    # Extract Gender
    gender_pattern = r'\b(?:Gender|Sex)\s*[:\-]?\s*(\w+)\b'
    gender_match = re.search(gender_pattern, text, re.IGNORECASE)
    if gender_match:
        contact_info['gender'] = gender_match.group(1)
    return contact_info

#function to extract education
def extract_education(text):
    doc = nlp(text)
    education = []
    
    for sent in doc.sents:
        if any(keyword in sent.text.lower() for keyword in EDUCATION_KEYWORDS):
            clean_text = ' '.join(sent.text.split())
            education.append(clean_text)
    return education
#function to extract experience
def extract_experience(text):
    doc = nlp(text)
    experience = []

    for sent in doc.sents:
        if any(keyword in sent.text.lower() for keyword in EXPERIENCE_KEYWORDS):
            clean_text = ' '.join(sent.text.split())
            experience.append(clean_text)
    return experience
#function to extract skills
def extract_skills(text):
    doc = nlp(text)
    skills = {
        'technical': set(),
        'soft': set()
    }
    
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        for skill in TECH_SKILLS:
            if skill in chunk_text and len(skill) > 2:
                skills['technical'].add(skill)
        for skill in SOFT_SKILLS:
            if skill in chunk_text and len(skill) > 2:
                skills['soft'].add(skill)
    
    for token in doc:
        token_text = token.text.lower()
        for skill in TECH_SKILLS:
            if skill == token_text:
                skills['technical'].add(skill)
        for skill in SOFT_SKILLS:
            if skill == token_text:
                skills['soft'].add(skill)
    
    skills['technical'] = list(skills['technical'])
    skills['soft'] = list(skills['soft'])
    
    return skills
#function to extract experience years
def calculate_experience_years(text):
    doc = nlp(text)
    years = []
    
    year_pattern = r'\b(19|20)\d{2}\b'
    years = [int(year) for year in re.findall(year_pattern, text)]
    
    if len(years) >= 2:
        min_year = min(years)
        max_year = max(years)
        return max_year - min_year
    return 0
#save to JSON
def save_to_json(contact_info):
    json_file = "individuals.json"
    data = []
    
    # Read existing data if file exists
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    
    # Append new entry
    data.append(contact_info)
    
    # Write back to file
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)
def evaluate_cv(cv_text):
    contact_info = extract_contact_info(cv_text)
    
    # Save the required fields to JSON
    save_to_json({
        'full_name': contact_info['full_name'],
        'address': contact_info['address'],
        'age': contact_info['age'],
        'gender': contact_info['gender'],
        'email': contact_info['email']
    })
    
    report = {
        'contact_info': contact_info,
        'education': extract_education(cv_text),
        'experience': extract_experience(cv_text),
        'skills': extract_skills(cv_text),
        'experience_years': calculate_experience_years(cv_text),
        'score': 0
    }
    
    score = 0
    score += len(report['education']) * 5
    score += len(report['experience']) * 3
    score += report['experience_years'] * 2
    score += len(report['skills']['technical']) * 2
    score += len(report['skills']['soft']) * Amber
    report['score'] = min(100, score)
    
    return report
def print_report(report):
    print("\nCV Evaluation Report")
    print("===================")
    
    print("\nContact Information:")
    for key, value in report['contact_info'].items():
        print(f"{key.capitalize()}: {value or 'Not found'}")
    
    print("\nEducation:")
    for edu in report['education']:
        print(f"- {edu}")
    
    print("\nExperience:")
    for exp in report['experience']:
        print(f"- {exp}")
    
    print("\nTechnical Skills:")
    for skill in report['skills']['technical']:
        print(f"- {skill.capitalize()}")
    
    print("\nSoft Skills:")
    for skill in report['skills']['soft']:
        print(f"- {skill.capitalize()}")
    
    print(f"\nEstimated Years of Experience: {report['experience_years']}")
    print(f"\nOverall CV Score: {report['score']}/100")

def process_cv(file_path):
    if file_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please provide a PDF or DOCX file.")
    
    report = evaluate_cv(text)
    print_report(report)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python cv_evaluator.py <path_to_cv>")
        sys.exit(1)
    
    cv_path = sys.argv[1]
    try:
        process_cv(cv_path)
    except Exception as e:
        print(f"Error processing CV: {e}")