#!/usr/bin/env python3
"""
Build Dependency Graph for Tier 1 from Universal Test Dataset

Tạo dependency graph từ universal_test_dataset để Tier 1 GNN có thể phân tích đúng
"""

import json
import pickle
from pathlib import Path
import networkx as nx
from typing import Dict, List, Any

def load_ground_truth(dataset_dir: Path) -> Dict[str, bool]:
    """Load ground truth labels"""
    ground_truth_file = dataset_dir / 'ground_truth.json'
    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
    return ground_truth

def load_package_metadata(package_dir: Path) -> Dict[str, Any]:
    """Load metadata for a single package"""
    metadata_file = package_dir / 'metadata.json'
    if not metadata_file.exists():
        return None
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    return metadata

def build_dependency_graph(dataset_dir: Path) -> tuple:
    """
    Build dependency graph từ universal_test_dataset
    
    Returns:
        G: networkx DiGraph
        package_info_dict: Dictionary of all package metadata
    """
    dataset_dir = Path(dataset_dir)
    
    # Load ground truth
    print("📋 Loading ground truth...")
    ground_truth = load_ground_truth(dataset_dir)
    
    # Initialize graph
    G = nx.DiGraph()
    package_info_dict = {}
    
    print(f"\n🔨 Building dependency graph...")
    
    # Iterate through packages
    packages_dir = dataset_dir / 'packages'
    for category in ['benign', 'malicious']:
        category_dir = packages_dir / category
        if not category_dir.exists():
            continue
        
        for package_dir in sorted(category_dir.iterdir()):
            if not package_dir.is_dir():
                continue
            
            package_name = package_dir.name
            
            # Load metadata
            metadata = load_package_metadata(package_dir)
            if metadata is None:
                print(f"⚠️  Warning: No metadata for {package_name}")
                continue
            
            # Extract info for Tier 1
            maloss_info = metadata.get('maloss_info', {})
            tier_info = metadata.get('tier_system_info', {})
            
            # Build package_info format that Tier 1 expects
            package_info = {
                'name': package_name,
                'downloads': maloss_info.get('downloads', 0),
                'author': maloss_info.get('author', 'unknown'),
                'homepage': maloss_info.get('homepage', ''),
                'upload_time': maloss_info.get('upload_time', ''),
                'dependencies': maloss_info.get('dependencies', []),
                'typosquatting_score': maloss_info.get('typosquatting_score', 0.0),
                
                # Additional features for RF
                'num_dependencies': len(maloss_info.get('dependencies', [])),
                'has_homepage': bool(maloss_info.get('homepage', '')),
                'has_author': bool(maloss_info.get('author', '')),
                'is_malicious': ground_truth.get(package_name, False),
                
                # SAST info
                'sast_issues': tier_info.get('sast_issues', 0),
                'high_severity': tier_info.get('high_severity_issues', 0),
                'medium_severity': tier_info.get('medium_severity_issues', 0),
                'low_severity': tier_info.get('low_severity_issues', 0),
            }
            
            # Add node to graph
            G.add_node(package_name, **package_info)
            
            # Store in dict
            package_info_dict[package_name] = package_info
            
            # Add dependency edges
            dependencies = maloss_info.get('dependencies', [])
            for dep in dependencies:
                # Add edge: package -> dependency
                G.add_edge(package_name, dep)
                
                # If dependency not in graph, add placeholder node
                if dep not in G.nodes:
                    G.add_node(dep, **{
                        'name': dep,
                        'downloads': 0,
                        'author': 'unknown',
                        'homepage': '',
                        'upload_time': '',
                        'dependencies': [],
                        'typosquatting_score': 0.0,
                        'num_dependencies': 0,
                        'has_homepage': False,
                        'has_author': False,
                        'is_malicious': False,
                        'sast_issues': 0,
                        'high_severity': 0,
                        'medium_severity': 0,
                        'low_severity': 0,
                    })
            
            print(f"  ✓ {package_name}: {len(dependencies)} dependencies")
    
    print(f"\n✅ Dependency graph built!")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Packages: {len(package_info_dict)}")
    
    return G, package_info_dict

def save_graph(G: nx.DiGraph, package_info_dict: Dict, output_dir: Path):
    """Save dependency graph and package info"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save graph as pickle
    graph_file = output_dir / 'universal_dependency_graph.pkl'
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f)
    print(f"\n💾 Saved graph: {graph_file}")
    
    # Save package_info_dict as JSON
    info_file = output_dir / 'universal_package_info.json'
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(package_info_dict, f, indent=2)
    print(f"💾 Saved package info: {info_file}")
    
    # Save graph statistics
    stats = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'num_packages': len(package_info_dict),
        'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        'density': nx.density(G),
        'is_connected': nx.is_weakly_connected(G),
    }
    
    stats_file = output_dir / 'graph_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"💾 Saved statistics: {stats_file}")
    
    return graph_file, info_file

def main():
    print("="*70)
    print("BUILD DEPENDENCY GRAPH FOR TIER 1")
    print("="*70)
    
    # Get dataset path
    dataset_path = input("\nDataset path (default: D:/NT521/DOAN/universal_test_dataset): ").strip()
    if not dataset_path:
        dataset_path = "D:/NT521/DOAN/universal_test_dataset"
    
    dataset_dir = Path(dataset_path)
    
    if not dataset_dir.exists():
        print(f"❌ Error: Dataset not found at {dataset_dir}")
        return
    
    # Build graph
    try:
        G, package_info_dict = build_dependency_graph(dataset_dir)
        
        # Save graph
        output_dir = dataset_dir.parent / 'tier1_data'
        graph_file, info_file = save_graph(G, package_info_dict, output_dir)
        
        print("\n" + "="*70)
        print("✅ DEPENDENCY GRAPH BUILD COMPLETE!")
        print("="*70)
        print(f"\nFiles created:")
        print(f"  📊 Graph: {graph_file}")
        print(f"  📄 Package Info: {info_file}")
        print(f"\nUse these files in Tier 1 benchmark!")
        
    except Exception as e:
        print(f"\n❌ Error building graph: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()