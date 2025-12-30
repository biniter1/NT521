# Universal Test Dataset

Created: 2025-12-05 22:14:11

## Statistics
- Total packages: 46
- Benign: 21
- Malicious: 25

## Structure
```
universal_test_dataset/
├── packages/
│   ├── benign/
│   │   └── ben-XXX/
│   │       ├── source/              # Python source code
│   │       ├── metadata.json        # Full metadata
│   │       ├── dependencies.json    # Dependency info
│   │       └── sast_report.json     # SAST results
│   └── malicious/
│       └── mal-XXX/
│           └── (same structure)
├── ground_truth.json                # Ground truth labels
└── README.md                        # This file
```

## Usage

### For MalOSS
```python
# MalOSS can use:
# - metadata.json (PyPI metadata + typosquatting score)
# - sast_report.json (Static analysis results)
# - dependencies.json (Dependency info)
```

### For 2-Tier System
```python
# 2-Tier can use:
# - source/ (Code for feature extraction)
# - metadata.json (For dependency graph)
# - dependencies.json (For Tier 1 GNN)
```

## Ground Truth Format
```json
{
  "packages": [
    {
      "package_name": "ben-001",
      "malicious": false,
      "source_lines": 1234,
      "sast_issues": 5,
      "dependencies_count": 3
    }
  ]
}
```
