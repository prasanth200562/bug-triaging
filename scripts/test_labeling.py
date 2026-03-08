from src.preprocessing.nlp_preprocessor import generate_tags

test_cases = [
    ("Terminal issue with bash", "Terminal"),
    ("The UI is broken and buttons are not showing", "UI/UX"),
    ("Copilot agent failed to predict gpt models", "AI/Copilot"),
    ("The system is very slow and lagging", "Performance"),
    ("VS Code editor syntax highlighting is broken", "Editor"),
    ("Git push failed to github repo", "Git/GitHub"),
    ("Backend API server returned 500 error on sql query", "Backend/API"),
    ("Random bug with no keywords", "General")
]

print("Verifying Tag Generation:")
print("-" * 30)
for text, expected in test_cases:
    tags = generate_tags(text)
    print(f"Input: {text}")
    print(f"Tags:  {tags}")
    print("-" * 30)

print("Verification Complete.")
