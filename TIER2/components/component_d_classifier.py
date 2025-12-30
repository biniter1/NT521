# ========================================
# component_d_classifier.py
# Component D: ML Classifier (Ensemble)
# ========================================

"""
Thư viện cần cài:
pip install numpy scikit-learn torch --break-system-packages
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Tier2NeuralNet(nn.Module):
    """
    Neural Network for Tier 2 classification
    """
    
    def __init__(self, input_dim: int = 58, hidden_dims: List[int] = [128, 64, 32]):
        super(Tier2NeuralNet, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x).squeeze(-1)


class Tier2Classifier:
    """
    Component D: ML Classifier
    Ensemble of Random Forest + Neural Network
    """
    
    def __init__(self, 
                 rf_model_path: Optional[str] = None,
                 nn_model_path: Optional[str] = None,
                 scaler_path: Optional[str] = None,
                 rf_weight: float = 0.5,
                 nn_weight: float = 0.5,
                 tier3_threshold: float = 70.0,
                 device: str = 'cpu'):
        """
        Initialize Tier 2 Classifier
        
        Args:
            rf_model_path: Path to Random Forest model
            nn_model_path: Path to Neural Network model
            scaler_path: Path to feature scaler
            rf_weight: Weight for RF predictions
            nn_weight: Weight for NN predictions
            tier3_threshold: Threshold to pass to Tier 3 (0-100)
            device: 'cuda' or 'cpu'
        """
        self.rf_weight = rf_weight
        self.nn_weight = nn_weight
        self.tier3_threshold = tier3_threshold
        self.device = torch.device(device)
        
        # Feature configuration
        self.expected_feature_count = 58  # A(25) + B(18) + C(15)
        self.feature_names = self._get_feature_names()
        
        # Load models if paths provided
        if rf_model_path and Path(rf_model_path).exists():
            self._load_rf_model(rf_model_path)
        else:
            self.rf_model = None
            print("⚠️ Random Forest model not loaded")
        
        if nn_model_path and Path(nn_model_path).exists():
            self._load_nn_model(nn_model_path)
        else:
            self.nn_model = None
            print("⚠️ Neural Network model not loaded")
        
        if scaler_path and Path(scaler_path).exists():
            self._load_scaler(scaler_path)
        else:
            self.scaler = StandardScaler()
            print("⚠️ Feature scaler not loaded, using default")
    
    def _get_feature_names(self) -> List[str]:
        """Define all expected feature names"""
        features = []
        
        # Component A features (25)
        features.extend([
            'total_imports', 'dangerous_imports_count', 'has_os_import',
            'has_subprocess_import', 'has_socket_import',
            'functions_defined', 'functions_called_count', 'dangerous_calls_count',
            'unique_functions', 'function_density',
            'file_operations_count', 'network_operations_count',
            'process_spawning_count', 'code_execution_count', 'has_api_abuse',
            'dynamic_types_count', 'type_confusion_risk', 'has_dynamic_operations',
            'tainted_flows_count', 'sink_locations_count', 'has_tainted_sink',
            'cyclomatic_complexity', 'max_nesting_depth', 'lines_of_code',
            'complexity_per_line'
        ])
        
        # Component B features (18)
        features.extend([
            'avg_string_entropy', 'max_string_entropy', 'high_entropy_count',
            'base64_count', 'hex_string_count', 'unicode_escape_count',
            'encoded_payload_count',
            'staged_execution_count', 'dynamic_import_count', 'runtime_code_gen_count',
            'time_check_count', 'trigger_condition_count',
            'obfuscation_method_count', 'has_identifier_obfuscation',
            'anti_debug_count', 'anti_vm_count', 'env_check_count',
            'total_obfuscation_score'
        ])
        
        # Component C features (15)
        features.extend([
            'total_api_calls', 'unique_api_calls', 'max_call_depth',
            'api_sequence_score',
            'suspicious_sequence_count', 'has_suspicious_sequence',
            'control_flow_complexity', 'max_nesting_depth_behavioral',
            'matched_signature_count', 'max_signature_confidence',
            'file_and_network', 'crypto_and_network',
            'persistence_behavior', 'data_exfil_behavior',
            'total_behavioral_risk'
        ])
        
        return features
    
    def _load_rf_model(self, model_path: str):
        """Load Random Forest model"""
        print(f"Loading Random Forest model from {model_path}...")
        model_data = joblib.load(model_path)
        self.rf_model = model_data['model']
        print("  ✓ Random Forest loaded")
    
    def _load_nn_model(self, model_path: str):
        """Load Neural Network model"""
        print(f"Loading Neural Network model from {model_path}...")
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        
        input_dim = checkpoint.get('input_dim', self.expected_feature_count)
        hidden_dims = checkpoint.get('hidden_dims', [128, 64, 32])
        
        self.nn_model = Tier2NeuralNet(input_dim, hidden_dims).to(self.device)
        self.nn_model.load_state_dict(checkpoint['model_state_dict'])
        self.nn_model.eval()
        
        print("  ✓ Neural Network loaded")
    
    def _load_scaler(self, scaler_path: str):
        """Load feature scaler"""
        print(f"Loading feature scaler from {scaler_path}...")
        self.scaler = joblib.load(scaler_path)
        print("  ✓ Scaler loaded")
    
    def combine_features(self, 
                        component_a: Dict,
                        component_b: Dict,
                        component_c: Dict) -> np.ndarray:
        """
        Combine features from all three components
        
        Args:
            component_a: Features from Enhanced Static Analysis
            component_b: Features from Obfuscation Detector
            component_c: Features from Behavioral Analyzer
        
        Returns:
            Feature vector as numpy array
        """
        # Extract feature dictionaries
        features_a = component_a.get('aggregated_features', {})
        features_b = component_b.get('aggregated_features', {})
        features_c = component_c.get('aggregated_features', {})
        
        # Combine all features
        combined_features = {}
        combined_features.update(features_a)
        combined_features.update(features_b)
        combined_features.update(features_c)
        
        # Create feature vector in correct order
        feature_vector = []
        missing_features = []
        
        for feature_name in self.feature_names:
            if feature_name in combined_features:
                value = combined_features[feature_name]
                # Convert boolean to int
                if isinstance(value, bool):
                    value = 1 if value else 0
                feature_vector.append(float(value))
            else:
                # Feature missing - use default value
                feature_vector.append(0.0)
                missing_features.append(feature_name)
        
        if missing_features:
            print(f"⚠️ Warning: {len(missing_features)} features missing: {missing_features[:5]}...")
        
        return np.array(feature_vector, dtype=np.float32)
    
    def predict(self, 
                component_a: Dict,
                component_b: Dict,
                component_c: Dict) -> Dict:
        """
        Make prediction using ensemble
        
        Returns:
            {
                'rf_score': float (0-100),
                'nn_score': float (0-100),
                'ensemble_score': float (0-100),
                'decision': 'MALICIOUS' or 'BENIGN',
                'pass_to_tier3': bool,
                'confidence': float,
                'feature_vector': np.ndarray,
                'feature_importance': Dict (top features)
            }
        """
        # Combine features
        features = self.combine_features(component_a, component_b, component_c)
        features = features.reshape(1, -1)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Random Forest prediction
        if self.rf_model is not None:
            rf_proba = self.rf_model.predict_proba(features_scaled)[0, 1]
            rf_score = rf_proba * 100
        else:
            rf_score = 50.0  # Default if model not loaded
            print("⚠️ RF model not available, using default score")
        
        # Neural Network prediction
        if self.nn_model is not None:
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features_scaled).to(self.device)
                nn_proba = self.nn_model(features_tensor).cpu().item()
                nn_score = nn_proba * 100
        else:
            nn_score = 50.0  # Default if model not loaded
            print("⚠️ NN model not available, using default score")
        
        # Ensemble score (weighted average)
        ensemble_score = (self.rf_weight * rf_score + 
                         self.nn_weight * nn_score)
        
        # Decision
        is_malicious = ensemble_score > self.tier3_threshold
        
        # Get feature importance from RF
        feature_importance = {}
        if self.rf_model is not None and hasattr(self.rf_model, 'feature_importances_'):
            importances = self.rf_model.feature_importances_
            # Get top 10 features
            top_indices = np.argsort(importances)[-10:][::-1]
            for idx in top_indices:
                if idx < len(self.feature_names):
                    feature_importance[self.feature_names[idx]] = float(importances[idx])
        
        result = {
            'rf_score': float(rf_score),
            'nn_score': float(nn_score),
            'ensemble_score': float(ensemble_score),
            'decision': 'MALICIOUS' if is_malicious else 'BENIGN',
            'pass_to_tier3': bool(is_malicious),
            'confidence': abs(ensemble_score - self.tier3_threshold),
            'feature_vector': features.flatten(),
            'feature_importance': feature_importance
        }
        
        return result
    
    def predict_batch(self,
                     analyses: List[Tuple[Dict, Dict, Dict]]) -> List[Dict]:
        """
        Batch prediction
        
        Args:
            analyses: List of (component_a, component_b, component_c) tuples
        
        Returns:
            List of prediction results
        """
        results = []
        
        for component_a, component_b, component_c in analyses:
            result = self.predict(component_a, component_b, component_c)
            results.append(result)
        
        return results
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        """Calculate statistics from batch results"""
        malicious = [r for r in results if r['decision'] == 'MALICIOUS']
        benign = [r for r in results if r['decision'] == 'BENIGN']
        
        stats = {
            'total_analyzed': len(results),
            'malicious_count': len(malicious),
            'benign_count': len(benign),
            'malicious_rate': len(malicious) / len(results) if results else 0,
            'pass_to_tier3_count': sum(1 for r in results if r['pass_to_tier3']),
            'avg_score_malicious': np.mean([r['ensemble_score'] for r in malicious]) if malicious else 0,
            'avg_score_benign': np.mean([r['ensemble_score'] for r in benign]) if benign else 0,
            'avg_rf_score': np.mean([r['rf_score'] for r in results]),
            'avg_nn_score': np.mean([r['nn_score'] for r in results]),
        }
        
        return stats
    
    def save_results(self, results: List[Dict], filepath: str):
        """Save prediction results to JSON"""
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = []
        for r in results:
            r_copy = r.copy()
            if 'feature_vector' in r_copy:
                r_copy['feature_vector'] = r_copy['feature_vector'].tolist()
            serializable_results.append(r_copy)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"✓ Results saved to: {filepath}")


class Tier2ClassifierTrainer:
    """
    Trainer for Tier 2 Classifier
    Use this in Google Colab for training
    """
    
    def __init__(self, input_dim: int = 58):
        self.input_dim = input_dim
        self.scaler = StandardScaler()
    
    def train_random_forest(self, 
                           X_train: np.ndarray, 
                           y_train: np.ndarray,
                           **rf_params) -> RandomForestClassifier:
        """
        Train Random Forest classifier
        
        Args:
            X_train: Training features
            y_train: Training labels
            **rf_params: Parameters for RandomForestClassifier
        
        Returns:
            Trained RF model
        """
        print("\n[Training Random Forest]")
        
        # Default parameters
        params = {
            'n_estimators': 200,
            'max_depth': 20,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'class_weight': 'balanced',
            'random_state': 42,
            'n_jobs': -1
        }
        params.update(rf_params)
        
        # Train
        rf_model = RandomForestClassifier(**params)
        rf_model.fit(X_train, y_train)
        
        print(f"  ✓ Random Forest trained with {params['n_estimators']} trees")
        
        return rf_model
    
    def train_neural_network(self,
                            X_train: np.ndarray,
                            y_train: np.ndarray,
                            X_val: np.ndarray,
                            y_val: np.ndarray,
                            hidden_dims: List[int] = [128, 64, 32],
                            epochs: int = 50,
                            batch_size: int = 32,
                            learning_rate: float = 0.001,
                            device: str = 'cpu') -> Tier2NeuralNet:
        """
        Train Neural Network classifier
        
        Returns:
            Trained NN model
        """
        print("\n[Training Neural Network]")
        
        device = torch.device(device)
        
        # Create model
        model = Tier2NeuralNet(self.input_dim, hidden_dims).to(device)
        
        # Loss and optimizer
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(device)
        y_train_tensor = torch.FloatTensor(y_train).to(device)
        X_val_tensor = torch.FloatTensor(X_val).to(device)
        y_val_tensor = torch.FloatTensor(y_val).to(device)
        
        # Training loop
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(epochs):
            model.train()
            
            # Mini-batch training
            num_batches = len(X_train) // batch_size
            total_loss = 0
            
            for i in range(num_batches):
                start_idx = i * batch_size
                end_idx = start_idx + batch_size
                
                batch_X = X_train_tensor[start_idx:end_idx]
                batch_y = y_train_tensor[start_idx:end_idx]
                
                # Forward pass
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / num_batches
            
            # Validation
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor).item()
            
            # Print progress
            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{epochs} - Train Loss: {avg_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"  Early stopping at epoch {epoch+1}")
                    break
        
        print(f"  ✓ Neural Network trained")
        
        return model
    
    def save_models(self,
                   rf_model: RandomForestClassifier,
                   nn_model: Tier2NeuralNet,
                   scaler: StandardScaler,
                   save_dir: str = './tier2_models'):
        """
        Save all trained models
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)
        
        # Save Random Forest
        rf_data = {
            'model': rf_model,
            'feature_count': self.input_dim
        }
        joblib.dump(rf_data, save_dir / 'tier2_rf_model.pkl')
        print(f"✓ Saved RF model to {save_dir / 'tier2_rf_model.pkl'}")
        
        # Save Neural Network
        nn_checkpoint = {
            'model_state_dict': nn_model.state_dict(),
            'input_dim': self.input_dim,
            'hidden_dims': [128, 64, 32]  # Should match training
        }
        torch.save(nn_checkpoint, save_dir / 'tier2_nn_model.pt')
        print(f"✓ Saved NN model to {save_dir / 'tier2_nn_model.pt'}")
        
        # Save scaler
        joblib.dump(scaler, save_dir / 'tier2_scaler.pkl')
        print(f"✓ Saved scaler to {save_dir / 'tier2_scaler.pkl'}")


# ===== EXAMPLE USAGE =====
if __name__ == '__main__':
    print("\n" + "="*60)
    print("COMPONENT D - ML CLASSIFIER")
    print("="*60)
    
    # Initialize classifier (without trained models for now)
    classifier = Tier2Classifier(
        rf_weight=0.5,
        nn_weight=0.5,
        tier3_threshold=70.0
    )
    
    # Create dummy features for testing
    dummy_component_a = {
        'aggregated_features': {
            'total_imports': 10,
            'dangerous_imports_count': 2,
            'has_os_import': 1,
            'has_subprocess_import': 0,
            'has_socket_import': 1,
            'functions_defined': 5,
            'functions_called_count': 20,
            'dangerous_calls_count': 3,
            'unique_functions': 15,
            'function_density': 0.5,
            'file_operations_count': 2,
            'network_operations_count': 5,
            'process_spawning_count': 1,
            'code_execution_count': 2,
            'has_api_abuse': 1,
            'dynamic_types_count': 1,
            'type_confusion_risk': 1,
            'has_dynamic_operations': 1,
            'tainted_flows_count': 2,
            'sink_locations_count': 2,
            'has_tainted_sink': 1,
            'cyclomatic_complexity': 10,
            'max_nesting_depth': 4,
            'lines_of_code': 100,
            'complexity_per_line': 0.1,
        }
    }
    
    dummy_component_b = {
        'aggregated_features': {
            'avg_string_entropy': 4.2,
            'max_string_entropy': 5.1,
            'high_entropy_count': 3,
            'base64_count': 2,
            'hex_string_count': 1,
            'unicode_escape_count': 0,
            'encoded_payload_count': 1,
            'staged_execution_count': 2,
            'dynamic_import_count': 1,
            'runtime_code_gen_count': 2,
            'time_check_count': 1,
            'trigger_condition_count': 1,
            'obfuscation_method_count': 3,
            'has_identifier_obfuscation': 1,
            'anti_debug_count': 1,
            'anti_vm_count': 0,
            'env_check_count': 1,
            'total_obfuscation_score': 8,
        }
    }
    
    dummy_component_c = {
        'aggregated_features': {
            'total_api_calls': 30,
            'unique_api_calls': 20,
            'max_call_depth': 3,
            'api_sequence_score': 20,
            'suspicious_sequence_count': 2,
            'has_suspicious_sequence': 1,
            'control_flow_complexity': 8,
            'max_nesting_depth_behavioral': 4,
            'matched_signature_count': 2,
            'max_signature_confidence': 0.8,
            'file_and_network': 1,
            'crypto_and_network': 0,
            'persistence_behavior': 1,
            'data_exfil_behavior': 1,
            'total_behavioral_risk': 65,
        }
    }
    
    # Make prediction
    print("\nMaking prediction with dummy features...")
    result = classifier.predict(
        dummy_component_a,
        dummy_component_b,
        dummy_component_c
    )
    
    print("\n" + "="*60)
    print("PREDICTION RESULT")
    print("="*60)
    print(f"RF Score: {result['rf_score']:.2f}/100")
    print(f"NN Score: {result['nn_score']:.2f}/100")
    print(f"Ensemble Score: {result['ensemble_score']:.2f}/100")
    print(f"Decision: {result['decision']}")
    print(f"Pass to Tier 3: {result['pass_to_tier3']}")
    print(f"Confidence: {result['confidence']:.2f}")
    
    print("\n✅ Component D initialized successfully!")