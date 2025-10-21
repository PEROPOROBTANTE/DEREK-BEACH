#!/usr/bin/env python3
"""
Environment Check Script for DEREK-BEACH
Verifies that the system meets all requirements for installation.
"""

import sys
import platform
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and (version.minor == 11 or version.minor == 12):
        print("✓ Python version is compatible")
        return True
    elif version.major == 3 and version.minor >= 11:
        print("⚠ Python version is newer than tested (3.11-3.12), may work")
        return True
    else:
        print("✗ Python version must be 3.11 or 3.12 (recommended)")
        return False


def check_pip():
    """Check if pip is available."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ pip is available: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("✗ pip is not available")
        return False


def check_system_dependencies():
    """Check for common system dependencies."""
    print("\nSystem Dependencies:")
    
    dependencies = {
        "git": ["git", "--version"],
        "java": ["java", "-version"],
    }
    
    results = {}
    for name, cmd in dependencies.items():
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                check=True
            )
            print(f"✓ {name} is available")
            results[name] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠ {name} not found (required for some features)")
            results[name] = False
    
    return results


def check_virtual_environment():
    """Check if running in a virtual environment."""
    in_venv = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        print("✓ Running in a virtual environment")
        return True
    else:
        print("⚠ Not running in a virtual environment (recommended)")
        print("  Create one with: python3 -m venv venv")
        print("  Activate with: source venv/bin/activate")
        return False


def check_requirements_file():
    """Check if requirements.txt exists."""
    req_file = Path("requirements.txt")
    if req_file.exists():
        print(f"✓ requirements.txt found")
        
        # Count packages
        with open(req_file) as f:
            packages = [
                line.strip() for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        print(f"  Contains {len(packages)} package specifications")
        return True
    else:
        print("✗ requirements.txt not found")
        return False


def check_installed_packages():
    """Check if key packages are installed."""
    key_packages = [
        'yaml',      # pyyaml
        'numpy',
        'pandas',
        'torch',
        'transformers',
        'sklearn',   # scikit-learn
        'pytest',
    ]
    
    print("\nInstalled Packages:")
    installed = []
    missing = []
    
    for package in key_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
            installed.append(package)
        except ImportError:
            print(f"✗ {package} is not installed")
            missing.append(package)
    
    return len(missing) == 0


def main():
    """Run all environment checks."""
    print("=" * 70)
    print("DEREK-BEACH Environment Check")
    print("=" * 70)
    print()
    
    print("System Information:")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print()
    
    checks = {
        "Python Version": check_python_version(),
        "pip": check_pip(),
        "Virtual Environment": check_virtual_environment(),
        "requirements.txt": check_requirements_file(),
    }
    
    # Check system dependencies
    sys_deps = check_system_dependencies()
    
    print()
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    
    # Count passed checks
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    print(f"Core Requirements: {passed}/{total} passed")
    
    if sys_deps.get('java'):
        print("✓ Java available (required for tabula-py)")
    else:
        print("⚠ Java not available (install for PDF table extraction)")
    
    print()
    
    # Check if packages are installed
    try:
        packages_ok = check_installed_packages()
    except Exception as e:
        print(f"\nCould not check installed packages: {e}")
        packages_ok = False
    
    print()
    print("=" * 70)
    
    if checks["Python Version"] and checks["pip"] and checks["requirements.txt"]:
        print("✓ Environment is ready for installation")
        print()
        print("Next steps:")
        if not checks["Virtual Environment"]:
            print("1. Create virtual environment: python3 -m venv venv")
            print("2. Activate it: source venv/bin/activate")
            print("3. Install dependencies: pip install -r requirements.txt")
        else:
            if not packages_ok:
                print("1. Install dependencies: pip install -r requirements.txt")
            else:
                print("✓ All packages installed!")
                print("Run: python3 validate_choreography.py")
    else:
        print("✗ Environment needs attention")
        print()
        print("Please fix the issues above before proceeding.")
        print("See INSTALLATION.md for detailed instructions.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
