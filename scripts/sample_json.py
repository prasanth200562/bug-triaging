import json
import os
from database.db_connection import SessionLocal
from api import models

# Load DB users
db = SessionLocal()
existing_usernames = {u.username.lower() for u in db.query(models.User).all()}
db.close()

# Load JSON
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "data", "processed", "bug_reports_cleaned.json")

with open(data_path, 'r', encoding='utf-8') as f:
    all_bugs = json.load(f)

# Sample some bugs
import random
random.seed(42)
sampled = random.sample(all_bugs, 500)

new_devs = set()
for bug in sampled:
    assignee = bug.get("assignee")
    if assignee and assignee != "unassigned":
        if assignee.lower() not in existing_usernames:
            new_devs.add(assignee)

print(f"Total unique assignees in sample of 500: {len(set(b.get('assignee') for b in sampled if b.get('assignee')))}")
print(f"New developers found in sample: {len(new_devs)}")
print(f"Examples: {list(new_devs)[:10]}")
