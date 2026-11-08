import os
import pathlib

PROJECT_ROOT = pathlib.Path.cwd()

print(" Checking artifacts in project root:", PROJECT_ROOT)
print("-" * 80)

# All expected artifacts from your 3 notebooks
EXPECTED_ARTIFACTS = {
    "Text Model Directory": "burnout_text_classifier_ft",
    "Behavior Model (Acadamic notebook)": "Data/model_artifacts/behavior_model_synthetic_labels.joblib",
    "Labeling Metadata": "Data/model_artifacts/labeling_metadata.json",
    "Reflective Journals CSV": "synthetic_reflective_journals_single.csv",
    "Academic Dataset CSV": "synthetic_academic_dataset_v2.csv",
    "Burnout Dataset CSV (burnout2classes notebook)": "data_with_burnout.csv",

    # LightGBM behavior model artifacts
    "LGBM Pipeline (full pipeline)": "saved_models_binary_high_v2_all/pipeline_with_preproc.pkl",
    "LGBM Model Only": "saved_models_binary_high_v2_all/final_pipeline_lgbm.pkl",
    "Preprocessor Only": "saved_models_binary_high_v2_all/preprocessor.pkl",
    "Decision Threshold": "saved_models_binary_high_v2_all/decision_threshold.pkl",
    "Random Search Results": "saved_models_binary_high_v2_all/rnd_search_lgbm.pkl",
}

def check_path(description, relative_path):
    full_path = PROJECT_ROOT / relative_path
    exists = full_path.exists()
    status = " FOUND" if exists else " MISSING"
    print(f"{status} — {description}: {relative_path}")

    if exists:
        print(f"      → Full path: {full_path.resolve()}")
    print()

def find_any_matching(name):
    """Search for the file anywhere in project tree."""
    matches = []
    for p in PROJECT_ROOT.rglob(name):
        matches.append(p.resolve())
    return matches

print("\n Checking expected artifacts...\n")

for desc, rel_path in EXPECTED_ARTIFACTS.items():
    check_path(desc, rel_path)

print("\n🔍 Searching entire project for alternate or duplicate artifacts...\n")

SEARCH_TARGETS = [
    "pipeline_with_preproc.pkl",
    "final_pipeline_lgbm.pkl",
    "decision_threshold.pkl",
    "behavior_model_synthetic_labels.joblib",
    "model.safetensors",
    "config.json",
]

for filename in SEARCH_TARGETS:
    print(f"Searching for: {filename}")
    found = find_any_matching(filename)
    if not found:
        print(f"    Not found anywhere in project.\n")
    else:
        print(f"    Found {len(found)} match(es):")
        for p in found:
            print(f"      → {p}")
        print()

print("-" * 80)
print("✔️ Artifact check completed.")
print("If any required files show  MISSING, rerun the corresponding notebook to generate them.")
print("-" * 80)
