"""Interactive chat service with guardrails for audio analysis discussions"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core import MistralClient
from ..config import get_settings
from ..utils.guardrails import ContentFilter

logger = logging.getLogger(__name__)


class ChatService:
    """Interactive chat service focused on audio analysis with conversation management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.mistral_client = MistralClient()
        self.content_filter = ContentFilter()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Keep last 10 exchanges
    
    def start_conversation(self) -> Dict[str, Any]:
        """
        Start a new conversation session
        
        Returns:
            Dictionary containing session information
        """
        self.conversation_history = []
        
        welcome_message = (
            "Hello! I'm your audio analysis assistant. I can help you understand "
            "audio files, spectrograms, and various audio processing concepts. "
            "\\n\\nWhat would you like to know about audio analysis today?"
        )
        
        return {
            'success': True,
            'message': welcome_message,
            'session_started': datetime.now().isoformat(),
            'capabilities': [
                'Audio file analysis and spectrogram generation',
                'Explanation of audio features and characteristics',
                'Discussion of audio processing concepts',
                'Spectrogram interpretation',
                'Audio format and technical questions'
            ]
        }
    
    def send_message(self, user_message: str, context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a message to the chat service
        
        Args:
            user_message: The user's message
            context_data: Optional context data (audio features, file info, etc.)
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Validate and filter the user message
            validation_result = self.content_filter.validate_question(user_message)
            
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'error': validation_result['reason'],
                    'user_message': user_message,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Use the modified question if available
            processed_message = validation_result.get('modified_question', user_message)
            
            # Build conversation context
            messages = self._build_conversation_context(processed_message, context_data)
            
            # Get response from Mistral
            response = self.mistral_client.chat_completion(messages)
            
            if response['success']:
                # Update conversation history
                self._update_conversation_history(user_message, response['content'])
                
                return {
                    'success': True,
                    'user_message': user_message,
                    'ai_response': response['content'],
                    'model_used': response.get('model'),
                    'usage': response.get('usage', {}),
                    'timestamp': datetime.now().isoformat(),
                    'conversation_length': len(self.conversation_history)
                }
            else:
                return {
                    'success': False,
                    'error': response['error'],
                    'user_message': user_message,
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Chat service error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_message': user_message,
                'timestamp': datetime.now().isoformat()
            }
    
    def ask_about_audio(self, question: str, audio_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ask a question about specific audio analysis results
        
        Args:
            question: The question about the audio
            audio_features: Audio features from analysis
            
        Returns:
            Dictionary containing the response
        """
        context_data = {
            'type': 'audio_analysis',
            'features': audio_features,
            'context_note': 'User is asking about a specific audio file they analyzed.'
        }
        
        return self.send_message(question, context_data)
    
    def explain_concept(self, concept: str) -> Dict[str, Any]:
        """
        Get an explanation of an audio analysis concept
        
        Args:
            concept: The concept to explain
            
        Returns:
            Dictionary containing the explanation
        """
        question = f"Please explain the audio analysis concept: {concept}"
        
        context_data = {
            'type': 'concept_explanation',
            'context_note': 'User wants to understand an audio analysis concept.'
        }
        
        return self.send_message(question, context_data)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation
        
        Returns:
            Dictionary containing conversation summary
        """
        if not self.conversation_history:
            return {
                'success': True,
                'message': 'No conversation history available.',
                'exchanges': 0
            }
        
        try:
            # Create a summary prompt
            history_text = self._format_history_for_summary()
            
            summary_prompt = (
                "Please provide a brief summary of our conversation about audio analysis. "
                f"Here's our conversation:\\n\\n{history_text}\\n\\n"
                "Focus on the key topics discussed and main insights shared."
            )
            
            response = self.mistral_client.ask_question(summary_prompt)
            
            return {
                'success': response['success'],
                'summary': response.get('content', 'Could not generate summary.'),
                'exchanges': len(self.conversation_history),
                'error': response.get('error') if not response['success'] else None
            }
        
        except Exception as e:
            logger.error(f"Error generating conversation summary: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'exchanges': len(self.conversation_history)
            }
    
    def clear_conversation(self) -> Dict[str, Any]:
        """
        Clear the conversation history
        
        Returns:
            Dictionary containing confirmation
        """
        previous_length = len(self.conversation_history)
        self.conversation_history = []
        
        return {
            'success': True,
            'message': f'Conversation history cleared. Removed {previous_length} exchanges.',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_conversation_history(self) -> Dict[str, Any]:
        """
        Get the current conversation history
        
        Returns:
            Dictionary containing conversation history
        """
        return {
            'success': True,
            'history': self.conversation_history.copy(),
            'exchanges': len(self.conversation_history),
            'timestamp': datetime.now().isoformat()
        }
    
    def _build_conversation_context(self, user_message: str, context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Build the conversation context for the API call"""
        messages = []
        
        # Add system prompt
        system_prompt = self.content_filter.get_system_prompt()
        
        # Add context data to system prompt if available
        if context_data:
            if context_data.get('type') == 'audio_analysis' and 'features' in context_data:
                features = context_data['features']
                system_prompt += f\"\\n\\nCurrent audio analysis context:\"
                
                if 'duration' in features:
                    system_prompt += f\"\\nDuration: {features['duration']:.2f} seconds\"
                if 'tempo' in features:
                    system_prompt += f\"\\nTempo: {features['tempo']:.1f} BPM\"
                if 'spectral_centroid' in features:
                    system_prompt += f\"\\nSpectral Centroid: {features['spectral_centroid']:.1f} Hz\"
        
        messages.append({\"role\": \"system\", \"content\": system_prompt})
        
        # Add recent conversation history
        for exchange in self.conversation_history[-5:]:  # Last 5 exchanges
            messages.append({\"role\": \"user\", \"content\": exchange['user']})
            messages.append({\"role\": \"assistant\", \"content\": exchange['assistant']})
        
        # Add current message
        messages.append({\"role\": \"user\", \"content\": user_message})
        
        return messages
    
    def _update_conversation_history(self, user_message: str, ai_response: str):
        \"\"\"Update the conversation history\"\"\"
        self.conversation_history.append({
            'user': user_message,
            'assistant': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim history if it gets too long
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def _format_history_for_summary(self) -> str:
        \"\"\"Format conversation history for summary generation\"\"\"
        formatted_history = []
        
        for i, exchange in enumerate(self.conversation_history, 1):
            formatted_history.append(f\"Exchange {i}:\")
            formatted_history.append(f\"User: {exchange['user']}\")
            formatted_history.append(f\"Assistant: {exchange['assistant'][:200]}...\")  # Truncate for summary
            formatted_history.append(\"\")
        
        return \"\\n\".join(formatted_history)
