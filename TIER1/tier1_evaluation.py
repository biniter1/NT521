# ========================================
# tier1_evaluation.py
# Đánh giá performance của Tier 1 system
# ========================================

"""
Đánh giá Tier 1 trên test set
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                            f1_score, roc_auc_score, confusion_matrix,
                            classification_report, roc_curve)
from tier1_inference import Tier1Ensemble
import networkx as nx
import pickle
import json

def evaluate_tier1_system(test_data_path: str = './tier1_training_data'):
    """
    Đánh giá Tier 1 system trên test set
    """
    
    print("\n" + "="*60)
    print("TIER 1 SYSTEM EVALUATION")
    print("="*60)
    
    # Load test data
    print("\nLoading test data...")
    
    # Load labels
    y = np.load(f'{test_data_path}/y_labels.npy')
    
    # Load metadata
    X_metadata = np.load(f'{test_data_path}/X_metadata.npy')
    
    # Load graphs
    with open(f'{test_data_path}/graph_data_list.pkl', 'rb') as f:
        graph_data_list = pickle.load(f)
    
    # Load split indices
    with open(f'{test_data_path}/split_indices.json', 'r') as f:
        split_indices = json.load(f)
    
    test_idx = split_indices['test_idx']
    
    # Load package names
    with open(f'{test_data_path}/package_names.json', 'r') as f:
        package_names = json.load(f)
    
    print(f"✓ Loaded {len(test_idx)} test samples")
    
    # Initialize Tier 1
    tier1 = Tier1Ensemble(
        gnn_model_path='gnn_model_final.pt',
        rf_model_path='rf_model_final.pkl',
        gnn_weight=0.6,
        rf_weight=0.4,
        tier2_threshold=50.0,
        device='cpu'
    )
    
    # Prepare data for inference
    # (Simplified - bạn cần adapt cho data thật của bạn)
    print("\nRunning Tier 1 inference on test set...")
    
    predictions = []
    true_labels = []
    scores = []
    
    # Giả sử bạn có cách tạo dependency graph và package info
    # Đây là phần bạn cần customize based on your data format
    
    for idx in test_idx:
        # Get true label
        true_label = y[idx]
        true_labels.append(true_label)
        
        # TODO: Create proper dependency graph and package info
        # This is placeholder
        dummy_graph = nx.DiGraph()
        dummy_graph.add_node(package_names[idx])
        
        dummy_info = {
            'name': package_names[idx],
            'downloads': 0,
            'description': '',
            # ... fill other fields from X_metadata[idx]
        }
        
        # Skip for now - just placeholder
        # result = tier1.predict_single(dummy_graph, package_names[idx], dummy_info)
        # predictions.append(result['ensemble_prediction'])
        # scores.append(result['final_score'])
    
    # Calculate metrics
    # (Uncomment when you have real predictions)
    """
    predictions = np.array(predictions)
    scores = np.array(scores) / 100  # Scale back to 0-1
    true_labels = np.array(true_labels)
    
    accuracy = accuracy_score(true_labels, predictions)
    precision = precision_score(true_labels, predictions, zero_division=0)
    recall = recall_score(true_labels, predictions, zero_division=0)
    f1 = f1_score(true_labels, predictions, zero_division=0)
    roc_auc = roc_auc_score(true_labels, scores)
    
    print("\n" + "="*60)
    print("TIER 1 ENSEMBLE RESULTS")
    print("="*60)
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print("="*60)
    
    # Confusion matrix
    cm = confusion_matrix(true_labels, predictions)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Benign', 'Malicious'],
                yticklabels=['Benign', 'Malicious'])
    plt.title('Tier 1 Ensemble - Confusion Matrix', fontsize=14, fontweight='bold')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('tier1_confusion_matrix.png', dpi=300)
    plt.show()
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(true_labels, predictions, 
                              target_names=['Benign', 'Malicious']))
    """
    
    print("\n✅ Evaluation placeholder completed!")
    print("⚠️ You need to customize this for your actual data format")

if __name__ == '__main__':
    evaluate_tier1_system()