# ========================================
# optimize_tier1.py
# Tự động tìm config tốt nhất cho Tier 1
# ========================================

from tier1_inference import Tier1Ensemble
import networkx as nx
import numpy as np
from itertools import product

def create_test_data():
    """Tạo test data"""
    test_cases = [
        # BENIGN cases
        {
            'name': 'numpy',
            'info': {
                'name': 'numpy',
                'downloads': 500000000,
                'description': 'Fundamental package for scientific computing',
                'homepage': 'https://numpy.org',
                'repository': 'https://github.com/numpy/numpy',
                'versions': ['1.20.0', '1.21.0', '1.22.0', '1.23.0'],
                'age_days': 5000,
                'author': 'NumPy Developers',
                'is_organization': True,
                'dependencies': [],
                'has_malicious_deps': False,
                'typosquatting_score': 0.0
            },
            'expected': 'BENIGN'
        },
        {
            'name': 'requests',
            'info': {
                'name': 'requests',
                'downloads': 300000000,
                'description': 'HTTP library',
                'homepage': 'https://requests.readthedocs.io',
                'repository': 'https://github.com/psf/requests',
                'versions': ['2.25.0', '2.26.0', '2.27.0'],
                'age_days': 4000,
                'author': 'Kenneth Reitz',
                'is_organization': False,
                'dependencies': ['urllib3', 'certifi'],
                'has_malicious_deps': False,
                'typosquatting_score': 0.0
            },
            'expected': 'BENIGN'
        },
        
        # SUSPICIOUS cases
        {
            'name': 'reqeusts',  # Typosquat
            'info': {
                'name': 'reqeusts',
                'downloads': 50,
                'description': '',
                'homepage': None,
                'repository': None,
                'versions': ['0.0.1'],
                'age_days': 2,
                'author': '',
                'is_organization': False,
                'dependencies': [],
                'has_malicious_deps': False,
                'typosquatting_score': 0.95
            },
            'expected': 'SUSPICIOUS'
        },
        {
            'name': 'numpу',  # Cyrillic 'у'
            'info': {
                'name': 'numpу',
                'downloads': 100,
                'description': '',
                'homepage': None,
                'repository': None,
                'versions': ['1.0.0'],
                'age_days': 1,
                'author': '',
                'is_organization': False,
                'dependencies': [],
                'has_malicious_deps': False,
                'typosquatting_score': 0.98
            },
            'expected': 'SUSPICIOUS'
        },
        {
            'name': 'bitcoin-stealer',
            'info': {
                'name': 'bitcoin-stealer',
                'downloads': 10,
                'description': '',
                'homepage': None,
                'repository': None,
                'versions': ['0.1.0'],
                'age_days': 1,
                'author': '',
                'is_organization': False,
                'dependencies': ['os', 'socket'],
                'has_malicious_deps': False,
                'typosquatting_score': 0.0
            },
            'expected': 'SUSPICIOUS'
        }
    ]
    
    # Create graph
    G = nx.DiGraph()
    package_info_dict = {}
    
    for case in test_cases:
        G.add_node(case['name'])
        package_info_dict[case['name']] = case['info']
        
        for dep in case['info'].get('dependencies', []):
            G.add_edge(case['name'], dep)
            if dep not in package_info_dict:
                package_info_dict[dep] = {
                    'name': dep,
                    'downloads': 100000,
                    'description': f'{dep} package',
                    'homepage': f'https://{dep}.org',
                    'repository': f'https://github.com/{dep}',
                    'versions': ['1.0.0'],
                    'age_days': 1000,
                    'author': 'Unknown',
                    'is_organization': False,
                    'dependencies': [],
                    'has_malicious_deps': False,
                    'typosquatting_score': 0.0
                }
    
    return test_cases, G, package_info_dict


def evaluate_config(gnn_w, rf_w, threshold, test_cases, G, package_info_dict):
    """Đánh giá một configuration"""
    
    try:
        tier1 = Tier1Ensemble(
            gnn_model_path='D:/NT521/DOAN/TIER1/models/gnn_model_final.pt',
            rf_model_path='D:/NT521/DOAN/TIER1/models/rf_model_final.pkl',
            gnn_weight=gnn_w,
            rf_weight=rf_w,
            tier2_threshold=threshold
        )
        
        correct = 0
        results = []
        
        for case in test_cases:
            result = tier1.predict_single(
                G, case['name'], case['info'], package_info_dict
            )
            
            if result['decision'] == case['expected']:
                correct += 1
            
            results.append(result)
        
        accuracy = correct / len(test_cases)
        
        # Calculate other metrics
        suspicious = [r for r in results if r['decision'] == 'SUSPICIOUS']
        benign = [r for r in results if r['decision'] == 'BENIGN']
        
        return {
            'gnn_weight': gnn_w,
            'rf_weight': rf_w,
            'threshold': threshold,
            'accuracy': accuracy,
            'correct': correct,
            'total': len(test_cases),
            'suspicious_count': len(suspicious),
            'benign_count': len(benign),
            'tier2_rate': len(suspicious) / len(test_cases)
        }
    
    except Exception as e:
        print(f"Error with config ({gnn_w}, {rf_w}, {threshold}): {e}")
        return None


def optimize_tier1():
    """Tìm configuration tốt nhất"""
    
    print("\n" + "="*60)
    print("TIER 1 CONFIGURATION OPTIMIZATION")
    print("="*60)
    
    # Load test data
    test_cases, G, package_info_dict = create_test_data()
    print(f"\nTest set: {len(test_cases)} packages")
    print(f"  Benign: {sum(1 for c in test_cases if c['expected'] == 'BENIGN')}")
    print(f"  Suspicious: {sum(1 for c in test_cases if c['expected'] == 'SUSPICIOUS')}")
    
    # Define search space
    gnn_weights = [0.3, 0.4, 0.5, 0.6, 0.7]
    thresholds = [50, 60, 70, 75, 80, 85]
    
    print(f"\nSearching {len(gnn_weights) * len(thresholds)} configurations...")
    
    # Grid search
    best_config = None
    best_accuracy = 0
    all_results = []
    
    for gnn_w in gnn_weights:
        rf_w = 1.0 - gnn_w
        
        for threshold in thresholds:
            print(f"\nTesting: GNN={gnn_w:.1f}, RF={rf_w:.1f}, Threshold={threshold}")
            
            result = evaluate_config(gnn_w, rf_w, threshold, test_cases, G, package_info_dict)
            
            if result:
                all_results.append(result)
                print(f"  Accuracy: {result['accuracy']:.1%} ({result['correct']}/{result['total']})")
                print(f"  Pass to Tier 2: {result['tier2_rate']:.1%}")
                
                if result['accuracy'] > best_accuracy:
                    best_accuracy = result['accuracy']
                    best_config = result
    
    # Print results
    print("\n" + "="*60)
    print("OPTIMIZATION RESULTS")
    print("="*60)
    
    if best_config:
        print("\n🏆 BEST CONFIGURATION:")
        print(f"  GNN Weight: {best_config['gnn_weight']:.2f}")
        print(f"  RF Weight: {best_config['rf_weight']:.2f}")
        print(f"  Threshold: {best_config['threshold']:.1f}")
        print(f"  Accuracy: {best_config['accuracy']:.1%}")
        print(f"  Pass to Tier 2 Rate: {best_config['tier2_rate']:.1%}")
    
    # Show top 5 configs
    print("\n📊 TOP 5 CONFIGURATIONS:")
    sorted_results = sorted(all_results, key=lambda x: x['accuracy'], reverse=True)
    
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"\n{i}. GNN={result['gnn_weight']:.2f}, RF={result['rf_weight']:.2f}, Threshold={result['threshold']:.1f}")
        print(f"   Accuracy: {result['accuracy']:.1%}, Tier 2 Rate: {result['tier2_rate']:.1%}")
    
    return best_config


if __name__ == '__main__':
    best_config = optimize_tier1()