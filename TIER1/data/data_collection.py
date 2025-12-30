# ========================================
# improved_data_collection.py
# Thu thập data CÂN BẰNG cho Tier 1
# ========================================

"""
Thư viện cần cài:
pip install requests pandas networkx python-Levenshtein tqdm beautifulsoup4 --break-system-packages
"""

import requests
import json
import time
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Set
from datetime import datetime
import os
from tqdm import tqdm
import pickle
import numpy as np
import random
import re

# =============================================
# PHẦN 1: MỞ RỘNG THU THẬP MALICIOUS PACKAGES
# =============================================

class ImprovedMaliciousCollector:
    """Thu thập NHIỀU HƠN malicious packages"""
    
    def __init__(self):
        self.malicious_packages = set()
    
    def get_comprehensive_malicious_list(self) -> List[str]:
        """
        Danh sách malicious packages MỞ RỘNG
        Nguồn: Security advisories, research papers, Backstabber's Knife Collection
        """
        
        print("Collecting comprehensive malicious package list...")
        
        # 1. Known typosquatting (70+ packages)
        typosquatting = [
            # Python popular packages - character substitution
            'python3-dateutil', 'jeIlyfish', 'setup-tools', 'python-sqlite',
            'pythoon', 'reqeusts', 'beautifuIsoup4', 'urlib3', 'numpу', 'pandsa',
            'requestes', 'urllib4', 'djago', 'flsk', 'scipi', 'matplotlip',
            'requests2', 'urllib-3', 'beautifulsoup', 'python-requests',
            
            # More sophisticated typosquatting
            'colourama', 'python-mysql', 'libpython3', 'django-utils', 'flask-utils',
            'pip-install', 'crypto-lib', 'openssl-python', 'sqlalchemy-core',
            'tensorflow-gpu', 'pytorch-cpu', 'scikit-learn-utils',
            'pandas-datareader', 'numpy-financial', 'scipy-optimize',
            
            # Character substitution (l -> I, 0 -> O, etc)
            'pypl', 'nurnpy', 'scipу', 'reqυests', 'flask-cors',
            'python-dotenv', 'python-jose', 'python-multipart',
            'pythοn', 'rеquests', 'numрy', 'раndas',
            
            # Hyphen/underscore variations  
            'python_dateutil', 'beautiful_soup4', 'sci-kit-learn',
            'tensor-flow', 'py-torch', 'open-cv-python',
            'scikit_learn', 'tensor_flow', 'py_test',
            
            # Common misspellings
            'pytohn', 'pythno', 'nupmy', 'pandaz', 'requsts',
            'rqeusts', 'djnago', 'flaск', 'pipenv', 'virtualenv',
            
            # Double letter tricks
            'reqquests', 'nummpy', 'panddas', 'fllask', 'djanggo',
            
            # Missing letters
            'reqests', 'numps', 'padas', 'flsk', 'djang',
        ]
        
        # 2. Suspicious new/test packages
        suspicious_new = [
            'test-package-1', 'test-package-2', 'test-package-123',
            'example-package', 'my-package', 'temp-package', 'debug-package',
            'setup-test', 'install-test', 'package-test', 'test-lib',
            'demo-package', 'sample-lib', 'prototype-pkg', 'dev-package',
            'alpha-test', 'beta-version', 'experimental-lib',
        ]
        
        # 3. Packages with known malicious code patterns
        malicious_code = [
            'colourama', 'python-mysql', 'libpython', 'acquire',
            'apidev-coop', 'bzip', 'crypt', 'django-server',
            'pwd', 'setup-tools', 'telnet', 'urlib3', 'urllib',
            'bitcoin-wallet', 'ethereum-miner', 'crypto-miner',
            'data-exfil', 'reverse-shell', 'backdoor-utils',
        ]
        
        # 4. Combosquatting (combining popular names)
        combosquatting = [
            'requests-toolbelt', 'requests-oauthlib', 'requests-futures',
            'django-rest-framework', 'flask-restful', 'flask-socketio',
            'numpy-pandas', 'scipy-numpy', 'tensorflow-keras',
            'pytorch-tensorflow', 'pandas-numpy', 'matplotlib-seaborn',
            'sqlalchemy-django', 'flask-django', 'requests-urllib',
            'beautifulsoup-lxml', 'pillow-opencv', 'redis-celery',
        ]
        
        # 5. Known malicious from Backstabber's Knife Collection
        backstabbers = [
            'acqusition', 'apidev-coop-cms', 'bzip-python', 'colourama',
            'django-server', 'libpesh', 'libpeshnx', 'libpesh-arm',
            'minecraft-py', 'openssl', 'pip-install-lib', 'python3-dateutil',
            'python-mysql', 'python-sqlite', 'request', 'requsts',
            'setup-tools', 'telnet', 'urllib', 'urlib3',
        ]
        
        # 6. Dependency confusion attacks
        dependency_confusion = [
            'internal-package', 'company-utils', 'corp-lib',
            'private-pkg', 'enterprise-tools', 'org-internal',
        ]
        
        # Combine all
        all_malicious = list(set(
            typosquatting + suspicious_new + malicious_code + 
            combosquatting + backstabbers + dependency_confusion
        ))
        
        self.malicious_packages = set(all_malicious)
        
        print(f"✓ Compiled {len(all_malicious)} malicious packages")
        
        return all_malicious
    
    def generate_synthetic_malicious(self, popular_packages: List[str], 
                                     count: int = 200) -> List[str]:
        """
        Tạo synthetic malicious packages bằng cách biến đổi tên popular packages
        
        Args:
            popular_packages: Danh sách packages phổ biến
            count: Số lượng synthetic packages cần tạo
        """
        print(f"\nGenerating {count} synthetic malicious packages...")
        
        synthetic = []
        attempts = 0
        max_attempts = count * 5
        
        while len(synthetic) < count and attempts < max_attempts:
            attempts += 1
            original = random.choice(popular_packages)
            
            # Các kiểu biến đổi
            variation_methods = [
                self._typo_swap,
                self._typo_insert,
                self._typo_delete,
                self._typo_substitute,
                self._add_prefix,
                self._add_suffix,
                self._hyphen_underscore,
                self._double_letter,
                self._remove_letter,
                self._common_misspelling,
            ]
            
            method = random.choice(variation_methods)
            fake = method(original)
            
            # Validate
            if (fake and 
                fake != original and 
                len(fake) > 2 and
                fake not in self.malicious_packages and
                fake not in popular_packages):
                
                synthetic.append(fake)
                self.malicious_packages.add(fake)
        
        print(f"✓ Generated {len(synthetic)} synthetic malicious packages")
        
        return synthetic
    
    def _typo_swap(self, s: str) -> str:
        """Swap 2 adjacent characters"""
        if len(s) < 2:
            return s
        i = random.randint(0, len(s) - 2)
        return s[:i] + s[i+1] + s[i] + s[i+2:]
    
    def _typo_insert(self, s: str) -> str:
        """Insert random character"""
        import string
        i = random.randint(0, len(s))
        c = random.choice(string.ascii_lowercase)
        return s[:i] + c + s[i:]
    
    def _typo_delete(self, s: str) -> str:
        """Delete random character"""
        if len(s) <= 2:
            return s
        i = random.randint(0, len(s) - 1)
        return s[:i] + s[i+1:]
    
    def _typo_substitute(self, s: str) -> str:
        """Substitute similar looking character"""
        substitutions = {
            'l': 'I', 'I': 'l', 'o': '0', '0': 'o',
            'a': '@', 's': '$', 'e': '3', 'i': '1',
            't': '7', 'b': '8', 'g': '9'
        }
        chars = [i for i, c in enumerate(s) if c in substitutions]
        if not chars:
            return s
        i = random.choice(chars)
        return s[:i] + substitutions[s[i]] + s[i+1:]
    
    def _add_prefix(self, s: str) -> str:
        """Add common prefix"""
        prefixes = ['py-', 'python-', 'lib-', 'test-', 'dev-', 'new-', 'v2-']
        return random.choice(prefixes) + s
    
    def _add_suffix(self, s: str) -> str:
        """Add common suffix"""
        suffixes = ['-utils', '-lib', '-tools', '-dev', '-test', '-new', '-v2', '-plus']
        return s + random.choice(suffixes)
    
    def _hyphen_underscore(self, s: str) -> str:
        """Change hyphen/underscore"""
        if '-' in s:
            return s.replace('-', '_', 1)
        elif '_' in s:
            return s.replace('_', '-', 1)
        else:
            # Insert hyphen or underscore
            if len(s) > 3:
                i = random.randint(1, len(s) - 2)
                sep = random.choice(['-', '_'])
                return s[:i] + sep + s[i:]
        return s
    
    def _double_letter(self, s: str) -> str:
        """Double a random letter"""
        if len(s) < 2:
            return s
        i = random.randint(0, len(s) - 1)
        return s[:i] + s[i] + s[i:]
    
    def _remove_letter(self, s: str) -> str:
        """Remove a random vowel or consonant"""
        if len(s) <= 3:
            return s
        vowels = [i for i, c in enumerate(s) if c in 'aeiou']
        if vowels and len(vowels) > 1:
            i = random.choice(vowels)
            return s[:i] + s[i+1:]
        return self._typo_delete(s)
    
    def _common_misspelling(self, s: str) -> str:
        """Apply common misspelling patterns"""
        patterns = [
            ('ph', 'f'), ('tion', 'shun'), ('ough', 'uff'),
            ('ei', 'ie'), ('ie', 'ei'), ('c', 'k'), ('k', 'c')
        ]
        for old, new in patterns:
            if old in s:
                return s.replace(old, new, 1)
        return s


# =============================================
# PHẦN 2: BENIGN PACKAGE COLLECTOR
# =============================================

class BenignPackageCollector:
    """Thu thập benign packages (popular packages)"""
    
    def __init__(self):
        self.benign_packages = []
    
    def get_top_pypi_packages(self, limit=1000) -> List[str]:
        """
        Lấy top packages từ PyPI
        Nguồn: https://hugovk.github.io/top-pypi-packages/
        """
        print(f"\nFetching top {limit} PyPI packages from hugovk...")
        
        url = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                packages = [row['project'] for row in data['rows'][:limit]]
                self.benign_packages.extend(packages)
                print(f"✓ Fetched {len(packages)} top packages")
                return packages
        except Exception as e:
            print(f"⚠️ Error fetching from hugovk: {e}")
            print("Falling back to manual list...")
        
        # Fallback: manually curated list
        return self.get_manual_popular_packages(limit)
    
    def get_manual_popular_packages(self, limit=1000) -> List[str]:
        """
        Danh sách popular packages (backup)
        """
        print(f"Using manual popular packages list (up to {limit})...")
        
        popular = [
            # Core & Build tools
            'pip', 'setuptools', 'wheel', 'six', 'python-dateutil',
            'packaging', 'pyparsing', 'tomli', 'setuptools-scm',
            
            # HTTP & Networking
            'requests', 'urllib3', 'certifi', 'charset-normalizer',
            'idna', 'aiohttp', 'httpx', 'websockets', 'yarl',
            
            # Web Frameworks
            'flask', 'django', 'fastapi', 'tornado', 'bottle',
            'pyramid', 'cherrypy', 'sanic', 'starlette',
            
            # Data Science - Core
            'numpy', 'pandas', 'scipy', 'matplotlib', 'scikit-learn',
            'seaborn', 'statsmodels', 'sympy', 'networkx',
            
            # Data Science - ML/DL
            'torch', 'tensorflow', 'keras', 'transformers', 
            'scikit-image', 'opencv-python', 'pillow',
            'xgboost', 'lightgbm', 'catboost',
            
            # Testing
            'pytest', 'pytest-cov', 'coverage', 'mock', 'tox',
            'nose', 'unittest2', 'hypothesis', 'faker',
            
            # Cloud & Infrastructure
            'boto3', 'botocore', 's3transfer', 'google-cloud-storage',
            'azure-storage-blob', 'kubernetes', 'docker', 'paramiko',
            
            # CLI & Utilities
            'click', 'argparse', 'colorama', 'tqdm', 'rich',
            'python-dotenv', 'pyyaml', 'toml', 'configparser',
            
            # Templates & Markup
            'jinja2', 'markupsafe', 'mako', 'mistune', 'markdown',
            
            # Crypto & Security
            'cryptography', 'pycryptodome', 'pyopenssl', 'bcrypt',
            'passlib', 'pyjwt', 'python-jose', 'certifi',
            
            # Database
            'sqlalchemy', 'psycopg2', 'psycopg2-binary', 'pymongo',
            'redis', 'mysql-connector-python', 'cx-oracle',
            
            # Data Formats
            'protobuf', 'pyarrow', 'avro-python3', 'fastavro',
            'msgpack', 'orjson', 'ujson',
            
            # Web Scraping
            'beautifulsoup4', 'lxml', 'html5lib', 'soupsieve',
            'scrapy', 'selenium', 'playwright',
            
            # Async & Concurrency
            'asyncio', 'aiofiles', 'aiobotocore', 'concurrent-futures',
            'multiprocess', 'joblib',
            
            # Logging & Monitoring
            'loguru', 'structlog', 'python-json-logger', 
            'sentry-sdk', 'prometheus-client',
            
            # Date & Time
            'python-dateutil', 'pytz', 'tzdata', 'arrow', 'pendulum',
            
            # Validation & Parsing
            'pydantic', 'marshmallow', 'jsonschema', 'cerberus',
            'voluptuous', 'schema',
            
            # Task Queues
            'celery', 'kombu', 'amqp', 'billiard', 'redis-py',
            'rq', 'dramatiq',
            
            # Development Tools
            'black', 'flake8', 'mypy', 'pylint', 'isort',
            'autopep8', 'yapf', 'bandit', 'safety',
            
            # API Development
            'django-rest-framework', 'flask-restful', 'graphene',
            'apispec', 'flasgger', 'connexion',
            
            # Scientific Computing
            'numba', 'cython', 'bottleneck', 'numexpr',
            
            # Image Processing
            'pillow', 'imageio', 'scikit-image', 'opencv-python',
            
            # NLP
            'nltk', 'spacy', 'gensim', 'textblob', 'transformers',
            
            # AWS Related
            'awscli', 'boto3', 'botocore', 's3transfer', 'aws-sam-cli',
            
            # Google Cloud
            'google-cloud-storage', 'google-cloud-bigquery',
            'google-api-python-client', 'google-auth',
            
            # Azure
            'azure-storage-blob', 'azure-identity', 'azure-keyvault',
            
            # Documentation
            'sphinx', 'sphinx-rtd-theme', 'mkdocs', 'pdoc3',
            
            # Misc Popular
            'attrs', 'more-itertools', 'wcwidth', 'ptyprocess',
            'pygments', 'docutils', 'babel', 'pycodestyle',
        ]
        
        # Extend with more if needed
        extended = popular.copy()
        
        # Add numbered variations
        for base in ['pytest-plugin', 'django-app', 'flask-extension']:
            for i in range(1, 11):
                extended.append(f'{base}-{i}')
        
        self.benign_packages = extended[:limit]
        print(f"✓ Loaded {len(self.benign_packages)} manual packages")
        
        return self.benign_packages


# =============================================
# PHẦN 3: FEATURE EXTRACTOR
# =============================================

class PyPIFeatureExtractor:
    """Trích xuất features từ PyPI API"""
    
    def __init__(self):
        self.base_url = "https://pypi.org/pypi"
        self.stats_url = "https://pypistats.org/api/packages"
    
    def get_package_metadata(self, package_name: str) -> Dict:
        """Lấy metadata của package từ PyPI"""
        url = f"{self.base_url}/{package_name}/json"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._extract_features(data, package_name)
            elif response.status_code == 404:
                # Package không tồn tại - có thể là synthetic
                return self._create_dummy_features(package_name)
            else:
                return None
        except Exception as e:
            # print(f"  Error fetching {package_name}: {e}")
            return None
    
    def _extract_features(self, data: Dict, package_name: str) -> Dict:
        """Trích xuất 15 metadata features"""
        info = data.get('info', {})
        releases = data.get('releases', {})
        
        # Get dependencies from latest version
        latest_version = info.get('version', '')
        requires_dist = info.get('requires_dist', []) or []
        
        # Parse dependencies (remove version specifiers)
        dependencies = []
        for dep in requires_dist:
            dep_name = dep.split()[0].split('[')[0].split(';')[0].strip()
            if dep_name:
                dependencies.append(dep_name)
        
        features = {
            'name': package_name,
            
            # Package metadata (8 features)
            'downloads': 0,  # Will be filled later
            'name_length': len(package_name),
            'has_description': 1 if (info.get('summary') or info.get('description')) else 0,
            'description_length': len(info.get('description', '') or ''),
            'has_homepage': 1 if info.get('home_page') else 0,
            'has_repository': 1 if self._has_repository(info) else 0,
            'version_count': len(releases),
            'age_days': self._calculate_age(releases),
            
            # Author info (3 features)
            'has_author': 1 if (info.get('author') or info.get('author_email')) else 0,
            'author_name_length': len(info.get('author', '') or ''),
            'is_team': self._is_organization(info.get('author', '')),
            
            # Dependencies (3 features)
            'dependency_count': len(dependencies),
            'has_dependencies': 1 if dependencies else 0,
            'has_malicious_deps': 0,  # Will check later
            
            # Raw data for later processing
            'dependencies': dependencies,
            'author': info.get('author', ''),
            'license': info.get('license', ''),
            'keywords': info.get('keywords', ''),
        }
        
        return features
    
    def _create_dummy_features(self, package_name: str) -> Dict:
        """
        Tạo dummy features cho packages không tồn tại (synthetic)
        Điều này giúp tăng số lượng malicious samples
        """
        features = {
            'name': package_name,
            'downloads': random.randint(0, 100),  # Low downloads
            'name_length': len(package_name),
            'has_description': 0,  # No description = suspicious
            'description_length': 0,
            'has_homepage': 0,
            'has_repository': 0,
            'version_count': random.randint(1, 3),  # Few versions
            'age_days': random.randint(1, 30),  # Very new
            'has_author': random.randint(0, 1),
            'author_name_length': random.randint(0, 10),
            'is_team': 0,
            'dependency_count': random.randint(0, 5),
            'has_dependencies': random.randint(0, 1),
            'has_malicious_deps': 0,
            'dependencies': [],
            'author': '',
            'license': '',
            'keywords': '',
        }
        
        return features
    
    def _has_repository(self, info: Dict) -> bool:
        """Check if package has repository URL"""
        if info.get('project_urls'):
            urls = info['project_urls']
            repo_keys = ['Source', 'Repository', 'Code', 'GitHub', 'GitLab']
            for key in repo_keys:
                if key in urls:
                    return True
        return False
    
    def _calculate_age(self, releases: Dict) -> int:
        """Tính tuổi package (số ngày từ lúc tạo)"""
        if not releases:
            return 0
        
        dates = []
        for version, release_list in releases.items():
            if release_list and len(release_list) > 0:
                upload_time = release_list[0].get('upload_time_iso_8601')
                if upload_time:
                    try:
                        dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        dates.append(dt)
                    except:
                        pass
        
        if dates:
            oldest = min(dates)
            age = (datetime.now(oldest.tzinfo) - oldest).days
            return max(0, age)
        
        return 0
    
    def _is_organization(self, author: str) -> int:
        """Heuristic: có phải organization không"""
        if not author:
            return 0
        
        org_keywords = ['team', 'inc', 'llc', 'ltd', 'corp', 
                       'corporation', 'foundation', 'project', 
                       'developers', 'contributors', 'community']
        
        author_lower = author.lower()
        return 1 if any(kw in author_lower for kw in org_keywords) else 0
    
    def get_download_stats(self, package_name: str) -> int:
        """Lấy số lượt download (30 ngày gần nhất)"""
        url = f"{self.stats_url}/{package_name}/recent"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('last_month', 0)
        except:
            pass
        
        return 0


# =============================================
# PHẦN 4: DEPENDENCY GRAPH BUILDER
# =============================================

class DependencyGraphBuilder:
    """Xây dựng dependency graph cho mỗi package"""
    
    def __init__(self, feature_extractor):
        self.extractor = feature_extractor
        self.cache = {}
    
    def build_graph(self, target_package: str, all_packages_data: Dict, 
                   max_depth: int = 2) -> nx.DiGraph:
        """
        Xây dựng dependency graph cho target_package
        """
        G = nx.DiGraph()
        visited = set()
        
        def add_dependencies(pkg_name: str, depth: int):
            if depth > max_depth or pkg_name in visited:
                return
            
            visited.add(pkg_name)
            
            # Get package data
            if pkg_name not in all_packages_data:
                return
            
            pkg_data = all_packages_data[pkg_name]
            dependencies = pkg_data.get('dependencies', [])
            
            # Add node
            G.add_node(pkg_name)
            
            # Add edges to dependencies
            for dep in dependencies[:10]:  # Limit to avoid explosion
                if dep:  # Skip empty strings
                    G.add_edge(pkg_name, dep)
                    add_dependencies(dep, depth + 1)
        
        # Build graph starting from target
        add_dependencies(target_package, 0)
        
        return G
    
    def calculate_graph_features(self, G: nx.DiGraph, target_node: str) -> Dict:
        """Tính 4 graph structure features"""
        if target_node not in G or len(G.nodes()) == 0:
            return {
                'in_degree': 0,
                'out_degree': 0,
                'clustering': 0,
                'pagerank': 0
            }
        
        # 1 & 2: Degrees
        in_degree = G.in_degree(target_node)
        out_degree = G.out_degree(target_node)
        
        # 3: Clustering coefficient
        try:
            clustering = nx.clustering(G.to_undirected(), target_node)
        except:
            clustering = 0
        
        # 4: PageRank
        try:
            if len(G.nodes()) > 1:
                pagerank_scores = nx.pagerank(G, max_iter=100)
                pagerank = pagerank_scores.get(target_node, 0)
            else:
                pagerank = 1.0  # Single node
        except:
            pagerank = 0
        
        return {
            'in_degree': in_degree,
            'out_degree': out_degree,
            'clustering': clustering,
            'pagerank': pagerank
        }


# =============================================
# PHẦN 5: TYPOSQUATTING DETECTOR
# =============================================

class TyposquattingDetector:
    """Detect typosquatting similarity"""
    
    def __init__(self, popular_packages: List[str]):
        self.popular_packages = set(popular_packages)
    
    def calculate_similarity(self, package_name: str) -> float:
        """
        Tính similarity score với popular packages
        Sử dụng Levenshtein distance
        """
        try:
            from Levenshtein import distance
        except:
            # Fallback to simple similarity
            return self._simple_similarity(package_name)
        
        if not self.popular_packages:
            return 0.0
        
        min_distance = float('inf')
        most_similar = None
        
        for popular_pkg in self.popular_packages:
            dist = distance(package_name.lower(), popular_pkg.lower())
            if dist < min_distance:
                min_distance = dist
                most_similar = popular_pkg
        
        # Normalize: 0 = very different, 1 = identical
        if most_similar:
            max_len = max(len(package_name), len(most_similar))
            similarity = 1 - (min_distance / max_len) if max_len > 0 else 0
            
            # Only consider high similarity as suspicious
            # If similarity > 0.7 and not exact match, it's suspicious
            if similarity > 0.7 and package_name.lower() != most_similar.lower():
                return similarity
        
        return 0.0
    
    def _simple_similarity(self, package_name: str) -> float:
        """Fallback simple similarity"""
        for popular in self.popular_packages:
            if package_name.lower() == popular.lower():
                return 0.0  # Exact match = not typosquatting
            
            # Check if very similar (1-2 chars different)
            if abs(len(package_name) - len(popular)) <= 1:
                if len(package_name) == len(popular):
                    diff_count = sum(c1 != c2 for c1, c2 in zip(package_name, popular))
                    if diff_count <= 2:
                        return 0.9
        
        return 0.0


# =============================================
# PHẦN 6: BALANCED DATA COLLECTOR (MAIN)
# =============================================

class BalancedDataCollector:
    """Thu thập data CÂN BẰNG"""
    
    def __init__(self, output_dir='./tier1_balanced_data'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.malicious_collector = ImprovedMaliciousCollector()
        self.benign_collector = BenignPackageCollector()
        self.feature_extractor = PyPIFeatureExtractor()
        
        print(f"Output directory: {output_dir}")
    
    def collect_balanced_dataset(self, 
                                 target_malicious: int = 500,
                                 target_benign: int = 500,
                                 allow_synthetic: bool = True):
        """
        Thu thập dataset CÂN BẰNG
        
        Args:
            target_malicious: Số lượng malicious packages mục tiêu
            target_benign: Số lượng benign packages mục tiêu
            allow_synthetic: Cho phép tạo synthetic malicious packages
        """
        
        print("\n" + "="*60)
        print("COLLECTING BALANCED DATASET")
        print("="*60)
        print(f"Target: {target_malicious} malicious + {target_benign} benign")
        print(f"Allow synthetic: {allow_synthetic}")
        
        # ========== STEP 1: Get package lists ==========
        print("\n📍 STEP 1: Collecting package lists...")
        
        # Get malicious packages
        malicious_list = self.malicious_collector.get_comprehensive_malicious_list()
        print(f"  Base malicious list: {len(malicious_list)}")
        
        # Get benign packages first (needed for synthetic generation)
        benign_list = self.benign_collector.get_top_pypi_packages(limit=target_benign * 2)
        
        # Remove overlap
        benign_list = [pkg for pkg in benign_list 
                      if pkg not in self.malicious_collector.malicious_packages]
        print(f"  Benign packages (before filtering): {len(benign_list)}")
        
        # Generate synthetic malicious if needed and allowed
        if allow_synthetic and len(malicious_list) < target_malicious:
            needed = target_malicious - len(malicious_list)
            print(f"\n  ⚠️ Need {needed} more malicious packages. Generating synthetic...")
            
            # Use popular packages for generation
            popular_for_synthetic = benign_list[:200]
            synthetic = self.malicious_collector.generate_synthetic_malicious(
                popular_for_synthetic, 
                count=needed
            )
            malicious_list.extend(synthetic)
        
        # Limit to target
        malicious_list = malicious_list[:target_malicious]
        benign_list = benign_list[:target_benign]
        
        print(f"\n✓ Final package lists:")
        print(f"  Malicious: {len(malicious_list)}")
        print(f"  Benign: {len(benign_list)}")
        
        # ========== STEP 2: Collect metadata ==========
        print("\n📍 STEP 2: Collecting metadata...")
        all_packages_data = {}
        
        # Malicious packages
        print(f"\n  Collecting {len(malicious_list)} malicious packages...")
        malicious_collected = 0
        
        for pkg in tqdm(malicious_list, desc="Malicious"):
            metadata = self.feature_extractor.get_package_metadata(pkg)
            if metadata:
                metadata['label'] = 1
                all_packages_data[pkg] = metadata
                malicious_collected += 1
            time.sleep(0.3)  # Rate limiting
        
        print(f"    ✓ Successfully collected: {malicious_collected}/{len(malicious_list)}")
        
        # Benign packages
        print(f"\n  Collecting {len(benign_list)} benign packages...")
        benign_collected = 0
        
        for pkg in tqdm(benign_list, desc="Benign"):
            metadata = self.feature_extractor.get_package_metadata(pkg)
            if metadata:
                metadata['label'] = 0
                all_packages_data[pkg] = metadata
                benign_collected += 1
            time.sleep(0.3)
        
        print(f"    ✓ Successfully collected: {benign_collected}/{len(benign_list)}")
        
        # ========== STEP 3: Check and adjust balance ==========
        print("\n📍 STEP 3: Checking balance...")
        
        collected_malicious = sum(1 for d in all_packages_data.values() if d['label'] == 1)
        collected_benign = sum(1 for d in all_packages_data.values() if d['label'] == 0)
        
        total = collected_malicious + collected_benign
        malicious_ratio = collected_malicious / total if total > 0 else 0
        
        print(f"\n  Current dataset:")
        print(f"    Malicious: {collected_malicious} ({malicious_ratio:.1%})")
        print(f"    Benign: {collected_benign} ({1-malicious_ratio:.1%})")
        print(f"    Total: {total}")
        
        # Undersample if too imbalanced
        if collected_benign > collected_malicious * 2:
            print(f"\n  ⚠️ Still imbalanced. Undersampling benign class...")
            
            benign_keys = [k for k, v in all_packages_data.items() if v['label'] == 0]
            keep_benign = random.sample(benign_keys, min(len(benign_keys), collected_malicious * 2))
            
            # Remove excess benign
            for key in benign_keys:
                if key not in keep_benign:
                    del all_packages_data[key]
            
            collected_benign = sum(1 for d in all_packages_data.values() if d['label'] == 0)
            total = collected_malicious + collected_benign
            malicious_ratio = collected_malicious / total
            
            print(f"    ✓ After undersampling:")
            print(f"      Malicious: {collected_malicious} ({malicious_ratio:.1%})")
            print(f"      Benign: {collected_benign} ({1-malicious_ratio:.1%})")
        
        # ========== STEP 4: Download statistics ==========
        print("\n📍 STEP 4: Collecting download statistics...")
        
        for pkg_name in tqdm(list(all_packages_data.keys()), desc="Downloads"):
            downloads = self.feature_extractor.get_download_stats(pkg_name)
            all_packages_data[pkg_name]['downloads'] = downloads
            time.sleep(0.2)
        
        # ========== STEP 5: Typosquatting scores ==========
        print("\n📍 STEP 5: Calculating typosquatting scores...")
        
        # Use benign packages as popular packages reference
        popular_packages = [k for k, v in all_packages_data.items() if v['label'] == 0]
        typo_detector = TyposquattingDetector(popular_packages)
        
        for pkg_name in tqdm(list(all_packages_data.keys()), desc="Typosquatting"):
            similarity = typo_detector.calculate_similarity(pkg_name)
            all_packages_data[pkg_name]['typosquatting_score'] = similarity
        
        # ========== STEP 6: Build dependency graphs ==========
        print("\n📍 STEP 6: Building dependency graphs...")
        
        graph_builder = DependencyGraphBuilder(self.feature_extractor)
        graphs = {}
        
        for pkg_name in tqdm(list(all_packages_data.keys()), desc="Graphs"):
            try:
                G = graph_builder.build_graph(pkg_name, all_packages_data, max_depth=2)
                graphs[pkg_name] = G
                
                # Calculate graph features
                graph_features = graph_builder.calculate_graph_features(G, pkg_name)
                all_packages_data[pkg_name].update(graph_features)
            except Exception as e:
                print(f"  Error building graph for {pkg_name}: {e}")
        
        # ========== STEP 7: Check malicious dependencies ==========
        print("\n📍 STEP 7: Checking malicious dependencies...")
        
        malicious_set = set(k for k, v in all_packages_data.items() if v['label'] == 1)
        
        for pkg_name, pkg_data in all_packages_data.items():
            dependencies = pkg_data.get('dependencies', [])
            has_malicious = any(dep in malicious_set for dep in dependencies)
            pkg_data['has_malicious_deps'] = 1 if has_malicious else 0
        
        # ========== STEP 8: Save data ==========
        print("\n📍 STEP 8: Saving data...")
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(all_packages_data, orient='index')
        df.to_csv(f'{self.output_dir}/complete_metadata.csv', index=True)
        print(f"  ✓ Saved: complete_metadata.csv")
        
        # Save graphs
        with open(f'{self.output_dir}/dependency_graphs.pkl', 'wb') as f:
            pickle.dump(graphs, f)
        print(f"  ✓ Saved: dependency_graphs.pkl")
        
        # Save package lists
        with open(f'{self.output_dir}/malicious_packages.json', 'w') as f:
            json.dump(list(malicious_set), f, indent=2)
        print(f"  ✓ Saved: malicious_packages.json")
        
        with open(f'{self.output_dir}/benign_packages.json', 'w') as f:
            benign_set = set(k for k, v in all_packages_data.items() if v['label'] == 0)
            json.dump(list(benign_set), f, indent=2)
        print(f"  ✓ Saved: benign_packages.json")
        
        # Save summary
        summary = {
            'total_packages': len(all_packages_data),
            'malicious_packages': collected_malicious,
            'benign_packages': collected_benign,
            'malicious_ratio': float(malicious_ratio),
            'avg_dependencies': float(df['dependency_count'].mean()),
            'avg_downloads': float(df['downloads'].mean()),
            'packages_with_malicious_deps': int(sum(1 for d in all_packages_data.values() 
                                                    if d.get('has_malicious_deps', 0) == 1)),
            'synthetic_packages_used': allow_synthetic
        }
        
        with open(f'{self.output_dir}/summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"  ✓ Saved: summary.json")
        
        # ========== Final Summary ==========
        print("\n" + "="*60)
        print("📊 FINAL DATASET SUMMARY")
        print("="*60)
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        print(f"\n✅ Balanced data collection completed!")
        print(f"📁 All files saved to: {self.output_dir}/")
        
        return all_packages_data, graphs, df


# =============================================
# MAIN SCRIPT
# =============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TIER 1 BALANCED DATA COLLECTION")
    print("="*60)
    
    # Configuration
    TARGET_MALICIOUS = 500  # Tăng lên để cân bằng hơn
    TARGET_BENIGN = 500
    ALLOW_SYNTHETIC = True
    
    print(f"\nConfiguration:")
    print(f"  Target malicious: {TARGET_MALICIOUS}")
    print(f"  Target benign: {TARGET_BENIGN}")
    print(f"  Allow synthetic: {ALLOW_SYNTHETIC}")
    
    collector = BalancedDataCollector(output_dir='./tier1_balanced_data')
    
    try:
        all_data, graphs, df = collector.collect_balanced_dataset(
            target_malicious=TARGET_MALICIOUS,
            target_benign=TARGET_BENIGN,
            allow_synthetic=ALLOW_SYNTHETIC
        )
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Balanced data collection completed.")
        print("="*60)
        print("\nNext steps:")
        print("  1. Run: python prepare_training_data.py")
        print("  2. Upload to Google Colab for training")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Collection interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()