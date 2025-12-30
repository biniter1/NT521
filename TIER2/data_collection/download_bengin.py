#!/usr/bin/env python3
"""Download benign PyPI packages"""

import subprocess
import tarfile
import zipfile
import tempfile
from pathlib import Path

# 50 benign packages từ PyPI
BENIGN_PACKAGES = [
    # Web frameworks (8)
    "flask", "django", "fastapi", "starlette", "jinja2", 
    "werkzeug", "tornado", "bottle",
    
    # HTTP clients (7)
    "requests", "httpx", "aiohttp", "urllib3", "certifi",
    "httplib2", "treq",
    
    # Data science (10)
    "numpy", "pandas", "scipy", "matplotlib", "scikit-learn",
    "pillow", "seaborn", "plotly", "bokeh", "altair",
    
    # Testing (6)
    "pytest", "pytest-cov", "coverage", "mock", "tox", "nose",
    
    # CLI tools (6)
    "click", "colorama", "tqdm", "rich", "typer", "argparse",
    
    # Serialization (5)
    "pyyaml", "toml", "jsonschema", "pydantic", "marshmallow",
    
    # Utilities (4)
    "six", "python-dateutil", "pytz", "attrs",
    
    # Web scraping (4)
    "beautifulsoup4", "lxml", "scrapy", "parsel",
]

def download_package(pkg_name, output_dir):
    """Download and extract package"""
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            print(f"  {pkg_name}...", end=" ")
            
            subprocess.run(
                ["pip", "download", "--no-deps", "--no-binary", ":all:", "-d", tmpdir, pkg_name],
                capture_output=True, check=True, timeout=30
            )
            
            archive = list(Path(tmpdir).glob("*"))[0]
            pkg_dir = output_dir / pkg_name
            pkg_dir.mkdir(exist_ok=True)
            
            if archive.suffix == '.gz' or '.tar.gz' in archive.name:
                with tarfile.open(archive, 'r:gz') as tar:
                    tar.extractall(pkg_dir)
            else:
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(pkg_dir)
            
            count = len(list(pkg_dir.glob("**/*.py")))
            print(f"✅ {count} files")
            return count
        except Exception as e:
            print(f"❌")
            return 0

def main():
    output = Path("benign_packages")
    output.mkdir(exist_ok=True)
    
    print(f"Downloading 50 benign packages from PyPI...\n")
    
    total = 0
    for pkg in BENIGN_PACKAGES:
        total += download_package(pkg, output)
    
    print(f"\n✅ Total: {total} Python files in {output}/")

if __name__ == "__main__":
    main()