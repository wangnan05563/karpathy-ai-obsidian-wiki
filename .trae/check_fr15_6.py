import json
import os

path = os.path.join(os.path.dirname(__file__), "test_result.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total: {len(data)}")
print("--- FR15* entries ---")
for t in data:
    name = t.get("test", "") or t.get("name", "")
    if "FR15" in name:
        status = t.get("status", "")
        msg = (t.get("details", "") or t.get("message", ""))[:200]
        print(f"[{status}] {name} | {msg}")

print("\n--- Failed entries ---")
for t in data:
    status = t.get("status", "")
    if status.upper() == "FAIL":
        name = t.get("test", "") or t.get("name", "")
        msg = (t.get("details", "") or t.get("message", ""))[:200]
        print(f"[{status}] {name} | {msg}")
