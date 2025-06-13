"""
Arabic QCM Generator with Diacritics using RAG and OpenAI.
"""
import os
import re
import json
import argparse
import sys
from typing import List, Dict, Any
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import faiss

# Set console encoding to UTF-8 for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

class ArabicDiacritizedQCMGenerator:
    def __init__(self, training_pdf_path: str = None):
        """
        Initialize the Arabic QCM generator with diacritics.
        """
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Default model
        
        # Initialize vector database
        self.index = None
        self.chunks = []
        self.embeddings = None
        
        # Load training data if provided
        if training_pdf_path and os.path.exists(training_pdf_path):
            self.load_training_data(training_pdf_path)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        text = ""
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean the input text by removing extra whitespaces."""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def create_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """Create chunks from the input text with larger chunk size for Arabic."""
        # Clean the text first
        text = self.clean_text(text)
        
        # Split into paragraphs
        paragraphs = text.split('\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If paragraph itself is too long, split it into sentences
            if len(paragraph) > chunk_size:
                # Use Arabic-specific sentence splitting
                sentences = re.split(r'[.!?؟،]', paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    # If adding this sentence would exceed chunk size, save current chunk and start a new one
                    if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                # Try to keep semantic units together
                # If adding this paragraph would exceed chunk size, save current chunk and start a new one
                if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    current_chunk += " " + paragraph if current_chunk else paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Ensure chunks have some overlap for context continuity
        if len(chunks) > 1:
            for i in range(1, len(chunks)):
                # Add a bit of the previous chunk to the current one for context
                words = chunks[i-1].split()
                if len(words) > 10:  # If previous chunk has enough words
                    overlap = " ".join(words[-10:])
                    chunks[i] = overlap + " " + chunks[i]
        
        return chunks
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a text using the OpenAI embeddings."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            print(f"Error embedding text: {e}")
            # Return a zero vector as fallback
            return np.zeros(1536)  # Ada-002 embedding size
    
    def load_training_data(self, pdf_path: str) -> None:
        """Load and index training data from a PDF."""
        print(f"Loading training data from {pdf_path}...")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        # Create chunks
        self.chunks = self.create_chunks(text)
        print(f"Created {len(self.chunks)} chunks from training data")
        
        # Embed chunks
        print("Embedding chunks...")
        self.embeddings = np.zeros((len(self.chunks), 1536))
        for i, chunk in enumerate(self.chunks):
            self.embeddings[i] = self.embed_text(chunk)
            if (i + 1) % 10 == 0:
                print(f"Embedded {i + 1}/{len(self.chunks)} chunks")
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(1536)
        self.index.add(self.embeddings.astype('float32'))
        print("Training data indexed successfully")
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 8) -> List[str]:
        """Retrieve relevant chunks for a query with improved selection."""
        if self.index is None or len(self.chunks) == 0:
            print("No training data loaded. Using only the query.")
            return [query]
        
        # Enhance query for better retrieval
        enhanced_query = f"معلومات عن: {query}"
        
        # Embed the query
        query_embedding = self.embed_text(enhanced_query)
        
        # Search the index
        k = min(top_k, len(self.chunks))
        distances, indices = self.index.search(query_embedding.reshape(1, -1).astype('float32'), k)
        
        # Get the relevant chunks
        relevant_chunks = [self.chunks[idx] for idx in indices[0]]
        
        # Print detailed debugging information
        print(f"\n=== RAG Retrieval Debug ===")
        print(f"Query: {query}")
        print(f"Retrieved {len(relevant_chunks)} chunks")
        for i, (chunk, idx, dist) in enumerate(zip(relevant_chunks, indices[0], distances[0])):
            print(f"\nChunk {i+1} (index {idx}, distance {dist:.4f}):")
            print(f"{chunk[:150]}...")
        print("===========================\n")
        
        # Filter out very dissimilar chunks (high distance)
        if len(distances[0]) > 0:
            threshold = distances[0][0] * 2.5  # Dynamic threshold based on best match
            filtered_chunks = [chunk for chunk, dist in zip(relevant_chunks, distances[0]) if dist < threshold]
            if filtered_chunks:
                relevant_chunks = filtered_chunks
        
        return relevant_chunks
    
    def generate_diacritized_qcm(self, text: str, num_questions: int = 3, direct_text: bool = False) -> List[Dict[str, Any]]:
        """Generate diacritized QCMs from a text."""
        # Check if this is a direct text query with specific instructions
        if text.startswith("أنشئ أسئلة اختيار من متعدد فقط عن النص التالي:"):
            direct_text = True
            # Extract the actual text from the instruction
            start_idx = text.find("\n\n") + 2
            end_idx = text.find("\n\nلا تستخدم")
            if start_idx > 1 and end_idx > start_idx:
                content_text = text[start_idx:end_idx].strip()
            else:
                content_text = text
                
            # Use the content directly without retrieval
            context = content_text
        else:
            # Retrieve relevant chunks
            relevant_chunks = self.retrieve_relevant_chunks(text, top_k=8)
            
            # Combine relevant chunks for context
            context = "\n\n".join(relevant_chunks)
        
        # Create prompt
        prompt = f"""
أنشئ {num_questions} أسئلة اختيار من متعدد باللغة العربية استنادًا فقط إلى النص التالي:

{context}

يجب أن تكون الأسئلة والإجابات مشكّلة بالكامل (مع جميع علامات التشكيل).
استخدم المعلومات الموجودة في النص فقط لإنشاء الأسئلة والإجابات.
لا تستخدم أي معلومات خارجية أو معرفة عامة غير موجودة في النص.
لكل سؤال، قدم إجابة صحيحة واحدة و3 إجابات خاطئة.

أريد النتيجة بالضبط بهذا الشكل JSON (بدون أي نص إضافي قبل أو بعد):
[
  {{
    "question": "السُّؤَالُ الْمُشَكَّلُ هُنَا بِالْكَامِلِ؟",
    "correct_answer": "الْإِجَابَةُ الصَّحِيحَةُ الْمُشَكَّلَةُ بِالْكَامِلِ",
    "choices": [
      "الْخِيَارُ الْأَوَّلُ الْمُشَكَّلُ بِالْكَامِلِ",
      "الْخِيَارُ الثَّانِي الْمُشَكَّلُ بِالْكَامِلِ",
      "الْخِيَارُ الثَّالِثُ الْمُشَكَّلُ بِالْكَامِلِ",
      "الْخِيَارُ الرَّابِعُ الْمُشَكَّلُ بِالْكَامِلِ"
    ]
  }}
]

تأكد من وضع جميع علامات التشكيل (الفتحة، الضمة، الكسرة، السكون، الشدة، التنوين) على كل حرف في الأسئلة والإجابات.
تأكد من أن الإجابة الصحيحة موجودة في قائمة الخيارات، وأن الخيارات مرتبة بشكل عشوائي.
تأكد من أن جميع الأسئلة والإجابات مستندة فقط إلى المعلومات الموجودة في النص المقدم.
"""

        try:
            print(f"Sending request to OpenAI using model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "أنت مساعد متخصص في إنشاء أسئلة اختيار من متعدد باللغة العربية مع التشكيل الكامل من النصوص التعليمية. استخدم فقط المعلومات الموجودة في النص المقدم. ضع علامات التشكيل الكاملة على كل حرف. أعطِ الإجابة بتنسيق JSON فقط."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            print(f"Received response from OpenAI")
            
            # Try to parse the JSON response
            try:
                # Clean the response to ensure it's valid JSON
                result = result.strip()
                if result.startswith('```json'):
                    result = result[7:]
                if result.endswith('```'):
                    result = result[:-3]
                
                result_json = json.loads(result)
                
                # Handle both direct array and object with questions array
                if isinstance(result_json, list):
                    qcms = result_json
                elif isinstance(result_json, dict) and "questions" in result_json:
                    qcms = result_json["questions"]
                else:
                    qcms = [result_json]
                
                # Ensure each QCM has the correct format
                for qcm in qcms:
                    # Ensure the correct answer is in the choices
                    if "correct_answer" in qcm and "choices" in qcm:
                        if qcm["correct_answer"] not in qcm["choices"]:
                            qcm["choices"].append(qcm["correct_answer"])
                
                return qcms
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}. Trying to extract QCMs manually.")
                # If JSON parsing fails, try to extract the QCMs manually
                return self._parse_non_json_response(result, num_questions)
        
        except Exception as e:
            print(f"Error generating QCMs: {str(e)}")
            return [{"question": "حدث خطأ في إنشاء السؤال", "correct_answer": "غير متوفر", "choices": ["غير متوفر"]}]
    
    def _parse_non_json_response(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Parse a non-JSON response to extract QCMs."""
        qcms = []
        
        # Try to find JSON-like structures in the text
        json_pattern = r'\{\s*"question":\s*"([^"]+)",\s*"correct_answer":\s*"([^"]+)",\s*"choices":\s*\[(.*?)\]\s*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            question = match[0]
            correct_answer = match[1]
            choices_text = match[2]
            
            # Extract choices
            choices = []
            choice_matches = re.findall(r'"([^"]+)"', choices_text)
            for choice in choice_matches:
                choices.append(choice)
            
            if question and choices:
                qcm = {
                    "question": question,
                    "correct_answer": correct_answer,
                    "choices": choices
                }
                
                # Ensure correct answer is in choices
                if correct_answer and correct_answer not in choices:
                    qcm["choices"].append(correct_answer)
                
                qcms.append(qcm)
        
        # If no JSON-like structures found, try to extract questions and answers directly
        if not qcms:
            # Split by question patterns
            question_blocks = re.split(r'السؤال \d+:|سؤال \d+:|Question \d+:', text)
            
            for block in question_blocks:
                if not block.strip():
                    continue
                    
                qcm = {"question": "", "correct_answer": "", "choices": []}
                
                # Extract question
                question_match = re.search(r'([^؟\n]+\؟)', block)
                if question_match:
                    qcm["question"] = question_match.group(1).strip()
                
                # Extract correct answer
                correct_match = re.search(r'الإجابة الصحيحة:([^\n]+)', block) or re.search(r'الجواب الصحيح:([^\n]+)', block)
                if correct_match:
                    qcm["correct_answer"] = correct_match.group(1).strip()
                
                # Extract choices
                choices = []
                choice_matches = re.findall(r'[أ-د]\) ([^\n]+)', block) or re.findall(r'[أ-د]\. ([^\n]+)', block)
                for choice in choice_matches:
                    choices.append(choice.strip())
                
                if choices:
                    qcm["choices"] = choices
                    
                    # Ensure correct answer is in choices
                    if qcm["correct_answer"] and qcm["correct_answer"] not in qcm["choices"]:
                        qcm["choices"].append(qcm["correct_answer"])
                
                if qcm["question"]:
                    qcms.append(qcm)
                    
                # Limit to requested number of questions
                if len(qcms) >= num_questions:
                    break
        
        # If no questions were extracted, create a placeholder
        if not qcms:
            qcms = [{"question": "تعذر استخراج الأسئلة من الاستجابة", "correct_answer": "غير متوفر", "choices": ["غير متوفر"]}]
        
        return qcms
    
    def process_text(self, text: str, output_path: str, num_questions: int = 3) -> None:
        """Process a text and generate QCMs."""
        print(f"Processing input text ({len(text)} characters)...")
        
        # Generate QCMs
        qcms = self.generate_diacritized_qcm(text, num_questions)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Save QCMs
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(qcms, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(qcms)} QCMs to {output_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Arabic Diacritized QCM Generator')
    parser.add_argument('--input', '-i', required=True, help='Path to the input text file')
    parser.add_argument('--output', '-o', default='diacritized_qcms.json', help='Path to save the output QCMs')
    parser.add_argument('--training', '-t', help='Path to the training PDF file')
    parser.add_argument('--num-questions', '-n', type=int, default=3, help='Number of questions to generate')
    parser.add_argument('--model', '-m', default='gpt-4o-mini', help='OpenAI model to use')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = ArabicDiacritizedQCMGenerator(args.training)
    
    # Set model if provided
    if args.model:
        generator.model = args.model
    
    # Read input text
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Process text
    generator.process_text(text, args.output, args.num_questions)

if __name__ == '__main__':
    main()