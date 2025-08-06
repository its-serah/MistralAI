"""Mistral AI client with guardrails and error handling"""

import logging
import time
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import get_settings
from ..utils.guardrails import ContentFilter

logger = logging.getLogger(__name__)


class MistralClient:
    """Mistral AI client with built-in guardrails and error handling"""
    
    def __init__(self):
        self.settings = get_settings()
        self.content_filter = ContentFilter() if self.settings.enable_content_filter else None
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        # Define retry strategy
        retry_strategy = Retry(
            total=self.settings.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for Mistral API requests"""
        return {
            "Authorization": f"Bearer {self.settings.mistral_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "MistralAI-AudioAnalysis/2.0.0"
        }
    
    def _prepare_payload(
        self, 
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Prepare the payload for Mistral API requests"""
        return {
            "model": self.settings.mistral_model,
            "messages": messages,
            "temperature": temperature or self.settings.temperature,
            "max_tokens": max_tokens or self.settings.max_tokens,
            "safe_prompt": True  # Enable Mistral's built-in safety
        }
    
    def _validate_and_filter_content(self, content: str) -> str:
        """Validate and filter content using guardrails"""
        if self.content_filter:
            # Check for inappropriate content
            if not self.content_filter.is_safe_content(content):
                raise ValueError("Content failed safety checks")
            
            # Filter content if needed
            content = self.content_filter.filter_content(content)
        
        return content
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Mistral AI
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Dictionary containing the response and metadata
            
        Raises:
            ValueError: If content fails safety checks
            requests.RequestException: If API request fails
        """
        try:
            # Validate input messages
            for message in messages:
                if 'content' in message:
                    message['content'] = self._validate_and_filter_content(message['content'])
            
            # Prepare request
            headers = self._prepare_headers()
            payload = self._prepare_payload(messages, temperature, max_tokens)
            
            logger.info(f"Sending request to Mistral API with {len(messages)} messages")
            
            # Make request with timeout
            response = self.session.post(
                self.settings.mistral_api_url,
                headers=headers,
                json=payload,
                timeout=self.settings.request_timeout
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                
                # Extract and validate response content
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    # Filter response content
                    if self.content_filter:
                        content = self.content_filter.filter_content(content)
                        result['choices'][0]['message']['content'] = content
                    
                    logger.info("Successfully received response from Mistral API")
                    return {
                        'success': True,
                        'response': result,
                        'content': content,
                        'usage': result.get('usage', {}),
                        'model': result.get('model', self.settings.mistral_model)
                    }
                else:
                    logger.error("Invalid response format from Mistral API")
                    return {
                        'success': False,
                        'error': "Invalid response format",
                        'response': result
                    }
            
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
        
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.settings.request_timeout} seconds"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        
        except ValueError as e:
            logger.error(f"Content validation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def ask_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a simple question to Mistral AI
        
        Args:
            question: The question to ask
            context: Optional context to provide
            
        Returns:
            Dictionary containing the response and metadata
        """
        messages = []
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Context: {context}"
            })
        
        messages.append({
            "role": "user",
            "content": question
        })
        
        return self.chat_completion(messages)
    
    def explain_spectrogram(
        self, 
        audio_features: Optional[Dict[str, Any]] = None,
        custom_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get an explanation of what a spectrogram shows
        
        Args:
            audio_features: Optional audio features to include in explanation
            custom_context: Optional custom context
            
        Returns:
            Dictionary containing the explanation response
        """
        # Base explanation prompt
        question = """Please explain what a spectrogram shows in audio analysis. 
        Focus on:
        1. What the visual representation means
        2. How frequency and time are displayed
        3. What different colors/intensities represent
        4. How this helps in understanding audio characteristics
        
        Keep the explanation clear and accessible while being technically accurate."""
        
        # Add audio features context if available
        if audio_features:
            context_parts = ["Audio Analysis Context:"]
            
            if 'duration' in audio_features:
                context_parts.append(f"- Duration: {audio_features['duration']:.2f} seconds")
            
            if 'tempo' in audio_features:
                context_parts.append(f"- Tempo: {audio_features['tempo']:.1f} BPM")
            
            if 'spectral_centroid' in audio_features:
                context_parts.append(f"- Spectral Centroid: {audio_features['spectral_centroid']:.1f} Hz")
            
            if 'rms_energy' in audio_features:
                context_parts.append(f"- RMS Energy: {audio_features['rms_energy']:.4f}")
            
            context = "\\n".join(context_parts)
            
            if custom_context:
                context += f"\\n\\nAdditional Context: {custom_context}"
        
        else:
            context = custom_context
        
        return self.ask_question(question, context)
    
    def health_check(self) -> bool:
        """
        Perform a health check on the Mistral API connection
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = self.ask_question("Hello, this is a health check. Please respond with 'OK'.")
            return response.get('success', False)
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
