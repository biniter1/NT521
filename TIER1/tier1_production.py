# ========================================
# tier1_production.py
# Production-ready Tier 1 System với best config
# ========================================

from tier1_inference import Tier1Ensemble
import json
import os

class Tier1Production:
    """
    Production Tier 1 System với optimized configuration
    """
    
    def __init__(self, config_path='tier1_config.json'):
        """
        Initialize với best config
        """
        # Load config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            best_config = config['best_configuration']
            
            self.gnn_weight = best_config['gnn_weight']
            self.rf_weight = best_config['rf_weight']
            self.threshold = best_config['tier2_threshold']
            
            print(f"Loaded optimized configuration:")
            print(f"  GNN Weight: {self.gnn_weight}")
            print(f"  RF Weight: {self.rf_weight}")
            print(f"  Threshold: {self.threshold}")
            print(f"  Expected Accuracy: {best_config['accuracy']:.1%}")
        else:
            # Fallback to default best config
            print("⚠️ Config file not found. Using default best config.")
            self.gnn_weight = 0.3
            self.rf_weight = 0.7
            self.threshold = 85.0
        
        # Initialize Tier 1
        self.tier1 = Tier1Ensemble(
            gnn_model_path='D:/NT521/DOAN/TIER1/models/gnn_model_final.pt',
            rf_model_path='D:/NT521/DOAN/TIER1/models/rf_model_final.pkl',
            gnn_weight=self.gnn_weight,
            rf_weight=self.rf_weight,
            tier2_threshold=self.threshold
        )
    
    def analyze_package(self, dependency_graph, package_name, package_info, package_info_dict=None):
        """
        Analyze một package với optimized config
        """
        return self.tier1.predict_single(
            dependency_graph, 
            package_name, 
            package_info, 
            package_info_dict
        )
    
    def analyze_batch(self, package_list, dependency_graph, package_info_dict):
        """
        Analyze batch packages
        """
        return self.tier1.predict_batch(
            package_list, 
            dependency_graph, 
            package_info_dict
        )
    
    def get_statistics(self, results):
        """Get statistics"""
        return self.tier1.get_statistics(results)
    
    def save_results(self, results, filepath):
        """Save results"""
        return self.tier1.save_results(results, filepath)


# Example usage
if __name__ == '__main__':
    print("\n" + "="*60)
    print("TIER 1 PRODUCTION SYSTEM")
    print("="*60)
    
    # Initialize with best config
    tier1_prod = Tier1Production(config_path='tier1_config.json')
    
    print("\n✅ Production system ready!")
    print("Use tier1_prod.analyze_package() or analyze_batch() to analyze packages")