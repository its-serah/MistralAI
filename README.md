# MistralAI Audio Analysis Tool

![CI/CD](https://github.com/AGC-Technical-Team/MistralAI/actions/workflows/main.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/mistral-audio-analysis.svg)](https://badge.fury.io/py/mistral-audio-analysis)

A powerful, modular, and text-based audio analysis tool that leverages Mistral AI for intelligent spectrogram explanations and audio-related discussions.

This refactored version applies clean code principles, separation of concerns, and robust error handling to provide a professional-grade tool for developers, researchers, and audio enthusiasts.

## ✨ Key Features

- **Modular Architecture**: Organized into logical layers (core, services, CLI) for maintainability and extensibility.
- **Environment-based Configuration**: Securely manage API keys and settings using `.env` files and environment variables.
- **Interactive Text-based Chat**: Engage in a conversation with an AI assistant focused on audio analysis.
- **Robust Audio Processing**: Load, analyze, and generate spectrograms from various audio formats.
- **LLM Guardrails**: Includes content filtering, safety checks, and topic focus to ensure professional and relevant AI interactions.
- **Detailed Audio Feature Extraction**: Get insights into tempo, energy, spectral characteristics, and more.
- **Error Handling & Retries**: Resilient client with automatic retries for API requests.
- **Easy Installation & Usage**: Packaged for easy installation via `pip` with a user-friendly CLI.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Pip package manager
- (Optional) `ffmpeg` for wider audio format support

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/its-serah/MistralAI.git
cd MistralAI

# Install the package
pip install -e .
```

### 2. Configuration

1.  **Copy the environment file**:

    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** and add your Mistral AI API key:

    ```ini
    MISTRAL_API_KEY=your_mistral_api_key_here
    ```

    *Get your API key from the [Mistral AI Console](https://console.mistral.ai/).*

### 3. Usage

The tool provides a command-line interface (`mistral-audio`).

#### Analyze an Audio File

This command processes an audio file, generates a spectrogram, and provides an AI-powered explanation.

```bash
# Analyze an audio file
mistral-audio analyze /path/to/your/audio.wav

# Ask a custom question about the audio
mistral-audio analyze audio.mp3 -q "What kind of mood does this music evoke?"
```

#### Interactive Chat Mode

Start an interactive session to discuss audio concepts or ask follow-up questions.

```bash
mistral-audio chat
```

Inside the chat, you can:
- Ask general questions (e.g., *"What is a spectral centroid?"*)
- Discuss results from a previous analysis
- Type `help` for commands or `quit` to exit.

#### System Health Check

Verify that your configuration and connections are working correctly.

```bash
mistral-audio health
```

## 🏗️ Project Structure

```
MistralAI/
├── src/
│   ├── config/      # Configuration management (Pydantic, .env)
│   ├── core/        # Core logic (AudioProcessor, MistralClient)
│   ├── services/    # Business logic (AudioAnalysisService, ChatService)
│   ├── utils/       # Utilities (validation, guardrails)
│   └── cli/         # Command-line interface (argparse)
├── requirements.txt # Project dependencies
├── .env.example     # Example environment variables
├── README.md
└── setup.py         # Package setup
```

## 🔧 Development

### Running Tests

To run the test suite:

```bash
pip install -e .[dev]
pytest
```

### Code Style

This project uses `black` for formatting and `flake8` for linting.

```bash
black src/
flake8 src/
```

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features.

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
