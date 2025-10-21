# DEREK-BEACH Quick Start Guide

Get started with DEREK-BEACH in 5 minutes!

## Prerequisites

- **Python 3.11 or 3.12** (check with `python3 --version`)
- **pip** package installer
- **Git** version control

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
cd DEREK-BEACH
```

### 2. Check Your Environment

```bash
python3 check_environment.py
```

This will verify your system is ready for installation.

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/macOS
# OR
venv\Scripts\activate     # On Windows
```

Your prompt should now show `(venv)`.

### 4. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This will take 5-10 minutes depending on your internet connection.

### 5. Verify Installation

```bash
# Run validation script
python3 validate_choreography.py

# Run tests
pytest tests/ -v
```

Expected output: All tests should pass ✅

## What's Next?

### Run Example Usage

```python
python3 example_usage.py
```

### Start an Analysis

```python
from metadata_service import MetadataService
from event_driven_choreographer import EventDrivenChoreographer, ChoreographyConfig

# Initialize services
metadata_service = MetadataService()
metadata_service.load_all()

config = ChoreographyConfig(
    enable_traceability=True,
    deterministic_seed=42,
)

choreographer = EventDrivenChoreographer(
    metadata_service=metadata_service,
    config=config,
)

# Start analysis
correlation_id = choreographer.start_analysis(
    document_reference="/path/to/plan.pdf",
    target_question_ids=["D1-Q1", "D2-Q1"],
    plan_name="Test Plan",
    plan_text="Your plan content here",
)
```

## Troubleshooting

### Python Version Issues

```bash
# Check version
python3 --version

# If not 3.11 or 3.12, install correct version
# Ubuntu/Debian:
sudo apt install python3.12

# macOS:
brew install python@3.12
```

### Installation Fails

```bash
# Try installing packages one at a time
pip install pyyaml numpy pandas
pip install torch
pip install transformers sentence-transformers
# ... continue with other packages
```

### Import Errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Need More Help?

- **Full Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Architecture Overview**: [README.md](README.md)
- **Choreography Protocol**: [CHOREOGRAPHY_PROTOCOL.md](CHOREOGRAPHY_PROTOCOL.md)
- **Issues**: [GitHub Issues](https://github.com/PEROPOROBTANTE/DEREK-BEACH/issues)

## System Requirements

### Minimum
- RAM: 8GB
- Storage: 5GB free
- CPU: 4+ cores

### Recommended
- RAM: 16GB
- Storage: 10GB free
- CPU: 8+ cores
- GPU: NVIDIA GPU with CUDA (optional)

---

**Ready to dive deeper?** Check out [INSTALLATION.md](INSTALLATION.md) for advanced configuration, deployment options, and troubleshooting.
