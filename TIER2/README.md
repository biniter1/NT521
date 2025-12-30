┌─────────────────────────────────────────────────────────┐
│             TIER 2: Advanced SAST Pipeline              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  INPUT: Suspicious packages from Tier 1 (score > 85)    │
│                                                           │
│  ┌───────────────────────────────────────────────┐      │
│  │  Component A: Enhanced Static Analysis        │      │
│  │  ├─ AST Parser                                │      │
│  │  ├─ API Detection (dangerous APIs)            │      │
│  │  ├─ Type Inference                            │      │
│  │  └─ Dataflow Analysis                         │      │
│  │  Output: 25+ static features                  │      │
│  └───────────────────────────────────────────────┘      │
│                           ↓                               │
│  ┌───────────────────────────────────────────────┐      │
│  │  Component B: Obfuscation & Evasion Detector  │      │
│  │  ├─ String Entropy Analysis                   │      │
│  │  ├─ Encoding Detection (base64/hex)           │      │
│  │  ├─ Multi-stage Payload Detection             │      │
│  │  └─ Logic Bomb Detection                      │      │
│  │  Output: 15+ obfuscation features             │      │
│  └───────────────────────────────────────────────┘      │
│                           ↓                               │
│  ┌───────────────────────────────────────────────┐      │
│  │  Component C: Behavioral Pattern Analyzer     │      │
│  │  ├─ API Call Sequences                        │      │
│  │  ├─ Temporal Patterns (cross-version)         │      │
│  │  └─ Known Attack Signatures                   │      │
│  │  Output: 10+ behavioral features              │      │
│  └───────────────────────────────────────────────┘      │
│                           ↓                               │
│  ┌───────────────────────────────────────────────┐      │
│  │  Component D: ML Classifier                   │      │
│  │  • Input: 50+ combined features               │      │
│  │  • Model: Random Forest + Neural Net ensemble │      │
│  │  • Output: Confidence score (0-100)           │      │
│  └───────────────────────────────────────────────┘      │
│                           ↓                               │
│  DECISION:                                               │
│    Score > 70 → Pass to Tier 3 (Dynamic Analysis)      │
│    Score ≤ 70 → Report & Mark as Analyzed               │
│                                                           │
└─────────────────────────────────────────────────────────┘