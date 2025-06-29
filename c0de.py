import re
import spacy
import json

nlp = spacy.load("en_core_web_sm")# Load the English NLP model

#regex pattrerns to ensure the genders and email are valid and in a correct format
gender_pattern = re.compile(r'^(male|female|non-binary|other)$', re.IGNORECASE)
email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

#function to tokenize the text and extract the required information
def analyze_individual(data):
    name = data.get("name", "")
    age = data.get("age", "")
    sex = data.get("sex", "")
    address = data.get("address", "")
    email = data.get("email", "")
    
    print("\n Individual Information:")
    print(f"Name: {name}")
    print(f"Age: {age}")
    print(f"Sex: {sex} (Valid: {bool(gender_pattern.match(sex))})")
    print(f"Address: {address}")
    print(f"Email: {email} (Valid: {bool(email_pattern.match(email))})")
    
    # Combine name, address, and email for NLP analysis
    text = f"{name}. {address}. {email}"
    doc = nlp(text)

    print("\n Tokens:")
    for token in doc:
        print(f" - {token.text}")

    print("\n🔍 Named Entities:")
    for ent in doc.ents:
        print(f" - {ent.text} ({ent.label_})")
        
# Main function to ask user input and analyze each individual
def input_and_analyze():
    try:
        with open("individuals.json", "r") as file:
            individuals = json.load(file)
        index = int(input("Enter the index of the individual to analyze (0 to {}): ".format(len(individuals) - 1)))
        if 0 <= index < len(individuals):
            selected = individuals[index]
            analyze_individual(selected)
        else:
            print("Invalid index. Please try again.")
    except FileNotFoundError:
        print("File 'individuals.json' not found. Please ensure the file exists.")
    except ValueError:
        print("Invalid input. Please enter a valid index number.")
        
# Run the main function
if __name__ == "__main__":
    input_and_analyze()