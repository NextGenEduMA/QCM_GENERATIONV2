import json
import os
from datetime import datetime

def generate_sample_json():
    """Generate a sample JSON object"""
    sample_data = {
        "id": 1,
        "title": "Sample QCM",
        "questions": [
            {
                "question": "What is JSON?",
                "options": [
                    "JavaScript Object Notation",
                    "Java Standard Output Network",
                    "JavaScript Oriented Notation",
                    "Java Source Object Network"
                ],
                "correct_answer": 0
            }
        ],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return sample_data

def save_json_to_file(data, filename):
    """Save JSON data to a file in the Saved_qcms folder"""
    # Ensure the directory exists
    save_dir = "Saved_qcms"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Create the full file path
    file_path = os.path.join(save_dir, filename)
    
    # Write the JSON data to the file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    return file_path

if __name__ == "__main__":
    # Generate sample JSON data
    json_data = generate_sample_json()
    
    # Create a filename with timestamp
    filename = f"qcm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save the JSON data to a file
    saved_path = save_json_to_file(json_data, filename)
    
    print(f"JSON file successfully saved to: {saved_path}")