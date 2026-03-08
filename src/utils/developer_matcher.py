
import re
import difflib
import json
from typing import List, Dict, Optional, Any

def normalize_name(name: str) -> str:
    if not name:
        return ""
    # Convert to lowercase
    name = name.lower()
    # Strip leading/trailing spaces
    name = name.strip()
    # Replace hyphens and underscores with spaces
    name = name.replace("-", " ").replace("_", " ")
    # Remove special characters (keep alphanumeric and spaces)
    name = re.sub(r'[^a-z0-9 ]', '', name)
    # Strip extra spaces result from character removal
    name = ' '.join(name.split())
    return name

def get_similarity(s1: str, s2: str) -> float:
    return difflib.SequenceMatcher(None, s1, s2).ratio()

class DeveloperMatcher:
    def __init__(self, developers: List[Dict[str, Any]]):
        """
        developers: List of dicts with {'id', 'username', 'full_name', 'email'}
        """
        self.developers = developers

    def match(self, incoming_name: str) -> Dict[str, Any]:
        if not incoming_name or incoming_name.lower() in ["unassigned", "none", "null", "no_assignee_found"]:
            return {
                "developer_found": False,
                "matched_developer_name": None,
                "similarity_score": 0.0,
                "status": "INPUT_EMPTY"
            }

        normalized_incoming = normalize_name(incoming_name)
        
        matches = []

        for dev in self.developers:
            # Fields to check
            checks = []
            if dev.get('full_name'):
                checks.append((normalize_name(dev['full_name']), dev['full_name']))
            if dev.get('username'):
                checks.append((normalize_name(dev['username']), dev['full_name']))
            if dev.get('email'):
                email_prefix = dev['email'].split('@')[0]
                checks.append((normalize_name(email_prefix), dev['full_name']))
            
            for normalized_check, original_name in checks:
                if not normalized_check:
                    continue
                
                # Exact Match
                if normalized_incoming == normalized_check:
                    matches.append({
                        "dev": dev,
                        "score": 1.0,
                        "status": "EXACT_MATCH",
                        "display_name": original_name
                    })
                    break # Move to next developer
                
                # Fuzzy Match
                score = get_similarity(normalized_incoming, normalized_check)
                if score >= 0.85:
                    matches.append({
                        "dev": dev,
                        "score": score,
                        "status": "FUZZY_MATCH",
                        "display_name": original_name
                    })

        if not matches:
             return {
                "developer_found": False,
                "matched_developer_name": None,
                "similarity_score": 0.0,
                "status": "NOT_IN_LIST",
                "incoming_name": incoming_name
            }

        # Group by developer to avoid multiple matches for same dev (e.g. username and fullname both match)
        # Keep highest score for each developer
        dev_best_matches = {}
        for m in matches:
            dev_id = m['dev'].get('id', m['dev'].get('username'))
            if dev_id not in dev_best_matches or m['score'] > dev_best_matches[dev_id]['score']:
                dev_best_matches[dev_id] = m
        
        unique_matches = list(dev_best_matches.values())
        unique_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Check for exact matches
        exact_matches = [m for m in unique_matches if m['status'] == "EXACT_MATCH"]
        if exact_matches:
            if len(exact_matches) > 1:
                return {
                    "developer_found": False,
                    "matched_developer_name": None,
                    "similarity_score": 1.0,
                    "status": "AMBIGUOUS_MATCH",
                    "incoming_name": incoming_name
                }
            return {
                "developer_found": True,
                "matched_developer_name": exact_matches[0]['display_name'],
                "similarity_score": 1.0,
                "status": "EXACT_MATCH",
                "incoming_name": incoming_name
            }

        # Check for fuzzy matches
        best_score = unique_matches[0]['score']
        top_fuzzy_matches = [m for m in unique_matches if m['score'] == best_score]
        
        if len(top_fuzzy_matches) > 1:
             return {
                "developer_found": False,
                "matched_developer_name": None,
                "similarity_score": float(best_score),
                "status": "AMBIGUOUS_MATCH",
                "incoming_name": incoming_name
            }

        return {
            "developer_found": True,
            "matched_developer_name": unique_matches[0]['display_name'],
            "similarity_score": float(unique_matches[0]['score']),
            "status": "FUZZY_MATCH",
            "incoming_name": incoming_name
        }
