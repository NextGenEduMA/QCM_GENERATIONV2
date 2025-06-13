"""
Simple FastAPI web application for Arabic QCM Generator.
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Import the QCM generator
from arabic_diacritized_qcm_v3 import ArabicDiacritizedQCMGenerator
from db import save_text_with_qcms, save_text_to_json, get_all_texts, get_text_by_id
from models import Text, QCM

# Initialize FastAPI app
app = FastAPI(title="Arabic QCM Generator")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Initialize QCM generator
generator = ArabicDiacritizedQCMGenerator()

# Store background tasks
background_tasks = {}

# Define models
class QCMRequest(BaseModel):
    text: str
    num_questions: int = 3
    model: str = "gpt-4o-mini"
    document_path: Optional[str] = None
    selected_paragraphs: Optional[List[int]] = None
    level: Optional[int] = 1
    difficulty: Optional[str] = "medium"

class TextRequest(BaseModel):
    text: str

class SaveQCMRequest(BaseModel):
    questions: List[Dict[str, Any]]
    text_content: str
    level: int = 1
    difficulty: str = "medium"

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_qcms(request: QCMRequest, background_tasks: BackgroundTasks):
    """Generate QCMs from text."""
    # Generate a unique task ID
    task_id = os.urandom(8).hex()
    
    # Start the generation task in the background
    background_tasks.add_task(
        generate_qcms_task, 
        task_id, 
        request.text, 
        request.num_questions, 
        request.model,
        request.document_path,
        request.selected_paragraphs,
        request.level,
        request.difficulty
    )
    
    return {"task_id": task_id, "status": "processing"}

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a generation task."""
    if task_id not in background_tasks:
        return {"status": "not_found"}
    
    status = background_tasks[task_id]["status"]
    
    if status == "completed":
        questions = background_tasks[task_id]["questions"]
        return {"status": status, "questions": questions}
    elif status == "error":
        error = background_tasks[task_id]["error"]
        return {"status": status, "error": error}
    else:
        return {"status": status}

@app.post("/extract-paragraphs", response_class=JSONResponse)
async def extract_paragraphs(request: TextRequest):
    """Extract paragraphs from text."""
    try:
        raw_text = request.text
        if not raw_text:
            return {"success": False, "message": "No text provided"}
        
        # Split text into paragraphs using Arabic punctuation
        paragraphs = []
        current_paragraph = ""
        
        for char in raw_text:
            current_paragraph += char
            # Arabic full stop (.) and comma (،) as delimiters
            if char in [".", "،", "؟", "!"]:
                if current_paragraph.strip():
                    paragraphs.append(current_paragraph.strip())
                current_paragraph = ""
        
        # Add the last paragraph if it's not empty
        if current_paragraph.strip():
            paragraphs.append(current_paragraph.strip())
        
        return {"success": True, "paragraphs": paragraphs}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file for training."""
    try:
        # Save the uploaded file
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Load the training data
        generator.load_training_data(file_path)
        
        # Print confirmation message
        print(f"PDF file uploaded and processed: {file.filename}")
        print("PDF content indexed for RAG-based question generation")
        
        return {"success": True, "message": "PDF uploaded successfully. The system will use RAG to generate questions based on this document."}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/save-question", response_class=JSONResponse)
async def save_question(question: dict):
    """Save a single question to JSON."""
    try:
        # Save to JSON file
        timestamp = int(time.time())
        json_filename = f"question_{timestamp}.json"
        
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(question, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": f"Question saved to {json_filename}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/save-qcm-set", response_class=JSONResponse)
async def save_qcm_set(request: SaveQCMRequest):
    """Save a set of QCMs to MongoDB and JSON file."""
    try:
        # Ensure Saved_qcms directory exists
        os.makedirs("Saved_qcms", exist_ok=True)
        
        # Save to MongoDB
        text_id = save_text_with_qcms(
            request.text_content,
            request.level,
            request.difficulty,
            request.questions
        )
        
        # Save to JSON file
        json_filename = f"text_{text_id}.json"
        full_path = save_text_to_json(text_id, json_filename)
        
        return {
            "success": True, 
            "message": f"QCM set saved to MongoDB and {full_path}",
            "text_id": text_id,
            "file": json_filename
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/texts", response_class=JSONResponse)
async def list_texts():
    """List all texts in the database."""
    try:
        texts = get_all_texts()
        return {"success": True, "texts": texts}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/texts/{text_id}", response_class=JSONResponse)
async def get_text(text_id: str):
    """Get a text by its ID."""
    try:
        text = get_text_by_id(text_id)
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "message": str(e)}

def generate_qcms_task(task_id: str, text: str, num_questions: int, model: str, 
                       document_path: Optional[str] = None, selected_paragraphs: Optional[List[int]] = None,
                       level: int = 1, difficulty: str = "medium"):
    """Background task to generate QCMs."""
    import time
    
    # Store task info
    background_tasks[task_id] = {
        "status": "processing",
        "timestamp": time.time()
    }
    
    try:
        # Set the model (always use gpt-4o-mini as requested)
        generator.model = "gpt-4o-mini"
        
        # Process selected paragraphs
        if selected_paragraphs and isinstance(selected_paragraphs, list):
            paragraphs = []
            # Split text into paragraphs
            all_paragraphs = []
            current_paragraph = ""
            
            for char in text:
                current_paragraph += char
                if char in [".", "،", "؟", "!"]:
                    if current_paragraph.strip():
                        all_paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
            
            if current_paragraph.strip():
                all_paragraphs.append(current_paragraph.strip())
            
            # Get selected paragraphs
            for idx in selected_paragraphs:
                if 0 <= idx < len(all_paragraphs):
                    paragraphs.append(all_paragraphs[idx])
            
            # Join selected paragraphs
            if paragraphs:
                text = " ".join(paragraphs)
            else:
                # If no paragraphs were selected, use the first paragraph
                text = all_paragraphs[0] if all_paragraphs else text
        
        # Generate QCMs using RAG (Retrieval Augmented Generation)
        # Setting direct_text=False to use RAG with the uploaded PDF
        qcms = generator.generate_diacritized_qcm(text, num_questions, direct_text=False)
        print(f"Generating {num_questions} QCMs using RAG with query: {text[:100]}...")
        
        # Improve each generated QCM
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client = OpenAI(api_key=api_key)
                
                improved_qcms = []
                for qcm in qcms:
                    # Create prompt for improvement
                    prompt = f"""
أنا بحاجة إلى تحسين سؤال اختيار من متعدد (QCM) بناءً على النص التالي:

النص:
{text}

السؤال الحالي:
{qcm["question"]}

الإجابة الصحيحة:
{qcm["correct_answer"]}

الخيارات:
{", ".join(qcm["choices"])}

يرجى تحسين السؤال والإجابات مع مراعاة ما يلي:
1. تأكد من أن السؤال والإجابات مرتبطة بالنص المقدم فقط.
2. تأكد من التشكيل الكامل لجميع الكلمات.
3. تأكد من صحة اللغة والنحو.
4. تأكد من أن الضمائر والسياق متناسقة.
5. تأكد من أن الإجابة الصحيحة واضحة وغير ملتبسة.
6. تأكد من أن الخيارات الخاطئة معقولة ولكن غير صحيحة بوضوح.

أعطني السؤال المحسن بتنسيق JSON كما يلي:
{
  "question": "السؤال المحسن مع التشكيل الكامل",
  "correct_answer": "الإجابة الصحيحة المحسنة مع التشكيل الكامل",
  "choices": [
    "الخيار الأول",
    "الخيار الثاني",
    "الخيار الثالث",
    "الخيار الرابع"
  ]
}

تأكد من أن الإجابة الصحيحة موجودة في قائمة الخيارات.
"""
                    
                    # Call OpenAI API
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "أنت مساعد متخصص في تحسين أسئلة الاختيار من متعدد باللغة العربية مع التشكيل الكامل."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000,
                        response_format={"type": "json_object"}
                    )
                    
                    # Parse response
                    import json
                    result = response.choices[0].message.content
                    improved_qcm = json.loads(result)
                    
                    # Ensure the correct answer is in the choices
                    if improved_qcm["correct_answer"] not in improved_qcm["choices"]:
                        improved_qcm["choices"].append(improved_qcm["correct_answer"])
                    
                    improved_qcms.append(improved_qcm)
                
                # Use improved QCMs if available
                if improved_qcms:
                    qcms = improved_qcms
        except Exception as e:
            print(f"Error improving QCMs: {e}")
        
        # Store the result
        background_tasks[task_id] = {
            "status": "completed",
            "questions": qcms,
            "text_content": text,
            "level": level,
            "difficulty": difficulty,
            "timestamp": time.time()
        }
    except Exception as e:
        # Store the error
        background_tasks[task_id] = {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

@app.post("/improve-question", response_class=JSONResponse)
async def improve_question(request: dict):
    """Improve a single question using GPT-4o Mini."""
    try:
        text = request.get("text", "")
        question = request.get("question", {})
        
        if not text or not question:
            return {"success": False, "message": "Missing text or question"}
        
        # Create prompt for improvement
        prompt = f"""
أنا بحاجة إلى تحسين سؤال اختيار من متعدد (QCM) بناءً على النص التالي:

النص:
{text}

السؤال الحالي:
{question["question"]}

الإجابة الصحيحة:
{question["correct_answer"]}

الخيارات:
{", ".join(question["choices"])}

يرجى تحسين السؤال والإجابات مع مراعاة ما يلي:
1. تأكد من أن السؤال والإجابات مرتبطة بالنص المقدم فقط.
2. تأكد من التشكيل الكامل لجميع الكلمات.
3. تأكد من صحة اللغة والنحو.
4. تأكد من أن الضمائر والسياق متناسقة.
5. تأكد من أن الإجابة الصحيحة واضحة وغير ملتبسة.
6. تأكد من أن الخيارات الخاطئة معقولة ولكن غير صحيحة بوضوح.

أعطني السؤال المحسن بتنسيق JSON كما يلي:
{
  "question": "السؤال المحسن مع التشكيل الكامل",
  "correct_answer": "الإجابة الصحيحة المحسنة مع التشكيل الكامل",
  "choices": [
    "الخيار الأول",
    "الخيار الثاني",
    "الخيار الثالث",
    "الخيار الرابع"
  ]
}

تأكد من أن الإجابة الصحيحة موجودة في قائمة الخيارات.
"""
        
        # Call OpenAI API
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"success": False, "message": "OpenAI API key not found"}
        
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد متخصص في تحسين أسئلة الاختيار من متعدد باللغة العربية مع التشكيل الكامل."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result = response.choices[0].message.content
        import json
        improved_question = json.loads(result)
        
        # Ensure the correct answer is in the choices
        if improved_question["correct_answer"] not in improved_question["choices"]:
            improved_question["choices"].append(improved_question["correct_answer"])
        
        return {
            "success": True,
            "improved_question": improved_question
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("simple_app:app", host="127.0.0.1", port=8000)