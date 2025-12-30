# ========================================
# tier1_inference.py
# Hệ thống Tier 1 hoàn chỉnh - Ensemble GNN + RF
# ========================================

"""
Thư viện cần cài:
pip install torch torch-geometric networkx scikit-learn pandas numpy joblib python-Levenshtein --break-system-packages
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
import networkx as nx
import numpy as np
import pandas as pd
import joblib
import json
from typing import Dict, List, Tuple
import os

# =============================================
# PHẦN 1: ĐỊNH NGHĨA MÔ HÌNH
# =============================================

class PackageGNN(nn.Module):
    """GNN Model (phải giống với training)"""
    def __init__(self, 
                 graph_feature_dim=4,
                 metadata_feature_dim=15,
                 hidden_dim=64,
                 num_gnn_layers=3,
                 dropout=0.3):
        super(PackageGNN, self).__init__()
        
        input_dim = graph_feature_dim + metadata_feature_dim
        
        self.convs = nn.ModuleList()
        self.convs.append(GCNConv(input_dim, hidden_dim))
        for _ in range(num_gnn_layers - 1):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
        
        self.batch_norms = nn.ModuleList([
            nn.BatchNorm1d(hidden_dim) for _ in range(num_gnn_layers)
        ])
        
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.dropout = dropout
    
    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            x = self.batch_norms[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = global_mean_pool(x, batch)
        risk_score = self.mlp(x)
        
        return risk_score.squeeze(-1)


# =============================================
# PHẦN 2: FEATURE EXTRACTOR
# =============================================

class FeatureExtractor:
    """Trích xuất features từ package info"""
    
    def __init__(self):
        self.popular_packages = set()
    
    def extract_graph_features(self, G: nx.DiGraph, node_id: str) -> np.ndarray:
        """Trích xuất 4 graph structure features"""
        features = []
        
        # In-degree
        in_degree = G.in_degree(node_id) if node_id in G else 0
        features.append(in_degree)
        
        # Out-degree
        out_degree = G.out_degree(node_id) if node_id in G else 0
        features.append(out_degree)
        
        # Clustering coefficient
        try:
            clustering = nx.clustering(G.to_undirected(), node_id) if node_id in G else 0
        except:
            clustering = 0
        features.append(clustering)
        
        # PageRank
        try:
            pagerank = nx.pagerank(G, max_iter=100)[node_id] if node_id in G else 0
        except:
            pagerank = 0
        features.append(pagerank)
        
        return np.array(features, dtype=np.float32)
    
    def extract_metadata_features(self, package_info: Dict) -> np.ndarray:
        """Trích xuất 15 metadata features"""
        features = []
        
        # Package metadata (8 features)
        downloads = package_info.get('downloads', 0)
        features.append(np.log1p(downloads))
        
        name = package_info.get('name', '')
        features.append(len(name))
        
        description = package_info.get('description', '')
        features.append(1 if description else 0)
        features.append(len(description))
        
        features.append(1 if package_info.get('homepage') else 0)
        features.append(1 if package_info.get('repository') else 0)
        features.append(len(package_info.get('versions', [])))
        
        age = package_info.get('age_days', 0)
        features.append(age)
        
        # Author info (3 features)
        author = package_info.get('author', '')
        features.append(1 if author else 0)
        features.append(len(author))
        
        is_team = 1 if package_info.get('is_organization', False) else 0
        features.append(is_team)
        
        # Dependencies info (3 features)
        dependencies = package_info.get('dependencies', [])
        features.append(len(dependencies))
        features.append(1 if dependencies else 0)
        
        has_malicious = package_info.get('has_malicious_deps', False)
        features.append(1 if has_malicious else 0)
        
        # Typosquatting (1 feature)
        similarity_score = package_info.get('typosquatting_score', 0.0)
        features.append(similarity_score)
        
        return np.array(features, dtype=np.float32)
    
    def extract_all_features(self, G: nx.DiGraph, node_id: str, 
                            package_info: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        Trích xuất cả graph features và metadata features
        Returns: (graph_features, metadata_features)
        """
        graph_features = self.extract_graph_features(G, node_id)
        metadata_features = self.extract_metadata_features(package_info)
        
        return graph_features, metadata_features


# =============================================
# PHẦN 3: TIER 1 ENSEMBLE SYSTEM
# =============================================

class Tier1Ensemble:
    """
    Hệ thống Tier 1 hoàn chỉnh
    Ensemble GNN + Random Forest
    """
    
    def __init__(self, 
                 gnn_model_path: str,
                 rf_model_path: str,
                 gnn_weight: float = 0.6,
                 rf_weight: float = 0.4,
                 tier2_threshold: float = 50.0,
                 device: str = 'cpu'):
        """
        Args:
            gnn_model_path: Path đến gnn_model_final.pt
            rf_model_path: Path đến rf_model_final.pkl
            gnn_weight: Trọng số cho GNN (default 0.6)
            rf_weight: Trọng số cho RF (default 0.4)
            tier2_threshold: Ngưỡng để pass sang Tier 2 (default 50.0)
            device: 'cuda' hoặc 'cpu'
        """
        
        self.device = torch.device(device)
        self.gnn_weight = gnn_weight
        self.rf_weight = rf_weight
        self.tier2_threshold = tier2_threshold
        
        # Load GNN model
        print("Loading GNN model...")
        gnn_checkpoint = torch.load(gnn_model_path, map_location=self.device, weights_only=False)
        
        # Get hyperparameters
        gnn_params = gnn_checkpoint.get('hyperparameters', {})
        self.gnn_model = PackageGNN(
            graph_feature_dim=gnn_params.get('graph_feature_dim', 4),
            metadata_feature_dim=gnn_params.get('metadata_feature_dim', 15),
            hidden_dim=gnn_params.get('hidden_dim', 64),
            num_gnn_layers=gnn_params.get('num_gnn_layers', 3),
            dropout=gnn_params.get('dropout', 0.3)
        ).to(self.device)
        
        self.gnn_model.load_state_dict(gnn_checkpoint['model_state_dict'])
        self.gnn_model.eval()
        
        # Get optimal threshold for GNN (if available)
        self.gnn_threshold = gnn_checkpoint.get('optimal_threshold', 0.5)
        
        print(f"✓ GNN model loaded (threshold: {self.gnn_threshold:.4f})")
        
        # Load Random Forest model
        print("Loading Random Forest model...")
        rf_data = joblib.load(rf_model_path)
        self.rf_model = rf_data['model']
        self.rf_scaler = rf_data['scaler']
        
        # Get optimal threshold for RF (if available)
        self.rf_threshold = rf_data.get('optimal_threshold', 0.5)
        
        print(f"✓ Random Forest model loaded (threshold: {self.rf_threshold:.4f})")
        
        # Feature extractor
        self.feature_extractor = FeatureExtractor()
        
        print(f"\n✅ Tier 1 Ensemble System initialized!")
        print(f"   GNN weight: {gnn_weight}")
        print(f"   RF weight: {rf_weight}")
        print(f"   Tier 2 threshold: {tier2_threshold}")
    
    def prepare_graph_data(self, G: nx.DiGraph, target_node: str,
                          package_info_dict: Dict) -> Data:
        """
        Chuẩn bị graph data cho GNN
        """
        # Get subgraph (k-hop neighborhood)
        k = 2
        subgraph_nodes = set([target_node])
        
        for _ in range(k):
            new_nodes = set()
            for node in subgraph_nodes:
                if node in G:
                    new_nodes.update(G.predecessors(node))
                    new_nodes.update(G.successors(node))
            subgraph_nodes.update(new_nodes)
        
        subgraph = G.subgraph(subgraph_nodes).copy()
        
        if target_node not in subgraph:
            subgraph.add_node(target_node)
        
        # Create node mapping
        nodes = list(subgraph.nodes())
        node_to_idx = {node: idx for idx, node in enumerate(nodes)}
        target_idx = node_to_idx[target_node]
        
        # Extract features for all nodes
        node_features = []
        for node in nodes:
            pkg_info = package_info_dict.get(node, {})
            graph_feat, metadata_feat = self.feature_extractor.extract_all_features(
                G, node, pkg_info
            )
            combined_feat = np.concatenate([graph_feat, metadata_feat])
            node_features.append(combined_feat)
        
        x = torch.tensor(np.array(node_features), dtype=torch.float32)
        
        # Create edge index
        edge_list = list(subgraph.edges())
        if len(edge_list) == 0:
            edge_index = torch.zeros((2, 0), dtype=torch.long)
        else:
            edge_index = torch.tensor([
                [node_to_idx[src] for src, _ in edge_list],
                [node_to_idx[dst] for _, dst in edge_list]
            ], dtype=torch.long)
        
        # Create batch (single graph)
        batch = torch.zeros(x.shape[0], dtype=torch.long)
        
        # Create PyG Data object
        data = Data(x=x, edge_index=edge_index, batch=batch)
        data.target_idx = target_idx
        
        return data
    
    def predict_single(self, 
                      dependency_graph: nx.DiGraph,
                      target_package: str,
                      package_info: Dict,
                      package_info_dict: Dict = None) -> Dict:
        """
        Predict cho một package
        
        Args:
            dependency_graph: Dependency graph chứa target package
            target_package: Tên package cần phân tích
            package_info: Thông tin của target package
            package_info_dict: Dict chứa info của tất cả packages trong graph
        
        Returns:
            Dict chứa kết quả phân tích
        """
        
        if package_info_dict is None:
            package_info_dict = {target_package: package_info}
        
        # ========== GNN Prediction ==========
        graph_data = self.prepare_graph_data(
            dependency_graph, 
            target_package, 
            package_info_dict
        )
        graph_data = graph_data.to(self.device)
        
        with torch.no_grad():
            gnn_score = self.gnn_model(graph_data).item()
        
        # ========== Random Forest Prediction ==========
        _, metadata_features = self.feature_extractor.extract_all_features(
            dependency_graph, target_package, package_info
        )
        
        # Scale features
        metadata_scaled = self.rf_scaler.transform(
            metadata_features.reshape(1, -1)
        )
        
        # Predict
        rf_score = self.rf_model.predict_proba(metadata_scaled)[0, 1]
        
        # ========== Ensemble ==========
        # Convert to 0-100 scale
        gnn_score_scaled = gnn_score * 100
        rf_score_scaled = rf_score * 100
        
        # Weighted average
        final_score = (self.gnn_weight * gnn_score_scaled + 
                      self.rf_weight * rf_score_scaled)
        
        # ========== Decision ==========
        is_suspicious = final_score > self.tier2_threshold
        
        # Classification using individual thresholds
        gnn_pred = 1 if gnn_score >= self.gnn_threshold else 0
        rf_pred = 1 if rf_score >= self.rf_threshold else 0
        
        # Ensemble classification (majority vote or threshold)
        ensemble_pred = 1 if is_suspicious else 0
        
        result = {
            'package_name': target_package,
            'gnn_score': float(gnn_score_scaled),
            'rf_score': float(rf_score_scaled),
            'final_score': float(final_score),
            'gnn_prediction': int(gnn_pred),
            'rf_prediction': int(rf_pred),
            'ensemble_prediction': int(ensemble_pred),
            'decision': 'SUSPICIOUS' if is_suspicious else 'BENIGN',
            'pass_to_tier2': bool(is_suspicious),
            'confidence': abs(final_score - self.tier2_threshold)  # Distance from threshold
        }
        
        return result
    
    def predict_batch(self, 
                     package_list: List[Tuple[str, Dict]],
                     dependency_graph: nx.DiGraph,
                     package_info_dict: Dict) -> List[Dict]:
        """
        Predict cho nhiều packages
        
        Args:
            package_list: List of (package_name, package_info)
            dependency_graph: Dependency graph
            package_info_dict: Dict chứa info của tất cả packages
        
        Returns:
            List of prediction results
        """
        results = []
        
        print(f"\nAnalyzing {len(package_list)} packages...")
        
        from tqdm import tqdm
        for package_name, package_info in tqdm(package_list, desc="Tier 1 Analysis"):
            try:
                result = self.predict_single(
                    dependency_graph,
                    package_name,
                    package_info,
                    package_info_dict
                )
                results.append(result)
            except Exception as e:
                print(f"\n⚠️ Error analyzing {package_name}: {e}")
                results.append({
                    'package_name': package_name,
                    'error': str(e),
                    'decision': 'ERROR'
                })
        
        return results
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        """Tính thống kê từ results"""
        suspicious = [r for r in results if r.get('decision') == 'SUSPICIOUS']
        benign = [r for r in results if r.get('decision') == 'BENIGN']
        errors = [r for r in results if r.get('decision') == 'ERROR']
        
        stats = {
            'total_analyzed': len(results),
            'suspicious_count': len(suspicious),
            'benign_count': len(benign),
            'error_count': len(errors),
            'suspicious_rate': len(suspicious) / len(results) if results else 0,
            'pass_to_tier2_count': sum(1 for r in results if r.get('pass_to_tier2', False)),
            'avg_score_suspicious': np.mean([r['final_score'] for r in suspicious]) if suspicious else 0,
            'avg_score_benign': np.mean([r['final_score'] for r in benign]) if benign else 0,
            'avg_confidence_suspicious': np.mean([r['confidence'] for r in suspicious]) if suspicious else 0,
            'avg_confidence_benign': np.mean([r['confidence'] for r in benign]) if benign else 0
        }
        
        return stats
    
    def save_results(self, results: List[Dict], filepath: str):
        """Lưu results ra file JSON"""
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✓ Results saved to: {filepath}")
    
    def print_summary(self, results: List[Dict]):
        """In summary của results"""
        stats = self.get_statistics(results)
        
        print("\n" + "="*60)
        print("TIER 1 ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total packages analyzed: {stats['total_analyzed']}")
        print(f"Suspicious (pass to Tier 2): {stats['suspicious_count']} ({stats['suspicious_rate']:.1%})")
        print(f"Benign: {stats['benign_count']}")
        print(f"Errors: {stats['error_count']}")
        print(f"\nAverage scores:")
        print(f"  Suspicious packages: {stats['avg_score_suspicious']:.2f}")
        print(f"  Benign packages: {stats['avg_score_benign']:.2f}")
        print(f"\nAverage confidence:")
        print(f"  Suspicious packages: {stats['avg_confidence_suspicious']:.2f}")
        print(f"  Benign packages: {stats['avg_confidence_benign']:.2f}")
        print("="*60)


# =============================================
# PHẦN 4: EXAMPLE USAGE
# =============================================

def example_usage():
    """
    Ví dụ cách sử dụng Tier 1 System
    """
    
    print("\n" + "="*60)
    print("TIER 1 ENSEMBLE SYSTEM - EXAMPLE")
    print("="*60)
    
    # Initialize Tier 1 system
    tier1 = Tier1Ensemble(
        gnn_model_path='D:/NT521\DOAN\GNN_TIER1/gnn_model_final.pt',
        rf_model_path='D:/NT521\DOAN\RF_TIER1/rf_model_final.pkl',
        gnn_weight=0.6,
        rf_weight=0.4,
        tier2_threshold=50.0,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    # Example: Create dummy dependency graph
    G = nx.DiGraph()
    G.add_edge('suspicious-package', 'dependency-1')
    G.add_edge('suspicious-package', 'dependency-2')
    G.add_edge('dependency-1', 'numpy')
    
    # Example: Package info
    package_info_dict = {
        'suspicious-package': {
            'name': 'suspicious-package',
            'downloads': 50,
            'description': '',
            'homepage': None,
            'repository': None,
            'versions': ['0.0.1'],
            'age_days': 3,
            'author': '',
            'is_organization': False,
            'dependencies': ['dependency-1', 'dependency-2'],
            'has_malicious_deps': False,
            'typosquatting_score': 0.85
        },
        'dependency-1': {
            'name': 'dependency-1',
            'downloads': 1000,
            'description': 'Some lib',
            'homepage': 'https://example.com',
            'repository': 'https://github.com/example',
            'versions': ['1.0.0', '1.0.1'],
            'age_days': 365,
            'author': 'Author Name',
            'is_organization': False,
            'dependencies': ['numpy'],
            'has_malicious_deps': False,
            'typosquatting_score': 0.0
        }
    }
    
    # Analyze single package
    result = tier1.predict_single(
        dependency_graph=G,
        target_package='suspicious-package',
        package_info=package_info_dict['suspicious-package'],
        package_info_dict=package_info_dict
    )
    
    print("\n" + "="*60)
    print(f"ANALYSIS RESULT: {result['package_name']}")
    print("="*60)
    print(f"GNN Score: {result['gnn_score']:.2f}/100")
    print(f"RF Score: {result['rf_score']:.2f}/100")
    print(f"Final Score: {result['final_score']:.2f}/100")
    print(f"Decision: {result['decision']}")
    print(f"Pass to Tier 2: {result['pass_to_tier2']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print("="*60)
    
    # Analyze batch
    package_list = [
        ('suspicious-package', package_info_dict['suspicious-package']),
        ('dependency-1', package_info_dict['dependency-1'])
    ]
    
    results = tier1.predict_batch(package_list, G, package_info_dict)
    
    # Print summary
    tier1.print_summary(results)
    
    # Save results
    tier1.save_results(results, 'tier1_results.json')


# =============================================
# MAIN
# =============================================

if __name__ == '__main__':
    # Chạy example
    example_usage()