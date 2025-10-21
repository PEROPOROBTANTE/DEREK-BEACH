# Installation Guide for DEREK-BEACH

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
cd DEREK-BEACH
```

### 2. Set Up Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install spaCy Language Models

The project requires Spanish language models for NLP processing:

```bash
# Large model (recommended for best accuracy)
python -m spacy download es_core_news_lg

# OR smaller model (faster but less accurate)
python -m spacy download es_core_news_sm
```

### 5. Install System Dependencies

#### Graphviz (required for visualization)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install graphviz
```

**macOS:**
```bash
brew install graphviz
```

**Windows:**
Download and install from: https://graphviz.org/download/

### 6. Verify Installation

```bash
# Test Python imports
python3 << 'EOF'
try:
    import numpy
    import pandas
    import scipy
    import networkx
    import spacy
    import yaml
    import pydantic
    print("✓ All core dependencies imported successfully!")
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
EOF

# Test spaCy model
python3 -c "import spacy; nlp = spacy.load('es_core_news_lg'); print('✓ spaCy model loaded')"

# Verify compilation
python3 -m py_compile esqueleto.py metadata_service.py dereck_beach.py
echo "✓ Core modules compile successfully"
```

## Package Descriptions

| Package | Purpose |
|---------|---------|
| **numpy** | Numerical computing and array operations |
| **pandas** | Data manipulation and analysis |
| **scipy** | Scientific computing and statistics |
| **networkx** | Graph and network analysis |
| **spacy** | Natural Language Processing |
| **PyMuPDF** | PDF document processing |
| **PyPDF2** | Alternative PDF library |
| **python-docx** | Word document processing |
| **pydantic** | Data validation using Python type hints |
| **pyyaml** | YAML configuration file parsing |
| **fuzzywuzzy** | Fuzzy string matching |
| **pydot** | Graph visualization interface |

## Troubleshooting

### Common Issues

#### 1. Import Error: No module named 'numpy'

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

#### 2. OSError: [E050] Can't find model 'es_core_news_lg'

**Solution:** Download spaCy language model
```bash
python -m spacy download es_core_news_lg
```

#### 3. pydot: Couldn't import dot_parser

**Solution:** Install Graphviz system package (see step 5 above)

#### 4. ImportError: No module named 'fitz'

**Solution:** Install PyMuPDF
```bash
pip install PyMuPDF
```

#### 5. SyntaxError in Python files

**Solution:** Ensure you're using Python 3.10 or higher
```bash
python3 --version
```

### Dependency Conflicts

If you encounter version conflicts, try installing with specific versions:

```bash
pip install numpy==1.21.0 pandas==1.3.0 scipy==1.7.0
```

Or use the frozen requirements (if available):
```bash
pip install -r requirements-frozen.txt
```

## Development Setup

### Additional Development Tools

For development, you may want to install additional tools:

```bash
# Linting and formatting
pip install black flake8 pylint mypy

# Testing
pip install pytest pytest-cov

# Documentation
pip install sphinx sphinx-rtd-theme
```

### Git Hooks (Optional)

Set up pre-commit hooks to check code before committing:

```bash
pip install pre-commit
pre-commit install
```

## Docker Setup (Alternative)

If you prefer using Docker:

```dockerfile
# Dockerfile (create this file)
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download es_core_news_lg

# Copy project files
COPY . .

CMD ["python3", "dereck_beach.py"]
```

Build and run:
```bash
docker build -t derek-beach .
docker run -it derek-beach
```

## Configuration

### Environment Variables

You may need to set the following environment variables:

```bash
# Python path (if modules can't be found)
export PYTHONPATH="${PYTHONPATH}:/path/to/DEREK-BEACH"

# Logging level
export LOG_LEVEL=INFO
```

### Configuration Files

The project uses several configuration files:

- `config.yaml` - Main configuration (may need to be created)
- `cuestionario.json` - Questionnaire definitions
- `rubric_scoring.json` - Scoring rubric
- `execution_mapping.yaml` - Execution mappings

Make sure these files exist and are properly formatted.

## Testing Installation

Run a simple test to verify everything works:

```bash
# Test metadata service
python3 -c "
from metadata_service import MetadataService
service = MetadataService()
print(f'✓ Loaded {len(service.get_all_questions())} questions')
"

# Test compilation of all modules
python3 << 'EOF'
from pathlib import Path
import py_compile

errors = []
for f in Path('.').rglob('*.py'):
    if '.git' not in str(f):
        try:
            py_compile.compile(str(f), doraise=True)
        except:
            errors.append(str(f))

if errors:
    print(f"✗ Compilation errors in {len(errors)} files")
else:
    print("✓ All Python files compile successfully")
EOF
```

## Support

For issues or questions:

1. Check the [COMPILATION_FIXES_SUMMARY.md](COMPILATION_FIXES_SUMMARY.md) for known issues
2. Review error messages carefully
3. Ensure all prerequisites are installed
4. Check Python version compatibility

## Next Steps

After successful installation:

1. Review the main documentation in `README.md`
2. Check the `SUMMARY.md` for project overview
3. Explore the `tests/` directory for usage examples
4. Run the example scripts to verify functionality

---

**Installation Status Checklist:**

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] `requirements.txt` dependencies installed
- [ ] spaCy language model downloaded
- [ ] Graphviz system package installed
- [ ] All verification tests passed
- [ ] Configuration files reviewed

Once all items are checked, your installation is complete! ✅
