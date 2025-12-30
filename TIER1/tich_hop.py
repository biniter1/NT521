from tier1_production import Tier1Production

# Initialize
tier1 = Tier1Production()

# Analyze
result = tier1.analyze_package(G, 'suspicious-pkg', info)

if result['pass_to_tier2']:
    # Pass to Tier 2 for deeper analysis
    print(f"⚠️ {result['package_name']} needs Tier 2 analysis")
else:
    print(f"✓ {result['package_name']} is benign")