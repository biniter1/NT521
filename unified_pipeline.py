"""
================================================================================
UNIFIED MALICIOUS CODE DETECTION PIPELINE
Tier 1 (GNN+RF Ensemble) → Tier 2 (ML Components)
================================================================================
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any
import warnings

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnifiedDetector:
    """
    Full pipeline: Tier 1 (GNN+RF) → Tier 2 (ML)
    """
    
    def __init__(self,
                 tier1_gnn_path: str,
                 tier1_rf_path: str,
                 tier2_models_dir: str,
                 tier2_components_dir: str,
                 gnn_weight: float = 0.3,
                 rf_weight: float = 0.7,
                 tier1_threshold: float = 90.0):
        """
        Initialize unified detector
        
        Args:
            tier1_gnn_path: Path to GNN model (.pt)
            tier1_rf_path: Path to RF model (.pkl)
            tier2_models_dir: Path to Tier 2 models
            tier2_components_dir: Path to Tier 2 components
            gnn_weight: Weight for GNN (default 0.6)
            rf_weight: Weight for RF (default 0.4)
            tier1_threshold: Threshold for Tier 2 escalation (default 85.0)
        """
        
        self.gnn_weight = gnn_weight
        self.rf_weight = rf_weight
        self.tier1_threshold = tier1_threshold
        
        self.stats = {
            'total': 0,
            'tier1_benign': 0,
            'tier2_benign': 0,
            'tier2_malicious': 0,
            'errors': 0,
            'tier1_time': 0.0,
            'tier2_time': 0.0
        }
        
        # Load both tiers
        self._load_tier1(tier1_gnn_path, tier1_rf_path)
        self._load_tier2(tier2_models_dir, tier2_components_dir)
        
        logger.info("✅ Unified Pipeline ready!")
    
    def _load_tier1(self, gnn_path: str, rf_path: str):
        """Load Tier 1: GNN + RF using Tier1Ensemble"""
        
        logger.info("Loading Tier 1 (GNN + RF)...")
        
        # Add tier1_inference to path
        tier1_dir = str(Path(gnn_path).parent.parent)  # D:/NT521/DOAN
        if tier1_dir not in sys.path:
            sys.path.insert(0, tier1_dir)
        
        # Import Tier1Ensemble
        from TIER1.tier1_inference import Tier1Ensemble
        
        # Initialize Tier 1 system
        self.tier1 = Tier1Ensemble(
            gnn_model_path=gnn_path,
            rf_model_path=rf_path,
            gnn_weight=self.gnn_weight,
            rf_weight=self.rf_weight,
            tier2_threshold=self.tier1_threshold,
            device='cpu'
        )
        
        logger.info("✅ Tier 1 loaded")
    
    def _load_tier2(self, models_dir: str, components_dir: str):
        """Load Tier 2: ML components"""
        
        logger.info("Loading Tier 2 (ML components)...")
        
        tier2_root = str(Path(models_dir).parent)
        if tier2_root not in sys.path:
            sys.path.insert(0, tier2_root)
        if components_dir not in sys.path:
            sys.path.insert(0, components_dir)
        
        from component_a_wrapper import ComponentAWrapper
        from component_b_wrapper import ComponentBWrapper
        from component_c_wrapper import ComponentCWrapper
        
        import joblib
        import tensorflow as tf
        
        self.comp_a = ComponentAWrapper()
        self.comp_b = ComponentBWrapper()
        self.comp_c = ComponentCWrapper()
        
        models_path = Path(models_dir)
        self.rf_model_t2 = joblib.load(models_path / 'component_d_rf.pkl')
        self.nn_model = tf.keras.models.load_model(models_path / 'component_d_nn.h5')
        self.scaler = joblib.load(models_path / 'component_d_scaler.pkl')
        
        with open(models_path / 'component_d_features.json', 'r') as f:
            self.feature_names = json.load(f)
        
        logger.info("✅ Tier 2 loaded")
    
    def analyze_package(self, code: str, package_name: str, G, node_info: Dict, all_nodes_info: Dict) -> Dict[str, Any]:
        """
        Analyze package với cả 2 tier
        
        Args:
            code: Python source code
            package_name: Package name
            G: Dependency graph (NetworkX DiGraph)
            node_info: Package metadata dict
            all_nodes_info: All packages metadata dict
        
        Returns:
            Analysis result
        """
        
        self.stats['total'] += 1
        
        logger.info(f"\n{'='*70}")
        logger.info(f"ANALYZING: {package_name}")
        logger.info(f"{'='*70}\n")
        
        # =====================================================
        # TIER 1: GNN + RF
        # =====================================================
        logger.info("🔍 TIER 1: GNN + RF Ensemble...")
        
        t1_start = time.time()
        
        try:
            # Use Tier1Ensemble.predict_single()
            tier1_result = self.tier1.predict_single(
                dependency_graph=G,
                target_package=package_name,
                package_info=node_info,
                package_info_dict=all_nodes_info
            )
            
            t1_elapsed = time.time() - t1_start
            self.stats['tier1_time'] += t1_elapsed
            
            logger.info(f"   ⏱️  Time: {t1_elapsed:.3f}s")
            logger.info(f"   📊 GNN: {tier1_result['gnn_score']:.1f}/100")
            logger.info(f"   📊 RF:  {tier1_result['rf_score']:.1f}/100")
            logger.info(f"   🎯 Final: {tier1_result['final_score']:.1f}/100")
            logger.info(f"   📋 Decision: {tier1_result['decision']}")
            
            # Check if pass to Tier 2
            if not tier1_result['pass_to_tier2']:
                logger.info(f"\n✅ TIER 1 DECISION: BENIGN (Stop here)")
                
                self.stats['tier1_benign'] += 1
                
                return {
                    'package_name': package_name,
                    'verdict': 'BENIGN',
                    'confidence': float(tier1_result['confidence']),
                    'tier_used': 'TIER1',
                    'tier1_score': float(tier1_result['final_score']),
                    'processing_time': t1_elapsed
                }
            
            logger.info(f"\n🧠 TIER 2: Deep ML Analysis...")
            logger.info(f"   (Tier 1 suspicious - score ≥ {self.tier1_threshold})")
            
            tier1_score = tier1_result['final_score']
            
        except Exception as e:
            logger.error(f"❌ Tier 1 error: {e}")
            import traceback
            traceback.print_exc()
            
            logger.info(f"\n⚠️  Tier 1 failed, escalating to Tier 2...")
            tier1_score = None
            t1_elapsed = time.time() - t1_start
        
        # =====================================================
        # TIER 2: ML Components
        # =====================================================
        
        t2_start = time.time()
        
        try:
            # Extract features
            logger.info(f"   [1/4] Component A: Static analysis...")
            features_a = self.comp_a.analyze(code)
            
            logger.info(f"   [2/4] Component B: Obfuscation detection...")
            features_b = self.comp_b.analyze(code)
            
            logger.info(f"   [3/4] Component C: Behavioral analysis...")
            features_c = self.comp_c.analyze(code)
            
            # Add prefixes
            all_features = {}
            for k, v in features_a.items():
                all_features[f'A_{k}'] = v
            for k, v in features_b.items():
                all_features[f'B_{k}'] = v
            for k, v in features_c.items():
                all_features[f'C_{k}'] = v
            
            # Create feature vector
            feature_vector = []
            for fname in self.feature_names:
                feature_vector.append(all_features.get(fname, 0))
            
            import numpy as np
            X = np.array(feature_vector).reshape(1, -1)
            X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
            X_scaled = self.scaler.transform(X)
            
            # Predict
            logger.info(f"   [4/4] Component D: ML classification...")
            
            rf_proba = self.rf_model_t2.predict_proba(X_scaled)[0, 1]
            
            # Use RF only (NN has issues)
            ensemble_proba = rf_proba
            verdict = 'MALICIOUS' if ensemble_proba > 0.5 else 'BENIGN'
            confidence = abs(ensemble_proba - 0.5) * 200
            
            t2_elapsed = time.time() - t2_start
            self.stats['tier2_time'] += t2_elapsed
            
            if verdict == 'MALICIOUS':
                self.stats['tier2_malicious'] += 1
            else:
                self.stats['tier2_benign'] += 1
            
            logger.info(f"   ⏱️  Time: {t2_elapsed:.3f}s")
            logger.info(f"   📊 RF: {rf_proba:.3f}")
            logger.info(f"   🎯 Ensemble: {ensemble_proba:.3f}")
            logger.info(f"   📋 Verdict: {verdict}")
            
            logger.info(f"\n✅ TIER 2 DECISION: {verdict}")
            
            return {
                'package_name': package_name,
                'verdict': verdict,
                'confidence': float(confidence),
                'tier_used': 'TIER2',
                'tier1_score': float(tier1_score) if tier1_score else None,
                'tier2_proba': float(ensemble_proba),
                'processing_time': t1_elapsed + t2_elapsed
            }
            
        except Exception as e:
            logger.error(f"❌ Tier 2 error: {e}")
            import traceback
            traceback.print_exc()
            
            self.stats['errors'] += 1
            
            return {
                'package_name': package_name,
                'verdict': 'ERROR',
                'confidence': 0.0,
                'error': str(e),
                'processing_time': time.time() - t2_start
            }
    
    def print_statistics(self):
        """Print statistics"""
        
        total = self.stats['total']
        if total == 0:
            return
        
        print("\n" + "="*70)
        print("UNIFIED PIPELINE STATISTICS")
        print("="*70)
        
        print(f"\n📊 Analysis Summary:")
        print(f"   Total: {total}")
        print(f"   Tier 1 BENIGN: {self.stats['tier1_benign']} ({self.stats['tier1_benign']/total*100:.1f}%)")
        print(f"   Tier 2 BENIGN: {self.stats['tier2_benign']} ({self.stats['tier2_benign']/total*100:.1f}%)")
        print(f"   Tier 2 MALICIOUS: {self.stats['tier2_malicious']} ({self.stats['tier2_malicious']/total*100:.1f}%)")
        
        if self.stats['errors'] > 0:
            print(f"   Errors: {self.stats['errors']}")
        
        tier2_analyzed = total - self.stats['tier1_benign']
        
        print(f"\n⏱️  Performance:")
        print(f"   Tier 1 avg: {self.stats['tier1_time']/total:.3f}s")
        if tier2_analyzed > 0:
            print(f"   Tier 2 avg: {self.stats['tier2_time']/tier2_analyzed:.3f}s")
        
        print("="*70)