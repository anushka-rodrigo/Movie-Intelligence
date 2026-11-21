import json
import subprocess
import sys

from config.paths import PROCESSED_DATA_DIR

MANIFEST = PROCESSED_DATA_DIR / "processed_data_manifest.json"


def run_pipeline():
    subprocess.run([sys.executable, "-m", "src.scripts.stage2_pipeline"], check=True)
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


first = run_pipeline()
second = run_pipeline()

print("\n=== Reproducibility: two full runs ===")
all_same = set(first) == set(second)
for name in sorted(first):
    same = first[name] == second.get(name)
    all_same = all_same and same
    print(f"{name:45s} {first[name]['rows']:>12,} rows   {'identical' if same else 'DIFFERENT'}")

print("\nRESULT:", "REPRODUCIBLE" if all_same else "NOT REPRODUCIBLE")

# Run from the project root with: python -m tests.check_reproducibility
