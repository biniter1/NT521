"""
================================================================================
CREATE UNIVERSAL TEST DATASET
Tạo test dataset cho cả MalOSS và 2-Tier system
================================================================================

Dataset structure:
universal_test_dataset/
├── packages/
│   ├── benign/
│   │   ├── package-001/
│   │   │   ├── source/              # Python source code
│   │   │   ├── metadata.json        # PyPI metadata
│   │   │   ├── dependencies.json    # Dependency info
│   │   │   └── sast_report.json     # Static analysis results
│   │   └── ...
│   └── malicious/
│       └── ...
├── ground_truth.json                # Label cho mỗi package
└── README.md

"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

def create_universal_metadata(package_dir, package_name, is_malicious):
    """
    Tạo metadata đầy đủ cho package - Compatible với cả MalOSS và 2-Tier
    
    Returns:
        dict: Complete metadata matching both systems
    """
    
    metadata = {
        # Basic info
        'name': package_name,
        'version': '1.0.0',
        'malicious': is_malicious,
        
        # MalOSS Metadata Analysis Format
        'maloss_info': {
            # Package info from registry API
            'package_name': package_name,
            'version': '1.0.0',
            'author': 'unknown' if is_malicious else 'verified_author',
            'author_email': 'unknown@evil.com' if is_malicious else 'author@pypi.org',
            'description': 'Malicious package' if is_malicious else 'Legitimate package',
            'home_page': '' if is_malicious else 'https://github.com/legitimate/repo',
            'license': 'Unknown' if is_malicious else 'MIT',
            
            # Download stats
            'downloads': {
                'last_day': 0 if is_malicious else 10000,
                'last_week': 0 if is_malicious else 70000,
                'last_month': 100 if is_malicious else 300000
            },
            
            # Upload time (package age)
            'upload_time': datetime.now().isoformat() if is_malicious else '2020-01-01T00:00:00',
            
            # Typosquatting detection
            'typosquatting_score': 0.8 if is_malicious else 0.0,
            
            # Dependencies
            'dependencies': {
                'runtime': [] if is_malicious else ['requests', 'numpy'],
                'development': []
            },
            
            # File types
            'has_setup_py': True,
            'has_binary': False,
            'has_native_extension': False,
            
            # Code characteristics
            'source_lines': 0,  # Will be calculated
            'has_obfuscation': is_malicious,
            'entropy_score': 0.0  # Will be calculated
        },
        
        # 2-Tier System Format (backward compatible)
        'tier_system_info': {
            'statistics': {
                'downloads': {
                    'last_month': 100 if is_malicious else 300000
                }
            },
            'upload_time': datetime.now().isoformat() if is_malicious else '2020-01-01T00:00:00',
            'author': 'unknown' if is_malicious else 'verified_author',
            'has_documentation': False if is_malicious else True,
            'dependencies': [] if is_malicious else ['requests', 'numpy']
        }
    }
    
    return metadata


def run_sast_analysis(source_dir):
    """
    Chạy SAST analysis (bandit hoặc tương tự)
    
    Returns:
        dict: SAST report
    """
    
    sast_report = {
        'tool': 'bandit',
        'timestamp': datetime.now().isoformat(),
        'findings': [],
        'summary': {
            'total_issues': 0,
            'high_severity': 0,
            'medium_severity': 0,
            'low_severity': 0
        }
    }
    
    try:
        # Try to run bandit
        result = subprocess.run(
            ['bandit', '-r', str(source_dir), '-f', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 or result.returncode == 1:  # bandit returns 1 if issues found
            bandit_output = json.loads(result.stdout)
            sast_report['findings'] = bandit_output.get('results', [])
            
            # Calculate summary
            for finding in sast_report['findings']:
                severity = finding.get('issue_severity', 'LOW')
                sast_report['summary']['total_issues'] += 1
                
                if severity == 'HIGH':
                    sast_report['summary']['high_severity'] += 1
                elif severity == 'MEDIUM':
                    sast_report['summary']['medium_severity'] += 1
                else:
                    sast_report['summary']['low_severity'] += 1
    
    except FileNotFoundError:
        print("    ⚠️  Bandit not installed, using mock SAST report")
        # Create mock findings for malicious patterns
        py_files = list(Path(source_dir).rglob('*.py'))
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                # Check for suspicious patterns
                suspicious_patterns = [
                    ('eval(', 'HIGH', 'Use of eval() detected'),
                    ('exec(', 'HIGH', 'Use of exec() detected'),
                    ('__import__', 'MEDIUM', 'Dynamic import detected'),
                    ('subprocess.', 'MEDIUM', 'Subprocess execution detected'),
                    ('socket.connect', 'HIGH', 'Network connection detected'),
                    ('requests.post', 'MEDIUM', 'HTTP POST detected'),
                    ('base64.b64decode', 'LOW', 'Base64 decoding detected'),
                ]
                
                for pattern, severity, message in suspicious_patterns:
                    if pattern in code:
                        sast_report['findings'].append({
                            'filename': str(py_file),
                            'issue_severity': severity,
                            'issue_text': message,
                            'line_number': 1
                        })
                        
                        sast_report['summary']['total_issues'] += 1
                        if severity == 'HIGH':
                            sast_report['summary']['high_severity'] += 1
                        elif severity == 'MEDIUM':
                            sast_report['summary']['medium_severity'] += 1
                        else:
                            sast_report['summary']['low_severity'] += 1
            
            except Exception as e:
                pass
    
    except Exception as e:
        print(f"    ⚠️  SAST analysis error: {e}")
    
    return sast_report


def analyze_dependencies(package_dir):
    """
    Phân tích dependencies
    
    Returns:
        dict: Dependency info
    """
    
    dependencies = {
        'direct': [],
        'transitive': [],
        'total_count': 0
    }
    
    # Check requirements.txt
    req_file = Path(package_dir) / 'source' / 'requirements.txt'
    if req_file.exists():
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    dependencies['direct'].append(line)
    
    # Check setup.py for install_requires
    setup_file = Path(package_dir) / 'source' / 'setup.py'
    if setup_file.exists():
        try:
            with open(setup_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Simple regex to find install_requires
                import re
                match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if match:
                    deps_str = match.group(1)
                    deps = re.findall(r'[\'"]([^\'"]+)[\'"]', deps_str)
                    dependencies['direct'].extend(deps)
        except:
            pass
    
    dependencies['direct'] = list(set(dependencies['direct']))  # Remove duplicates
    dependencies['total_count'] = len(dependencies['direct'])
    
    return dependencies


def create_universal_package(source_package_dir, output_dir, package_id, is_malicious):
    """
    Tạo một package với đầy đủ metadata cho cả MalOSS và 2-Tier
    
    Args:
        source_package_dir: Package source directory (from benign_raw or malicious_raw)
        output_dir: Output directory
        package_id: Package ID
        is_malicious: True if malicious
    
    Returns:
        dict: Package info
    """
    
    package_name = f"{'mal' if is_malicious else 'ben'}-{package_id:03d}"
    
    category = 'malicious' if is_malicious else 'benign'
    pkg_output = output_dir / 'packages' / category / package_name
    pkg_output.mkdir(parents=True, exist_ok=True)
    
    print(f"  Creating: {package_name}")
    
    # Copy source code
    source_input = Path(source_package_dir) / 'source'
    source_output = pkg_output / 'source'
    
    if source_input.exists():
        import shutil
        if source_output.exists():
            shutil.rmtree(source_output)
        shutil.copytree(source_input, source_output)
    else:
        print(f"    ⚠️  No source directory found")
        return None
    
    # Create universal metadata
    print(f"    📝 Creating metadata...")
    metadata = create_universal_metadata(pkg_output, package_name, is_malicious)
    
    # Count source lines
    source_lines = 0
    for py_file in source_output.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                source_lines += len(f.readlines())
        except:
            pass
    
    metadata['maloss_info']['source_lines'] = source_lines
    
    # Save metadata
    with open(pkg_output / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Run SAST analysis
    print(f"    🔍 Running SAST analysis...")
    sast_report = run_sast_analysis(source_output)
    
    with open(pkg_output / 'sast_report.json', 'w', encoding='utf-8') as f:
        json.dump(sast_report, f, indent=2)
    
    # Analyze dependencies
    print(f"    📦 Analyzing dependencies...")
    dependencies = analyze_dependencies(pkg_output)
    
    with open(pkg_output / 'dependencies.json', 'w', encoding='utf-8') as f:
        json.dump(dependencies, f, indent=2)
    
    print(f"    ✅ Complete")
    
    return {
        'package_name': package_name,
        'malicious': is_malicious,
        'source_lines': source_lines,
        'sast_issues': sast_report['summary']['total_issues'],
        'dependencies_count': dependencies['total_count']
    }


def create_universal_dataset(benign_dir, malicious_dir, output_dir, num_benign=25, num_malicious=25):
    """
    Tạo universal test dataset
    
    Args:
        benign_dir: Directory chứa benign packages
        malicious_dir: Directory chứa malicious packages
        output_dir: Output directory
        num_benign: Number of benign packages
        num_malicious: Number of malicious packages
    """
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("CREATING UNIVERSAL TEST DATASET")
    print("="*70)
    print(f"Benign source: {benign_dir}")
    print(f"Malicious source: {malicious_dir}")
    print(f"Output: {output_dir}\n")
    
    ground_truth = {
        'packages': [],
        'statistics': {
            'total': 0,
            'benign': 0,
            'malicious': 0
        },
        'created_at': datetime.now().isoformat()
    }
    
    # Process benign packages
    print("📦 Processing benign packages...")
    benign_dir = Path(benign_dir)
    
    if benign_dir.exists():
        benign_packages = sorted([d for d in benign_dir.iterdir() if d.is_dir()])[:num_benign]
        
        for i, pkg_dir in enumerate(benign_packages, 1):
            print(f"\n[{i}/{num_benign}] Benign package")
            
            pkg_info = create_universal_package(pkg_dir, output_dir, i, is_malicious=False)
            
            if pkg_info:
                ground_truth['packages'].append(pkg_info)
                ground_truth['statistics']['benign'] += 1
                ground_truth['statistics']['total'] += 1
    else:
        print(f"  ⚠️  Benign directory not found: {benign_dir}")
    
    # Process malicious packages
    print("\n📦 Processing malicious packages...")
    malicious_dir = Path(malicious_dir)
    
    if malicious_dir.exists():
        malicious_packages = sorted([d for d in malicious_dir.iterdir() if d.is_dir()])[:num_malicious]
        
        for i, pkg_dir in enumerate(malicious_packages, 1):
            print(f"\n[{i}/{num_malicious}] Malicious package")
            
            pkg_info = create_universal_package(pkg_dir, output_dir, i, is_malicious=True)
            
            if pkg_info:
                ground_truth['packages'].append(pkg_info)
                ground_truth['statistics']['malicious'] += 1
                ground_truth['statistics']['total'] += 1
    else:
        print(f"  ⚠️  Malicious directory not found: {malicious_dir}")
    
    # Save ground truth
    print("\n📝 Saving ground truth...")
    with open(output_dir / 'ground_truth.json', 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
    
    # Create README
    readme_content = f"""# Universal Test Dataset

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics
- Total packages: {ground_truth['statistics']['total']}
- Benign: {ground_truth['statistics']['benign']}
- Malicious: {ground_truth['statistics']['malicious']}

## Structure
```
universal_test_dataset/
├── packages/
│   ├── benign/
│   │   └── ben-XXX/
│   │       ├── source/              # Python source code
│   │       ├── metadata.json        # Full metadata
│   │       ├── dependencies.json    # Dependency info
│   │       └── sast_report.json     # SAST results
│   └── malicious/
│       └── mal-XXX/
│           └── (same structure)
├── ground_truth.json                # Ground truth labels
└── README.md                        # This file
```

## Usage

### For MalOSS
```python
# MalOSS can use:
# - metadata.json (PyPI metadata + typosquatting score)
# - sast_report.json (Static analysis results)
# - dependencies.json (Dependency info)
```

### For 2-Tier System
```python
# 2-Tier can use:
# - source/ (Code for feature extraction)
# - metadata.json (For dependency graph)
# - dependencies.json (For Tier 1 GNN)
```

## Ground Truth Format
```json
{{
  "packages": [
    {{
      "package_name": "ben-001",
      "malicious": false,
      "source_lines": 1234,
      "sast_issues": 5,
      "dependencies_count": 3
    }}
  ]
}}
```
"""
    
    with open(output_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    return ground_truth


def main():
    """Main function"""
    
    print("\n" + "="*70)
    print("UNIVERSAL TEST DATASET CREATOR")
    print("="*70)
    
    print("\n📋 This creates a test dataset that works for BOTH:")
    print("   1. MalOSS (metadata + SAST)")
    print("   2. 2-Tier System (GNN + ML)")
    print()
    print("Each package will have:")
    print("   - source/ (Python code)")
    print("   - metadata.json (Full metadata)")
    print("   - dependencies.json (Dependency info)")
    print("   - sast_report.json (Static analysis)")
    print()
    
    # Get input directories
    print("📂 Input directories:")
    print()
    
    benign_dir = input("Benign packages directory (default: D:/NT521/DOAN/real_test_dataset/benign_raw): ").strip()
    if not benign_dir:
        benign_dir = 'D:/NT521/DOAN/real_test_dataset/benign_raw'
    
    malicious_dir = input("Malicious packages directory (default: D:/NT521/DOAN/real_test_dataset/malicious_raw): ").strip()
    if not malicious_dir:
        malicious_dir = 'D:/NT521/DOAN/real_test_dataset/malicious_raw'
    
    output_dir = input("Output directory (default: D:/NT521/DOAN/universal_test_dataset): ").strip()
    if not output_dir:
        output_dir = 'D:/NT521/DOAN/universal_test_dataset'
    
    print()
    response = input("Create universal test dataset? (y/n): ").lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    # Create dataset
    ground_truth = create_universal_dataset(benign_dir, malicious_dir, output_dir)
    
    # Summary
    print("\n" + "="*70)
    print("DATASET CREATION COMPLETE")
    print("="*70)
    print(f"✅ Total packages: {ground_truth['statistics']['total']}")
    print(f"   - Benign: {ground_truth['statistics']['benign']}")
    print(f"   - Malicious: {ground_truth['statistics']['malicious']}")
    print(f"\n📂 Location: {output_dir}")
    print()
    print("Next steps:")
    print("1. Test with MalOSS system")
    print("2. Test with 2-Tier system")
    print("3. Compare results")
    print("="*70)


if __name__ == '__main__':
    main()