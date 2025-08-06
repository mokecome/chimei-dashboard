"""
AI processing module for speech-to-text and content analysis.
"""
from .llm_analyzer import analyze_feedback
from .speech_to_text import SpeechService, speech_service

__all__ = [
    "analyze_feedback",
    "SpeechService", 
    "speech_service"
]