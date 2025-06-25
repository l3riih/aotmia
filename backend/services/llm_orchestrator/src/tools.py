"""Tools available to the LLM agent."""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool, tool
from pydantic import BaseModel, Field
import json


class SearchAtomsTool(BaseTool):
    """Search for learning atoms in the knowledge base."""
    
    name: str = "search_atoms"
    description: str = "Search for relevant learning atoms by topic, keywords, or difficulty level"
    
    def _run(self, query: str, difficulty: Optional[str] = None) -> str:
        """Execute atom search."""
        # TODO: Integrate with actual atom database
        return json.dumps({
            "atoms": [
                {"id": "atom_001", "title": "Introduction to concept", "difficulty": "basic"},
                {"id": "atom_002", "title": "Advanced applications", "difficulty": "advanced"}
            ]
        })
    
    async def _arun(self, query: str, difficulty: Optional[str] = None) -> str:
        """Async version."""
        return self._run(query, difficulty)


class GetUserProgressTool(BaseTool):
    """Get user's learning progress and history."""
    
    name: str = "get_user_progress"
    description: str = "Retrieve user's progress, mastery levels, and learning history"
    
    def _run(self, user_id: str, atom_id: Optional[str] = None) -> str:
        """Get user progress data."""
        # TODO: Integrate with actual user progress database
        return json.dumps({
            "user_id": user_id,
            "overall_progress": 0.65,
            "atoms_completed": 12,
            "current_streak": 5,
            "mastery_levels": {"atom_001": 0.8, "atom_002": 0.6}
        })
    
    async def _arun(self, user_id: str, atom_id: Optional[str] = None) -> str:
        """Async version."""
        return self._run(user_id, atom_id)


class GenerateQuestionInput(BaseModel):
    """Input for question generation."""
    atom_id: str = Field(description="ID of the atom to generate questions for")
    question_type: str = Field(description="Type of question: multiple_choice, true_false, short_answer")
    difficulty: str = Field(description="Difficulty level: easy, medium, hard")
    count: int = Field(default=1, description="Number of questions to generate")


@tool("generate_questions", args_schema=GenerateQuestionInput)
def generate_questions(atom_id: str, question_type: str, difficulty: str, count: int = 1) -> str:
    """Generate questions for a specific learning atom."""
    # TODO: Integrate with actual question generation service
    return json.dumps({
        "questions": [
            {
                "id": "q_001",
                "type": question_type,
                "difficulty": difficulty,
                "text": "Sample question about the atom content?",
                "options": ["A", "B", "C", "D"] if question_type == "multiple_choice" else None
            }
        ]
    })


class EvaluateAnswerInput(BaseModel):
    """Input for answer evaluation."""
    question_id: str = Field(description="ID of the question")
    user_answer: str = Field(description="User's answer to evaluate")
    correct_answer: Optional[str] = Field(None, description="Correct answer for comparison")


@tool("evaluate_answer", args_schema=EvaluateAnswerInput)
def evaluate_answer(question_id: str, user_answer: str, correct_answer: Optional[str] = None) -> str:
    """Evaluate a user's answer and provide feedback."""
    # TODO: Integrate with actual evaluation service
    return json.dumps({
        "is_correct": True,
        "score": 0.9,
        "feedback": "Great job! Your answer correctly identifies the key concept.",
        "suggestions": ["Consider also thinking about..."],
        "misconceptions": []
    })


@tool("update_learning_path")
def update_learning_path(user_id: str, performance_data: Dict[str, Any]) -> str:
    """Update user's learning path based on performance."""
    # TODO: Integrate with planning service
    return json.dumps({
        "updated": True,
        "next_atoms": ["atom_003", "atom_004"],
        "review_needed": ["atom_001"],
        "difficulty_adjustment": "increase"
    })


# Collect all tools for easy access
AVAILABLE_TOOLS = [
    SearchAtomsTool(),
    GetUserProgressTool(),
    generate_questions,
    evaluate_answer,
    update_learning_path
] 