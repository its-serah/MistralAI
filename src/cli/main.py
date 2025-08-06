"""Main CLI interface for MistralAI audio analysis"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src.services import AudioAnalysisService, ChatService
from src.config import get_settings


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def analyze_audio_file(file_path: str, custom_question: Optional[str] = None):
    """Analyze a single audio file"""
    try:
        analysis_service = AudioAnalysisService()
        
        print(f"\\nAnalyzing audio file: {file_path}")
        print("-" * 50)
        
        result = analysis_service.analyze_audio_with_explanation(
            file_path=file_path,
            custom_question=custom_question,
            include_features=True
        )
        
        if result['success']:
            print(f"✅ Analysis completed successfully!")
            print(f"📊 Spectrogram saved to: {result['audio_analysis']['spectrogram_path']}")
            
            # Display audio features
            features = result['audio_analysis']['features']
            if features:
                print(f"\\n🎵 Audio Features:")
                print(f"   Duration: {features.get('duration', 'N/A'):.2f} seconds")
                print(f"   Sample Rate: {features.get('sample_rate', 'N/A')} Hz")
                print(f"   Tempo: {features.get('tempo', 'N/A'):.1f} BPM")
                print(f"   RMS Energy: {features.get('rms_energy', 'N/A'):.4f}")
                print(f"   Spectral Centroid: {features.get('spectral_centroid', 'N/A'):.1f} Hz")
            
            # Display AI explanation
            if result['ai_explanation']['success']:
                print(f"\\n🤖 AI Explanation:")
                print(f"{result['ai_explanation']['content']}")
            else:
                print(f"\\n❌ AI explanation failed: {result['ai_explanation']['error']}")
        else:
            print(f"❌ Analysis failed: {result['error']}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def interactive_chat():
    """Start interactive chat mode"""
    try:
        chat_service = ChatService()
        
        # Start conversation
        start_result = chat_service.start_conversation()
        print("\\n" + "="*60)
        print("🎤 MISTRAL AUDIO ANALYSIS CHAT")
        print("="*60)
        print(start_result['message'])
        print("\\nCapabilities:")
        for capability in start_result['capabilities']:
            print(f"  • {capability}")
        
        print("\\n" + "-"*60)
        print("Commands: 'quit' or 'exit' to leave, 'clear' to clear history, 'summary' for conversation summary")
        print("-"*60)
        
        while True:
            try:
                # Get user input
                user_input = input("\\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\\n👋 Goodbye! Thank you for using MistralAI Audio Analysis.")
                    break
                elif user_input.lower() == 'clear':
                    result = chat_service.clear_conversation()
                    print(f"\\n🗑️  {result['message']}")
                    continue
                elif user_input.lower() == 'summary':
                    result = chat_service.get_conversation_summary()
                    if result['success']:
                        print(f"\\n📋 Conversation Summary:")
                        print(f"{result['summary']}")
                        print(f"\\n(Based on {result['exchanges']} exchanges)")
                    else:
                        print(f"\\n❌ Could not generate summary: {result.get('error', 'Unknown error')}")
                    continue
                elif user_input.lower().startswith('help'):
                    print_help()
                    continue
                
                # Send message to chat service
                print("\\n🤖 Assistant: ", end="", flush=True)
                response = chat_service.send_message(user_input)
                
                if response['success']:
                    print(response['ai_response'])
                else:
                    print(f"❌ Error: {response['error']}")
            
            except KeyboardInterrupt:
                print("\\n\\n👋 Goodbye! (Interrupted by user)")
                break
            except EOFError:
                print("\\n\\n👋 Goodbye! (End of input)")
                break
    
    except Exception as e:
        print(f"❌ Chat service error: {str(e)}")


def print_help():
    """Print help information"""
    help_text = '''
🎤 MistralAI Audio Analysis Help

CHAT COMMANDS:
  help          - Show this help message
  clear         - Clear conversation history  
  summary       - Get conversation summary
  quit/exit/bye - Exit the chat

EXAMPLE QUESTIONS:
  "What is a spectrogram?"
  "How do I interpret the colors in a spectrogram?"
  "What does spectral centroid mean?"
  "Explain MFCC features"
  "How does tempo detection work?"
  
ANALYSIS WORKFLOW:
  1. Use 'analyze' command to process audio files
  2. Use 'chat' mode to ask questions about results
  3. Combine both for comprehensive audio analysis
'''
    print(help_text)


def health_check():
    """Perform system health check"""
    try:
        analysis_service = AudioAnalysisService()
        
        print("\\n🔍 System Health Check")
        print("-" * 30)
        
        health_result = analysis_service.health_check()
        
        if health_result['overall_healthy']:
            print("✅ System is healthy!")
        else:
            print("❌ System has issues!")
        
        print(f"\\n📊 Component Status:")
        for component, status in health_result['components'].items():
            status_emoji = "✅" if status else "❌"
            print(f"   {status_emoji} {component.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")
        
        if health_result.get('errors'):
            print(f"\\n❌ Errors:")
            for error in health_result['errors']:
                print(f"   • {error}")
    
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description="MistralAI Audio Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s analyze audio.wav                    # Analyze audio file
  %(prog)s analyze audio.wav -q "What genre is this?"  # Custom question
  %(prog)s chat                                # Interactive chat mode
  %(prog)s health                             # System health check
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze audio files')
    analyze_parser.add_argument('file', help='Path to audio file')
    analyze_parser.add_argument('-q', '--question', help='Custom question to ask about the audio')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Start interactive chat mode')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check system health')
    
    # Global options
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--env-file', help='Path to .env file (default: .env)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Set custom env file if specified
    if args.env_file:
        os.environ['ENV_FILE'] = args.env_file
    
    # Check if we have a command
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Validate settings (this will fail early if API key is missing)
        settings = get_settings()
        
        if args.command == 'analyze':
            analyze_audio_file(args.file, args.question)
        elif args.command == 'chat':
            interactive_chat()
        elif args.command == 'health':
            health_check()
    
    except ValueError as e:
        if "MISTRAL_API_KEY" in str(e):
            print("❌ Error: Mistral AI API key is required!")
            print("\\nPlease set your API key:")
            print("  1. Create a .env file with: MISTRAL_API_KEY=your_api_key_here")
            print("  2. Or set environment variable: export MISTRAL_API_KEY=your_api_key_here")
            print("\\nGet your API key from: https://console.mistral.ai/")
        else:
            print(f"❌ Configuration error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
