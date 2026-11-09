import glob
import json


def all_items(items):
    for item in items:
        yield item
        if "items" in item:
            yield from all_items(item["items"])


def style(p):
    items = [i for s in p["sets"] for i in all_items(s["items"])]
    return {
        "num_sets": len(p["sets"]),
        "has_kick_set": any("kick" in s["name"].lower() for s in p["sets"]),
        "uses_rounds": any("items" in i for i in items),
        "named_drills": sum(1 for i in items if i.get("drill")),
        "equipment_used": sum(1 for i in items if i.get("equipment")),
    }


def average(practices):
    rows = [style(p) for p in practices]
    return {k: sum(r[k] for r in rows) / len(rows) for k in rows[0]}


real = [json.loads(line)["output"] for line in open("test.jsonl")]
baseline = [json.load(open(f)) for f in sorted(glob.glob("baseline/*.json"))]

real_avg = average(real)
base_avg = average(baseline)

print(f"{'metric':<16}{'real':>8}{'baseline':>10}")
for k in real_avg:
    print(f"{k:<16}{real_avg[k]:>8.2f}{base_avg[k]:>10.2f}")