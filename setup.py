"""Setup configuration for MistralAI Audio Analysis package"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "requests>=2.28.0",
        "pydantic>=1.10.0",
        "python-dotenv>=0.19.0",
        "librosa>=0.9.0",
        "matplotlib>=3.5.0",
        "numpy>=1.21.0",
        "urllib3>=1.26.0",
    ]

setup(
    name="mistral-audio-analysis",
    version="2.0.0",
    description="A modular audio analysis tool with Mistral AI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AGC Technical Team (Refactored)",
    author_email="contact@agc-tech.com",
    url="https://github.com/its-serah/MistralAI",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "audio": [
            "soundfile>=0.10.0",
            "ffmpeg-python>=0.2.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "mistral-audio=src.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    keywords="audio analysis spectrogram mistral ai machine learning",
    project_urls={
        "Bug Reports": "https://github.com/its-serah/MistralAI/issues",
        "Source": "https://github.com/its-serah/MistralAI",
        "Documentation": "https://github.com/its-serah/MistralAI#readme",
    },
)
