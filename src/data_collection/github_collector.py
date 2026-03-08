import requests
import os
import json

# ---------------- CONFIG ----------------
# Try to load from .env manually if python-dotenv is not available
def load_env_manually():
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env_manually()
GITHUB_TOKEN = os.getenv("GITHUB_PAT")

REPOSITORIES = [
    ("microsoft", "vscode"),
    ("microsoft", "vscode-python"),
    ("microsoft", "vscode-eslint"),
    ("microsoft", "vscode-jupyter"),
    ("microsoft", "vscode-cpptools")
]

PER_PAGE = 100
START_YEAR = 2022
MAX_TOTAL_ISSUES = 9000   # overall limit
# ----------------------------------------

def get_headers():
    headers = {
        "Accept": "application/vnd.github+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers

def fetch_repo_issues(owner, repo, limit_per_repo=10, state="closed"):
    import random
    collected = []
    # Add randomization to the page to discover different bugs each time
    page = random.randint(1, 5) 
    base_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = get_headers()

    while len(collected) < limit_per_repo:
        params = {
            "state": state,
            "per_page": min(PER_PAGE, limit_per_repo * 2),
            "page": page
        }

        try:
            response = requests.get(base_url, headers=headers, params=params)
            
            if response.status_code == 401:
                # Token is invalid, try without it
                print("Warning: GITHUB_PAT is invalid (401). Retrying without token...")
                headers_no_token = headers.copy()
                headers_no_token.pop("Authorization", None)
                response = requests.get(base_url, headers=headers_no_token, params=params)
            
            if response.status_code == 403:
                # Provide a clearer error for rate limiting
                reset_time = response.headers.get('X-RateLimit-Reset')
                msg = f"GitHub Rate Limit Exceeded for {owner}/{repo}."
                if not GITHUB_TOKEN:
                    msg += " Consider adding GITHUB_PAT to your .env file to increase limits."
                raise Exception(msg)
            elif response.status_code != 200:
                raise Exception(f"GitHub API Error ({response.status_code}): {response.text}")
        except Exception as e:
            # Re-raise to be caught by the API route
            raise e

        issues = response.json()
        if not issues:
            break

        for issue in issues:
            # Ignore pull requests
            if "pull_request" in issue:
                continue

            # Must have assignee for training data, but for live fetching maybe not?
            # User said "ignores the developer or other dtail only bug tittle and description"
            # So we don't strictly need assignee here, but let's keep it if available.
            
            # Filter by closed year only if we are in "closed" state
            if state == "closed" and "closed_at" in issue and issue["closed_at"]:
                closed_year = int(issue["closed_at"][:4])
                if closed_year < START_YEAR:
                    continue

            collected.append({
                "repository": f"{owner}/{repo}",
                "issue_id": issue["id"],
                "issue_number": issue["number"],
                "title": issue["title"],
                "body": issue["body"] or "",
                "assignee": issue["assignee"]["login"] if issue["assignee"] else "unassigned",
                "state": issue["state"],
                "created_at": issue["created_at"],
                "closed_at": issue.get("closed_at")
            })

            if len(collected) >= limit_per_repo:
                break

        print(f"COLLECTED {repo}: {len(collected)} issues")
        page += 1

    return collected

def fetch_bugs_from_github(total_limit=10, state="open"):
    """
    Higher-level function for fetching bugs from configured repositories.
    """
    all_collected = []
    
    # Distribute the limit across repositories
    limit_per_repo = max(1, total_limit // len(REPOSITORIES))
    
    for owner, repo in REPOSITORIES:
        remaining = total_limit - len(all_collected)
        if remaining <= 0:
            break
        
        # Adjust limit for the last repo if needed
        current_limit = min(limit_per_repo, remaining)
        if owner == REPOSITORIES[-1][0] and repo == REPOSITORIES[-1][1]:
            current_limit = remaining
            
        repo_issues = fetch_repo_issues(owner, repo, current_limit, state=state)
        all_collected.extend(repo_issues)
        
    return all_collected[:total_limit]


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_PAT not set")

    print(f"\nCollecting up to {MAX_TOTAL_ISSUES} issues...")
    all_issues = fetch_bugs_from_github(total_limit=MAX_TOTAL_ISSUES, state="closed")

    os.makedirs("data/raw", exist_ok=True)

    with open("data/raw/github_issues_raw.json", "w", encoding="utf-8") as f:
        json.dump(all_issues, f, indent=4)

    print(f"\nDONE: Total collected bugs = {len(all_issues)}")
