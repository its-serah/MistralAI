"""Content filtering and guardrails for LLM interactions"""

import re
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


class ContentFilter:
    """Content filter with safety guardrails for LLM interactions"""
    
    def __init__(self):
        self.setup_filters()
    
    def setup_filters(self):
        """Setup content filtering patterns and rules"""
        
        # Inappropriate content patterns (basic filtering)
        self.inappropriate_patterns = [
            r'\b(?:hate|violence|harmful|illegal|dangerous)\b',
            r'\b(?:attack|harm|hurt|kill|destroy)\b',
            r'\b(?:personal\s+information|private\s+data|ssn|credit\s+card)\b',
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.inappropriate_patterns
        ]
        
        # Topics we want to keep focused on audio analysis
        self.allowed_topics = {
            'audio', 'spectrogram', 'frequency', 'sound', 'music', 'acoustic',
            'signal', 'processing', 'analysis', 'waveform', 'amplitude',
            'decibel', 'hertz', 'pitch', 'tone', 'harmony', 'rhythm',
            'tempo', 'beat', 'melody', 'voice', 'speech', 'recording'
        }
        
        # System prompts for focused responses
        self.system_context = """
        You are an audio analysis assistant. Your responses should be:
        1. Focused on audio, music, and sound analysis topics
        2. Educational and informative
        3. Professional and appropriate
        4. Clear and accessible to users with varying technical backgrounds
        
        Avoid discussing unrelated topics and maintain focus on audio analysis.
        """
    
    def is_safe_content(self, content: str) -> bool:
        """
        Check if content is safe and appropriate
        
        Args:
            content: Content to check
            
        Returns:
            True if content is safe, False otherwise
        """
        if not content or not content.strip():
            return True
        
        content_lower = content.lower()
        
        # Check for inappropriate patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content_lower):
                logger.warning(f"Content failed safety check: inappropriate pattern detected")
                return False
        
        # Check for extremely long content that might be spam
        if len(content) > 5000:
            logger.warning("Content failed safety check: too long")
            return False
        
        # Check for repetitive content (potential spam)
        words = content_lower.split()
        if len(words) > 10:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
                logger.warning("Content failed safety check: too repetitive")
                return False
        
        return True
    
    def filter_content(self, content: str) -> str:
        """
        Filter and clean content
        
        Args:
            content: Content to filter
            
        Returns:
            Filtered content
        """
        if not content:
            return content
        
        # Remove potential sensitive data patterns
        filtered = self._remove_sensitive_data(content)
        
        # Clean up formatting
        filtered = self._clean_formatting(filtered)
        
        # Ensure content stays on topic (basic check)
        if not self._is_on_topic(filtered):
            logger.info("Content appears off-topic, adding context note")
            filtered = self._add_topic_redirect(filtered)
        
        return filtered
    
    def _remove_sensitive_data(self, content: str) -> str:
        """Remove potential sensitive data patterns"""
        
        # Remove potential email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                        '[EMAIL_REMOVED]', content)
        
        # Remove potential phone numbers
        content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 
                        '[PHONE_REMOVED]', content)
        
        # Remove potential URLs (keep only safe domains)
        content = re.sub(r'https?://(?!(?:wikipedia|github|docs\.python|librosa))[^\s]+', 
                        '[URL_REMOVED]', content)
        
        return content
    
    def _clean_formatting(self, content: str) -> str:
        """Clean up content formatting"""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove excessive punctuation
        content = re.sub(r'[!?]{3,}', '!', content)
        content = re.sub(r'\.{4,}', '...', content)
        
        # Clean up line breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _is_on_topic(self, content: str) -> bool:
        """Check if content is related to audio analysis"""
        content_lower = content.lower()
        words = set(re.findall(r'\b\w+\b', content_lower))
        
        # Check if any audio-related terms are present
        audio_terms_found = words.intersection(self.allowed_topics)
        
        # If it's a short response and has at least one audio term, consider it on-topic
        if len(content) < 200 and len(audio_terms_found) > 0:
            return True
        
        # For longer content, require more audio-related terms
        if len(content) >= 200:
            return len(audio_terms_found) >= 2
        
        # If no audio terms but short and seems like acknowledgment, allow it
        short_responses = {'ok', 'yes', 'no', 'hello', 'thanks', 'thank you'}
        if len(words) <= 3 and any(word in short_responses for word in words):
            return True
        
        return len(audio_terms_found) > 0
    
    def _add_topic_redirect(self, content: str) -> str:
        """Add a note to redirect conversation back to audio topics"""
        redirect_note = (
            "\n\n[Note: I focus on audio analysis topics. "
            "If you have questions about spectrograms, audio features, "
            "or sound analysis, I'd be happy to help!]"
        )
        
        return content + redirect_note
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for maintaining conversation focus"""
        return self.system_context
    
    def validate_question(self, question: str) -> Dict[str, any]:
        """
        Validate a user question before sending to LLM
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with validation result and potentially modified question
        """
        if not self.is_safe_content(question):
            return {
                'is_valid': False,
                'reason': 'Question contains inappropriate content',
                'modified_question': None
            }
        
        # Clean the question
        cleaned_question = self.filter_content(question)
        
        # If question is completely off-topic, suggest alternatives
        if not self._is_on_topic(cleaned_question):
            return {
                'is_valid': True,
                'reason': 'Question is off-topic but allowed',
                'modified_question': (
                    cleaned_question + 
                    " (Please provide an audio analysis perspective if possible.)"
                )
            }
        
        return {
            'is_valid': True,
            'reason': 'Question passed all checks',
            'modified_question': cleaned_question if cleaned_question != question else None
        }
