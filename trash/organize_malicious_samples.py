"""
================================================================================
ORGANIZE MALICIOUS PYTHON FILES INTO PACKAGES
Tổ chức 253 malicious .py files thành package structure
================================================================================
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

def detect_malware_type(py_file_path):
    """
    Detect malware type from Python code content
    
    Returns:
        str: Malware type
    """
    
    try:
        with open(py_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read().lower()
        
        # Malware patterns
        patterns = {
            'credential_stealer': [
                '.aws/credentials', '.ssh/', 'password', 'token', 
                'cookie', 'keyring', 'credentials', 'secret'
            ],
            'backdoor': [
                'socket.connect', 'subprocess.popen', 'os.system',
                'exec(', 'eval(', 'compile(', 'backdoor'
            ],
            'reverse_shell': [
                'socket.connect', 'subprocess.pipe', '/bin/sh', 
                '/bin/bash', 'cmd.exe', 'reverse', 'shell'
            ],
            'data_exfiltration': [
                'requests.post', 'urllib.request', 'zipfile',
                'shutil.copy', 'http.client', 'exfiltrate', 'upload'
            ],
            'keylogger': [
                'pynput', 'keyboard', 'mouse', 'listener', 
                'on_press', 'keylog'
            ],
            'cryptominer': [
                'xmrig', 'miner', 'stratum', 'mining', 
                'hashrate', 'crypto'
            ],
            'ransomware': [
                'encrypt', 'ransom', 'decrypt', 'cipher',
                'fernet', 'aes', 'rsa'
            ],
            'trojan': [
                'trojan', 'payload', 'dropper', 'malware'
            ],
            'typosquatting': [
                '__import__', 'import requests', 'import urllib',
                'pip install'
            ]
        }
        
        # Check patterns
        detected_types = []
        for malware_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in code:
                    detected_types.append(malware_type)
                    break
        
        if detected_types:
            return detected_types[0]  # Return first match
        else:
            return 'unknown'
    
    except Exception as e:
        return 'unknown'


def extract_package_name(filename):
    """
    Extract package name from filename
    
    Examples:
        artifact_lab_3_package_7e532784... → artifact-lab-3
        aptx-0.2_setup.py → aptx
    """
    
    # Remove common suffixes
    name = filename.replace('_setup.py', '')
    name = name.replace('_module.py', '')
    name = name.replace('__init__.py', '')
    name = name.replace('.py', '')
    
    # Try to extract package name from various patterns
    # Pattern 1: artifact_lab_3_package_XXX → artifact-lab-3
    if '_package_' in name:
        name = name.split('_package_')[0]
    
    # Pattern 2: builderkno<br/>wer-0.1.12_XXX → builderknower
    if '-' in name and '_' in name:
        # Take part before version number
        parts = name.split('_')[0].split('-')
        name = parts[0]
    
    # Replace underscores with hyphens (PyPI convention)
    name = name.replace('_', '-')
    
    # Take first meaningful part if multiple hyphens
    if name.count('-') > 2:
        parts = name.split('-')
        name = '-'.join(parts[:2])
    
    return name.lower()


def organize_malicious_files(input_dir, output_dir, max_packages=25):
    """
    Organize malicious Python files into package structure
    
    Args:
        input_dir: Directory containing .py files (malicious_samples/)
        output_dir: Output directory (malicious_raw/)
        max_packages: Maximum number of packages to create
    """
    
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("ORGANIZING MALICIOUS PYTHON FILES")
    print("="*70)
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Max packages: {max_packages}\n")
    
    # Find all Python files
    py_files = list(input_dir.rglob('*.py'))
    
    print(f"📂 Found {len(py_files)} Python files\n")
    
    if not py_files:
        print("❌ No Python files found!")
        return 0
    
    # Group files by package name
    package_groups = {}
    
    for py_file in py_files:
        pkg_name = extract_package_name(py_file.name)
        
        if pkg_name not in package_groups:
            package_groups[pkg_name] = []
        
        package_groups[pkg_name].append(py_file)
    
    print(f"📦 Grouped into {len(package_groups)} unique packages\n")
    
    # Sort by number of files (packages with more files first)
    sorted_packages = sorted(
        package_groups.items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    # Create packages
    created = 0
    
    for pkg_name, files in sorted_packages[:max_packages]:
        if created >= max_packages:
            break
        
        print(f"[{created+1}/{max_packages}] Creating: {pkg_name} ({len(files)} files)")
        
        # Create package directory
        pkg_dir = output_dir / f"malicious-{created+1:03d}"
        pkg_dir.mkdir(exist_ok=True)
        
        # Create source directory
        source_dir = pkg_dir / 'source'
        source_dir.mkdir(exist_ok=True)
        
        # Copy Python files
        main_file = None
        
        for i, py_file in enumerate(files):
            # Determine filename
            if 'setup.py' in py_file.name:
                dest_name = 'setup.py'
            elif '__init__' in py_file.name:
                dest_name = '__init__.py'
                if not main_file:
                    main_file = dest_name
            elif i == 0:
                dest_name = '__init__.py'
                main_file = dest_name
            else:
                dest_name = f"{py_file.stem}_{i}{py_file.suffix}"
            
            dest_file = source_dir / dest_name
            
            try:
                shutil.copy2(py_file, dest_file)
            except Exception as e:
                print(f"  ⚠️  Error copying {py_file.name}: {e}")
        
        print(f"  ✅ Copied {len(files)} Python files")
        
        # Detect malware type from main file
        if main_file:
            malware_type = detect_malware_type(source_dir / main_file)
        else:
            # Use first file
            first_file = list(source_dir.glob('*.py'))[0]
            malware_type = detect_malware_type(first_file)
        
        print(f"  🔍 Detected type: {malware_type}")
        
        # Calculate file hash
        file_hash = hashlib.md5()
        for py_file in source_dir.glob('*.py'):
            with open(py_file, 'rb') as f:
                file_hash.update(f.read())
        
        # Create metadata
        metadata = {
            'package_name': pkg_name,
            'malicious': True,
            'malware_type': malware_type,
            'source': 'real_malicious_samples',
            'version': '1.0.0',
            'author': 'unknown',
            'file_count': len(files),
            'file_hash': file_hash.hexdigest(),
            'original_files': [f.name for f in files],
            'created_at': datetime.now().isoformat()
        }
        
        with open(pkg_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Created metadata.json\n")
        
        created += 1
    
    return created


def main():
    """Main function"""
    
    print("\n" + "="*70)
    print("MALICIOUS SAMPLES ORGANIZER")
    print("="*70)
    
    print("\n📋 This script will:")
    print("1. Find all .py files in malicious_samples/")
    print("2. Group them by package name")
    print("3. Create package structure in malicious_raw/")
    print("4. Detect malware type")
    print("5. Generate metadata.json")
    print()
    
    # Get input directory
    input_dir = input("Enter malicious_samples path (default: D:/NT521/DOAN/TIER2/malicious_samples): ").strip()
    if not input_dir:
        input_dir = 'D:/NT521/DOAN/TIER2/malicious_samples'
    
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        print(f"\n❌ Directory not found: {input_dir}")
        return
    
    # Get output directory
    output_dir = input("Enter output path (default: D:/NT521/DOAN/real_test_dataset/malicious_raw): ").strip()
    if not output_dir:
        output_dir = 'D:/NT521/DOAN/real_test_dataset/malicious_raw'
    
    output_dir = Path(output_dir)
    
    # Get max packages
    max_input = input("How many packages to create? (default: 25): ").strip()
    max_packages = int(max_input) if max_input.isdigit() else 25
    
    print()
    response = input(f"Create {max_packages} packages from {input_dir}? (y/n): ").lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    # Organize files
    created = organize_malicious_files(input_dir, output_dir, max_packages)
    
    # Summary
    print("\n" + "="*70)
    print("ORGANIZATION COMPLETE")
    print("="*70)
    print(f"✅ Created: {created} packages")
    print(f"📂 Location: {output_dir}")
    print()
    print("Next steps:")
    print("1. Verify packages in malicious_raw/")
    print("2. Run: python download_real_benign.py")
    print("3. Run: python create_universal_test_dataset.py")
    print("="*70)


if __name__ == '__main__':
    main()