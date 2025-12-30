"""
================================================================================
DOWNLOAD REAL BENIGN PACKAGES FROM PYPI
Download top popular packages với metadata thật
================================================================================
"""

import os
import sys
import json
import time
import shutil
import tarfile
import zipfile
import requests
import subprocess
from pathlib import Path
from datetime import datetime

# Top 25 popular PyPI packages
BENIGN_PACKAGES = [
    'requests',
    'urllib3', 
    'certifi',
    'setuptools',
    'pip',
    'wheel',
    'six',
    'python-dateutil',
    'idna',
    'charset-normalizer',
    'numpy',
    'pandas',
    'pytest',
    'click',
    'pyyaml',
    'packaging',
    'attrs',
    'jinja2',
    'markupsafe',
    'werkzeug',
    'flask',
    'cryptography',
    'boto3',
    's3transfer',
    'botocore'
]

def get_pypi_metadata(package_name):
    """
    Lấy metadata từ PyPI JSON API
    
    Returns:
        dict: Package metadata hoặc None nếu fail
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        print(f"  Fetching metadata from {url}...")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract useful info
        info = data.get('info', {})
        
        metadata = {
            'package_name': package_name,
            'version': info.get('version', ''),
            'author': info.get('author', ''),
            'author_email': info.get('author_email', ''),
            'summary': info.get('summary', ''),
            'description': info.get('description', ''),
            'home_page': info.get('home_page', ''),
            'project_url': info.get('project_url', ''),
            'license': info.get('license', ''),
            'classifiers': info.get('classifiers', []),
            'requires_python': info.get('requires_python', ''),
            'requires_dist': info.get('requires_dist', []),
            'project_urls': info.get('project_urls', {}),
        }
        
        # Get download stats (if available)
        # Note: PyPI doesn't provide download stats in JSON API
        # We'll use placeholder values
        metadata['downloads_last_month'] = None  # Not available
        
        # Calculate age (from upload time)
        releases = data.get('releases', {})
        if releases and info.get('version'):
            version_data = releases.get(info['version'], [])
            if version_data:
                upload_time = version_data[0].get('upload_time', '')
                if upload_time:
                    upload_date = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                    age_days = (datetime.now(upload_date.tzinfo) - upload_date).days
                    metadata['age_days'] = age_days
        
        return metadata
        
    except Exception as e:
        print(f"  ❌ Error fetching metadata: {e}")
        return None


def download_package_source(package_name, output_dir):
    """
    Download package source code (.tar.gz hoặc .zip)
    
    Args:
        package_name: Package name
        output_dir: Directory to save
    
    Returns:
        Path to source code hoặc None
    """
    try:
        pkg_dir = Path(output_dir) / package_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  Downloading source...")
        
        # Download using pip (gets .tar.gz or .whl)
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'download',
            '--no-deps',  # No dependencies
            '--no-binary', ':all:',  # Source only, no wheels
            package_name,
            '-d', str(pkg_dir)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"  ⚠️  Failed to download source: {result.stderr}")
            return None
        
        # Find downloaded file
        downloaded_files = list(pkg_dir.glob('*.tar.gz')) + list(pkg_dir.glob('*.zip'))
        
        if not downloaded_files:
            print(f"  ⚠️  No source archive found")
            return None
        
        archive_file = downloaded_files[0]
        print(f"  Downloaded: {archive_file.name}")
        
        # Extract archive
        extract_dir = pkg_dir / 'source'
        extract_dir.mkdir(exist_ok=True)
        
        print(f"  Extracting...")
        
        if archive_file.suffix == '.gz':
            with tarfile.open(archive_file, 'r:gz') as tar:
                tar.extractall(extract_dir)
        elif archive_file.suffix == '.zip':
            with zipfile.ZipFile(archive_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        
        # Find Python files
        py_files = list(extract_dir.rglob('*.py'))
        
        if not py_files:
            print(f"  ⚠️  No Python files found in archive")
            return None
        
        print(f"  ✅ Found {len(py_files)} Python files")
        
        # Keep archive for reference
        return extract_dir
        
    except subprocess.TimeoutExpired:
        print(f"  ❌ Download timeout")
        return None
    except Exception as e:
        print(f"  ❌ Error downloading: {e}")
        return None


def get_main_python_file(source_dir):
    """
    Tìm file Python chính trong package
    
    Priority:
    1. __init__.py in main package folder
    2. main.py, app.py, cli.py
    3. First .py file found
    """
    source_dir = Path(source_dir)
    
    # Find package directory (usually has same name as package)
    subdirs = [d for d in source_dir.iterdir() if d.is_dir()]
    
    if not subdirs:
        return None
    
    # Usually first subdir is the extracted folder
    main_dir = subdirs[0]
    
    # Look for __init__.py
    init_files = list(main_dir.rglob('__init__.py'))
    if init_files:
        # Return first __init__.py
        return init_files[0]
    
    # Look for common entry points
    for name in ['main.py', 'app.py', 'cli.py', '__main__.py']:
        files = list(main_dir.rglob(name))
        if files:
            return files[0]
    
    # Return any .py file
    py_files = list(main_dir.rglob('*.py'))
    if py_files:
        return py_files[0]
    
    return None


def main():
    """Download benign packages"""
    
    print("\n" + "="*70)
    print("DOWNLOADING REAL BENIGN PACKAGES FROM PYPI")
    print("="*70)
    
    output_dir = Path('D:/NT521/DOAN/real_test_dataset/benign_raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    failed = []
    
    print(f"\nDownloading {len(BENIGN_PACKAGES)} packages to {output_dir}\n")
    
    for i, pkg_name in enumerate(BENIGN_PACKAGES, 1):
        print(f"[{i}/{len(BENIGN_PACKAGES)}] Processing: {pkg_name}")
        print("-" * 70)
        
        try:
            # Get metadata
            metadata = get_pypi_metadata(pkg_name)
            
            if not metadata:
                print(f"  ❌ Failed to get metadata\n")
                failed.append(pkg_name)
                continue
            
            # Download source
            source_dir = download_package_source(pkg_name, output_dir)
            
            if not source_dir:
                print(f"  ❌ Failed to download source\n")
                failed.append(pkg_name)
                continue
            
            # Get main Python file
            main_file = get_main_python_file(source_dir)
            
            if not main_file:
                print(f"  ⚠️  No suitable Python file found\n")
                failed.append(pkg_name)
                continue
            
            print(f"  📄 Main file: {main_file.name}")
            
            # Save metadata
            pkg_dir = output_dir / pkg_name
            metadata_file = pkg_dir / 'metadata.json'
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Saved metadata to {metadata_file.name}")
            
            success_count += 1
            print(f"  ✅ Success!\n")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}\n")
            failed.append(pkg_name)
            continue
    
    # Summary
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)
    print(f"Total packages: {len(BENIGN_PACKAGES)}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed packages:")
        for pkg in failed:
            print(f"  - {pkg}")
    
    print(f"\n📂 Output directory: {output_dir}")
    print("="*70)


if __name__ == '__main__':
    main()