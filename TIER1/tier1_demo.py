# ========================================
# tier1_demo.py - FIXED VERSION
# ========================================

from tier1_inference import Tier1Ensemble
import networkx as nx
import os

def demo_tier1():
    """Demo Tier 1 với một số packages giả định"""
    
    print("\n" + "="*60)
    print("TIER 1 DEMO - PACKAGE ANALYSIS")
    print("="*60)
    
    # Check if model files exist
    gnn_model_path = 'D:/NT521/DOAN/TIER1/models/gnn_model_final.pt'
    rf_model_path = 'D:/NT521/DOAN/TIER1/models/rf_model_final.pkl'
    
    if not os.path.exists(gnn_model_path):
        print(f"\n❌ ERROR: GNN model not found at {gnn_model_path}")
        print("\nPlease:")
        print("  1. Download 'gnn_model_final.pt' from Google Colab")
        print("  2. Create 'models/' folder in current directory")
        print("  3. Place the file in models/ folder")
        return
    
    if not os.path.exists(rf_model_path):
        print(f"\n❌ ERROR: RF model not found at {rf_model_path}")
        print("\nPlease:")
        print("  1. Download 'rf_model_final.pkl' from Google Colab")
        print("  2. Create 'models/' folder in current directory")
        print("  3. Place the file in models/ folder")
        return
    
    print(f"✓ Found GNN model: {gnn_model_path}")
    print(f"✓ Found RF model: {rf_model_path}")
    
    # Initialize Tier 1
    tier1 = Tier1Ensemble(
        gnn_model_path=gnn_model_path,
        rf_model_path=rf_model_path,
        gnn_weight=0.3,
        rf_weight=0.7,
        tier2_threshold=85.0
    )
    
    # Test cases
    test_cases = [
        {
            'name': 'typosquat-reqeusts',
            'info': {
                'name': 'reqeusts',
                'downloads': 25,
                'description': '',
                'homepage': None,
                'repository': None,
                'versions': ['0.0.1'],
                'age_days': 1,
                'author': '',
                'is_organization': False,
                'dependencies': [],
                'has_malicious_deps': False,
                'typosquatting_score': 0.95
            },
            'expected': 'SUSPICIOUS'
        },
        {
            'name': 'legitimate-package',
            'info': {
                'name': 'legitimate-package',
                'downloads': 50000,
                'description': 'A well-established package',
                'homepage': 'https://example.com',
                'repository': 'https://github.com/example/package',
                'versions': ['1.0.0', '1.1.0', '1.2.0', '2.0.0'],
                'age_days': 730,
                'author': 'John Doe',
                'is_organization': False,
                'dependencies': ['requests', 'numpy'],
                'has_malicious_deps': False,
                'typosquatting_score': 0.0
            },
            'expected': 'BENIGN'
        },
        {
            'name': 'new-suspicious-package',
            'info': {
                'name': 'crypto-miner-2024',
                'downloads': 10,
                'description': '',
                'homepage': None,
                'repository': None,
                'versions': ['0.1.0'],
                'age_days': 2,
                'author': '',
                'is_organization': False,
                'dependencies': ['os', 'sys', 'socket'],
                'has_malicious_deps': False,
                'typosquatting_score': 0.0
            },
            'expected': 'SUSPICIOUS'
        }
    ]
    
    # Create simple dependency graph
    G = nx.DiGraph()
    for case in test_cases:
        G.add_node(case['name'])
        for dep in case['info'].get('dependencies', []):
            G.add_edge(case['name'], dep)
            G.add_node(dep)  # Add dependency nodes too
    
    # Create package_info_dict with all nodes
    package_info_dict = {}
    for case in test_cases:
        package_info_dict[case['name']] = case['info']
    
    # Add info for dependency nodes (with default values)
    for case in test_cases:
        for dep in case['info'].get('dependencies', []):
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
    
    # Analyze each package
    results = []
    for case in test_cases:
        print(f"\n{'='*60}")
        print(f"Analyzing: {case['name']}")
        print(f"Expected: {case['expected']}")
        print(f"{'='*60}")
        
        try:
            result = tier1.predict_single(
                dependency_graph=G,
                target_package=case['name'],
                package_info=case['info'],
                package_info_dict=package_info_dict
            )
            
            print(f"GNN Score: {result['gnn_score']:.2f}/100")
            print(f"RF Score: {result['rf_score']:.2f}/100")
            print(f"Final Score: {result['final_score']:.2f}/100")
            print(f"Decision: {result['decision']}")
            print(f"Pass to Tier 2: {'YES' if result['pass_to_tier2'] else 'NO'}")
            print(f"Confidence: {result['confidence']:.2f}")
            
            match = "✓ CORRECT" if result['decision'] == case['expected'] else "✗ INCORRECT"
            print(f"\n{match}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    if results:
        tier1.print_summary(results)
        tier1.save_results(results, 'tier1_demo_results.json')
    
    print("\n✅ Demo completed!")

if __name__ == '__main__':
    demo_tier1()