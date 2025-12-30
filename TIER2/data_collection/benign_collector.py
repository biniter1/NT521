"""
Benign Package Collector
Downloads TOP popular Python packages from PyPI as benign samples
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BenignPackageCollector:
    def __init__(self, output_dir: str = "real_packages_v3/benign"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata = {
            "source": "PyPI (Top Popular Packages)",
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_packages": 0,
            "packages": []
        }
        
        # Top 200 most popular PyPI packages (legitimate ones)
        self.top_packages = [
            # Data Science & ML
            "numpy", "pandas", "matplotlib", "scipy", "scikit-learn",
            "tensorflow", "torch", "keras", "seaborn", "plotly",
            "opencv-python", "pillow", "nltk", "spacy", "transformers",
            
            # Web Frameworks
            "django", "flask", "fastapi", "tornado", "bottle",
            "aiohttp", "requests", "httpx", "urllib3", "beautifulsoup4",
            
            # DevOps & Cloud
            "boto3", "azure-identity", "azure-storage-blob", 
            "google-cloud-storage", "docker", "kubernetes",
            
            # Database
            "sqlalchemy", "psycopg2-binary", "pymongo", "redis",
            "elasticsearch", "mysql-connector-python",
            
            # Testing
            "pytest", "pytest-cov", "coverage", "mock", "tox",
            "selenium", "playwright",
            
            # Async & Concurrency
            "asyncio", "celery", "dramatiq", "rq",
            
            # Utilities
            "click", "pyyaml", "toml", "python-dotenv", "configparser",
            "dateutil", "pytz", "tzdata", "six", "setuptools",
            
            # Security & Crypto
            "cryptography", "pycryptodome", "bcrypt", "passlib",
            "pyjwt", "oauthlib",
            
            # Networking
            "paramiko", "fabric", "netmiko", "scapy",
            
            # File Processing
            "openpyxl", "xlrd", "xlsxwriter", "pypdf2", "pdfplumber",
            "python-docx", "markdown", "jinja2",
            
            # API & Serialization
            "pydantic", "marshmallow", "jsonschema", "protobuf",
            "msgpack", "orjson",
            
            # Logging & Monitoring
            "loguru", "sentry-sdk", "prometheus-client",
            
            # CLI
            "typer", "rich", "colorama", "tqdm", "progressbar2",
            
            # Scraping
            "scrapy", "lxml", "html5lib", "cssselect",
            
            # Image Processing
            "imageio", "scikit-image", "pdf2image",
            
            # Additional popular packages
            "certifi", "charset-normalizer", "idna", "packaging",
            "pyparsing", "wcwidth", "typing-extensions", "zipp",
            "importlib-metadata", "attrs", "iniconfig", "pluggy",
            "tomli", "exceptiongroup", "annotated-types", "pydantic-core",
            "anyio", "sniffio", "h11", "httpcore", "certifi",
            "greenlet", "soupsieve", "distlib", "filelock",
            "platformdirs", "virtualenv", "pip", "wheel",
            "black", "flake8", "pylint", "mypy", "isort",
            "autopep8", "yapf", "pycodestyle", "pyflakes",
            "sphinx", "docutils", "alabaster", "babel",
            "imagesize", "snowballstemmer", "sphinxcontrib-*",
            "werkzeug", "itsdangerous", "markupsafe", "blinker",
            "sqlparse", "asgiref", "pyasn1", "rsa",
            "cachetools", "pyasn1-modules", "google-auth",
            "s3transfer", "jmespath", "botocore",
            "charset-normalizer", "urllib3", "requests",
            "filelock", "fsspec", "packaging",
            "networkx", "joblib", "threadpoolctl",
            "cycler", "kiwisolver", "fonttools", "contourpy",
            "pyparsing", "python-dateutil", "pytz",
            "tzdata", "numpy", "pandas", "matplotlib",
            "wcwidth", "prompt-toolkit", "pygments",
            "decorator", "ipython", "traitlets", "ptyprocess",
            "pexpect", "pickleshare", "backcall", "jedi",
            "parso", "matplotlib-inline", "stack-data",
            "asttokens", "executing", "pure-eval",
            "pyzmq", "tornado", "jupyter-core", "jupyter-client",
            "nbformat", "nbclient", "nbconvert", "mistune",
            "pandocfilters", "defusedxml", "bleach", "webencodings",
            "tinycss2", "jupyterlab-pygments", "notebook",
            "qtconsole", "ipykernel", "ipywidgets", "widgetsnbextension",
            "ipython-genutils", "send2trash", "terminado",
            "argon2-cffi", "argon2-cffi-bindings", "cffi",
            "pycparser", "soupsieve", "beautifulsoup4",
            "prometheus-client", "nest-asyncio", "debugpy",
            "comm", "psutil", "packaging"
        ]
        
        # Remove duplicates and limit to 193 packages
        self.top_packages = list(dict.fromkeys(self.top_packages))[:193]
    
    def download_package(self, package_name: str) -> bool:
        """Download a package from PyPI using pip"""
        try:
            logger.info(f"Downloading {package_name}...")
            
            # Create temp download directory
            temp_dir = Path("temp_download")
            temp_dir.mkdir(exist_ok=True)
            
            # Download package source (not wheel)
            result = subprocess.run(
                ["pip", "download", "--no-binary", ":all:", 
                 "--no-deps", "-d", str(temp_dir), package_name],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.warning(f"Could not download {package_name} (source), trying with binary...")
                
                # Clear temp dir
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(exist_ok=True)
                
                # Try downloading with binary (wheel)
                result = subprocess.run(
                    ["pip", "download", "--no-deps", "-d", str(temp_dir), package_name],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to download {package_name}")
                    return False
            
            # Find downloaded file
            downloaded_files = list(temp_dir.glob("*"))
            
            if not downloaded_files:
                logger.error(f"No files downloaded for {package_name}")
                return False
            
            # Extract the package
            package_file = downloaded_files[0]
            
            if package_file.suffix == ".whl":
                # Extract wheel file
                extract_dir = temp_dir / "extracted"
                extract_dir.mkdir(exist_ok=True)
                
                import zipfile
                with zipfile.ZipFile(package_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
            elif package_file.suffix == ".gz" or ".tar" in package_file.name:
                # Extract tar.gz file
                import tarfile
                extract_dir = temp_dir / "extracted"
                extract_dir.mkdir(exist_ok=True)
                
                with tarfile.open(package_file, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
            
            else:
                logger.warning(f"Unknown file type: {package_file}")
                return False
            
            # Find the main package directory
            extracted_items = list(extract_dir.iterdir())
            
            if not extracted_items:
                logger.error(f"No extracted content for {package_name}")
                return False
            
            # Usually the first directory is the package
            package_dir = extracted_items[0]
            
            # Copy to output directory
            dest_path = self.output_dir / package_name
            
            if dest_path.exists():
                shutil.rmtree(dest_path)
            
            shutil.copytree(package_dir, dest_path)
            
            # Count Python files
            py_files = list(dest_path.rglob("*.py"))
            
            # Save metadata
            self.metadata["packages"].append({
                "package_name": package_name,
                "py_files_count": len(py_files),
                "total_size": sum(f.stat().st_size for f in py_files if f.is_file()),
                "path": package_name
            })
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir)
            
            logger.info(f"✅ Downloaded {package_name} ({len(py_files)} .py files)")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {package_name}: {e}")
            
            # Cleanup on error
            if Path("temp_download").exists():
                shutil.rmtree("temp_download")
            
            return False
    
    def download_all(self) -> int:
        """Download all packages"""
        logger.info(f"Starting download of {len(self.top_packages)} packages...")
        
        downloaded = 0
        failed = []
        
        for i, package_name in enumerate(self.top_packages, 1):
            try:
                logger.info(f"[{i}/{len(self.top_packages)}] Processing {package_name}...")
                
                if self.download_package(package_name):
                    downloaded += 1
                else:
                    failed.append(package_name)
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Unexpected error with {package_name}: {e}")
                failed.append(package_name)
        
        self.metadata["total_packages"] = downloaded
        self.metadata["failed_packages"] = failed
        
        logger.info(f"\n✅ Successfully downloaded: {downloaded}/{len(self.top_packages)}")
        
        if failed:
            logger.warning(f"❌ Failed packages ({len(failed)}): {', '.join(failed[:10])}...")
        
        return downloaded
    
    def save_metadata(self):
        """Save collection metadata"""
        metadata_file = self.output_dir / "benign_metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_file}")
    
    def print_summary(self):
        """Print collection summary"""
        print("\n" + "=" * 60)
        print("BENIGN PACKAGE COLLECTION SUMMARY")
        print("=" * 60)
        
        total_packages = self.metadata["total_packages"]
        total_py_files = sum(p["py_files_count"] for p in self.metadata["packages"])
        
        print(f"\n📦 Total Packages: {total_packages}")
        print(f"📄 Total Python Files: {total_py_files}")
        print(f"📁 Output Directory: {self.output_dir}")
        print("=" * 60 + "\n")


def main():
    """Main execution"""
    print("=" * 60)
    print("Benign Package Collector")
    print("Downloading TOP 193 popular PyPI packages")
    print("=" * 60)
    print()
    
    collector = BenignPackageCollector()
    
    downloaded = collector.download_all()
    
    if downloaded > 0:
        collector.save_metadata()
        collector.print_summary()
        
        print("✅ Collection complete!")
        print("\nNext step: Merge with malicious packages")
    else:
        print("❌ No packages were downloaded!")
    
    return downloaded > 0


if __name__ == "__main__":
    main()