from tier1_inference import Tier1Ensemble

tier1 = Tier1Ensemble(
        gnn_model_path='gnn_model_final.pt',
        rf_model_path='f_model_final.pkl',
        gnn_weight=0.3,
        rf_weight=0.7,
        tier2_threshold=85.0
    )
# Analyze một package
result = tier1.predict_single(G, 'package-name', package_info)

# Xem kết quả
if result['pass_to_tier2']:
    print(f"⚠️ Suspicious! Pass to Tier 2 for analysis")
    print(f"Risk score: {result['final_score']:.2f}/100")
else:
    print(f"✓ Benign package")