# ========================================
# prepare_training_data.py
# Chuẩn bị data cho GNN và Random Forest
# ========================================

"""
Thư viện cần cài:
pip install pandas numpy networkx torch torch-geometric scikit-learn --break-system-packages
"""

import pandas as pd
import numpy as np
import pickle
import networkx as nx
import torch
from torch_geometric.data import Data
from sklearn.model_selection import train_test_split
import json

class TrainingDataPreparator:
    """Chuẩn bị data cho training"""
    
    def __init__(self, data_dir='./tier1_data'):
        self.data_dir = data_dir
        
        # Load data
        print("Loading collected data...")
        self.df = pd.read_csv(f'{data_dir}/complete_metadata.csv', index_col=0)
        
        with open(f'{data_dir}/dependency_graphs.pkl', 'rb') as f:
            self.graphs = pickle.load(f)
        
        print(f"✓ Loaded {len(self.df)} packages")
        print(f"✓ Loaded {len(self.graphs)} graphs")
    
    def prepare_metadata_features(self) -> np.ndarray:
        """
        Chuẩn bị 15 metadata features cho Random Forest
        """
        print("\nPreparing metadata features (15 dims)...")
        
        feature_columns = [
            'downloads', 'name_length', 'has_description', 'description_length',
            'has_homepage', 'has_repository', 'version_count', 'age_days',
            'has_author', 'author_name_length', 'is_team',
            'dependency_count', 'has_dependencies', 'has_malicious_deps',
            'typosquatting_score'
        ]
        
        # Fill missing values
        for col in feature_columns:
            if col not in self.df.columns:
                self.df[col] = 0
            self.df[col] = self.df[col].fillna(0)
        
        X_metadata = self.df[feature_columns].values.astype(np.float32)
        
        print(f"✓ Metadata features shape: {X_metadata.shape}")
        
        return X_metadata
    
    def prepare_graph_data(self) -> list:
        """
        Chuẩn bị graph data cho GNN
        """
        print("\nPreparing graph data for GNN...")
        
        # 4 graph structure features
        graph_feature_columns = ['in_degree', 'out_degree', 'clustering', 'pagerank']
        
        # 15 metadata features
        metadata_columns = [
            'downloads', 'name_length', 'has_description', 'description_length',
            'has_homepage', 'has_repository', 'version_count', 'age_days',
            'has_author', 'author_name_length', 'is_team',
            'dependency_count', 'has_dependencies', 'has_malicious_deps',
            'typosquatting_score'
        ]
        
        pyg_data_list = []
        
        for pkg_name, row in self.df.iterrows():
            if pkg_name not in self.graphs:
                continue
            
            G = self.graphs[pkg_name]
            
            if len(G.nodes()) == 0:
                continue
            
            # Convert to PyG Data
            pyg_data = self._networkx_to_pyg(
                G, pkg_name, row, 
                graph_feature_columns, 
                metadata_columns
            )
            
            if pyg_data is not None:
                pyg_data_list.append(pyg_data)
        
        print(f"✓ Created {len(pyg_data_list)} PyG Data objects")
        
        return pyg_data_list
    
    def _networkx_to_pyg(self, G: nx.DiGraph, target_node: str, 
                        row: pd.Series, graph_cols: list, 
                        metadata_cols: list) -> Data:
        """Convert NetworkX graph to PyTorch Geometric Data"""
        
        try:
            # Node mapping
            nodes = list(G.nodes())
            node_to_idx = {node: idx for idx, node in enumerate(nodes)}
            
            if target_node not in node_to_idx:
                return None
            
            # Node features (19 dims = 4 graph + 15 metadata)
            node_features = []
            
            for node in nodes:
                # Get graph features for this node
                if node == target_node:
                    graph_feat = row[graph_cols].values.astype(np.float32)
                else:
                    # For non-target nodes, use default values
                    graph_feat = np.zeros(4, dtype=np.float32)
                
                # Get metadata features
                if node in self.df.index:
                    metadata_feat = self.df.loc[node, metadata_cols].values.astype(np.float32)
                else:
                    metadata_feat = np.zeros(15, dtype=np.float32)
                
                # Combine
                combined = np.concatenate([graph_feat, metadata_feat])
                node_features.append(combined)
            
            x = torch.tensor(np.array(node_features), dtype=torch.float32)
            
            # Edge index
            edge_list = list(G.edges())
            if len(edge_list) == 0:
                edge_index = torch.zeros((2, 0), dtype=torch.long)
            else:
                edge_index = torch.tensor([
                    [node_to_idx[src] for src, _ in edge_list],
                    [node_to_idx[dst] for _, dst in edge_list]
                ], dtype=torch.long)
            
            # Label
            label = torch.tensor([row['label']], dtype=torch.float32)
            
            # Create PyG Data
            data = Data(x=x, edge_index=edge_index, y=label)
            data.target_idx = node_to_idx[target_node]
            data.package_name = target_node
            
            return data
            
        except Exception as e:
            print(f"Error converting {target_node}: {e}")
            return None
    
    def split_data(self, test_size=0.2, val_size=0.1, random_state=42):
        """
        Split data thành train/val/test
        """
        print("\nSplitting data...")
        
        labels = self.df['label'].values
        indices = np.arange(len(labels))
        
        # Train + Val vs Test
        train_val_idx, test_idx = train_test_split(
            indices, 
            test_size=test_size, 
            stratify=labels,
            random_state=random_state
        )
        
        # Train vs Val
        train_labels = labels[train_val_idx]
        train_idx, val_idx = train_test_split(
            train_val_idx,
            test_size=val_size / (1 - test_size),
            stratify=train_labels,
            random_state=random_state
        )
        
        split_info = {
            'train_idx': train_idx.tolist(),
            'val_idx': val_idx.tolist(),
            'test_idx': test_idx.tolist(),
            'train_size': len(train_idx),
            'val_size': len(val_idx),
            'test_size': len(test_idx)
        }
        
        print(f"  Train: {len(train_idx)} samples")
        print(f"  Val:   {len(val_idx)} samples")
        print(f"  Test:  {len(test_idx)} samples")
        
        return split_info
    
    def save_prepared_data(self, output_dir='./tier1_training_data'):
        """
        Lưu data đã chuẩn bị
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "="*60)
        print("SAVING PREPARED DATA")
        print("="*60)
        
        # 1. Metadata features for RF
        X_metadata = self.prepare_metadata_features()
        y = self.df['label'].values
        
        np.save(f'{output_dir}/X_metadata.npy', X_metadata)
        np.save(f'{output_dir}/y_labels.npy', y)
        print(f"✓ Saved metadata: X_metadata.npy, y_labels.npy")
        
        # 2. Graph data for GNN
        graph_data_list = self.prepare_graph_data()
        
        with open(f'{output_dir}/graph_data_list.pkl', 'wb') as f:
            pickle.dump(graph_data_list, f)
        print(f"✓ Saved graph data: graph_data_list.pkl")
        
        # 3. Split indices
        split_info = self.split_data()
        
        with open(f'{output_dir}/split_indices.json', 'w') as f:
            json.dump(split_info, f, indent=2)
        print(f"✓ Saved split indices: split_indices.json")
        
        # 4. Package names
        package_names = self.df.index.tolist()
        with open(f'{output_dir}/package_names.json', 'w') as f:
            json.dump(package_names, f, indent=2)
        print(f"✓ Saved package names: package_names.json")
        
        print(f"\n✅ All training data prepared and saved to: {output_dir}/")
        
        return {
            'X_metadata': X_metadata,
            'y': y,
            'graph_data': graph_data_list,
            'split_info': split_info
        }


if __name__ == '__main__':
    print("\n" + "="*60)
    print("PREPARE TRAINING DATA")
    print("="*60)
    
    preparator = TrainingDataPreparator(data_dir='./tier1_balanced_data')
    
    result = preparator.save_prepared_data(output_dir='./tier1_training_data')
    
    print("\n✅ Data preparation completed!")
    print("\nNext steps:")
    print("  1. Upload folder 'tier1_training_data' to Google Colab")
    print("  2. Run training notebooks for GNN and Random Forest")