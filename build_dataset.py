import glob
import json
from validator import item_distance

practices = []
for path in sorted(glob.glob("converted/*.json")):
    with open(path) as f:
        p = json.load(f)
        if p.get("skip"):
            continue
        practices.append(p)

def make_input(p):
    parts = [f"group: {p['group']}"]
    if p.get("focus"):
        parts.append(f"focus: {p['focus']}")
    total = p.get("total_distance") or computed_total(p)
    if total:
        parts.append(f"about {total} {p['unit']}")
    return "Write a swim practice. " + ", ".join(parts)

def computed_total(p):
    sets = []
    for s in p["sets"]:
        d = [item_distance(i) for i in s["items"]]
        if None in d:
            return None
        sets.append(s["reps"] * sum(d))
    return sum(sets)

train, test = [], []
for p in practices:
    output = {k: v for k, v in p.items() if k != "date"}
    example = {"input": make_input(p), "output": output}
    if p["date"] >= "2026-10-19":
        test.append(example)
    else:
        train.append(example)

for name, rows in [("train.jsonl", train), ("test.jsonl", test)]:
    with open(name, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

print(len(train), "train,", len(test), "test")