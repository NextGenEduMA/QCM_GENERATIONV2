"""
Data models for the Arabic QCM Generator.
"""
from typing import List, Dict, Any, Optional, Literal
from enum import IntEnum, Enum
from pydantic import BaseModel, Field

class QCM(BaseModel):
    """QCM model representing a multiple choice question."""
    question: str
    correct_answer: str
    wrong_answer1: str
    wrong_answer2: str
    wrong_answer3: str

class TextLevel(IntEnum):
    """Enumeration of text levels."""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6

class TextDifficulty(str, Enum):
    """Enumeration of text difficulties."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Text(BaseModel):
    """Text model representing an uploaded text with its QCMs."""
    id: Optional[str] = None
    content: str
    level: int = Field(..., ge=1, le=6)
    difficulty: Literal["easy", "medium", "hard"]
    qcms: List[QCM] = []