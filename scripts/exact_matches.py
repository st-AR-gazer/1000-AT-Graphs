import json

def find_matches(obj):
    matches = []
    if isinstance(obj, dict):
        if "atTime" in obj and "finalTime" in obj and obj["atTime"] == obj["finalTime"]:
            matches.append(obj)
        for value in obj.values():
            matches.extend(find_matches(value))
    elif isinstance(obj, list):
        for item in obj:
            matches.extend(find_matches(item))
    return matches

with open("export.json", "r", encoding="utf-8") as f:
    data = json.load(f)

matches = find_matches(data)
for match in matches:
    print(match)
