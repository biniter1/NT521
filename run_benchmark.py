"""
================================================================================
BENCHMARK UNIFIED PIPELINE
Test với synthetic metadata + real code
================================================================================
"""

import json
import time
import sys
import pickle
from pathlib import Path
from typing import List, Dict
from datetime import datetime

sys.path.insert(0, 'D:/NT521/DOAN')


BASE_DIR = Path(__file__).resolve().parent

def load_unified_dataset(dataset_dir: str):
    """Load unified dataset với metadata + graph"""
    
    
    dataset_folder_path = BASE_DIR / 'unified_test_dataset'
    # Load metadata
    with open(dataset_folder_path / 'packages_metadata.json', 'r') as f:
        data = json.load(f)
    
    packages = data['packages']
    
    # Load graph
    with open(dataset_folder_path / 'dependency_graph.gpickle', 'rb') as f:
        G = pickle.load(f)
    
    return packages, G


def run_benchmark(detector, packages, G):
    """Run benchmark"""
    
    print("\n" + "="*70)
    print("RUNNING BENCHMARK")
    print("="*70)
    
    benign_count = sum(1 for p in packages if p['ground_truth'] == 'BENIGN')
    malicious_count = sum(1 for p in packages if p['ground_truth'] == 'MALICIOUS')
    
    print(f"Total: {len(packages)}")
    print(f"  Benign: {benign_count}")
    print(f"  Malicious: {malicious_count}")
    print()
    
    results = []
    
    # Build all_nodes_info
    all_nodes_info = {}
    for pkg in packages:
        all_nodes_info[pkg['package_name']] = pkg['metadata']
    
    for i, pkg in enumerate(packages, 1):
        print(f"[{i}/{len(packages)}] {pkg['package_name']}...", end=' ')
        
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
            print(f"{status} {result['verdict']}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                'package_name': pkg['package_name'],
                'ground_truth': pkg['ground_truth'],
                'verdict': 'ERROR',
                'correct': False,
                'error': str(e)
            })
    
    return calculate_metrics(results)


def calculate_metrics(results):
    """Calculate metrics"""
    
    valid = [r for r in results if r['verdict'] != 'ERROR']
    total = len(valid)
    
    if total == 0:
        return {'error': 'No valid results'}
    
    correct = sum(1 for r in valid if r['correct'])
    
    tp = sum(1 for r in valid if r['ground_truth'] == 'MALICIOUS' and r['verdict'] == 'MALICIOUS')
    tn = sum(1 for r in valid if r['ground_truth'] == 'BENIGN' and r['verdict'] == 'BENIGN')
    fp = sum(1 for r in valid if r['ground_truth'] == 'BENIGN' and r['verdict'] == 'MALICIOUS')
    fn = sum(1 for r in valid if r['ground_truth'] == 'MALICIOUS' and r['verdict'] == 'BENIGN')
    
    accuracy = correct / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Tier distribution
    tier1_decisions = sum(1 for r in valid if r.get('tier_used') == 'TIER1')
    tier2_decisions = sum(1 for r in valid if r.get('tier_used') == 'TIER2')
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'confusion_matrix': {'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn},
        'tier_distribution': {
            'tier1': tier1_decisions,
            'tier2': tier2_decisions
        },
        'results': results
    }


def print_report(metrics):
    """Print report"""
    
    print("\n" + "="*70)
    print("BENCHMARK RESULTS")
    print("="*70)
    
    if 'error' in metrics:
        print(f"❌ {metrics['error']}")
        return
    
    print(f"\n📊 Overall:")
    print(f"   Accuracy:  {metrics['accuracy']:.1%}")
    print(f"   Precision: {metrics['precision']:.1%}")
    print(f"   Recall:    {metrics['recall']:.1%}")
    print(f"   F1-Score:  {metrics['f1_score']:.1%}")
    
    cm = metrics['confusion_matrix']
    print(f"\n🎯 Confusion Matrix:")
    print(f"   TP: {cm['tp']}, TN: {cm['tn']}")
    print(f"   FP: {cm['fp']}, FN: {cm['fn']}")
    
    td = metrics['tier_distribution']
    print(f"\n🔀 Tier Distribution:")
    print(f"   Tier 1 decisions: {td['tier1']} ({td['tier1']/metrics['total']*100:.1f}%)")
    print(f"   Tier 2 decisions: {td['tier2']} ({td['tier2']/metrics['total']*100:.1f}%)")
    
    print("="*70)


def main():
    """Main"""
    
    print("\n" + "="*70)
    print("UNIFIED PIPELINE BENCHMARK")
    print("="*70)
    
    from unified_pipeline import UnifiedDetector
    
    detector = UnifiedDetector(
        tier1_gnn_path=str(BASE_DIR / 'Model_TIER1/GNN_TIER1/gnn_model_final.pt'),
        tier1_rf_path=str(BASE_DIR / 'Model_TIER1/RF_TIER1/rf_model_final.pkl'),
        tier2_models_dir=str(BASE_DIR / 'TIER2/models'),
        tier2_components_dir=str(BASE_DIR / 'TIER2/components'),
        tier1_threshold=90.0 
    )
    
    packages, G = load_unified_dataset(str(BASE_DIR /'/unified_test_dataset'))
    
    print(f"\n✅ Loaded {len(packages)} packages")
    
    metrics = run_benchmark(detector, packages, G)
    
    print_report(metrics)
    detector.print_statistics()
    
    # Save
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'unified_benchmark_{timestamp}.json', 'w') as f:
        json.dump(metrics, f, indent=2)


if __name__ == '__main__':
    main()