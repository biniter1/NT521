"""
component_a_wrapper.py
Component A Wrapper - Enhanced Static Analysis
"""

from component_a_static import EnhancedStaticAnalyzer
from pathlib import Path
import tempfile
import os


class ComponentAWrapper:
    """Wrapper for Component A - Enhanced Static Analyzer"""
    
    def __init__(self):
        self.analyzer = EnhancedStaticAnalyzer()
    
    def analyze(self, code: str) -> dict:
        """
        Analyze code for static features
        
        Args:
            code: Python source code string
            
        Returns:
            Dictionary with 25 static features
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
            features = self.analyzer.extract_features_vector(results)
            return features
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass