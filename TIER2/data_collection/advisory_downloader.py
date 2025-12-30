"""
PyPI Advisory Database Downloader
Downloads malware info from PyPI Advisory Database
Source: https://github.com/pypa/advisory-database
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import logging
import time
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvisoryDownloader:
    def __init__(self, output_dir: str = "real_packages_v3/malicious/advisory"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.repo_url = "https://github.com/pypa/advisory-database.git"
        self.temp_repo_dir = Path("temp_advisory_repo")
        
        self.metadata = {
            "source": "PyPI-Advisory-Database",
            "url": self.repo_url,
            "advisories": []
        }
    
    def clone_repository(self) -> bool:
        """Clone the PyPI Advisory Database"""
        try:
            logger.info(f"Cloning repository: {self.repo_url}")
            
            if self.temp_repo_dir.exists():
                shutil.rmtree(self.temp_repo_dir)
            
            result = subprocess.run(
                ["git", "clone", "--depth", "1", self.repo_url, str(self.temp_repo_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                return False
            
            logger.info("✅ Repository cloned")
            return True
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
    
    def find_advisory_files(self) -> List[Path]:
        """Find all advisory YAML files"""
        advisory_files = []
        
        search_paths = [
            self.temp_repo_dir / "vulns",
            self.temp_repo_dir / "malware",
            self.temp_repo_dir
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                advisory_files.extend(list(search_path.glob("**/*.yaml")))
                advisory_files.extend(list(search_path.glob("**/*.yml")))
        
        logger.info(f"Found {len(advisory_files)} advisory files")
        return advisory_files
    
    def parse_advisory(self, yaml_file: Path) -> Optional[Dict]:
        """Parse advisory YAML to extract malicious package info"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            advisory_info = {
                "advisory_id": yaml_file.stem,
                "yaml_file": str(yaml_file.relative_to(self.temp_repo_dir))
            }
            
            # Extract package name
            if 'package' in data:
                advisory_info['package_name'] = data['package'].get('name', '')
            elif 'id' in data:
                advisory_info['package_name'] = data['id'].split('/')[0] if '/' in data['id'] else ''
            
            # Extract details
            if 'details' in data:
                advisory_info['details'] = data['details']
            elif 'summary' in data:
                advisory_info['details'] = data['summary']
            
            # Check if malware
            is_malware = any(keyword in str(data).lower() 
                           for keyword in ['malware', 'malicious', 'backdoor', 'trojan'])
            
            advisory_info['is_malware'] = is_malware
            
            return advisory_info
            
        except Exception as e:
            logger.error(f"Error parsing {yaml_file}: {e}")
            return None
    
    def create_malicious_sample(self, advisory_info: Dict) -> Optional[Path]:
        """Create Python file representing malicious package"""
        try:
            package_name = advisory_info.get('package_name', 'unknown')
            
            py_dir = self.output_dir / "advisory_samples"
            py_dir.mkdir(exist_ok=True)
            
            safe_name = "".join(c for c in package_name if c.isalnum() or c in ('_', '-'))
            py_file = py_dir / f"{safe_name}_{advisory_info['advisory_id']}.py"
            
            content = f'''"""
Malicious Package from PyPI Advisory Database

Package: {package_name}
Advisory ID: {advisory_info['advisory_id']}
Details: {advisory_info.get('details', 'No details')[:200]}

This is a placeholder representing a known malicious package.
Actual malicious code removed for safety.

Source: PyPI Advisory Database
"""

# MALICIOUS PACKAGE MARKER
__malicious__ = True
__package_name__ = "{package_name}"
__advisory_id__ = "{advisory_info['advisory_id']}"

# Common malicious indicators (sanitized)
import base64
import subprocess
import socket

# Flagged as malicious by PyPI
# Original functionality removed
'''
            
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Created sample: {py_file.name}")
            return py_file
            
        except Exception as e:
            logger.error(f"Error creating sample: {e}")
            return None
    
    def process_advisories(self, advisory_files: List[Path]) -> int:
        """Process all advisory files"""
        processed = 0
        
        logger.info(f"Processing {len(advisory_files)} advisories...")
        
        for yaml_file in advisory_files:
            try:
                advisory_info = self.parse_advisory(yaml_file)
                
                if not advisory_info or not advisory_info.get('is_malware'):
                    continue
                
                sample_file = self.create_malicious_sample(advisory_info)
                if sample_file:
                    advisory_info['sample_file'] = str(sample_file)
                
                self.metadata['advisories'].append(advisory_info)
                processed += 1
                
                if processed % 10 == 0:
                    logger.info(f"Processed {processed} malware advisories")
                
            except Exception as e:
                logger.error(f"Error processing {yaml_file}: {e}")
        
        logger.info(f"✅ Processed {processed} malware advisories")
        return processed
    
    def save_metadata(self):
        """Save metadata"""
        metadata_file = self.output_dir / "advisory_metadata.json"
        
        self.metadata["total_advisories"] = len(self.metadata["advisories"])
        self.metadata["download_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_file}")
    
    def cleanup(self):
        """Remove temporary files"""
        if self.temp_repo_dir.exists():
            shutil.rmtree(self.temp_repo_dir)
            logger.info("Cleaned up")
    
    def download_all(self) -> bool:
        """Main download method"""
        try:
            if not self.clone_repository():
                return False
            
            advisory_files = self.find_advisory_files()
            
            if not advisory_files:
                logger.error("No advisory files found")
                return False
            
            processed = self.process_advisories(advisory_files)
            
            if processed == 0:
                logger.warning("No malware advisories found")
                return False
            
            self.save_metadata()
            self.cleanup()
            
            logger.info("✅ Download complete!")
            return True
            
        except Exception as e:
            logger.error(f"Error: {e}")
            self.cleanup()
            return False


def main():
    print("=" * 60)
    print("PyPI Advisory Database Downloader")
    print("=" * 60)
    
    downloader = AdvisoryDownloader()
    success = downloader.download_all()
    
    if success:
        print(f"\n✅ SUCCESS!")
        print(f"📦 Processed {len(downloader.metadata['advisories'])} malware advisories")
        print(f"📁 Location: {downloader.output_dir}")
    else:
        print("\n❌ FAILED!")
    
    return success


if __name__ == "__main__":
    main()