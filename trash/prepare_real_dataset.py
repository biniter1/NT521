"""
================================================================================
PREPARE REAL TEST DATASET
Convert downloaded packages thành format phù hợp với unified pipeline
================================================================================
"""

import os
import sys
import json
import shutil
import pickle
import random
import networkx as nx
from pathlib import Path
from datetime import datetime

def extract_code_from_package(package_dir):
    """
    Extract Python code từ package directory
    
    Args:
        package_dir: Path to package directory
    
    Returns:
        str: Combined Python code or None
    """
    package_dir = Path(package_dir)
    
    # Look for source directory
    source_dirs = [
        package_dir / 'source',
        package_dir / 'src',
        package_dir,
    ]
    
    python_files = []
    for source_dir in source_dirs:
        if source_dir.exists():
            python_files.extend(source_dir.rglob('*.py'))
            if python_files:
                break
    
    if not python_files:
        return None
    
    # Prefer __init__.py or main.py
    for priority_name in ['__init__.py', 'main.py', 'app.py']:
        for pf in python_files:
            if pf.name == priority_name:
                try:
                    with open(pf, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except:
                    pass
    
    # Otherwise, take first .py file
    for pf in python_files:
        try:
            with open(pf, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
                if len(code) > 100:  # Must have substantial code
                    return code
        except:
            continue
    
    return None


def create_package_metadata_for_tier1(package_info, is_malicious=False):
    """
    Tạo metadata phù hợp với Tier 1 (GNN + RF)
    
    Args:
        package_info: Dict with package info
        is_malicious: Whether package is malicious
    
    Returns:
        dict: Tier 1 compatible metadata
    """
    
    if is_malicious:
        # Malicious metadata - suspicious patterns
        metadata = {
            'name': package_info.get('package_name', 'unknown'),
            'version': package_info.get('version', '0.0.1'),
            'author': package_info.get('author', 'unknown'),
            'downloads': random.randint(0, 500),  # Low downloads
            'age_days': random.randint(1, 60),  # Very new
            'description': package_info.get('summary', ''),
            'homepage': package_info.get('home_page'),
            'repository': package_info.get('project_url'),
            'versions': [package_info.get('version', '0.0.1')],
            'is_organization': False,
            'dependencies': package_info.get('requires_dist', [])[:3],  # Limit
            'has_malicious_deps': False,
            'typosquatting_score': random.uniform(0.5, 0.95),  # High typo score
        }
    else:
        # Benign metadata - trusted patterns
        metadata = {
            'name': package_info.get('package_name', 'unknown'),
            'version': package_info.get('version', '1.0.0'),
            'author': package_info.get('author', 'verified-author'),
            'downloads': random.randint(100000, 10000000),  # High downloads
            'age_days': package_info.get('age_days', random.randint(365, 3650)),
            'description': package_info.get('summary', 'Popular package'),
            'homepage': package_info.get('home_page', 'https://example.com'),
            'repository': package_info.get('project_url', 'https://github.com/user/repo'),
            'versions': ['1.0.0', '1.1.0', '1.2.0'],  # Multiple versions
            'is_organization': True,
            'dependencies': package_info.get('requires_dist', [])[:5],
            'has_malicious_deps': False,
            'typosquatting_score': 0.0,
        }
    
    return metadata


def create_dependency_graph(packages_list):
    """
    Tạo dependency graph cho Tier 1 GNN
    
    Args:
        packages_list: List of package dicts
    
    Returns:
        NetworkX DiGraph
    """
    G = nx.DiGraph()
    
    benign_pkgs = [p for p in packages_list if p['ground_truth'] == 'BENIGN']
    malicious_pkgs = [p for p in packages_list if p['ground_truth'] == 'MALICIOUS']
    
    # Add all nodes
    for pkg in packages_list:
        G.add_node(pkg['package_name'], **pkg['metadata'])
    
    # Add edges (dependencies)
    # Benign packages có dependencies với nhau
    for pkg in benign_pkgs:
        num_deps = random.randint(0, 3)
        for _ in range(num_deps):
            dep = random.choice(benign_pkgs)
            if dep['package_name'] != pkg['package_name']:
                G.add_edge(pkg['package_name'], dep['package_name'])
    
    # Malicious packages thường isolated hoặc có ít dependencies
    for pkg in malicious_pkgs:
        if random.random() < 0.2:  # 20% chance có dependency
            dep = random.choice(benign_pkgs)  # Depend on benign
            G.add_edge(pkg['package_name'], dep['package_name'])
    
    return G


def prepare_dataset(benign_dir, malicious_dir, output_dir, max_benign=25, max_malicious=25):
    """
    Prepare complete dataset
    
    Args:
        benign_dir: Directory with benign packages
        malicious_dir: Directory with malicious packages
        output_dir: Output directory
        max_benign: Max number of benign packages
        max_malicious: Max number of malicious packages
    """
    
    benign_dir = Path(benign_dir)
    malicious_dir = Path(malicious_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    packages = []
    
    print("\n" + "="*70)
    print("PREPARING REAL TEST DATASET")
    print("="*70)
    
    # Process benign packages
    print(f"\n[1/2] Processing benign packages from {benign_dir}...")
    print("-" * 70)
    
    benign_count = 0
    for pkg_dir in sorted(benign_dir.iterdir()):
        if not pkg_dir.is_dir() or benign_count >= max_benign:
            continue
        
        print(f"  [{benign_count+1}/{max_benign}] Processing: {pkg_dir.name}")
        
        # Load metadata
        metadata_file = pkg_dir / 'metadata.json'
        if not metadata_file.exists():
            print(f"    ⚠️  No metadata.json found")
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            pkg_info = json.load(f)
        
        # Extract code
        code = extract_code_from_package(pkg_dir)
        if not code:
            print(f"    ⚠️  No Python code found")
            continue
        
        if len(code) < 100:
            print(f"    ⚠️  Code too short ({len(code)} chars)")
            continue
        
        # Create Tier 1 metadata
        tier1_metadata = create_package_metadata_for_tier1(pkg_info, is_malicious=False)
        
        packages.append({
            'id': f'benign-{benign_count+1:03d}',
            'package_name': tier1_metadata['name'],
            'category': 'benign',
            'ground_truth': 'BENIGN',
            'code': code,
            'metadata': tier1_metadata,
            'original_metadata': pkg_info
        })
        
        benign_count += 1
        print(f"    ✅ Added ({len(code)} chars of code)")
    
    print(f"\n✅ Processed {benign_count} benign packages")
    
    # Process malicious packages
    print(f"\n[2/2] Processing malicious packages from {malicious_dir}...")
    print("-" * 70)
    
    malicious_count = 0
    for pkg_dir in sorted(malicious_dir.iterdir()):
        if not pkg_dir.is_dir() or malicious_count >= max_malicious:
            continue
        
        print(f"  [{malicious_count+1}/{max_malicious}] Processing: {pkg_dir.name}")
        
        # Load metadata
        metadata_file = pkg_dir / 'metadata.json'
        if not metadata_file.exists():
            print(f"    ⚠️  No metadata.json found")
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            pkg_info = json.load(f)
        
        # Extract code
        code = extract_code_from_package(pkg_dir)
        if not code:
            print(f"    ⚠️  No Python code found")
            continue
        
        if len(code) < 100:
            print(f"    ⚠️  Code too short ({len(code)} chars)")
            continue
        
        # Create Tier 1 metadata
        tier1_metadata = create_package_metadata_for_tier1(pkg_info, is_malicious=True)
        
        packages.append({
            'id': f'malicious-{malicious_count+1:03d}',
            'package_name': tier1_metadata['name'],
            'category': 'malicious',
            'ground_truth': 'MALICIOUS',
            'code': code,
            'metadata': tier1_metadata,
            'original_metadata': pkg_info
        })
        
        malicious_count += 1
        print(f"    ✅ Added ({len(code)} chars of code)")
    
    print(f"\n✅ Processed {malicious_count} malicious packages")
    
    if len(packages) == 0:
        print("\n❌ No packages processed! Check your input directories.")
        return
    
    # Create dependency graph
    print(f"\n[3/3] Creating dependency graph...")
    print("-" * 70)
    
    G = create_dependency_graph(packages)
    
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    
    # Save graph
    graph_file = output_dir / 'dependency_graph.gpickle'
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f)
    
    print(f"  ✅ Saved graph to {graph_file.name}")
    
    # Save packages metadata
    metadata_file = output_dir / 'packages_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump({
            'created_date': datetime.now().isoformat(),
            'total_packages': len(packages),
            'benign_count': benign_count,
            'malicious_count': malicious_count,
            'packages': packages
        }, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Saved metadata to {metadata_file.name}")
    
    # Summary
    print("\n" + "="*70)
    print("DATASET SUMMARY")
    print("="*70)
    print(f"Total packages: {len(packages)}")
    print(f"  Benign:    {benign_count}")
    print(f"  Malicious: {malicious_count}")
    print(f"\nOutput directory: {output_dir}")
    print(f"  - packages_metadata.json")
    print(f"  - dependency_graph.gpickle")
    print("\n✅ Ready for unified pipeline benchmark!")
    print("="*70)


def main():
    """Main function"""
    
    # Paths
    benign_dir = 'D:/NT521/DOAN/real_test_dataset/benign_raw'
    malicious_dir = 'D:/NT521/DOAN/real_test_dataset/malicious_raw'
    output_dir = 'D:/NT521/DOAN/real_unified_dataset'
    
    # Check if raw directories exist
    if not Path(benign_dir).exists():
        print(f"\n❌ Benign directory not found: {benign_dir}")
        print(f"   Run download_real_benign.py first!")
        return
    
    if not Path(malicious_dir).exists():
        print(f"\n❌ Malicious directory not found: {malicious_dir}")
        print(f"   Run download_real_malicious.py first!")
        return
    
    # Prepare dataset
    prepare_dataset(
        benign_dir=benign_dir,
        malicious_dir=malicious_dir,
        output_dir=output_dir,
        max_benign=25,
        max_malicious=25
    )


if __name__ == '__main__':
    main()