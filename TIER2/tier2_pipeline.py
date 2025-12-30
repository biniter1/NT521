"""
tier2_pipeline.py
COMPLETE TIER 2 PIPELINE - END-TO-END MALWARE DETECTION
Integrates Components A, B, C, D for production use
"""

import sys
from pathlib import Path
import pickle
import numpy as np
from tensorflow import keras
import json
import logging

# Add components directory to path
COMPONENTS_DIR = Path(__file__).parent / "components"
sys.path.insert(0, str(COMPONENTS_DIR))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Tier2MalwareDetector:
    """
    Complete Tier 2 Pipeline
    Input: Python package or code
    Output: Malicious probability + detailed analysis
    """
    
    def __init__(self, models_dir="models"):
        self.models_dir = Path(models_dir)
        
        # Load components
        logger.info("Loading Tier 2 components...")
        self._load_components()
        
        # Load trained models
        logger.info("Loading trained models...")
        self._load_models()
        
        logger.info("✅ Tier 2 initialized successfully")
    
    def _load_components(self):
        """Load Components A, B, C"""
        try:
            from component_a_wrapper import ComponentAWrapper
            from component_b_wrapper import ComponentBWrapper
            from component_c_wrapper import ComponentCWrapper
            
            self.component_a = ComponentAWrapper()
            self.component_b = ComponentBWrapper()
            self.component_c = ComponentCWrapper()
            
            logger.info("✅ Components A, B, C loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load components: {e}")
            raise
    
    def _load_models(self):
        """Load trained Random Forest and Neural Network"""
        try:
            import joblib
            
            # Load Random Forest
            rf_path = self.models_dir / "component_d_rf.pkl"
            logger.info(f"Loading Random Forest from: {rf_path}")
            
            self.rf_model = joblib.load(rf_path)
            logger.info("✅ Random Forest loaded")
            
            # Load Neural Network
            nn_path = self.models_dir / "component_d_nn.h5"
            logger.info(f"Loading Neural Network from: {nn_path}")
            
            self.nn_model = keras.models.load_model(nn_path)
            logger.info("✅ Neural Network loaded")
            
            # Load Scaler
            scaler_path = self.models_dir / "component_d_scaler.pkl"
            logger.info(f"Loading Scaler from: {scaler_path}")
            
            self.scaler = joblib.load(scaler_path)
            logger.info("✅ Scaler loaded")
            
            # Load feature names
            features_path = self.models_dir / "component_d_features.json"
            logger.info(f"Loading feature names from: {features_path}")
            
            with open(features_path, 'r') as f:
                self.feature_names = json.load(f)
            
            logger.info(f"✅ Feature names loaded ({len(self.feature_names)} features)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def analyze_code(self, code: str, identifier: str = "sample") -> dict:
        """Analyze Python code through complete Tier 2 pipeline"""
        logger.info(f"\n{'='*70}")
        logger.info(f"TIER 2 ANALYSIS: {identifier}")
        logger.info(f"{'='*70}")
        
        result = {
            "identifier": identifier,
            "components": {},
            "features": {},
            "predictions": {},
            "final_verdict": None
        }
        
        try:
            # STEP 1: Component A - Static Analysis
            logger.info("\n[1/4] Running Component A: Static Analysis...")
            features_a = self.component_a.analyze(code)
            result["components"]["A_static"] = features_a
            logger.info(f"   ✓ Extracted {len(features_a)} static features")
            
            # STEP 2: Component B - Obfuscation Detection
            logger.info("\n[2/4] Running Component B: Obfuscation Detection...")
            features_b = self.component_b.analyze(code)
            result["components"]["B_obfuscation"] = features_b
            logger.info(f"   ✓ Extracted {len(features_b)} obfuscation features")
            
            # STEP 3: Component C - Behavioral Analysis
            logger.info("\n[3/4] Running Component C: Behavioral Analysis...")
            features_c = self.component_c.analyze(code)
            result["components"]["C_behavioral"] = features_c
            logger.info(f"   ✓ Extracted {len(features_c)} behavioral features")
            
            # STEP 4: Combine features
            logger.info("\n[4/4] Running Component D: ML Classification...")
            
            # Combine all features with A_, B_, C_ prefixes
            combined_features = {}
            for key, value in features_a.items():
                combined_features[f'A_{key}'] = value
            for key, value in features_b.items():
                combined_features[f'B_{key}'] = value
            for key, value in features_c.items():
                combined_features[f'C_{key}'] = value
            
            # 🔍 DEBUG: Print feature counts
            logger.info(f"\n🔍 DEBUG INFO:")
            logger.info(f"   Component A features: {len(features_a)}")
            logger.info(f"   Component B features: {len(features_b)}")
            logger.info(f"   Component C features: {len(features_c)}")
            logger.info(f"   Combined features: {len(combined_features)}")
            logger.info(f"   Expected features: {len(self.feature_names)}")
            
            # 🔍 DEBUG: Check missing features
            combined_keys = set(combined_features.keys())
            expected_keys = set(self.feature_names)
            
            missing = expected_keys - combined_keys
            extra = combined_keys - expected_keys
            
            if missing:
                logger.warning(f"   ⚠️  Missing features: {missing}")
            if extra:
                logger.warning(f"   ⚠️  Extra features: {extra}")
            
            # Create feature vector matching training order
            feature_vector = []
            for feature_name in self.feature_names:
                value = combined_features.get(feature_name, 0)
                
                # Handle boolean values
                if isinstance(value, bool):
                    value = 1 if value else 0
                
                feature_vector.append(value)
            logger.info(f"   Feature vector length: {len(feature_vector)}")
            result["features"]["vector"] = feature_vector
            result["features"]["count"] = len(feature_vector)
            
            # Scale features
            feature_array = np.array(feature_vector).reshape(1, -1)
            feature_scaled = self.scaler.transform(feature_array)
            
            # PREDICTIONS
            
            # Random Forest prediction
            rf_proba = self.rf_model.predict_proba(feature_scaled)[0]
            rf_prediction = self.rf_model.predict(feature_scaled)[0]
            
            result["predictions"]["random_forest"] = {
                "malicious_probability": float(rf_proba[1]),
                "benign_probability": float(rf_proba[0]),
                "prediction": "malicious" if rf_prediction == 1 else "benign"
            }
            
            logger.info(f"   RF Prediction: {result['predictions']['random_forest']['prediction'].upper()}")
            logger.info(f"   RF Confidence: {rf_proba[1]*100:.2f}%")
            
            # Neural Network prediction
            nn_proba = self.nn_model.predict(feature_scaled, verbose=0)[0][0]
            nn_prediction = 1 if nn_proba > 0.5 else 0
            
            result["predictions"]["neural_network"] = {
                "malicious_probability": float(nn_proba),
                "benign_probability": float(1 - nn_proba),
                "prediction": "malicious" if nn_prediction == 1 else "benign"
            }
            
            logger.info(f"   NN Prediction: {result['predictions']['neural_network']['prediction'].upper()}")
            logger.info(f"   NN Confidence: {nn_proba*100:.2f}%")
            
            # Ensemble prediction (50% RF + 50% NN)
            ensemble_proba = 0.5 * rf_proba[1] + 0.5 * nn_proba
            ensemble_prediction = 1 if ensemble_proba > 0.5 else 0
            
            result["predictions"]["ensemble"] = {
                "malicious_probability": float(ensemble_proba),
                "benign_probability": float(1 - ensemble_proba),
                "prediction": "malicious" if ensemble_prediction == 1 else "benign",
                "confidence": float(max(ensemble_proba, 1 - ensemble_proba))
            }
            
            # Final verdict
            result["final_verdict"] = {
                "prediction": "MALICIOUS" if ensemble_prediction == 1 else "BENIGN",
                "confidence": result["predictions"]["ensemble"]["confidence"] * 100,
                "risk_score": ensemble_proba * 100
            }
            
            logger.info(f"\n{'='*70}")
            logger.info(f"FINAL VERDICT: {result['final_verdict']['prediction']}")
            logger.info(f"Confidence: {result['final_verdict']['confidence']:.2f}%")
            logger.info(f"Risk Score: {result['final_verdict']['risk_score']:.2f}/100")
            logger.info(f"{'='*70}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            result["error"] = str(e)
            return result
    
    def analyze_file(self, filepath: Path) -> dict:
        """
        Analyze a Python file
        
        Args:
            filepath: Path to .py file
            
        Returns:
            Analysis results
        """
        logger.info(f"Reading file: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            return self.analyze_code(code, identifier=filepath.name)
            
        except Exception as e:
            logger.error(f"❌ Failed to read file: {e}")
            return {"error": str(e)}
    
    def batch_analyze(self, files: list) -> list:
        """
        Analyze multiple files
        
        Args:
            files: List of file paths
            
        Returns:
            List of analysis results
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"BATCH ANALYSIS: {len(files)} files")
        logger.info(f"{'='*70}\n")
        
        results = []
        
        for i, filepath in enumerate(files, 1):
            logger.info(f"\n[{i}/{len(files)}] Analyzing: {filepath}")
            
            result = self.analyze_file(Path(filepath))
            results.append(result)
        
        # Summary
        malicious_count = sum(1 for r in results if r.get('final_verdict', {}).get('prediction') == 'MALICIOUS')
        benign_count = len(results) - malicious_count
        
        logger.info(f"\n{'='*70}")
        logger.info(f"BATCH ANALYSIS SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total files:  {len(results)}")
        logger.info(f"Malicious:    {malicious_count}")
        logger.info(f"Benign:       {benign_count}")
        logger.info(f"{'='*70}\n")
        
        return results


# ========================================
# COMMAND LINE INTERFACE
# ========================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Tier 2 Malware Detector')
    parser.add_argument('--file', type=str, help='Python file to analyze')
    parser.add_argument('--code', type=str, help='Python code string to analyze')
    parser.add_argument('--batch', type=str, nargs='+', help='Multiple files to analyze')
    parser.add_argument('--models', type=str, default='models', help='Models directory')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = Tier2MalwareDetector(models_dir=args.models)
    
    # Analyze
    if args.file:
        result = detector.analyze_file(Path(args.file))
        print(json.dumps(result, indent=2))
        
    elif args.code:
        result = detector.analyze_code(args.code, identifier="cli_input")
        print(json.dumps(result, indent=2))
        
    elif args.batch:
        results = detector.batch_analyze(args.batch)
        
        # Save results
        output_file = "batch_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()