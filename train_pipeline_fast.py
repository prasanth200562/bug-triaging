import subprocess
import time
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_script(script_path):
    print(f"\n--- Running: {script_path.name} ---")
    # Use the current Python interpreter
    result = subprocess.run([sys.executable, str(script_path)])
    
    if result.returncode != 0:
        print(f"\nERROR in {script_path.name}")
        exit(1)

def main():
    scripts = [
        BASE_DIR / "src/feature_engineering/tfidf_vectorizer.py",
        BASE_DIR / "src/models/train_base_models.py", 
        BASE_DIR / "src/models/train_ensemble.py"
    ]
    
    for script in scripts:
        run_script(script)
        
    print("\nFat Training Pipeline Completed Successfully.")

if __name__ == "__main__":
    main()
