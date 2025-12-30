"""
component_c_wrapper.py
Component C Wrapper - Behavioral Pattern Analysis
"""

from component_c_behavioral import BehavioralPatternAnalyzer
from pathlib import Path
import tempfile
import os


class ComponentCWrapper:
    """Wrapper for Component C - Behavioral Pattern Analyzer"""
    
    def __init__(self):
        self.analyzer = BehavioralPatternAnalyzer()
    
    def analyze(self, code: str) -> dict:
        """
        Analyze code for behavioral patterns
        
        Args:
            code: Python source code string
            
        Returns:
            Dictionary with 12 behavioral features
        """
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_file.write(code)
            temp_path = Path(temp_file.name)
        
        try:
            results = self.analyzer.analyze_file(temp_path)
            feature_vector = self.analyzer.extract_features_vector(results)
            
            # Return 12 features (excluding 3 removed during training)
            features = {
                'total_api_calls': feature_vector.get('total_api_calls', 0),
                'unique_api_calls': feature_vector.get('unique_api_calls', 0),
                'max_call_depth': feature_vector.get('max_call_depth', 0),
                'api_sequence_score': feature_vector.get('api_sequence_score', 0),
                'suspicious_sequence_count': feature_vector.get('suspicious_sequence_count', 0),
                'has_suspicious_sequence': feature_vector.get('has_suspicious_sequence', 0),
                'control_flow_complexity': feature_vector.get('control_flow_complexity', 0),
                'max_nesting_depth': feature_vector.get('max_nesting_depth', 0),
                'file_and_network': feature_vector.get('file_and_network', 0),
                'crypto_and_network': feature_vector.get('crypto_and_network', 0),
                'persistence_behavior': feature_vector.get('persistence_behavior', 0),
                'data_exfil_behavior': feature_vector.get('data_exfil_behavior', 0),
            }
            
            return features
            
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass