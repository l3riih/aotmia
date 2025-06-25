from enum import Enum


class TaskType(str, Enum):
    """Types of tasks the LLM orchestrator can handle."""
    
    # Content processing tasks
    ATOMIZATION = "atomization"
    CONTENT_EXPLANATION = "content_explanation"
    CONTENT_SUMMARIZATION = "content_summarization"
    
    # Question & assessment tasks
    QUESTION_GENERATION = "question_generation"
    ANSWER_EVALUATION = "answer_evaluation"
    FEEDBACK_GENERATION = "feedback_generation"
    
    # Learning path tasks
    LEARNING_PLANNING = "learning_planning"
    PROGRESS_ANALYSIS = "progress_analysis"
    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"
    
    # Conversational tasks
    TUTORING_DIALOGUE = "tutoring_dialogue"
    CONCEPT_CLARIFICATION = "concept_clarification"
    MOTIVATION_MESSAGE = "motivation_message"
    
    # Agent meta-tasks
    TASK_PLANNING = "task_planning"
    SELF_REFLECTION = "self_reflection"
    ERROR_RECOVERY = "error_recovery" 