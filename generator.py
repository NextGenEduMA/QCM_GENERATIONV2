"""
QCM generator module for Arabic text.
"""
import json
import os
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ArabicQCMGenerator:
    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo"):
        """
        Initialize the Arabic QCM generator.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: OpenAI model to use
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OpenAI API key not provided and not found in environment")
        
        openai.api_key = api_key
        self.model = model
    
    def generate_qcm(self, text_chunk: str) -> Dict[str, Any]:
        """
        Generate a QCM from a text chunk using OpenAI.
        
        Args:
            text_chunk: Text chunk to generate QCM from
            
        Returns:
            Dictionary containing the QCM
        """
        prompt = f"""النص التالي:
"{text_chunk}"

أنشئ سؤالا اختيار من متعدد (QCM) باللغة العربية حول هذا المقطع. قدم:
- السؤال
- الجواب الصحيح
- 3 خيارات غير صحيحة

النتيجة يجب أن تكون بهذا الشكل JSON:
{{
  "question": "السؤال هنا",
  "correct_answer": "الجواب الصحيح هنا",
  "choices": [
    "الخيار الأول",
    "الخيار الثاني",
    "الخيار الثالث",
    "الخيار الرابع"
  ]
}}

تأكد من أن الجواب الصحيح موجود في قائمة الخيارات، وأن الخيارات مرتبة بشكل عشوائي."""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "أنت مساعد متخصص في إنشاء أسئلة اختيار من متعدد باللغة العربية من النصوص التعليمية."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            
            # Try to parse the JSON response
            try:
                qcm = json.loads(result)
                # Ensure the correct answer is in the choices
                if qcm["correct_answer"] not in qcm["choices"]:
                    qcm["choices"].append(qcm["correct_answer"])
                return qcm
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract the QCM manually
                return self._parse_non_json_response(result)
        
        except Exception as e:
            print(f"Error generating QCM: {e}")
            return {
                "question": "حدث خطأ في إنشاء السؤال",
                "correct_answer": "غير متوفر",
                "choices": ["غير متوفر"]
            }
    
    def _parse_non_json_response(self, text: str) -> Dict[str, Any]:
        """
        Parse a non-JSON response to extract the QCM.
        
        Args:
            text: Text response from OpenAI
            
        Returns:
            Dictionary containing the QCM
        """
        lines = text.strip().split('\n')
        question = ""
        correct_answer = ""
        choices = []
        
        for line in lines:
            if line.startswith('س:') or line.startswith('السؤال:'):
                question = line.split(':', 1)[1].strip()
            elif '(صحيح)' in line:
                correct_part = line.split('(صحيح)')[0].strip()
                if '.' in correct_part or 'أ' in correct_part:
                    correct_answer = correct_part.split('.', 1)[1].strip() if '.' in correct_part else correct_part.split('أ', 1)[1].strip()
                else:
                    correct_answer = correct_part
                choices.append(correct_answer)
            elif line.startswith('أ.') or line.startswith('ب.') or line.startswith('ج.') or line.startswith('د.') or \
                 line.startswith('أ-') or line.startswith('ب-') or line.startswith('ج-') or line.startswith('د-'):
                choice = line.split('.', 1)[1].strip() if '.' in line else line.split('-', 1)[1].strip()
                choices.append(choice)
        
        return {
            "question": question,
            "correct_answer": correct_answer,
            "choices": choices
        }