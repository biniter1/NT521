#!/usr/bin/env python3
"""Download packages that failed - with multiple strategies"""

import subprocess
import tarfile
import zipfile
import tempfile
import requests
from pathlib import Path
import json
import time

# Các gói thất bại từ log của bạn
FAILED_PACKAGES = [
    "numpy", "pandas", "scipy", "matplotlib", 
    "scikit-learn", "plotly", "pyyaml", "lxml"
]

def download_with_wheel(pkg_name, output_dir):
    """Strategy 1: Download wheel (binary) và extract Python files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            print(f"  📦 {pkg_name} (trying wheel)...", end=" ")
            
            # Download wheel version
            subprocess.run(
                ["pip", "download", "--no-deps", "-d", tmpdir, pkg_name],
                capture_output=True, check=True, timeout=60
            )
            
            archive = list(Path(tmpdir).glob("*"))[0]
            pkg_dir = output_dir / pkg_name
            pkg_dir.mkdir(exist_ok=True)
            
            # Extract wheel or tar.gz
            if archive.suffix == '.whl':
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(pkg_dir)
            elif '.tar.gz' in archive.name:
                with tarfile.open(archive, 'r:gz') as tar:
                    tar.extractall(pkg_dir)
            elif archive.suffix == '.zip':
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(pkg_dir)
            
            count = len(list(pkg_dir.glob("**/*.py")))
            print(f"✅ {count} files")
            return count
        except Exception as e:
            print(f"❌ {str(e)[:50]}")
            return 0

def download_from_github(pkg_name, github_url, output_dir):
    """Strategy 2: Clone from GitHub official repo"""
    try:
        print(f"  🔗 {pkg_name} (from GitHub)...", end=" ")
        
        pkg_dir = output_dir / pkg_name
        
        subprocess.run(
            ["git", "clone", "--depth", "1", github_url, str(pkg_dir)],
            capture_output=True, check=True, timeout=120
        )
        
        count = len(list(pkg_dir.glob("**/*.py")))
        print(f"✅ {count} files")
        return count
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return 0

def download_from_pypi_api(pkg_name, output_dir):
    """Strategy 3: Use PyPI JSON API to get source distribution"""
    try:
        print(f"  🌐 {pkg_name} (PyPI API)...", end=" ")
        
        # Get package info from PyPI
        resp = requests.get(f"https://pypi.org/pypi/{pkg_name}/json", timeout=10)
        data = resp.json()
        
        # Find source distribution (.tar.gz)
        sdist_url = None
        for url_info in data['urls']:
            if url_info['packagetype'] == 'sdist':
                sdist_url = url_info['url']
                break
        
        if not sdist_url:
            # Try wheel if sdist not available
            for url_info in data['urls']:
                if url_info['packagetype'] == 'bdist_wheel':
                    sdist_url = url_info['url']
                    break
        
        if not sdist_url:
            raise Exception("No distribution found")
        
        # Download file
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "package"
            
            r = requests.get(sdist_url, timeout=60)
            archive_path.write_bytes(r.content)
            
            pkg_dir = output_dir / pkg_name
            pkg_dir.mkdir(exist_ok=True)
            
            # Extract
            if '.tar.gz' in sdist_url or '.tgz' in sdist_url:
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(pkg_dir)
            elif '.whl' in sdist_url or '.zip' in sdist_url:
                with zipfile.ZipFile(archive_path) as zf:
                    zf.extractall(pkg_dir)
            
            count = len(list(pkg_dir.glob("**/*.py")))
            print(f"✅ {count} files")
            return count
            
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return 0

# GitHub URLs cho các gói phổ biến
GITHUB_REPOS = {
    "numpy": "https://github.com/numpy/numpy.git",
    "pandas": "https://github.com/pandas-dev/pandas.git",
    "scipy": "https://github.com/scipy/scipy.git",
    "matplotlib": "https://github.com/matplotlib/matplotlib.git",
    "scikit-learn": "https://github.com/scikit-learn/scikit-learn.git",
    "plotly": "https://github.com/plotly/plotly.py.git",
    "pyyaml": "https://github.com/yaml/pyyaml.git",
    "lxml": "https://github.com/lxml/lxml.git",
}

def main():
    output = Path("benign_packages")
    output.mkdir(exist_ok=True)
    
    print(f"📥 Downloading {len(FAILED_PACKAGES)} failed packages with multiple strategies...\n")
    
    total = 0
    success_count = 0
    
    for pkg in FAILED_PACKAGES:
        print(f"\n🔄 Attempting: {pkg}")
        count = 0
        
        # Strategy 1: Try wheel first (fastest)
        count = download_with_wheel(pkg, output)
        
        # Strategy 2: Try PyPI API if wheel failed
        if count == 0:
            time.sleep(1)  # Rate limiting
            count = download_from_pypi_api(pkg, output)
        
        # Strategy 3: Try GitHub as last resort
        if count == 0 and pkg in GITHUB_REPOS:
            time.sleep(1)
            count = download_from_github(pkg, GITHUB_REPOS[pkg], output)
        
        if count > 0:
            success_count += 1
            total += count
    
    print(f"\n" + "="*60)
    print(f"✅ Successfully downloaded: {success_count}/{len(FAILED_PACKAGES)} packages")
    print(f"📊 Total Python files: {total}")
    print(f"📁 Output directory: {output}/")
    print("="*60)

if __name__ == "__main__":
    main()