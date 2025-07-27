import re
import spacy
import os
import json
import pdfplumber
import docx
from collections import defaultdict
import sys

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Load config from JSON files
def load_config():
    try:
        with open("config/patterns.json", "r") as f:
            patterns = json.load(f)
        with open("config/skills_keywords.json", "r") as f:
            skills_keywords = json.load(f)
        return patterns, skills_keywords
    except FileNotFoundError as e:
        print(f"Error: Config file missing - {e}")
        sys.exit(1)

PATTERNS, SKILLS_KEYWORDS = load_config()

# File processing
def extract_text(file_path):
    if file_path.lower().endswith('.pdf'):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages)
    elif file_path.lower().endswith('.docx'):
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)
    else:
        raise ValueError("Unsupported file format. Use PDF or DOCX.")

# Information extraction
def extract_contact_info(text):
    doc = nlp(text)
    contact_info = {field: None for field in ['full_name', 'address', 'email', 'age', 'gender']}
    
    # Name extraction
    for ent in doc.ents:
        if ent.label_ == 'PERSON' and not contact_info['full_name']:
            contact_info['full_name'] = ent.text
            break

    # Address extraction
    address_match = re.search(PATTERNS['address'], text)
    contact_info['address'] = address_match.group(0) if address_match else None

    # Email extraction
    email_match = re.search(PATTERNS['email'], text)
    contact_info['email'] = email_match.group(0) if email_match else None

    # Age extraction
    age_match = re.search(PATTERNS['age'], text, re.IGNORECASE)
    contact_info['age'] = age_match.group(1) if age_match else None

    # Gender extraction
    gender_match = re.search(PATTERNS['gender'], text, re.IGNORECASE)
    contact_info['gender'] = gender_match.group(1) if gender_match else None

    return contact_info

def extract_section(text, keywords):
    doc = nlp(text)
    return [
        ' '.join(sent.text.split()) 
        for sent in doc.sents 
        if any(kw in sent.text.lower() for kw in keywords)
    ]

def extract_skills(text):
    doc = nlp(text)
    skills = defaultdict(set)
    
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        for category, skill_list in SKILLS_KEYWORDS['skills'].items():
            for skill in skill_list:
                if skill.lower() in chunk_text:
                    skills[category].add(skill)
    
    return {k: list(v) for k, v in skills.items()}

def calculate_experience(text):
    years = [int(year) for year in re.findall(PATTERNS['year'], text)]
    return max(years) - min(years) if len(years) >= 2 else 0

# Scoring and output
def evaluate_cv(text):
    contact_info = extract_contact_info(text)
    report = {
        'contact_info': contact_info,
        'education': extract_section(text, SKILLS_KEYWORDS['education']),
        'experience': extract_section(text, SKILLS_KEYWORDS['experience']),
        'skills': extract_skills(text),
        'experience_years': calculate_experience(text),
        'score': 0
    }
    
    # Calculate score
    weights = {
        'education': 5,
        'experience': 3,
        'experience_years': 2,
        'technical': 2,
        'soft': 1
    }
    report['score'] = min(100, 
        len(report['education']) * weights['education'] +
        len(report['experience']) * weights['experience'] +
        report['experience_years'] * weights['experience_years'] +
        len(report['skills'].get('technical', [])) * weights['technical'] +
        len(report['skills'].get('soft', [])) * weights['soft']
    )
    
    return report

def save_to_json(data):
    os.makedirs("output", exist_ok=True)
    output_file = "output/individuals.json"
    
    existing_data = []
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            existing_data = json.load(f)
    
    existing_data.append(data)
    with open(output_file, "w") as f:
        json.dump(existing_data, f, indent=2)

def print_report(report):
    print("\nCV Evaluation Report".center(50, '='))
    for section, content in report.items():
        if isinstance(content, dict):
            print(f"\n{section.replace('_', ' ').title()}:")
            for k, v in content.items():
                print(f"{k.replace('_', ' ').title()}: {v or 'N/A'}")
        elif isinstance(content, list):
            print(f"\n{section.title()}:")
            for item in content:
                print(f"- {item}")
        else:
            print(f"{section.title()}: {content}")

# Main workflow
def process_cv(file_path):
    text = extract_text(file_path)
    report = evaluate_cv(text)
    save_to_json(report['contact_info'])
    print_report(report)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cv_evaluator.py <path_to_cv>")
        sys.exit(1)
    
    try:
        process_cv(sys.argv[1])
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
