# Unified Malicious Code Detection Pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive multi-tier system for detecting malicious Python packages using machine learning and static analysis techniques. The system employs a two-tier architecture combining graph neural networks, ensemble methods, and advanced static analysis components.

## 🏗️ Architecture Overview

The detection pipeline consists of two main tiers:

### TIER 1: Fast Graph-Based Screening
- **GNN (Graph Neural Network)**: Analyzes dependency graph structures and package metadata
- **Random Forest**: Processes metadata features for complementary analysis
- **Ensemble**: Weighted combination of GNN and RF predictions
- **Threshold**: Packages scoring > 90 pass to Tier 2

### TIER 2: Deep Static Analysis
Four specialized components for thorough malware detection:

#### Component A: Enhanced Static Analysis
- AST (Abstract Syntax Tree) parsing
- API detection for dangerous functions
- Type inference analysis
- Dataflow analysis
- **Output**: 25+ static features

#### Component B: Obfuscation & Evasion Detector
- String entropy analysis
- Encoding detection (base64/hex)
- Multi-stage payload detection
- Logic bomb detection
- **Output**: 15+ obfuscation features

#### Component C: Behavioral Pattern Analyzer
- API call sequence analysis
- Temporal pattern recognition
- Known attack signature detection
- **Output**: 10+ behavioral features

#### Component D: ML Classifier
- Ensemble of Random Forest + Neural Network
- Input: 50+ combined features from A+B+C
- **Output**: Confidence score (0-100)

## 📊 Performance Metrics

Based on benchmark results:
- **Accuracy**: 95.2%
- **Precision**: 93.8%
- **Recall**: 91.4%
- **F1-Score**: 92.6%
- **Tier 1 Processing**: ~0.15s per package
- **Tier 2 Processing**: ~0.45s per package

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PyTorch 2.0+
- CUDA-compatible GPU (recommended)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd malicious-detection-pipeline
```

2. **Install dependencies**
```bash
pip install torch torch-geometric networkx scikit-learn pandas numpy joblib python-Levenshtein
```

3. **Download pre-trained models**
```bash
# Models are included in the repository
# TIER1: Model_TIER1/GNN_TIER1/gnn_model_final.pt
# TIER1: Model_TIER1/RF_TIER1/rf_model_final.pkl
# TIER2: TIER2/models/component_d_*.pkl
```

### Basic Usage

```python
from unified_pipeline import UnifiedDetector

# Initialize detector
detector = UnifiedDetector(
    tier1_gnn_path='Model_TIER1/GNN_TIER1/gnn_model_final.pt',
    tier1_rf_path='Model_TIER1/RF_TIER1/rf_model_final.pkl',
    tier2_models_dir='TIER2/models',
    tier2_components_dir='TIER2/components',
    tier1_threshold=90.0
)

# Analyze a package
result = detector.analyze_package(
    code=python_source_code,
    package_name='suspicious-package',
    G=dependency_graph,  # NetworkX DiGraph
    node_info=package_metadata,
    all_nodes_info=all_packages_metadata
)

print(f"Verdict: {result['verdict']}")
print(f"Confidence: {result['confidence']}")
print(f"Processing Time: {result['processing_time']:.3f}s")
```

## 📁 Project Structure

```
├── TIER1/                          # Tier 1: GNN + RF Ensemble
│   ├── data/                       # Data collection and training scripts
│   ├── models/                     # Pre-trained GNN and RF models
│   ├── tier1_inference.py          # Main inference engine
│   ├── tier1_evaluation.py         # Evaluation and metrics
│   ├── tier1_demo.py              # Demo scripts
│   ├── optimize.py                 # Hyperparameter optimization
│   └── tier1_config.json           # Configuration file
├── TIER2/                          # Tier 2: Advanced Static Analysis
│   ├── components/                 # Analysis components (A, B, C, D)
│   │   ├── component_a_static.py   # Static analysis
│   │   ├── component_b_obfuscation.py  # Obfuscation detection
│   │   ├── component_c_behavioral.py   # Behavioral analysis
│   │   └── component_d_classifier.py   # ML classifier
│   ├── data_collection/            # Data collection scripts
│   ├── models/                     # Trained ML models
│   ├── rules/                      # Detection rules and signatures
│   ├── utils/                      # Utility functions
│   └── README.md                   # Tier 2 documentation
├── unified_pipeline.py             # Main unified pipeline
├── run_benchmark.py               # Benchmarking script
├── unified_test_dataset/          # Test dataset
├── trash/                         # Development and debug scripts
├── Model_TIER1/                   # Additional model storage
└── README.md                      # This file
```

## 🔧 Configuration

### TIER1 Configuration
Edit `TIER1/tier1_config.json`:
```json
{
  "gnn_weight": 0.6,
  "rf_weight": 0.4,
  "tier2_threshold": 90.0,
  "device": "cuda"
}
```

### TIER2 Rules
Detection rules are stored in `TIER2/rules/`:
- `static_analysis_rules.json`
- `obfuscation_rules.json`
- `behavioral_rules.json`

## 🧪 Testing and Benchmarking

### Run Benchmark
```bash
python run_benchmark.py
```

### Run Universal Benchmark
```bash
python run_benchmark_universal.py
```

### Custom Testing
```python
# Load test dataset
from unified_pipeline import UnifiedDetector

detector = UnifiedDetector(...)
packages, G = load_unified_dataset('unified_test_dataset')

# Run analysis
results = []
for pkg in packages:
    result = detector.analyze_package(...)
    results.append(result)

# Print statistics
detector.print_statistics()
```

## 📈 Model Training

### TIER1 Training
1. **Data Collection**: Run `TIER1/data/data_collection.py`
2. **Feature Extraction**: Use `TIER1/data/data_training.py`
3. **GNN Training**: Custom training script (not included)
4. **RF Training**: Custom training script (not included)

### TIER2 Training
1. **Data Collection**: Scripts in `TIER2/data_collection/`
2. **Feature Generation**: `TIER2/components/tier2_data_generator.py`
3. **Model Training**: `TIER2/components/training_csv.py`

## 🔍 Components Details

### TIER1 Components

#### GNN Model
- **Architecture**: 3-layer GCN with MLP classifier
- **Input**: Graph structure (4 features) + metadata (15 features)
- **Features**:
  - Graph: in-degree, out-degree, clustering coefficient, PageRank
  - Metadata: downloads, description length, repository info, dependencies

#### Random Forest Model
- **Features**: 15 metadata features
- **Hyperparameters**: Tuned via `optimize.py`

### TIER2 Components

#### Component A: Static Analysis
- AST parsing for code structure
- Dangerous API detection
- Type inference and dataflow analysis

#### Component B: Obfuscation Detection
- Entropy analysis for obfuscated strings
- Encoding pattern recognition
- Multi-stage payload detection

#### Component C: Behavioral Analysis
- API call sequence modeling
- Temporal pattern analysis
- Signature-based detection

#### Component D: ML Classifier
- Random Forest + Neural Network ensemble
- Feature scaling and normalization
- Probability calibration

## 📊 Data Collection

### Malicious Samples
- `TIER2/data_collection/download_malicious.py`
- Sources: Advisory databases, malware repositories
- Categories: Backdoors, trojans, ransomware, etc.

### Benign Samples
- `download_real_bengin.py`
- Sources: PyPI popular packages
- Filtering: High-download, well-maintained packages

### Dataset Merging
- `TIER2/data_collection/merge_dataset.py`
- Balancing classes and feature engineering

## 🛠️ Development

### Adding New Features
1. Extend feature extractors in respective components
2. Update model training pipelines
3. Retrain and validate models
4. Update benchmark datasets

### Debugging
- Use scripts in `trash/` for debugging
- `trash/debug_tier2_models.py`
- `trash/debug_components.py`
- `trash/check_feature_names.py`

### Optimization
- Run `TIER1/optimize.py` for hyperparameter tuning
- Profile performance bottlenecks
- Optimize model architectures

## 📋 Requirements

### Core Dependencies
```
torch>=2.0.0
torch-geometric>=2.3.0
networkx>=3.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
python-Levenshtein>=0.21.0
```

### Optional Dependencies
```
tqdm>=4.65.0        # Progress bars
matplotlib>=3.7.0   # Visualization
seaborn>=0.12.0     # Advanced plotting
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- PyTorch Geometric team for GNN implementation
- Scikit-learn contributors
- Open source security research community
- Python Package Index (PyPI) for benign samples

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Check existing documentation
- Review benchmark results and examples

## 🔄 Version History

- **v1.0.0**: Initial release with TIER1 and TIER2
- **v1.1.0**: Added universal benchmark suite
- **v1.2.0**: Improved feature extraction and model accuracy

---

**Note**: This system is designed for research and security analysis purposes. Always verify results with multiple tools and human expertise for critical security decisions.
