"""
tier2_feature_extractor.py
FINAL VERSION - Extracts 58 features using Components A, B, C
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging
from tqdm import tqdm
import traceback

# Import wrappers
from component_a_wrapper import ComponentAWrapper
from component_b_wrapper import ComponentBWrapper
from component_c_wrapper import ComponentCWrapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Tier2FeatureExtractor:
    """
    Tier 2 Feature Extractor
    Extracts 58 features: 25 (A) + 18 (B) + 15 (C)
    """
    
    def __init__(self, 
                 dataset_dir: str = "real_packages_v3/merged",
                 output_file: str = "tier2_training_data.csv"):
        
        self.dataset_dir = Path(dataset_dir)
        self.output_file = Path(output_file)
        
        self.benign_dir = self.dataset_dir / "benign"
        self.malicious_dir = self.dataset_dir / "malicious"
        
        # Initialize components
        logger.info("Initializing components...")
        self.component_a = ComponentAWrapper()
        self.component_b = ComponentBWrapper()
        self.component_c = ComponentCWrapper()
        logger.info("✅ Components initialized")
        
        self.all_features = []
    
    def get_python_code(self, file_path: Path) -> Optional[str]:
        """Read Python code from file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None
    
    def extract_features_from_code(self, code: str, identifier: str) -> Optional[Dict]:
        """
        Extract 58 features from code using Components A, B, C
        
        Returns:
            Dictionary with all features + label + metadata
        """
        if not code or len(code.strip()) == 0:
            return None
        
        try:
            features = {'identifier': identifier}
            
            # Component A: Static Analysis (25 features)
            try:
                features_a = self.component_a.analyze(code)
                for key, value in features_a.items():
                    features[f'A_{key}'] = value
            except Exception as e:
                logger.warning(f"Component A failed for {identifier}: {str(e)[:100]}")
                # Fill with zeros
                for i in range(25):
                    features[f'A_feature_{i}'] = 0
            
            # Component B: Obfuscation Detection (18 features)
            try:
                features_b = self.component_b.analyze(code)
                for key, value in features_b.items():
                    features[f'B_{key}'] = value
            except Exception as e:
                logger.warning(f"Component B failed for {identifier}: {str(e)[:100]}")
                for i in range(18):
                    features[f'B_feature_{i}'] = 0
            
            # Component C: Behavioral Analysis (15 features)
            try:
                features_c = self.component_c.analyze(code)
                for key, value in features_c.items():
                    features[f'C_{key}'] = value
            except Exception as e:
                logger.warning(f"Component C failed for {identifier}: {str(e)[:100]}")
                for i in range(15):
                    features[f'C_feature_{i}'] = 0
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for {identifier}: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def process_benign_packages(self) -> List[Dict]:
        """Process benign packages"""
        logger.info("Processing benign packages...")
        
        if not self.benign_dir.exists():
            logger.error(f"Benign directory not found: {self.benign_dir}")
            return []
        
        benign_features = []
        package_folders = list(self.benign_dir.iterdir())
        
        logger.info(f"Found {len(package_folders)} benign package folders")
        
        for package_folder in tqdm(package_folders, desc="Benign packages"):
            if not package_folder.is_dir():
                continue
            
            try:
                # Find Python files
                py_files = list(package_folder.rglob("*.py"))[:10]  # Max 10 files per package
                
                if not py_files:
                    logger.warning(f"No Python files in {package_folder.name}")
                    continue
                
                # Concatenate code from multiple files
                combined_code = ""
                for py_file in py_files:
                    code = self.get_python_code(py_file)
                    if code:
                        combined_code += code + "\n\n"
                
                if not combined_code.strip():
                    continue
                
                # Extract features
                identifier = package_folder.name
                features = self.extract_features_from_code(combined_code, identifier)
                
                if features:
                    features['label'] = 0  # Benign
                    features['source'] = 'benign'
                    features['package_name'] = package_folder.name
                    benign_features.append(features)
                    
            except Exception as e:
                logger.error(f"Error processing {package_folder.name}: {e}")
        
        logger.info(f"✅ Processed {len(benign_features)} benign packages")
        return benign_features
    
    def process_malicious_samples(self) -> List[Dict]:
        """Process malicious Python files"""
        logger.info("Processing malicious samples...")
        
        if not self.malicious_dir.exists():
            logger.error(f"Malicious directory not found: {self.malicious_dir}")
            return []
        
        malicious_features = []
        py_files = list(self.malicious_dir.glob("*.py"))
        
        logger.info(f"Found {len(py_files)} malicious Python files")
        
        for py_file in tqdm(py_files, desc="Malicious samples"):
            try:
                code = self.get_python_code(py_file)
                
                if not code or not code.strip():
                    continue
                
                identifier = py_file.stem
                features = self.extract_features_from_code(code, identifier)
                
                if features:
                    features['label'] = 1  # Malicious
                    features['source'] = 'malicious'
                    features['package_name'] = py_file.stem
                    malicious_features.append(features)
                    
            except Exception as e:
                logger.error(f"Error processing {py_file.name}: {e}")
        
        logger.info(f"✅ Processed {len(malicious_features)} malicious samples")
        return malicious_features
    
    def extract_all_features(self) -> pd.DataFrame:
        """Main extraction pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Tier 2 Feature Extraction")
        logger.info("=" * 60)
        
        # Process benign
        benign_features = self.process_benign_packages()
        
        # Process malicious
        malicious_features = self.process_malicious_samples()
        
        # Combine
        all_features = benign_features + malicious_features
        
        if not all_features:
            logger.error("No features extracted!")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(all_features)
        
        logger.info(f"\n✅ Feature extraction complete!")
        logger.info(f"   Total samples: {len(df)}")
        logger.info(f"   Benign: {len(benign_features)}")
        logger.info(f"   Malicious: {len(malicious_features)}")
        logger.info(f"   Features: {len(df.columns)} columns")
        
        return df
    
    def save_features(self, df: pd.DataFrame):
        """Save features to CSV"""
        df.to_csv(self.output_file, index=False)
        logger.info(f"✅ Features saved to {self.output_file}")
        
        # Save summary
        summary = {
            "total_samples": len(df),
            "benign_count": len(df[df['label'] == 0]),
            "malicious_count": len(df[df['label'] == 1]),
            "feature_count": len(df.columns),
            "component_a_features": len([c for c in df.columns if c.startswith('A_')]),
            "component_b_features": len([c for c in df.columns if c.startswith('B_')]),
            "component_c_features": len([c for c in df.columns if c.startswith('C_')]),
        }
        
        summary_file = self.output_file.parent / "feature_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"✅ Summary saved to {summary_file}")
    
    def print_summary(self, df: pd.DataFrame):
        """Print extraction summary"""
        print("\n" + "=" * 60)
        print("TIER 2 FEATURE EXTRACTION SUMMARY")
        print("=" * 60)
        
        print(f"\n📊 DATASET:")
        print(f"   Total samples: {len(df)}")
        print(f"   Benign: {len(df[df['label'] == 0])} ({len(df[df['label'] == 0])/len(df)*100:.1f}%)")
        print(f"   Malicious: {len(df[df['label'] == 1])} ({len(df[df['label'] == 1])/len(df)*100:.1f}%)")
        
        print(f"\n📈 FEATURES:")
        print(f"   Total features: {len(df.columns)}")
        
        # Count by component
        comp_a = len([c for c in df.columns if c.startswith('A_')])
        comp_b = len([c for c in df.columns if c.startswith('B_')])
        comp_c = len([c for c in df.columns if c.startswith('C_')])
        
        print(f"   Component A (Static): {comp_a}")
        print(f"   Component B (Obfuscation): {comp_b}")
        print(f"   Component C (Behavioral): {comp_c}")
        print(f"   Metadata: {len(df.columns) - comp_a - comp_b - comp_c}")
        
        print("\n📁 OUTPUT:")
        print(f"   CSV file: {self.output_file}")
        if self.output_file.exists():
            print(f"   Size: {self.output_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        print("=" * 60 + "\n")


def main():
    """Main execution"""
    print("=" * 60)
    print("Tier 2 Feature Extractor")
    print("Components A + B + C → 58 Features")
    print("=" * 60)
    print()
    
    extractor = Tier2FeatureExtractor()
    
    # Extract features
    df = extractor.extract_all_features()
    
    if df is None:
        print("\n❌ FAILED! Feature extraction failed")
        return False
    
    # Save features
    extractor.save_features(df)
    
    # Print summary
    extractor.print_summary(df)
    
    print("✅ SUCCESS! Features extracted and saved")
    print("\n📋 Next steps:")
    print("   1. Upload tier2_training_data.csv to Google Colab")
    print("   2. Train Component D (Random Forest + Neural Network)")
    print("   3. Evaluate performance")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
