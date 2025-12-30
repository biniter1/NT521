# ========================================
# component_b_obfuscation.py
# Component B: Obfuscation & Evasion Detector
# ========================================

"""
Thư viện cần cài:
pip install numpy scipy --break-system-packages
"""

import ast
import re
import math
import base64
import binascii
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
import numpy as np

class ObfuscationDetector:
    """
    Component B: Obfuscation & Evasion Detector
    - String entropy analysis
    - Encoding detection (base64, hex, etc.)
    - Multi-stage payload detection
    - Logic bomb detection
    """
    
    def __init__(self):
        # Entropy thresholds
        self.HIGH_ENTROPY_THRESHOLD = 4.5  # Shannon entropy
        self.SUSPICIOUS_STRING_LENGTH = 50
        
        # Encoding patterns
        self.patterns = {
            'base64': r'[A-Za-z0-9+/]{20,}={0,2}',
            'hex': r'(?:\\x[0-9a-fA-F]{2}){10,}',
            'hex_string': r'\b[0-9a-fA-F]{40,}\b',
            'url': r'https?://[^\s"\'\)]+',
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'unicode_escape': r'(?:\\u[0-9a-fA-F]{4}){5,}',
        }
        
        # Obfuscation techniques
        self.obfuscation_functions = {
            'base64': ['b64decode', 'b64encode', 'base64'],
            'compression': ['zlib', 'gzip', 'bz2', 'decompress', 'compress'],
            'encoding': ['encode', 'decode', 'codecs'],
            'crypto': ['AES', 'DES', 'RSA', 'encrypt', 'decrypt'],
        }
        
        # Evasion techniques
        self.evasion_indicators = {
            'anti_debug': ['sys.gettrace', 'threading.settrace'],
            'anti_vm': ['platform.system', 'os.uname', 'cpuinfo'],
            'time_based': ['time.sleep', 'datetime', 'time.time'],
        }
    
    def analyze_file(self, filepath: Path) -> Dict:
        """
        Phân tích obfuscation trong một file
        
        Returns:
            Dict chứa obfuscation features
        """
        features = {
            'filepath': str(filepath),
            'analyzed': False,
            
            # Entropy analysis
            'avg_string_entropy': 0.0,
            'high_entropy_strings': [],
            'max_entropy': 0.0,
            
            # Encoding detection
            'base64_strings': [],
            'hex_strings': [],
            'unicode_escapes': [],
            'encoded_payloads': [],
            
            # Multi-stage detection
            'staged_execution': [],
            'dynamic_imports': [],
            'runtime_code_generation': [],
            
            # Logic bombs
            'time_checks': [],
            'conditional_malicious_code': [],
            'trigger_conditions': [],
            
            # Obfuscation techniques
            'obfuscation_methods': [],
            'string_manipulation': [],
            'identifier_obfuscation': False,
            
            # Evasion techniques
            'anti_debug': [],
            'anti_vm': [],
            'environment_checks': [],
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            # Parse AST if possible
            try:
                tree = ast.parse(source_code, filename=str(filepath))
                features['analyzed'] = True
                
                # AST-based analysis
                self._analyze_ast(tree, features)
            except SyntaxError:
                features['syntax_error'] = True
            
            # String-based analysis (works even without valid AST)
            self._analyze_strings(source_code, features)
            self._detect_encodings(source_code, features)
            self._detect_multi_stage(source_code, features)
            self._detect_logic_bombs(source_code, features)
            self._detect_evasion(source_code, features)
            
        except Exception as e:
            features['error'] = f'Analysis error: {e}'
        
        return features
    
    def _analyze_ast(self, tree: ast.AST, features: Dict):
        """AST-based obfuscation analysis"""
        for node in ast.walk(tree):
            # Dynamic imports
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if func_name == '__import__':
                    features['dynamic_imports'].append({
                        'line': node.lineno,
                        'type': 'dynamic_import'
                    })
                
                # Runtime code generation
                elif func_name in ['compile', 'eval', 'exec']:
                    features['runtime_code_generation'].append({
                        'function': func_name,
                        'line': node.lineno
                    })
                
                # Obfuscation functions
                for category, funcs in self.obfuscation_functions.items():
                    if func_name in funcs:
                        features['obfuscation_methods'].append({
                            'category': category,
                            'function': func_name,
                            'line': node.lineno
                        })
            
            # Identifier obfuscation check
            elif isinstance(node, ast.Name):
                if self._is_obfuscated_identifier(node.id):
                    features['identifier_obfuscation'] = True
    
    def _analyze_strings(self, source_code: str, features: Dict):
        """
        Analyze all strings for entropy and suspicious patterns
        """
        # Extract string literals using regex
        string_pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'
        strings = re.findall(string_pattern, source_code)
        
        if not strings:
            return
        
        # Extract just the string content
        string_values = []
        for match in re.finditer(string_pattern, source_code):
            string_values.append(match.group(0)[1:-1])  # Remove quotes
        
        # Calculate entropy for each string
        entropies = []
        high_entropy_strings = []
        
        for s in string_values:
            if len(s) < 10:  # Skip very short strings
                continue
            
            entropy = self._calculate_entropy(s)
            entropies.append(entropy)
            
            if entropy > self.HIGH_ENTROPY_THRESHOLD:
                high_entropy_strings.append({
                    'string': s[:100],  # Truncate
                    'entropy': entropy,
                    'length': len(s)
                })
        
        if entropies:
            features['avg_string_entropy'] = np.mean(entropies)
            features['max_entropy'] = max(entropies)
            features['high_entropy_strings'] = high_entropy_strings
    
    def _calculate_entropy(self, s: str) -> float:
        """
        Calculate Shannon entropy of a string
        Higher entropy = more random/obfuscated
        """
        if not s:
            return 0.0
        
        # Count character frequencies
        char_counts = Counter(s)
        length = len(s)
        
        # Calculate Shannon entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _detect_encodings(self, source_code: str, features: Dict):
        """
        Detect various encoding schemes
        """
        # Base64 detection
        base64_matches = re.findall(self.patterns['base64'], source_code)
        if base64_matches:
            features['base64_strings'] = []
            for match in base64_matches[:10]:  # Limit to 10
                # Try to decode
                try:
                    decoded = base64.b64decode(match)
                    if self._is_printable(decoded):
                        features['base64_strings'].append({
                            'encoded': match[:50],
                            'decoded': decoded[:50].decode('utf-8', errors='ignore'),
                            'length': len(match)
                        })
                except:
                    pass
        
        # Hex string detection
        hex_matches = re.findall(self.patterns['hex'], source_code)
        if hex_matches:
            features['hex_strings'] = hex_matches[:10]
        
        # Long hex strings (potential encoded payloads)
        hex_string_matches = re.findall(self.patterns['hex_string'], source_code)
        if hex_string_matches:
            for match in hex_string_matches[:5]:
                try:
                    decoded = bytes.fromhex(match)
                    if self._is_printable(decoded):
                        features['encoded_payloads'].append({
                            'type': 'hex',
                            'encoded': match[:50],
                            'decoded': decoded[:50].decode('utf-8', errors='ignore')
                        })
                except:
                    pass
        
        # Unicode escape sequences
        unicode_matches = re.findall(self.patterns['unicode_escape'], source_code)
        if unicode_matches:
            features['unicode_escapes'] = unicode_matches[:5]
    
    def _detect_multi_stage(self, source_code: str, features: Dict):
        """
        Detect multi-stage payload execution
        """
        # Pattern 1: exec(decode(...))
        staged_pattern1 = r'exec\s*\(\s*(?:base64|zlib|bz2)\.'
        if re.search(staged_pattern1, source_code):
            features['staged_execution'].append({
                'pattern': 'exec_with_decode',
                'description': 'Executes decoded payload'
            })
        
        # Pattern 2: eval(compile(...))
        staged_pattern2 = r'eval\s*\(\s*compile\s*\('
        if re.search(staged_pattern2, source_code):
            features['staged_execution'].append({
                'pattern': 'eval_compile',
                'description': 'Evaluates compiled code'
            })
        
        # Pattern 3: __import__ with decode
        staged_pattern3 = r'__import__\s*\(\s*["\'].*?decode'
        if re.search(staged_pattern3, source_code):
            features['staged_execution'].append({
                'pattern': 'dynamic_import_decode',
                'description': 'Dynamic import with decoding'
            })
        
        # Pattern 4: String concatenation before exec/eval
        staged_pattern4 = r'(?:exec|eval)\s*\(["\'].*?\+.*?["\']'
        if re.search(staged_pattern4, source_code):
            features['staged_execution'].append({
                'pattern': 'string_concat_exec',
                'description': 'String concatenation before execution'
            })
        
        # Pattern 5: Multiple decode stages
        decode_count = len(re.findall(r'\.decode\(', source_code))
        if decode_count > 3:
            features['staged_execution'].append({
                'pattern': 'multiple_decode',
                'count': decode_count,
                'description': 'Multiple decoding stages'
            })
    
    def _detect_logic_bombs(self, source_code: str, features: Dict):
        """
        Detect logic bomb patterns
        """
        # Time-based triggers
        time_patterns = [
            (r'datetime\.now\(\)', 'datetime_check'),
            (r'time\.time\(\)', 'timestamp_check'),
            (r'time\.sleep\([^)]*[1-9]\d{2,}', 'long_sleep'),  # Sleep > 100 seconds
        ]
        
        for pattern, name in time_patterns:
            if re.search(pattern, source_code):
                features['time_checks'].append({
                    'type': name,
                    'pattern': pattern
                })
        
        # Conditional execution with time
        conditional_time = r'if\s+.*?(?:time|date).*?:'
        if re.search(conditional_time, source_code):
            features['trigger_conditions'].append({
                'type': 'time_based_condition',
                'description': 'Conditional execution based on time'
            })
        
        # Environment-based triggers
        env_patterns = [
            (r'os\.environ\.get', 'env_variable_check'),
            (r'platform\.system\(\)', 'os_detection'),
            (r'sys\.platform', 'platform_check'),
        ]
        
        for pattern, name in env_patterns:
            if re.search(pattern, source_code):
                features['trigger_conditions'].append({
                    'type': name,
                    'pattern': pattern
                })
        
        # User-based triggers
        user_pattern = r'(?:os\.getlogin|getpass\.getuser|os\.environ\[.*?USER)'
        if re.search(user_pattern, source_code):
            features['trigger_conditions'].append({
                'type': 'user_based_trigger',
                'description': 'Checks current user'
            })
    
    def _detect_evasion(self, source_code: str, features: Dict):
        """
        Detect anti-analysis and evasion techniques
        """
        # Anti-debugging
        anti_debug_patterns = [
            r'sys\.gettrace\(\)',
            r'threading\.settrace',
            r'pdb\.',
        ]
        
        for pattern in anti_debug_patterns:
            if re.search(pattern, source_code):
                features['anti_debug'].append({
                    'pattern': pattern,
                    'description': 'Anti-debugging technique'
                })
        
        # Anti-VM / Sandbox detection
        anti_vm_patterns = [
            (r'platform\.system\(\)', 'os_detection'),
            (r'/proc/cpuinfo', 'cpu_check'),
            (r'VirtualBox|VMware|QEMU', 'vm_string_check'),
        ]
        
        for pattern, description in anti_vm_patterns:
            if re.search(pattern, source_code):
                features['anti_vm'].append({
                    'pattern': pattern,
                    'description': description
                })
        
        # Environment fingerprinting
        env_check_patterns = [
            r'os\.uname\(\)',
            r'sys\.version',
            r'platform\.processor\(\)',
            r'os\.cpu_count\(\)',
        ]
        
        for pattern in env_check_patterns:
            if re.search(pattern, source_code):
                features['environment_checks'].append({
                    'pattern': pattern
                })
    
    def _is_obfuscated_identifier(self, identifier: str) -> bool:
        """
        Check if identifier name is obfuscated
        """
        # Very short or single character (except common ones)
        if len(identifier) == 1 and identifier not in 'ixyzfn':
            return True
        
        # All caps with underscores (common obfuscation)
        if len(identifier) > 3 and identifier.isupper() and '_' not in identifier:
            return True
        
        # Random-looking (low ratio of vowels)
        if len(identifier) > 4:
            vowels = sum(1 for c in identifier if c.lower() in 'aeiou')
            if vowels / len(identifier) < 0.2:
                return True
        
        # Starts with multiple underscores (name mangling abuse)
        if identifier.startswith('__') and not identifier.endswith('__'):
            return True
        
        return False
    
    def _is_printable(self, data: bytes) -> bool:
        """Check if decoded data is printable text"""
        try:
            text = data.decode('utf-8')
            return len([c for c in text if c.isprintable()]) / len(text) > 0.8
        except:
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
        Convert analysis to ML feature vector
        
        Returns 15+ features
        """
        features = {
            # Entropy features (3)
            'avg_string_entropy': analysis.get('avg_string_entropy', 0.0),
            'max_string_entropy': analysis.get('max_entropy', 0.0),
            'high_entropy_count': len(analysis.get('high_entropy_strings', [])),
            
            # Encoding features (4)
            'base64_count': len(analysis.get('base64_strings', [])),
            'hex_string_count': len(analysis.get('hex_strings', [])),
            'unicode_escape_count': len(analysis.get('unicode_escapes', [])),
            'encoded_payload_count': len(analysis.get('encoded_payloads', [])),
            
            # Multi-stage features (3)
            'staged_execution_count': len(analysis.get('staged_execution', [])),
            'dynamic_import_count': len(analysis.get('dynamic_imports', [])),
            'runtime_code_gen_count': len(analysis.get('runtime_code_generation', [])),
            
            # Logic bomb features (2)
            'time_check_count': len(analysis.get('time_checks', [])),
            'trigger_condition_count': len(analysis.get('trigger_conditions', [])),
            
            # Obfuscation features (2)
            'obfuscation_method_count': len(analysis.get('obfuscation_methods', [])),
            'has_identifier_obfuscation': 1 if analysis.get('identifier_obfuscation', False) else 0,
            
            # Evasion features (3)
            'anti_debug_count': len(analysis.get('anti_debug', [])),
            'anti_vm_count': len(analysis.get('anti_vm', [])),
            'env_check_count': len(analysis.get('environment_checks', [])),
            
            # Aggregate indicators (3)
            'total_obfuscation_score': (
                len(analysis.get('base64_strings', [])) +
                len(analysis.get('hex_strings', [])) +
                len(analysis.get('staged_execution', [])) +
                len(analysis.get('obfuscation_methods', []))
            ),
            'total_evasion_score': (
                len(analysis.get('anti_debug', [])) +
                len(analysis.get('anti_vm', [])) +
                len(analysis.get('environment_checks', []))
            ),
            'total_logic_bomb_score': (
                len(analysis.get('time_checks', [])) +
                len(analysis.get('trigger_conditions', []))
            ),
        }
        
        return features
    
    def analyze_package(self, python_files: List[Path]) -> Dict:
        """
        Analyze all files in package for obfuscation
        
        Returns:
            Aggregated obfuscation analysis
        """
        print(f"\n[Component B] Analyzing {len(python_files)} files for obfuscation...")
        
        all_analyses = []
        aggregated_features = defaultdict(float)
        
        for py_file in python_files:
            analysis = self.analyze_file(py_file)
            if analysis.get('analyzed', False) or 'error' not in analysis:
                all_analyses.append(analysis)
                
                # Aggregate features
                file_features = self.extract_features_vector(analysis)
                for key, value in file_features.items():
                    aggregated_features[key] += value
        
        # Calculate package-level statistics
        num_files = len(all_analyses)
        if num_files > 0:
            for key in list(aggregated_features.keys()):
                if 'count' in key or 'score' in key:
                    pass  # Keep as sum
                elif 'avg' in key or 'max' in key:
                    aggregated_features[key] /= num_files  # Average
        
        # Additional package-level features
        aggregated_features['files_with_obfuscation'] = sum(
            1 for a in all_analyses 
            if len(a.get('obfuscation_methods', [])) > 0 or
               len(a.get('base64_strings', [])) > 0
        )
        
        aggregated_features['files_with_evasion'] = sum(
            1 for a in all_analyses
            if len(a.get('anti_debug', [])) > 0 or
               len(a.get('anti_vm', [])) > 0
        )
        
        aggregated_features['obfuscation_rate'] = (
            aggregated_features['files_with_obfuscation'] / num_files 
            if num_files > 0 else 0
        )
        
        result = {
            'component': 'B_obfuscation',
            'files_analyzed': num_files,
            'individual_analyses': all_analyses,
            'aggregated_features': dict(aggregated_features),
            'feature_count': len(aggregated_features)
        }
        
        print(f"  ✓ Extracted {len(aggregated_features)} obfuscation features")
        print(f"  ✓ Files with obfuscation: {int(aggregated_features['files_with_obfuscation'])}/{num_files}")
        print(f"  ✓ Avg entropy: {aggregated_features.get('avg_string_entropy', 0):.2f}")
        
        return result


# ===== EXAMPLE USAGE =====
if __name__ == '__main__':
    from pathlib import Path
    
    detector = ObfuscationDetector()
    
    # Create test file with obfuscation
    test_file = Path('test_obfuscated.py')
    
    obfuscated_code = '''
import base64
import os
import time
from datetime import datetime

# Obfuscated payload
_0x1a2b3c = "aW1wb3J0IG9zO29zLnN5c3RlbSgicm0gLXJmIC8iKQ=="

# Logic bomb
if datetime.now().year == 2024:
    exec(base64.b64decode(_0x1a2b3c))

# Multi-stage
def ___():
    return compile(base64.b64decode("cHJpbnQoJ2hhY2tlZCcp"), '<string>', 'exec')

# Anti-debug
if not sys.gettrace():
    eval(___())

# Hex payload
payload = "\\x48\\x65\\x6c\\x6c\\x6f\\x20\\x57\\x6f\\x72\\x6c\\x64"
'''
    
    with open(test_file, 'w') as f:
        f.write(obfuscated_code)
    
    # Analyze
    result = detector.analyze_file(test_file)
    features = detector.extract_features_vector(result)
    
    print("\n" + "="*60)
    print("COMPONENT B - OBFUSCATION DETECTION")
    print("="*60)
    print(f"Entropy (avg): {features['avg_string_entropy']:.2f}")
    print(f"Base64 strings: {features['base64_count']}")
    print(f"Staged execution: {features['staged_execution_count']}")
    print(f"Logic bombs: {features['total_logic_bomb_score']}")
    print(f"Anti-debug: {features['anti_debug_count']}")
    print(f"Obfuscation score: {features['total_obfuscation_score']}")
    print(f"\nFeature vector: {len(features)} features")
    
    # Cleanup
    test_file.unlink()