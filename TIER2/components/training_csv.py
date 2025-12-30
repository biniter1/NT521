#!/usr/bin/env python3
"""
Create training CSV from extracted malicious and benign packages
Output: tier2_training_data.csv (ready for Colab)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add components to path
sys.path.append("D:/NT521/DOAN/TIER2/components")

from component_a_wrapper import ComponentAWrapper
from component_b_wrapper import ComponentBWrapper
from component_c_wrapper import ComponentCWrapper

def extract_features_from_file(filepath, label, comp_a, comp_b, comp_c):
    """Extract 57 features from a single file"""
    try:
        code = filepath.read_text(encoding='utf-8', errors='ignore')
        
        if len(code) < 10:
            return None
        
        # Extract features
        features_a = comp_a.analyze(code)
        features_b = comp_b.analyze(code)
        features_c = comp_c.analyze(code)
        
        # Combine features
        features = {}
        
        # Add Component A features with prefix
        for key, val in features_a.items():
            features[f'A_{key}'] = val
        
        # Add Component B features with prefix
        for key, val in features_b.items():
            features[f'B_{key}'] = val
        
        # Add Component C features with prefix
        for key, val in features_c.items():
            features[f'C_{key}'] = val
        
        # Add metadata
        features['identifier'] = filepath.name
        features['source'] = 'malicious' if label == 1 else 'benign'
        features['package_name'] = filepath.stem.split('_')[0]
        features['label'] = label
        
        return features
        
    except Exception as e:
        print(f"  Error {filepath.name}: {e}")
        return None

def main():
    print("="*70)
    print("CREATE TRAINING CSV FOR TIER 2")
    print("="*70)
    
    # Initialize extractors
    print("\n[1/4] Loading feature extractors...")
    comp_a = ComponentAWrapper()
    comp_b = ComponentBWrapper()
    comp_c = ComponentCWrapper()
    
    # Load malicious samples
    print("\n[2/4] Processing malicious samples...")
    malicious_dir = Path("malicious_samples")
    
    if not malicious_dir.exists():
        print(f"❌ Directory not found: {malicious_dir}")
        print("Run: python extract_malicious.py first")
        return
    
    malicious_files = list(malicious_dir.glob("*.py"))
    print(f"   Found {len(malicious_files)} files")
    
    malicious_data = []
    for idx, f in enumerate(malicious_files, 1):
        print(f"   [{idx}/{len(malicious_files)}] {f.name}...", end=" ")
        features = extract_features_from_file(f, 1, comp_a, comp_b, comp_c)
        if features:
            malicious_data.append(features)
            print("✅")
        else:
            print("❌")
    
    # Load benign samples
    print("\n[3/4] Processing benign samples...")
    benign_dir = Path("benign_packages")
    
    if not benign_dir.exists():
        print(f"❌ Directory not found: {benign_dir}")
        return
    
    benign_files = list(benign_dir.glob("**/*.py"))
    print(f"   Found {len(benign_files)} files")
    
    # Balance - take same number as malicious
    target_count = len(malicious_data)
    if len(benign_files) > target_count:
        benign_files = np.random.choice(benign_files, target_count, replace=False)
    
    benign_data = []
    for idx, f in enumerate(benign_files, 1):
        print(f"   [{idx}/{len(benign_files)}] {f.name}...", end=" ")
        features = extract_features_from_file(f, 0, comp_a, comp_b, comp_c)
        if features:
            benign_data.append(features)
            print("✅")
        else:
            print("❌")
        
        if len(benign_data) >= target_count:
            break
    
    # Create DataFrame
    print("\n[4/4] Creating CSV...")
    all_data = malicious_data + benign_data
    df = pd.DataFrame(all_data)
    
    # Replace NaN and inf
    df = df.fillna(0)
    df = df.replace([np.inf, -np.inf], 0)
    
    # Save
    output_file = "tier2_training_data.csv"
    df.to_csv(output_file, index=False)
    
    # Summary
    print(f"\n{'='*70}")
    print("CSV CREATED!")
    print(f"{'='*70}")
    print(f"File: {output_file}")
    print(f"Size: {Path(output_file).stat().st_size / 1024:.1f} KB")
    print(f"\nDataset:")
    print(f"  Total samples: {len(df)}")
    print(f"  Malicious: {len(malicious_data)} ({len(malicious_data)/len(df)*100:.1f}%)")
    print(f"  Benign: {len(benign_data)} ({len(benign_data)/len(df)*100:.1f}%)")
    print(f"  Features: {len(df.columns) - 4}")  # Exclude metadata columns
    
    print(f"\n✅ Ready to upload to Google Colab!")
    print(f"   1. Open: https://colab.research.google.com/")
    print(f"   2. Upload tier2_training_colab.py")
    print(f"   3. Upload {output_file}")
    print(f"   4. Run all cells")

if __name__ == "__main__":
    main()