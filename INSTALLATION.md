# DEREK-BEACH Installation and Deployment Guide

Complete guide for installing dependencies and deploying the FARFAN 3.0 Policy Analysis System.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Dependency Installation](#dependency-installation)
5. [System Dependencies](#system-dependencies)
6. [Virtual Environment Setup](#virtual-environment-setup)
7. [GPU Support (Optional)](#gpu-support-optional)
8. [Language Models](#language-models)
9. [Verification](#verification)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)
12. [Common Issues](#common-issues)

---

## Prerequisites

### Required Software

- **Python**: Version 3.11 or 3.12 (recommended: 3.12.3)
- **pip**: Python package installer (usually included with Python)
- **git**: Version control system

### Check Your Python Version

```bash
python3 --version
# Should output: Python 3.11.x or Python 3.12.x
```

If you don't have the correct Python version:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

**macOS (using Homebrew):**
```bash
brew install python@3.12
```

**Windows:**
Download and install from [python.org](https://www.python.org/downloads/)

---

## System Requirements

### Minimum Requirements
- **RAM**: 8GB (16GB recommended)
- **Storage**: 5GB free space for dependencies and models
- **CPU**: Multi-core processor (4+ cores recommended)

### Recommended Requirements
- **RAM**: 16GB+ (especially for ML models)
- **Storage**: 10GB+ free space
- **CPU**: 8+ cores
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster processing)

---

## Installation Methods

### Method 1: Standard Installation (Recommended)

This method uses a virtual environment to isolate dependencies.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
cd DEREK-BEACH
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

Your prompt should now show `(venv)` prefix.

#### Step 3: Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

#### Step 4: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

This will install all dependencies listed in `requirements.txt`.

---

### Method 2: Development Installation

For contributors and developers who want to make changes.

```bash
# Clone the repository
git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
cd DEREK-BEACH

# Create and activate virtual environment
python3 -m venv venv-dev
source venv-dev/bin/activate  # On Windows: venv-dev\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install in editable mode with development dependencies
pip install -r requirements.txt

# Verify installation
pytest tests/ -v
```

---

## Dependency Installation

### Core Dependencies

The `requirements.txt` includes the following categories of dependencies:

#### 1. Core Data Processing
- **PyYAML**: Configuration file parsing
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation

#### 2. Machine Learning & NLP
- **PyTorch**: Deep learning framework
- **Transformers**: Pre-trained language models
- **Sentence-Transformers**: Sentence embeddings
- **scikit-learn**: Machine learning utilities
- **spaCy**: NLP processing

#### 3. Statistical Analysis
- **SciPy**: Scientific computing
- **PyMC**: Bayesian modeling
- **ArviZ**: Bayesian visualization

#### 4. PDF Processing
- **PyMuPDF** (fitz): PDF text extraction
- **pdfplumber**: Advanced PDF parsing
- **camelot-py**: Table extraction from PDFs
- **tabula-py**: Java-based table extraction

#### 5. Testing
- **pytest**: Testing framework
- **pytest-cov**: Code coverage
- **pytest-asyncio**: Async testing support

---

## System Dependencies

Some Python packages require system-level dependencies.

### For Ubuntu/Debian:

```bash
# Update package lists
sudo apt update

# Install system dependencies for PDF processing
sudo apt install -y \
    ghostscript \
    libpoppler-cpp-dev \
    poppler-utils \
    tesseract-ocr \
    libsm6 \
    libxext6 \
    libxrender-dev

# Install Java (required for tabula-py)
sudo apt install -y default-jre

# Install development tools (for building some packages)
sudo apt install -y \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    antiword \
    unrtf
```

### For macOS:

```bash
# Using Homebrew
brew install ghostscript poppler tesseract

# Install Java (required for tabula-py)
brew install openjdk
```

### For Windows:

1. **Ghostscript**: Download and install from [ghostscript.com](https://www.ghostscript.com/download/gsdnld.html)
2. **Poppler**: Download from [poppler for Windows](https://blog.alivate.com.au/poppler-windows/)
3. **Tesseract**: Download from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
4. **Java**: Download from [java.com](https://www.java.com/download/)

Add the installation paths to your system PATH environment variable.

---

## Virtual Environment Setup

### Why Use a Virtual Environment?

Virtual environments:
- Isolate project dependencies
- Prevent conflicts between projects
- Allow different Python versions per project
- Make deployment reproducible

### Creating a Virtual Environment

```bash
# Navigate to project directory
cd DEREK-BEACH

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Deactivating the Virtual Environment

```bash
deactivate
```

### Managing Multiple Environments

For different deployment scenarios:

```bash
# Development environment
python3 -m venv venv-dev

# Production environment
python3 -m venv venv-prod

# Testing environment
python3 -m venv venv-test
```

---

## GPU Support (Optional)

For faster processing with NVIDIA GPUs:

### Step 1: Check GPU Availability

```bash
nvidia-smi
```

### Step 2: Install CUDA-enabled PyTorch

```bash
# Uninstall CPU version
pip uninstall torch

# Install GPU version (CUDA 11.8 example)
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1:
# pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cu121
```

### Step 3: Verify GPU Support

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
```

---

## Language Models

### Installing spaCy Language Models

```bash
# Activate your virtual environment first
source venv/bin/activate

# English models
python -m spacy download en_core_web_sm  # Small (12 MB)
python -m spacy download en_core_web_md  # Medium (40 MB)
python -m spacy download en_core_web_lg  # Large (560 MB)

# Spanish models (if needed)
python -m spacy download es_core_news_sm  # Small
python -m spacy download es_core_news_md  # Medium
python -m spacy download es_core_news_lg  # Large
```

### Pre-downloading Transformer Models

Some models will be downloaded automatically on first use. To pre-download:

```python
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Download sentence transformer models
model = SentenceTransformer('all-MiniLM-L6-v2')

# Download classification pipeline
classifier = pipeline('sentiment-analysis')
```

---

## Verification

### Step 1: Validate Choreography

```bash
python3 validate_choreography.py
```

Expected output:
```
✓ All validation checks passed
✓ Choreography system is ready
```

### Step 2: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/validation/test_interface_contracts.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

Expected output:
```
========================== 26 passed in 0.74s ==========================
```

### Step 3: Verify Imports

```python
# Test in Python REPL
python3 -c "
from metadata_service import MetadataService
from event_driven_choreographer import EventDrivenChoreographer
from events import EventType
print('✓ All imports successful')
"
```

### Step 4: Check Dependencies

```bash
# List installed packages
pip list

# Check for conflicts
pip check
```

---

## Deployment

### Local Development Deployment

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run validation
python3 validate_choreography.py

# 3. Run example usage
python3 example_usage.py

# 4. Start analysis (if applicable)
python3 orchestrator_example.py
```

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ghostscript \
    libpoppler-cpp-dev \
    poppler-utils \
    tesseract-ocr \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run validation on build
RUN python3 validate_choreography.py

# Default command
CMD ["python3", "orchestrator_example.py"]
```

Build and run:

```bash
# Build image
docker build -t derek-beach:latest .

# Run container
docker run -it derek-beach:latest
```

### Production Deployment

For production environments:

```bash
# 1. Clone repository on production server
git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
cd DEREK-BEACH

# 2. Create production virtual environment
python3 -m venv venv-prod
source venv-prod/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install language models
python -m spacy download en_core_web_sm

# 5. Run validation
python3 validate_choreography.py

# 6. Run tests
pytest tests/ -v

# 7. Configure for production
# - Set up logging
# - Configure monitoring
# - Set environment variables
# - Set up error tracking

# 8. Start application
python3 <your_main_script>.py
```

---

## Troubleshooting

### Issue: Python Version Mismatch

**Problem**: `requirements.txt` requires Python 3.11+

**Solution**:
```bash
# Check Python version
python3 --version

# If version is < 3.11, install newer Python
# See Prerequisites section above
```

### Issue: pip Installation Fails

**Problem**: Permission denied or access errors

**Solution**:
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# OR install for user only (not recommended)
pip install --user -r requirements.txt
```

### Issue: PyTorch Installation Fails

**Problem**: Timeout or memory error during installation

**Solution**:
```bash
# Install PyTorch separately first
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu

# Then install other dependencies
pip install -r requirements.txt
```

### Issue: camelot-py Installation Fails

**Problem**: Missing system dependencies

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install -y ghostscript libpoppler-cpp-dev

# Then reinstall
pip install camelot-py[cv]
```

### Issue: Java Not Found (tabula-py)

**Problem**: `Java not found` error

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install default-jre

# macOS
brew install openjdk

# Windows: Install Java from java.com
# Add to PATH environment variable
```

### Issue: spaCy Model Not Found

**Problem**: `Can't find model 'en_core_web_sm'`

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

### Issue: CUDA Out of Memory

**Problem**: GPU memory exhausted

**Solution**:
```python
# Use CPU instead
import torch
device = torch.device('cpu')

# Or reduce batch size in your code
```

### Issue: Import Errors

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check for missing packages
pip check
```

---

## Common Issues

### Dependency Conflicts

If you encounter version conflicts:

```bash
# Create fresh virtual environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Install with no dependencies first
pip install --no-deps -r requirements.txt

# Then install dependencies
pip install -r requirements.txt
```

### Slow Installation

To speed up installation:

```bash
# Use pre-built wheels
pip install --prefer-binary -r requirements.txt

# Use multiple workers
pip install -r requirements.txt --use-pep517
```

### Memory Issues During Installation

```bash
# Install packages one at a time
pip install numpy pandas scipy
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers
# ... continue with other packages
```

---

## Additional Resources

### Documentation Links

- [Project README](README.md)
- [Choreography Protocol](CHOREOGRAPHY_PROTOCOL.md)
- [Interface Contract Audit](INTERFACE_CONTRACT_AUDIT_REPORT.md)

### Python Package Documentation

- [PyTorch](https://pytorch.org/docs/)
- [Transformers](https://huggingface.co/docs/transformers/)
- [spaCy](https://spacy.io/usage)
- [PyMC](https://www.pymc.io/welcome.html)
- [Pandas](https://pandas.pydata.org/docs/)

### Support

For issues specific to DEREK-BEACH:
- Open an issue on [GitHub](https://github.com/PEROPOROBTANTE/DEREK-BEACH/issues)
- Check existing issues for solutions

---

## Version Compatibility Matrix

| Python Version | Status | Notes |
|---------------|--------|-------|
| 3.10.x | ⚠️ Partial | Some packages may need version adjustments |
| 3.11.x | ✅ Supported | Fully tested |
| 3.12.x | ✅ Recommended | Best performance and compatibility |
| 3.13.x | ❌ Not supported | Dependencies not yet compatible |

| OS | Status | Notes |
|----|--------|-------|
| Ubuntu 20.04+ | ✅ Supported | Recommended for production |
| Ubuntu 22.04+ | ✅ Supported | Best support |
| Debian 11+ | ✅ Supported | Fully compatible |
| macOS 12+ | ✅ Supported | Intel and Apple Silicon |
| Windows 10+ | ⚠️ Partial | Some PDF tools may need manual setup |
| Windows 11 | ⚠️ Partial | Some PDF tools may need manual setup |

---

## Quick Reference

### Essential Commands

```bash
# Create environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Validate installation
python3 validate_choreography.py

# Run tests
pytest tests/ -v

# Deactivate environment
deactivate
```

### Environment Variables (Optional)

```bash
# Set in ~/.bashrc or ~/.zshrc
export DEREK_BEACH_HOME=/path/to/DEREK-BEACH
export DEREK_BEACH_DATA=/path/to/data
export DEREK_BEACH_LOGS=/path/to/logs
```

---

**Last Updated**: 2025-10-21  
**Version**: 1.0.0  
**Python Version**: 3.11+ (3.12 recommended)
