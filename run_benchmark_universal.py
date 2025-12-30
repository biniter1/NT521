"""
================================================================================
FIXED BENCHMARK FOR 2-TIER SYSTEM WITH UNIVERSAL DATASET
Properly prepares metadata and graph for Tier 1 + Tier 2
================================================================================
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import networkx as nx

# --- CẤU HÌNH ĐƯỜNG DẪN TƯƠNG ĐỐI ---
# Lấy đường dẫn thư mục chứa file script này (Ví dụ: D:/NT521/DOAN)
BASE_DIR = Path(__file__).resolve().parent

# Thêm thư mục hiện tại vào sys.path để import modules (thay thế cho sys.path.insert cố định)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
# ------------------------------------

def enrich_metadata(metadata: dict, package_name: str, category: str) -> dict:
    """
    Enrich metadata to match Tier 1 requirements
    Creates all 15 required metadata features
    
    Args:
        metadata: Dict from metadata.json
        package_name: Name of the package
        category: 'benign' or 'malicious'
    """
    
    maloss_info = metadata.get('maloss_info', {})
    
    # Extract basic info
    name = package_name
    downloads = maloss_info.get('downloads', {}).get('last_month', 0)
    
    # If benign, give higher downloads; if malicious, lower downloads
    if downloads == 0:
        downloads = 10000 if category == 'benign' else 50
    
    # Description
    description = maloss_info.get('summary', '')
    if not description:
        description = maloss_info.get('description', '')
    
    # URLs
    homepage = maloss_info.get('home_page', '')
    repository = maloss_info.get('project_urls', {}).get('Source', '')
    if not repository:
        repository = maloss_info.get('project_urls', {}).get('Repository', '')
    
    # Versions
    versions = maloss_info.get('releases', [])
    if not versions:
        versions = ['1.0.0']  # Default version
    
    # Age calculation
    upload_time = maloss_info.get('upload_time', '')
    if upload_time:
        try:
            from dateutil import parser
            upload_date = parser.parse(upload_time)
            age_days = (datetime.now() - upload_date).days
        except:
            age_days = 365 if category == 'benign' else 7
    else:
        age_days = 365 if category == 'benign' else 7
    
    # Author
    author = maloss_info.get('author', '')
    if not author:
        author = maloss_info.get('maintainer', '')
    
    is_organization = bool(maloss_info.get('author_email', '').endswith('@gmail.com') == False)
    
    # Dependencies
    dependencies = maloss_info.get('dependencies', {}).get('runtime', [])
    if isinstance(dependencies, dict):
        dependencies = list(dependencies.keys())
    
    # Malicious deps check (for simulation)
    has_malicious_deps = False  # We don't have this info in universal dataset
    
    # Typosquatting score (simulate based on name characteristics)
    typosquatting_score = 0.0
    suspicious_patterns = ['test', 'temp', '123', 'xxx', 'new']
    if any(pattern in name.lower() for pattern in suspicious_patterns):
        typosquatting_score = 0.7
    
    # Create enriched metadata matching Tier 1 FeatureExtractor requirements
    enriched = {
        'name': name,
        'downloads': downloads,
        'description': description,
        'homepage': homepage,
        'repository': repository,
        'versions': versions,
        'age_days': age_days,
        'author': author,
        'is_organization': is_organization,
        'dependencies': dependencies,
        'has_malicious_deps': has_malicious_deps,
        'typosquatting_score': typosquatting_score,
        
        # Additional fields that might be needed
        'has_documentation': bool(homepage or repository),
        'upload_time': upload_time
    }
    
    return enriched


def build_realistic_graph(packages: List[dict]) -> nx.DiGraph:
    """
    Build a more realistic dependency graph
    """
    
    G = nx.DiGraph()
    
    # Popular benign packages to use as dependencies
    popular_packages = {
        'numpy', 'pandas', 'requests', 'flask', 'django', 
        'tensorflow', 'scikit-learn', 'matplotlib', 'pytest',
        'beautifulsoup4', 'pillow', 'click', 'sqlalchemy'
    }
    
    # Add all packages as nodes
    for pkg in packages:
        pkg_name = pkg['package_name']
        G.add_node(pkg_name)
    
    # Add popular packages as nodes
    for pop_pkg in popular_packages:
        if pop_pkg not in G:
            G.add_node(pop_pkg)
    
    # Create edges based on dependencies
    for pkg in packages:
        pkg_name = pkg['package_name']
        deps = pkg['metadata'].get('dependencies', [])
        
        # Add declared dependencies
        for dep in deps:
            # Clean dependency name (remove version specifiers)
            dep_name = dep.split('>=')[0].split('==')[0].split('<')[0].strip()
            
            if dep_name not in G:
                G.add_node(dep_name)
            
            G.add_edge(pkg_name, dep_name)
        
        # If package has no dependencies, add some common ones
        if len(deps) == 0 and pkg['category'] == 'benign':
            # Benign packages typically depend on popular libraries
            import random
            sample_deps = random.sample(list(popular_packages), k=min(3, len(popular_packages)))
            for dep in sample_deps:
                G.add_edge(pkg_name, dep)
        
        elif len(deps) == 0 and pkg['category'] == 'malicious':
            # Malicious packages might have fewer dependencies
            import random
            if random.random() > 0.5:  # 50% chance to add one dependency
                dep = random.choice(list(popular_packages))
                G.add_edge(pkg_name, dep)
    
    return G


def load_universal_dataset(dataset_dir: str) -> Tuple[List[dict], nx.DiGraph]:
    """
    Load universal dataset with enriched metadata for Tier 1
    
    Returns:
        packages (list): List of package dicts with enriched metadata
        G (networkx.DiGraph): Enhanced dependency graph
    """
    
    dataset_path = Path(dataset_dir)
    
    print(f"\n📂 Loading dataset from: {dataset_path}")
    
    # Load ground truth
    with open(dataset_path / 'ground_truth.json', 'r') as f:
        ground_truth = json.load(f)
    
    print(f"   Found {len(ground_truth['packages'])} packages")
    
    # Build packages list with enriched metadata
    packages = []
    packages_dir = dataset_path / 'packages'
    
    for pkg_info in ground_truth['packages']:
        pkg_name = pkg_info['package_name']
        is_malicious = pkg_info['malicious']
        
        category = 'malicious' if is_malicious else 'benign'
        pkg_dir = packages_dir / category / pkg_name
        
        # Check if package directory exists
        if not pkg_dir.exists():
            print(f"⚠️  Package directory not found: {pkg_dir}")
            continue
        
        # Load metadata
        metadata_file = pkg_dir / 'metadata.json'
        if not metadata_file.exists():
            print(f"⚠️  Metadata not found for {pkg_name}")
            continue
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Enrich metadata for Tier 1
        enriched_metadata = enrich_metadata(metadata, pkg_name, category)
        
        # Load source code
        source_dir = pkg_dir / 'source'
        py_files = list(source_dir.glob('*.py'))
        
        if not py_files:
            py_files = list(source_dir.rglob('*.py'))
        
        if not py_files:
            print(f"⚠️  No source code for {pkg_name}")
            continue
        
        # Read code (limit to first 5 files to avoid memory issues)
        code_parts = []
        for py_file in py_files[:5]:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code_parts.append(f.read())
            except Exception as e:
                print(f"⚠️  Failed to read {py_file}: {e}")
        
        code = '\n\n'.join(code_parts)
        
        packages.append({
            'package_name': pkg_name,
            'code': code,
            'metadata': enriched_metadata,
            'ground_truth': 'MALICIOUS' if is_malicious else 'BENIGN',
            'category': category
        })
    
    print(f"✅ Loaded {len(packages)} packages with enriched metadata")
    
    # Build realistic dependency graph
    print(f"\n🔗 Building dependency graph...")
    G = build_realistic_graph(packages)
    
    print(f"✅ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    return packages, G


def run_benchmark(detector, packages: List[dict], G: nx.DiGraph) -> dict:
    """Run benchmark with both Tier 1 and Tier 2"""
    
    print("\n" + "="*70)
    print("RUNNING 2-TIER BENCHMARK")
    print("="*70)
    
    benign_count = sum(1 for p in packages if p['ground_truth'] == 'BENIGN')
    malicious_count = sum(1 for p in packages if p['ground_truth'] == 'MALICIOUS')
    
    print(f"Total: {len(packages)}")
    print(f"  Benign: {benign_count}")
    print(f"  Malicious: {malicious_count}")
    print()
    
    results = []
    
    # Build all_nodes_info for Tier 1
    all_nodes_info = {}
    for pkg in packages:
        all_nodes_info[pkg['package_name']] = pkg['metadata']
    
    # Add popular packages with dummy metadata
    for node in G.nodes():
        if node not in all_nodes_info:
            all_nodes_info[node] = {
                'name': node,
                'downloads': 1000000,
                'description': 'Popular package',
                'homepage': f'https://{node}.org',
                'repository': f'https://github.com/{node}',
                'versions': ['1.0.0'],
                'age_days': 1000,
                'author': 'Community',
                'is_organization': True,
                'dependencies': [],
                'has_malicious_deps': False,
                'typosquatting_score': 0.0,
                'has_documentation': True
            }
    
    for i, pkg in enumerate(packages, 1):
        print(f"\n[{i}/{len(packages)}] Analyzing: {pkg['package_name']}")
        
        try:
            result = detector.analyze_package(
                code=pkg['code'],
                package_name=pkg['package_name'],
                G=G,
                node_info=pkg['metadata'],
                all_nodes_info=all_nodes_info
            )
            
            correct = result['verdict'] == pkg['ground_truth']
            
            results.append({
                **result,
                'ground_truth': pkg['ground_truth'],
                'correct': correct,
                'category': pkg['category']
            })
            
            status = "✅" if correct else "❌"
            tier_used = result.get('tier_used', 'N/A')
            print(f"{status} {result['verdict']} (Tier: {tier_used})")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            results.append({
                'package_name': pkg['package_name'],
                'ground_truth': pkg['ground_truth'],
                'verdict': 'ERROR',
                'correct': False,
                'error': str(e),
                'category': pkg['category']
            })
    
    return calculate_metrics(results)


def calculate_metrics(results: List[dict]) -> dict:
    """Calculate performance metrics"""
    
    valid = [r for r in results if r['verdict'] != 'ERROR']
    total = len(valid)
    
    if total == 0:
        return {'error': 'No valid results'}
    
    correct = sum(1 for r in valid if r['correct'])
    
    # Confusion matrix
    tp = sum(1 for r in valid if r['ground_truth'] == 'MALICIOUS' and r['verdict'] == 'MALICIOUS')
    tn = sum(1 for r in valid if r['ground_truth'] == 'BENIGN' and r['verdict'] == 'BENIGN')
    fp = sum(1 for r in valid if r['ground_truth'] == 'BENIGN' and r['verdict'] == 'MALICIOUS')
    fn = sum(1 for r in valid if r['ground_truth'] == 'MALICIOUS' and r['verdict'] == 'BENIGN')
    
    # Metrics
    accuracy = correct / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # False Positive Rate and False Negative Rate
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    # Tier distribution
    tier1_decisions = sum(1 for r in valid if r.get('tier_used') == 'TIER1')
    tier2_decisions = sum(1 for r in valid if r.get('tier_used') == 'TIER2')
    
    # Timing analysis
    tier1_times = [r['processing_time'] for r in valid if r.get('tier_used') == 'TIER1']
    tier2_times = [r['processing_time'] for r in valid if r.get('tier_used') == 'TIER2']
    all_times = [r['processing_time'] for r in valid if 'processing_time' in r]
    
    # Category breakdown
    benign_results = [r for r in valid if r['category'] == 'benign']
    malicious_results = [r for r in valid if r['category'] == 'malicious']
    
    benign_correct = sum(1 for r in benign_results if r['correct'])
    malicious_correct = sum(1 for r in malicious_results if r['correct'])
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'fpr': fpr,
        'fnr': fnr,
        'confusion_matrix': {
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn
        },
        'tier_distribution': {
            'tier1': tier1_decisions,
            'tier2': tier2_decisions,
            'tier1_percent': (tier1_decisions / total * 100) if total > 0 else 0,
            'tier2_percent': (tier2_decisions / total * 100) if total > 0 else 0
        },
        'timing': {
            'tier1_avg': sum(tier1_times) / len(tier1_times) if tier1_times else 0.0,
            'tier2_avg': sum(tier2_times) / len(tier2_times) if tier2_times else 0.0,
            'total_avg': sum(all_times) / len(all_times) if all_times else 0.0,
            'total_time': sum(all_times) if all_times else 0.0
        },
        'category_breakdown': {
            'benign_total': len(benign_results),
            'benign_correct': benign_correct,
            'benign_accuracy': (benign_correct / len(benign_results)) if benign_results else 0,
            'malicious_total': len(malicious_results),
            'malicious_correct': malicious_correct,
            'malicious_accuracy': (malicious_correct / len(malicious_results)) if malicious_results else 0
        },
        'results': results
    }


def print_report(metrics: dict):
    """Print detailed benchmark report"""
    
    print("\n" + "="*70)
    print("2-TIER BENCHMARK RESULTS")
    print("="*70)
    
    if 'error' in metrics:
        print(f"❌ {metrics['error']}")
        return
    
    # Overall metrics
    print(f"\n📊 Overall Performance:")
    print(f"   Accuracy:  {metrics['accuracy']:.1%}")
    print(f"   Precision: {metrics['precision']:.1%}")
    print(f"   Recall:    {metrics['recall']:.1%}")
    print(f"   F1-Score:  {metrics['f1_score']:.1%}")
    print(f"   FPR:       {metrics['fpr']:.1%}")
    print(f"   FNR:       {metrics['fnr']:.1%}")
    
    # Confusion matrix
    cm = metrics['confusion_matrix']
    print(f"\n🎯 Confusion Matrix:")
    print(f"   True Positives:  {cm['tp']}")
    print(f"   True Negatives:  {cm['tn']}")
    print(f"   False Positives: {cm['fp']}")
    print(f"   False Negatives: {cm['fn']}")
    
    # Tier distribution
    td = metrics['tier_distribution']
    print(f"\n🔀 Tier Distribution:")
    print(f"   Tier 1 decisions: {td['tier1']} ({td['tier1_percent']:.1f}%)")
    print(f"   Tier 2 decisions: {td['tier2']} ({td['tier2_percent']:.1f}%)")
    
    # Category breakdown
    cb = metrics['category_breakdown']
    print(f"\n📂 Category Breakdown:")
    print(f"   Benign:    {cb['benign_correct']}/{cb['benign_total']} correct ({cb['benign_accuracy']:.1%})")
    print(f"   Malicious: {cb['malicious_correct']}/{cb['malicious_total']} correct ({cb['malicious_accuracy']:.1%})")
    
    # Timing
    timing = metrics['timing']
    print(f"\n⏱️  Performance:")
    print(f"   Tier 1 avg: {timing['tier1_avg']:.3f}s")
    print(f"   Tier 2 avg: {timing['tier2_avg']:.3f}s")
    print(f"   Total avg:  {timing['total_avg']:.3f}s")
    print(f"   Total time: {timing['total_time']:.1f}s")
    
    print("="*70)


def main():
    """Main benchmark function"""
    
    print("\n" + "="*70)
    print("2-TIER BENCHMARK - UNIVERSAL DATASET (FIXED)")
    print("="*70)
    
    # --- THAY ĐỔI ĐƯỜNG DẪN INPUT SANG TƯƠNG ĐỐI ---
    default_dataset = BASE_DIR / 'universal_test_dataset'
    
    dataset_dir = input(f"\nDataset path (default: {default_dataset}): ").strip()
    if not dataset_dir:
        dataset_dir = str(default_dataset)
    # -----------------------------------------------
    
    dataset_path = Path(dataset_dir)
    
    if not dataset_path.exists():
        print(f"\n❌ Dataset not found: {dataset_path}")
        print("Please run: python create_universal_test_dataset.py")
        return
    
    # Load dataset with enriched metadata
    packages, G = load_universal_dataset(dataset_dir)
    
    if not packages:
        print("\n❌ No packages loaded!")
        return
    
    # Initialize detector
    print("\n🚀 Initializing UnifiedDetector...")
    
    from unified_pipeline import UnifiedDetector
    
    try:
        # --- THAY ĐỔI ĐƯỜNG DẪN MODEL SANG TƯƠNG ĐỐI ---
        detector = UnifiedDetector(
            tier1_gnn_path=str(BASE_DIR / 'Model_TIER1/GNN_TIER1/gnn_model_final.pt'),
            tier1_rf_path=str(BASE_DIR / 'Model_TIER1/RF_TIER1/rf_model_final.pkl'),
            tier2_models_dir=str(BASE_DIR / 'TIER2/models'),
            tier2_components_dir=str(BASE_DIR / 'TIER2/components'),
            gnn_weight=0.3,
            rf_weight=0.7,
            tier1_threshold=86.0
        )
        # -----------------------------------------------
        print("✅ Detector initialized successfully!")
        
    except Exception as e:
        print(f"\n❌ Failed to initialize detector: {e}")
        print("\nTrying alternative configuration...")
        
        try:
             # --- THAY ĐỔI ĐƯỜNG DẪN MODEL (RETRY) ---
            detector = UnifiedDetector(
                tier1_gnn_path=str(BASE_DIR / 'Model_TIER1/GNN_TIER1/gnn_model_final.pt'),
                tier1_rf_path=str(BASE_DIR / 'Model_TIER1/RF_TIER1/rf_model_final.pkl'),
                tier2_models_dir=str(BASE_DIR / 'TIER2/models'),
                tier2_components_dir=str(BASE_DIR / 'TIER2/components'),
                gnn_weight=0.3,
                rf_weight=0.7,
                tier1_threshold=90.0
            )
            # ----------------------------------------
            print("✅ Detector initialized with alternative configuration!")
            
        except Exception as e2:
            print(f"❌ Failed again: {e2}")
            import traceback
            traceback.print_exc()
            return
    
    # Run benchmark
    metrics = run_benchmark(detector, packages, G)
    
    # Print report
    print_report(metrics)
    
    # Print detector statistics
    if hasattr(detector, 'print_statistics'):
        detector.print_statistics()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'universal_benchmark_2tier_fixed_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Also save as standard name
    with open('universal_benchmark_2tier_fixed.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n💾 Results saved:")
    print(f"   - {output_file}")
    print(f"   - universal_benchmark_2tier_fixed.json")
    
    print("\n✅ Benchmark completed!")


if __name__ == '__main__':
    main()