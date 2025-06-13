"""
MongoDB database integration for the Arabic QCM Generator.
"""
import os
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from bson import ObjectId
from models import Text, QCM

# Initialize MongoDB client
client = MongoClient("mongodb://localhost:27017/")
db = client["gen_qcm"]
texts_collection = db["gen_qcm"]  # Use the students collection as specified
counter_collection = db["counters"]

# Initialize counter if it doesn't exist
if "text_id" not in counter_collection.find_one({"_id": "counters"}, {"_id": 0}) if counter_collection.find_one({"_id": "counters"}) else {}:
    counter_collection.update_one(
        {"_id": "counters"},
        {"$set": {"text_id": 0}},
        upsert=True
    )

def get_next_text_id() -> int:
    """Get the next sequential text ID and increment the counter."""
    result = counter_collection.find_one_and_update(
        {"_id": "counters"},
        {"$inc": {"text_id": 1}},
        return_document=True,
        upsert=True
    )
    return result["text_id"]

def save_text_with_qcms(text_content: str, level: int, difficulty: str, qcms: List[Dict[str, Any]]) -> str:
    """
    Save a text with its QCMs to MongoDB.
    
    Args:
        text_content: The content of the text
        level: The level of the text (1-6)
        difficulty: The difficulty of the text (easy, medium, hard)
        qcms: List of QCMs generated from the text
    
    Returns:
        The ID of the saved text
    """
    # Get the next sequential ID
    text_id = get_next_text_id()
    
    # Format QCMs to match our schema
    formatted_qcms = []
    for qcm in qcms:
        # Extract the correct answer and wrong answers
        correct_answer = qcm["correct_answer"]
        wrong_answers = [choice for choice in qcm["choices"] if choice != correct_answer]
        
        # Ensure we have exactly 3 wrong answers
        while len(wrong_answers) < 3:
            wrong_answers.append("لا إجابة")
        
        # Create QCM object
        formatted_qcm = {
            "question": qcm["question"],
            "correct_answer": correct_answer,
            "wrong_answer1": wrong_answers[0],
            "wrong_answer2": wrong_answers[1] if len(wrong_answers) > 1 else "لا إجابة",
            "wrong_answer3": wrong_answers[2] if len(wrong_answers) > 2 else "لا إجابة"
        }
        formatted_qcms.append(formatted_qcm)
    
    # Create text document
    text_doc = {
        "_id": text_id,
        "content": text_content,
        "level": level,
        "difficulty": difficulty,
        "qcms": formatted_qcms
    }
    
    # Insert into MongoDB
    texts_collection.insert_one(text_doc)
    
    # Return the ID
    return str(text_id)

def save_text_to_json(text_id: str, output_path: Optional[str] = None) -> str:
    """
    Save a text and its QCMs to a JSON file.
    
    Args:
        text_id: The ID of the text in MongoDB
        output_path: Optional path to save the JSON file
    
    Returns:
        The path to the saved JSON file
    """
    import json
    
    # Get the text from MongoDB
    text_doc = texts_collection.find_one({"_id": int(text_id)})
    if not text_doc:
        raise ValueError(f"Text with ID {text_id} not found")
    
    # Ensure Saved_qcms directory exists
    os.makedirs("Saved_qcms", exist_ok=True)
    
    # Generate output path if not provided
    if not output_path:
        output_path = f"text_{text_id}.json"
    
    # Add directory prefix to path if not already specified
    if not output_path.startswith("Saved_qcms/"):
        output_path = f"Saved_qcms/{output_path}"
    
    # Save to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(text_doc, f, ensure_ascii=False, indent=2)
    
    return output_path

def get_all_texts() -> List[Dict[str, Any]]:
    """Get all texts from MongoDB."""
    texts = list(texts_collection.find())
    return texts

def get_text_by_id(text_id: str) -> Dict[str, Any]:
    """Get a text by its ID."""
    text = texts_collection.find_one({"_id": int(text_id)})
    if not text:
        raise ValueError(f"Text with ID {text_id} not found")
    return text

def import_text_from_json(json_path: str) -> str:
    """
    Import a text from a JSON file into MongoDB.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        The ID of the imported text
    """
    import json
    
    # Read the JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract text content, level, difficulty, and questions
    text_content = data.get("text_content", "")
    level = data.get("level", 1)
    difficulty = data.get("difficulty", "medium")
    questions = data.get("questions", [])
    
    # Save to MongoDB
    return save_text_with_qcms(text_content, level, difficulty, questions)