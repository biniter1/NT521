"""
================================================================================
PREPARE UNIFIED TEST DATASET
Tạo synthetic metadata cho test dataset để sử dụng cả Tier 1 + Tier 2
================================================================================
"""

import os
import json
import random
import pickle
from pathlib import Path
import networkx as nx


def create_synthetic_metadata(file_name, category, index):
    """Tạo metadata giả cho package"""
    
    package_name = f"{category}-package-{index:03d}"
    
    if category == 'benign':
        # Metadata TỐT - giống package thật
        metadata = {
            'package_name': package_name,
            'version': f'{random.randint(1,5)}.{random.randint(0,20)}.{random.randint(0,10)}',
            'author': random.choice([
                'python-team', 'opensource-dev', 'community-team',
                'verified-author', 'trusted-publisher'
            ]),
            'author_email': f'{package_name}@example.com',
            'downloads_last_month': random.randint(100000, 5000000),
            'age_days': random.randint(365, 3650),  # 1-10 năm
            'has_homepage': True,
            'has_documentation': True,
            'has_source_repository': True,
            'license': random.choice(['MIT', 'Apache-2.0', 'BSD-3-Clause']),
            'num_maintainers': random.randint(2, 10),
            'num_releases': random.randint(20, 200),
            'has_wheels': True,
            'python_versions': ['3.7', '3.8', '3.9', '3.10', '3.11'],
            'description_length': random.randint(100, 500),
            'typosquatting_score': 0.0,
            'is_verified': True,
            'has_security_policy': True
        }
    else:
        # Metadata ĐÁNG NGỜ - malicious
        metadata = {
            'package_name': package_name,
            'version': '0.0.1',
            'author': random.choice(['user123', 'unknown', 'temp-user', 'anon-dev']),
            'author_email': f'{random.randint(1000,9999)}@temp.com',
            'downloads_last_month': random.randint(0, 100),
            'age_days': random.randint(1, 30),
            'has_homepage': random.choice([True, False]),
            'has_documentation': False,
            'has_source_repository': False,
            'license': random.choice(['UNKNOWN', None, '']),
            'num_maintainers': 1,
            'num_releases': 1,
            'has_wheels': False,
            'python_versions': ['3.9'],
            'description_length': random.randint(10, 50),
            'typosquatting_score': random.uniform(0.6, 0.95),
            'is_verified': False,
            'has_security_policy': False
        }
    
    return metadata


def create_dependency_graph(packages_metadata):
    """Tạo dependency graph"""
    
    G = nx.DiGraph()
    
    benign_packages = [p for p in packages_metadata if p['category'] == 'benign']
    malicious_packages = [p for p in packages_metadata if p['category'] == 'malicious']
    
    # Add all nodes
    for pkg in packages_metadata:
        G.add_node(pkg['package_name'], **pkg['metadata'])
    
    # Benign packages có dependencies
    for i, pkg in enumerate(benign_packages):
        num_deps = random.randint(0, 3)
        for _ in range(num_deps):
            dep = random.choice(benign_packages)
            if dep['package_name'] != pkg['package_name']:
                G.add_edge(pkg['package_name'], dep['package_name'])
    
    # Malicious packages isolated (no dependencies)
    
    return G


def main():
    """Prepare unified dataset"""
    
    test_dataset_dir = Path('D:/NT521/DOAN/test_dataset')
    output_dir = Path('D:/NT521/DOAN/unified_test_dataset')
    output_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print("PREPARING UNIFIED TEST DATASET")
    print("="*70)
    
    packages_metadata = []
    
    # Process benign
    benign_dir = test_dataset_dir / 'benign'
    print(f"\n📂 Processing benign files...")
    
    benign_files = sorted(benign_dir.glob('*.py'))
    for i, file in enumerate(benign_files, 1):
        with open(file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        metadata = create_synthetic_metadata(file.name, 'benign', i)
        
        packages_metadata.append({
            'id': f'benign-{i:03d}',
            'package_name': metadata['package_name'],
            'category': 'benign',
            'ground_truth': 'BENIGN',
            'source_file': file.name,
            'code': code,
            'metadata': metadata
        })
        
        print(f"  [{i}/{len(benign_files)}] {file.name} → {metadata['package_name']}")
    
    # Process malicious
    malicious_dir = test_dataset_dir / 'malicious'
    print(f"\n📂 Processing malicious files...")
    
    malicious_files = sorted(malicious_dir.glob('*.py'))
    for i, file in enumerate(malicious_files, 1):
        with open(file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        metadata = create_synthetic_metadata(file.name, 'malicious', i)
        
        packages_metadata.append({
            'id': f'malicious-{i:03d}',
            'package_name': metadata['package_name'],
            'category': 'malicious',
            'ground_truth': 'MALICIOUS',
            'source_file': file.name,
            'code': code,
            'metadata': metadata
        })
        
        print(f"  [{i}/{len(malicious_files)}] {file.name} → {metadata['package_name']}")
    
    # Create graph
    print(f"\n🔗 Creating dependency graph...")
    G = create_dependency_graph(packages_metadata)
    print(f"   Nodes: {G.number_of_nodes()}")
    print(f"   Edges: {G.number_of_edges()}")
    
    # Save
    graph_file = output_dir / 'dependency_graph.gpickle'
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f)
    print(f"   ✅ Saved: {graph_file}")
    
    metadata_file = output_dir / 'packages_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump({
            'total_packages': len(packages_metadata),
            'benign_count': len(benign_files),
            'malicious_count': len(malicious_files),
            'packages': packages_metadata
        }, f, indent=2)
    print(f"   ✅ Saved: {metadata_file}")
    
    print("\n" + "="*70)
    print("DONE!")
    print(f"Total: {len(packages_metadata)} packages")
    print(f"Output: {output_dir}")
    print("="*70)


if __name__ == '__main__':
    main()

