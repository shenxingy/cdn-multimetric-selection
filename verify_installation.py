"""
Verification script to check if all required packages are installed correctly.
Run this after setup to ensure your environment is ready.
"""

import sys
import importlib
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    return True


def check_packages():
    """Check if all essential packages can be imported"""
    packages = {
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'sklearn': 'scikit-learn',
        'matplotlib': 'Matplotlib',
        'seaborn': 'Seaborn',
        'ripe.atlas.cousteau': 'RIPE Atlas Cousteau',
        'jupyter': 'Jupyter',
        'tqdm': 'tqdm',
        'requests': 'Requests',
    }
    
    optional_packages = {
        'xgboost': 'XGBoost',
        'lightgbm': 'LightGBM',
        'plotly': 'Plotly',
    }
    
    print("\n📦 Checking required packages:")
    all_ok = True
    
    for package, name in packages.items():
        try:
            mod = importlib.import_module(package)
            version = getattr(mod, '__version__', 'installed')
            print(f"  ✓ {name}: {version}")
        except ImportError:
            print(f"  ❌ {name}: Not installed")
            all_ok = False
    
    print("\n📦 Checking optional packages:")
    for package, name in optional_packages.items():
        try:
            mod = importlib.import_module(package)
            version = getattr(mod, '__version__', 'installed')
            print(f"  ✓ {name}: {version}")
        except ImportError:
            print(f"  ⚠️  {name}: Not installed (optional)")
    
    return all_ok


def check_directories():
    """Check if project directories exist"""
    required_dirs = [
        'data/raw',
        'data/processed',
        'notebooks',
        'src',
        'results',
    ]
    
    print("\n📁 Checking project structure:")
    all_ok = True
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - Missing")
            all_ok = False
    
    return all_ok


def check_env_file():
    """Check if .env file exists and has API keys"""
    print("\n🔧 Checking configuration:")
    env_path = Path('.env')
    
    if env_path.exists():
        print("  ✓ .env file exists")
        
        # Check if API keys are configured
        with open(env_path, 'r') as f:
            content = f.read()
            if 'your_api_key_here' in content:
                print("  ⚠️  RIPE Atlas API key not configured")
                print("     Edit .env and add your API key")
                return True
            else:
                # Count how many keys are configured
                key_count = content.count('RIPE_ATLAS_API_KEY')
                print(f"  ✓ RIPE Atlas API keys configured ({key_count} keys found)")
        return True
    else:
        print("  ❌ .env file missing")
        return False


def main():
    print("=" * 60)
    print("CDN Server Selection Project - Environment Verification")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_packages(),
        check_directories(),
        check_env_file(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed! Environment is ready.")
        print("\nNext steps:")
        print("1. Start Jupyter: jupyter notebook")
        print("2. Begin with notebooks/exploratory/")
        print("3. Test RIPE Atlas connection")
    else:
        print("❌ Some checks failed. Please fix issues above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
