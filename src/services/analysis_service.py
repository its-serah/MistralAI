"""Audio analysis service that orchestrates audio processing and AI explanations"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..core import AudioProcessor, MistralClient
from ..config import get_settings

logger = logging.getLogger(__name__)


class AudioAnalysisService:
    """Service that combines audio processing with AI-powered explanations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.audio_processor = AudioProcessor()
        self.mistral_client = MistralClient()
    
    def analyze_audio_with_explanation(
        self, 
        file_path: str,
        custom_question: Optional[str] = None,
        include_features: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete audio analysis with AI explanation
        
        Args:
            file_path: Path to the audio file
            custom_question: Custom question to ask about the audio
            include_features: Whether to include detailed audio features
            
        Returns:
            Dictionary containing analysis results and AI explanation
        """
        try:
            logger.info(f"Starting audio analysis for: {file_path}")
            
            # Perform audio analysis
            audio_result = self.audio_processor.analyze_audio_file(file_path)
            
            if not audio_result['success']:
                return {
                    'success': False,
                    'error': f"Audio analysis failed: {audio_result['error']}",
                    'stage': 'audio_processing'
                }
            
            # Prepare features for AI context
            features = audio_result['features'] if include_features else None
            
            # Get AI explanation
            if custom_question:
                ai_result = self.mistral_client.ask_question(
                    custom_question, 
                    context=self._format_audio_context(features, file_path)
                )
            else:
                ai_result = self.mistral_client.explain_spectrogram(
                    audio_features=features,
                    custom_context=f"Analyzing audio file: {Path(file_path).name}"
                )
            
            # Combine results
            result = {
                'success': True,
                'file_path': file_path,
                'audio_analysis': {
                    'spectrogram_path': audio_result['spectrogram_path'],
                    'features': audio_result['features'] if include_features else None,
                },
                'ai_explanation': {
                    'success': ai_result['success'],
                    'content': ai_result.get('content', ''),
                    'error': ai_result.get('error') if not ai_result['success'] else None
                },
                'metadata': {
                    'model_used': ai_result.get('model', self.settings.mistral_model),
                    'analysis_timestamp': self._get_timestamp(),
                    'custom_question': custom_question
                }
            }
            
            logger.info(f"Audio analysis completed successfully for: {file_path}")
            return result
        
        except Exception as e:
            logger.error(f"Audio analysis service error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'service_orchestration'
            }
    
    def analyze_multiple_files(
        self, 
        file_paths: list,
        custom_question: Optional[str] = None,
        include_features: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze multiple audio files
        
        Args:
            file_paths: List of paths to audio files
            custom_question: Custom question to ask about the audio
            include_features: Whether to include detailed audio features
            
        Returns:
            Dictionary containing results for all files
        """
        results = {
            'success': True,
            'total_files': len(file_paths),
            'successful_analyses': 0,
            'failed_analyses': 0,
            'results': {},
            'errors': []
        }
        
        for file_path in file_paths:
            try:
                result = self.analyze_audio_with_explanation(
                    file_path, custom_question, include_features
                )
                
                results['results'][file_path] = result
                
                if result['success']:
                    results['successful_analyses'] += 1
                else:
                    results['failed_analyses'] += 1
                    results['errors'].append({
                        'file': file_path,
                        'error': result['error']
                    })
            
            except Exception as e:
                results['failed_analyses'] += 1
                results['errors'].append({
                    'file': file_path,
                    'error': str(e)
                })
                logger.error(f"Failed to analyze {file_path}: {str(e)}")
        
        results['success'] = results['successful_analyses'] > 0
        
        logger.info(
            f"Batch analysis completed: {results['successful_analyses']}/{results['total_files']} successful"
        )
        
        return results
    
    def generate_spectrogram_only(self, file_path: str) -> Dict[str, Any]:
        """
        Generate only the spectrogram without AI explanation
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing spectrogram generation result
        """
        try:
            # Load audio
            signal, sample_rate = self.audio_processor.load_audio_file(file_path)
            
            # Generate spectrogram
            spectrogram_path = self.audio_processor.generate_spectrogram(signal, sample_rate)
            
            return {
                'success': True,
                'file_path': file_path,
                'spectrogram_path': spectrogram_path,
                'audio_info': {
                    'duration': len(signal) / sample_rate,
                    'sample_rate': sample_rate
                }
            }
        
        except Exception as e:
            logger.error(f"Spectrogram generation failed for {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def get_audio_features_only(self, file_path: str) -> Dict[str, Any]:
        """
        Extract only audio features without generating spectrogram
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing audio features
        """
        try:
            # Load audio
            signal, sample_rate = self.audio_processor.load_audio_file(file_path)
            
            # Extract features
            features = self.audio_processor.extract_audio_features(signal, sample_rate)
            
            return {
                'success': True,
                'file_path': file_path,
                'features': features
            }
        
        except Exception as e:
            logger.error(f"Feature extraction failed for {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _format_audio_context(self, features: Optional[Dict[str, Any]], file_path: str) -> str:
        """Format audio features into context for AI"""
        if not features:
            return f"Audio file: {Path(file_path).name}"
        
        context_parts = [f"Audio Analysis of: {Path(file_path).name}"]
        
        if 'duration' in features:
            context_parts.append(f"Duration: {features['duration']:.2f} seconds")
        
        if 'tempo' in features:
            context_parts.append(f"Tempo: {features['tempo']:.1f} BPM")
        
        if 'spectral_centroid' in features:
            context_parts.append(f"Spectral Centroid: {features['spectral_centroid']:.1f} Hz")
        
        if 'rms_energy' in features:
            context_parts.append(f"RMS Energy: {features['rms_energy']:.4f}")
        
        return "\\n".join(context_parts)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components
        
        Returns:
            Dictionary containing health status of all components
        """
        try:
            # Check Mistral API connection
            api_healthy = self.mistral_client.health_check()
            
            # Check if output directories exist and are writable
            directories_ok = True
            directory_errors = []
            
            for directory in [self.settings.output_directory, self.settings.temp_directory]:
                try:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    test_file = Path(directory) / "test_write.tmp"
                    test_file.touch()
                    test_file.unlink()
                except Exception as e:
                    directories_ok = False
                    directory_errors.append(f"{directory}: {str(e)}")
            
            overall_health = api_healthy and directories_ok
            
            return {
                'overall_healthy': overall_health,
                'components': {
                    'mistral_api': api_healthy,
                    'directories': directories_ok,
                    'audio_processor': True,  # Always available if librosa is installed
                },
                'errors': directory_errors if directory_errors else None,
                'timestamp': self._get_timestamp()
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'overall_healthy': False,
                'error': str(e),
                'timestamp': self._get_timestamp()
            }
