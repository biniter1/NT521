"""
component_b_wrapper.py
Component B Wrapper - Obfuscation & Evasion Detector
"""

from component_b_obfuscation import ObfuscationDetector
from pathlib import Path
import tempfile
import os


class ComponentBWrapper:
    """Wrapper for Component B - Obfuscation Detector"""
    
    def __init__(self):
        self.detector = ObfuscationDetector()
    
    def analyze(self, code: str) -> dict:
        """
        Analyze code for obfuscation features
        
        Args:
            code: Python source code string
            
        Returns:
            Dictionary with 20 obfuscation features
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
            results = self.detector.analyze_file(temp_path)
            features = self.detector.extract_features_vector(results)
            return features
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass