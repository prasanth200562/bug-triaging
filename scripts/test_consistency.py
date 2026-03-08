import sys
from src.prediction.assign_developer import assigner

test_title = "ctrl + space not work for terminal show suggestions"
test_body = "vs code version: 1.108.1 - os version: macos - edge version: 110.0.1587.41"

print(f"Testing consistency for: {test_title}")
print("-" * 50)

for i in range(5):
    results = assigner.predict(test_title, test_body)
    if results:
        top = results[0]
        print(f"Run {i+1}: {top['developer']} ({top['confidence']:.4f})")
    else:
        print(f"Run {i+1}: Failed to get prediction")
