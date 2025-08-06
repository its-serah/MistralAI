"""Audio processing functionality"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

from ..config import get_settings
from ..utils.validators import validate_audio_file

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio file processing and spectrogram generation"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def load_audio_file(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load an audio file and return signal and sample rate
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (signal, sample_rate)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
            Exception: If file cannot be loaded
        """
        try:
            # Validate file
            validate_audio_file(file_path, self.settings)
            
            # Load audio with librosa
            signal, sample_rate = librosa.load(
                file_path, 
                sr=self.settings.audio_sample_rate,
                duration=self.settings.max_audio_duration
            )
            
            logger.info(f"Successfully loaded audio file: {file_path}")
            logger.info(f"Sample rate: {sample_rate}, Duration: {len(signal)/sample_rate:.2f}s")
            
            return signal, sample_rate
            
        except FileNotFoundError:
            logger.error(f"Audio file not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {str(e)}")
            raise
    
    def generate_spectrogram(
        self, 
        signal: np.ndarray, 
        sample_rate: int,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate and save a spectrogram from audio signal
        
        Args:
            signal: Audio signal array
            sample_rate: Sample rate of the audio
            output_path: Optional custom output path
            
        Returns:
            Path to the generated spectrogram image
        """
        try:
            # Set up matplotlib for non-interactive backend
            plt.switch_backend('Agg')
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Generate mel spectrogram
            spectrogram = librosa.feature.melspectrogram(
                y=signal, 
                sr=sample_rate,
                n_mels=128,
                fmax=8000
            )
            
            # Convert to dB scale
            spectrogram_db = librosa.power_to_db(spectrogram, ref=np.max)
            
            # Display spectrogram
            librosa.display.specshow(
                spectrogram_db,
                sr=sample_rate,
                x_axis='time',
                y_axis='mel',
                fmax=8000
            )
            
            # Customize plot
            plt.colorbar(format='%+2.0f dB')
            plt.title('Mel Spectrogram')
            plt.xlabel('Time (s)')
            plt.ylabel('Frequency (Hz)')
            plt.tight_layout()
            
            # Determine output path
            if output_path is None:
                output_path = os.path.join(
                    self.settings.output_directory, 
                    "spectrogram.png"
                )
            
            # Save the figure
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Spectrogram saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating spectrogram: {str(e)}")
            plt.close()  # Ensure we clean up on error
            raise
    
    def extract_audio_features(self, signal: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Extract various audio features from the signal
        
        Args:
            signal: Audio signal array
            sample_rate: Sample rate of the audio
            
        Returns:
            Dictionary containing extracted features
        """
        try:
            features = {}
            
            # Basic features
            features['duration'] = len(signal) / sample_rate
            features['sample_rate'] = sample_rate
            features['rms_energy'] = np.sqrt(np.mean(signal**2))
            
            # Spectral features
            features['spectral_centroid'] = np.mean(librosa.feature.spectral_centroid(y=signal, sr=sample_rate))
            features['spectral_bandwidth'] = np.mean(librosa.feature.spectral_bandwidth(y=signal, sr=sample_rate))
            features['spectral_rolloff'] = np.mean(librosa.feature.spectral_rolloff(y=signal, sr=sample_rate))
            features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(signal))
            
            # MFCC features (first 13 coefficients)
            mfcc = librosa.feature.mfcc(y=signal, sr=sample_rate, n_mfcc=13)
            features['mfcc_mean'] = np.mean(mfcc, axis=1).tolist()
            features['mfcc_std'] = np.std(mfcc, axis=1).tolist()
            
            # Tempo and beat features
            tempo, _ = librosa.beat.beat_track(y=signal, sr=sample_rate)
            features['tempo'] = float(tempo)
            
            logger.info("Successfully extracted audio features")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {str(e)}")
            raise
    
    def analyze_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Complete audio analysis including loading, feature extraction, and spectrogram generation
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Load audio
            signal, sample_rate = self.load_audio_file(file_path)
            
            # Extract features
            features = self.extract_audio_features(signal, sample_rate)
            
            # Generate spectrogram
            spectrogram_path = self.generate_spectrogram(signal, sample_rate)
            
            # Compile results
            analysis_result = {
                'file_path': file_path,
                'spectrogram_path': spectrogram_path,
                'features': features,
                'success': True
            }
            
            logger.info(f"Complete audio analysis finished for: {file_path}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Audio analysis failed for {file_path}: {str(e)}")
            return {
                'file_path': file_path,
                'error': str(e),
                'success': False
            }
