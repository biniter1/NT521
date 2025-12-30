"""
Dataset Merger - FOR TIER 2 TRAINING
Combines benign packages with malicious samples
"""

import os
import json
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Tier2DatasetMerger:
    def __init__(self):
        self.benign_dir = Path("real_packages_v3/benign")
        self.malicious_dir = Path("real_packages_v3/malicious/backstabber")
        self.output_dir = Path("real_packages_v3/merged")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata = {
            "dataset_name": "Tier2_Training_Dataset",
            "benign": {"count": 0, "py_files": 0},
            "malicious": {"count": 0, "py_files": 0},
            "total": 0
        }
    
    def merge(self) -> bool:
        """
        Merge strategy:
        - Benign: Copy package folders (keep structure)
        - Malicious: Copy .py files (flattened)
        """
        
        logger.info("Starting dataset merge for TIER 2...")
        
        # Step 1: Create benign directory
        benign_output = self.output_dir / "benign"
        benign_output.mkdir(exist_ok=True)
        
        # Copy benign packages
        benign_count = 0
        benign_py_count = 0
        
        for package_folder in self.benign_dir.iterdir():
            if not package_folder.is_dir():
                continue
            
            try:
                dest = benign_output / package_folder.name
                if dest.exists():
                    shutil.rmtree(dest)
                
                shutil.copytree(package_folder, dest)
                
                py_files = len(list(dest.rglob("*.py")))
                benign_py_count += py_files
                benign_count += 1
                
            except Exception as e:
                logger.error(f"Error copying {package_folder.name}: {e}")
        
        logger.info(f"✅ Copied {benign_count} benign packages ({benign_py_count} .py files)")
        
        # Step 2: Create malicious directory
        malicious_output = self.output_dir / "malicious"
        malicious_output.mkdir(exist_ok=True)
        
        # Copy malicious samples
        malicious_samples = self.malicious_dir / "samples"
        malicious_count = 0
        
        if malicious_samples.exists():
            for py_file in malicious_samples.glob("*.py"):
                try:
                    dest = malicious_output / py_file.name
                    shutil.copy2(py_file, dest)
                    malicious_count += 1
                    
                except Exception as e:
                    logger.error(f"Error copying {py_file.name}: {e}")
        
        logger.info(f"✅ Copied {malicious_count} malicious samples")
        
        # Step 3: Save metadata
        self.metadata["benign"] = {
            "count": benign_count,
            "py_files": benign_py_count
        }
        self.metadata["malicious"] = {
            "count": malicious_count,
            "py_files": malicious_count  # Each sample is 1 file
        }
        self.metadata["total"] = benign_count + malicious_count
        
        metadata_file = self.output_dir / "merge_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("TIER 2 DATASET MERGE SUMMARY")
        print("=" * 60)
        print(f"\n📊 BENIGN:")
        print(f"   Packages: {benign_count}")
        print(f"   Python files: {benign_py_count}")
        
        print(f"\n🔴 MALICIOUS:")
        print(f"   Samples: {malicious_count}")
        
        total = benign_count + malicious_count
        print(f"\n📈 TOTAL: {total} samples")
        print(f"   Benign: {benign_count} ({benign_count/total*100:.1f}%)")
        print(f"   Malicious: {malicious_count} ({malicious_count/total*100:.1f}%)")
        print("=" * 60 + "\n")
        
        return True


def main():
    print("=" * 60)
    print("TIER 2 Dataset Merger")
    print("=" * 60)
    print()
    
    merger = Tier2DatasetMerger()
    success = merger.merge()
    
    if success:
        print("✅ Merge complete!")
        print("\n📋 Next step: Feature extraction using Components A, B, C")
    else:
        print("❌ Merge failed!")
    
    return success


if __name__ == "__main__":
    main()