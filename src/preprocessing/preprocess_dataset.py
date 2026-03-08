import json
import re
from pathlib import Path
from tqdm import tqdm
import sys
import os

# Add src to path to import nlp_preprocessor
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.preprocessing import nlp_preprocessor

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_FILE = BASE_DIR / "data/raw/github_issues_raw.json"
OUTPUT_FILE = BASE_DIR / "data/processed/bug_reports_nlp_ready.json"

def load_data():
    print(f"Loading raw data from {RAW_DATA_FILE}...")
    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_assignee_blacklist(data):
    assignees = set()
    for item in data:
        if item.get('assignee'):
            assignees.add(item['assignee'].lower())
    print(f"Found {len(assignees)} unique assignees to blacklist.")
    return assignees

def remove_names(text, blacklist):
    if not text:
        return ""
    
    # Simple strategy: Replace names with generic token or empty string
    # We accept that this might break some sentences, but it removes leakage.
    # We iterate over the blacklist. For efficiency, we could use a single regex.
    
    # Sort by length descending to replace longer names first (if any overlaps)
    sorted_names = sorted(list(blacklist), key=len, reverse=True)
    
    # Escape names for regex
    escaped_names = [re.escape(name) for name in sorted_names]
    
    # Create a giant regex: \b(name1|name2|...)\b
    # \b ensures we don't match substrings of other words (e.g. "ray" in "array")
    pattern = r'\b(?:' + '|'.join(escaped_names) + r')\b'
    
    # Case insensitive replacement
    return re.sub(pattern, "[LEAKAGE_REMOVED]", text.lower(), flags=re.IGNORECASE)

def main():
    data = load_data()
    blacklist = get_assignee_blacklist(data)
    
    processed_data = []
    
    print("Preprocessing descriptions (removing names + NLP pipeline)...")
    for item in tqdm(data):
        title = item.get('title', '') or ''
        body = item.get('body', '') or ''
        full_text = f"{title} {body}"
        
        # 1. Clean Leakage
        clean_text = remove_names(full_text, blacklist)
        
        # 2. NLP Preprocessing
        final_tokens = nlp_preprocessor.preprocess_text(clean_text)
        
        if final_tokens.strip():
            processed_data.append({
                "issue_id": item.get("issue_id"),
                "assignee": item.get("assignee"),
                "combined_text": final_tokens
            })
            
    print(f"Saving {len(processed_data)} processed reports to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=4)
        
    print("Done.")

if __name__ == "__main__":
    main()
