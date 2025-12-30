#!/usr/bin/env python3
"""
Download malicious samples from https://github.com/lxyeternal/pypi_malregistry
Strategy: Download individual files via GitHub API, không clone 15GB repo
"""

import requests
import base64
import time
from pathlib import Path

# Chọn các package đại diện cho từng loại tấn công
# Format: (package_name, version, attack_type)
SELECTED_PACKAGES = [
    # Backdoor/Reverse Shell
    ("pyspliter", "1.0.2", "backdoor"),
    ("builderknower", "0.1.12", "backdoor"),
    ("rock51", "1.0.0", "backdoor"),
    
    # Data Exfiltration
    ("vertica_parser", "99.9.9", "exfiltration"),
    ("lr_utils_lib", "1.0.0", "exfiltration"),
    ("thesis-package", "1.0.0", "exfiltration"),
    ("puffioner131", "9999", "exfiltration"),
    
    # Obfuscated
    ("auto_scrubber", "0.1", "obfuscated"),
    ("xFileSyncerx", "0.0.2", "obfuscated"),
    ("cipherbcrypt", "1.4", "obfuscated"),
    ("pyzelf", "2.0.1", "obfuscated"),
    
    # Typosquatting
    ("requestn", "8.0", "typosquatting"),
    ("testjsonn1", "0.7", "typosquatting"),
    ("urllib7", "1.26.12", "typosquatting"),
    ("studypong", "10.45", "typosquatting"),
    
    # Discord/Telegram
    ("discomusic", "0.0.3", "webhook"),
    ("proxyfullscrapers", "0.1", "webhook"),
    
    # Persistence
    ("utilitytool2", "0.0.9", "persistence"),
    ("juphelper", "0.1.6", "persistence"),
    
    # Misc
    ("netfetcher", "1.7.5", "misc"),
    ("h99ai", "0.1.0", "misc"),
]

def download_file_from_github(repo_owner, repo_name, file_path):
    """Download single file via GitHub API"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    
    try:
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if 'content' in data:
                # Decode base64 content
                content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                return content
        
        # Rate limit
        if resp.status_code == 403:
            print("   ⚠️  Rate limit, waiting 60s...")
            time.sleep(60)
            return download_file_from_github(repo_owner, repo_name, file_path)
        
        return None
    except:
        return None

def try_download_package_files(pkg_name, version, output_dir):
    """Thử download các file Python từ package"""
    repo_owner = "lxyeternal"
    repo_name = "pypi_malregistry"
    
    # Các vị trí có thể có file setup.py hoặc __init__.py
    possible_paths = [
        f"{pkg_name}/{version}/setup.py",
        f"{pkg_name}/{version}/__init__.py",
        f"{pkg_name}/{version}/{pkg_name}/__init__.py",
        f"{pkg_name}/{version}/{pkg_name}/setup.py",
    ]
    
    downloaded = 0
    
    for path in possible_paths:
        content = download_file_from_github(repo_owner, repo_name, path)
        
        if content and len(content) > 10:  # Valid file
            # Save
            filename = f"{pkg_name}_{version}_{Path(path).name}"
            (output_dir / filename).write_text(content, encoding='utf-8')
            downloaded += 1
            time.sleep(0.5)  # Rate limit protection
    
    return downloaded

def main():
    output = Path("malicious_samples")
    output.mkdir(exist_ok=True)
    
    print("Downloading malicious samples from GitHub...")
    print(f"Target: ~{len(SELECTED_PACKAGES)} packages")
    print("⚠️  Note: GitHub API limit is 60 requests/hour\n")
    
    total_files = 0
    successful = 0
    
    for idx, (pkg, ver, attack_type) in enumerate(SELECTED_PACKAGES, 1):
        print(f"[{idx}/{len(SELECTED_PACKAGES)}] {pkg} ({attack_type})...", end=" ")
        
        count = try_download_package_files(pkg, ver, output)
        
        if count > 0:
            print(f"✅ {count} files")
            total_files += count
            successful += 1
        else:
            print("❌")
    
    print(f"\n{'='*70}")
    print(f"✅ Downloaded {total_files} files from {successful}/{len(SELECTED_PACKAGES)} packages")
    print(f"📂 Saved to: {output}/")
    print(f"{'='*70}")
    
    if total_files < 10:
        print("\n⚠️  Too few files downloaded (GitHub API limit or removed packages)")
        print("Alternative: Use embedded malicious samples in training script")

if __name__ == "__main__":
    main()