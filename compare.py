import difflib
import json
import sys

PRACTICE_FIELDS = ["date", "group", "focus", "phase", "unit", "total_distance"]
SET_FIELDS = ["name", "category", "reps", "set_distance"]
ITEM_FIELDS = ["total_reps", "distance", "stroke", "type", "interval_seconds", "rest_seconds",
               "equipment", "drill", "effort", "breathing", "breathing_pattern", "pattern_per", "start"]


def load(path):
    with open(path) as f:
        return json.load(f)


def flatten(items, multiplier=1, rotation=None):
    out = []
    for item in items:
        if "items" in item:
            out += flatten(item["items"], multiplier * item["reps"],
                           item.get("stroke_rotation") or rotation)
        else:
            leaf = dict(item)
            leaf["total_reps"] = multiplier * item["reps"]
            leaf["equipment"] = sorted(item.get("equipment") or [])
            if rotation:
                leaf["stroke"] = rotation
            out.append(leaf)
    return out


def norm(text):
    return " ".join(str(text).lower().split())


def align(pred, truth, key):
    matcher = difflib.SequenceMatcher(a=[key(x) for x in pred], b=[key(x) for x in truth], autojunk=False)
    pairs, missing, extra = [], [], []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            pairs += list(zip(pred[i1:i2], truth[j1:j2]))
        else:
            extra += pred[i1:i2]
            missing += truth[j1:j2]
    return pairs, missing, extra


class Score:
    def __init__(self):
        self.right = {}
        self.total = {}
        self.diffs = []

    def check(self, level, field, p, t, where):
        key = f"{level}.{field}"
        self.total[key] = self.total.get(key, 0) + 1
        if p == t:
            self.right[key] = self.right.get(key, 0) + 1
        else:
            self.diffs.append(f"{where} | {field}: predicted {p!r}, expected {t!r}")

    def accuracy(self):
        total = sum(self.total.values())
        return 100 * sum(self.right.values()) / total if total else 0.0


def describe(item):
    return f"{item['total_reps']}x{item.get('distance')} {item.get('type')}"


def compare(pred_path, truth_path):
    pred, truth = load(pred_path), load(truth_path)
    score = Score()
    missing_items, extra_items = [], []

    for field in PRACTICE_FIELDS:
        score.check("practice", field, pred.get(field), truth.get(field), "practice")

    set_pairs, missing_sets, extra_sets = align(pred["sets"], truth["sets"], key=lambda s: norm(s["name"]))
    for s in missing_sets:
        missing_items.append(f"whole set '{s['name']}'")
    for s in extra_sets:
        extra_items.append(f"whole set '{s['name']}'")

    for ps, ts in set_pairs:
        where = f"set '{ts['name']}'"
        for field in SET_FIELDS:
            p, t = ps.get(field), ts.get(field)
            if field == "name":
                p, t = norm(p), norm(t)
            score.check("set", field, p, t, where)

        p_items, t_items = flatten(ps["items"]), flatten(ts["items"])
        item_pairs, miss, extra = align(p_items, t_items, key=lambda i: i.get("distance"))
        missing_items += [f"{where}: {describe(i)}" for i in miss]
        extra_items += [f"{where}: {describe(i)}" for i in extra]
        for n, (pi, ti) in enumerate(item_pairs, 1):
            for field in ITEM_FIELDS:
                score.check("item", field, pi.get(field), ti.get(field), f"{where} item {n} ({describe(ti)})")

    print(f"\n{pred_path}  vs  {truth_path}")
    print(f"Field accuracy: {score.accuracy():.1f}%  "
          f"({sum(score.right.values())}/{sum(score.total.values())} fields)")
    print(f"Missing items: {len(missing_items)}   Extra items: {len(extra_items)}")

    weak = sorted((score.right.get(k, 0) / v, k) for k, v in score.total.items())
    weak = [f"{k} {100 * r:.0f}%" for r, k in weak if r < 1]
    if weak:
        print("Weakest fields: " + ", ".join(weak))

    for line in score.diffs:
        print(f"  ✗ {line}")
    for line in missing_items:
        print(f"  − missing {line}")
    for line in extra_items:
        print(f"  + extra {line}")
    return score.accuracy()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare.py <predicted.json> <hand_made.json>")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])
