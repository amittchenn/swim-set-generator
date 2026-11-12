import glob
import json
import re
import sys

GROUPS = {"competitive", "sprint", "distance", "intermediate", "intro", "mixed", "recreational", "masters", "developmental"}
FOCUSES = {"recovery", "endurance", "speed", "technique", "race_pace", "lactate_tolerance", None}
PHASES = {"base", "build", "taper", None}
UNITS = {"yards", "meters"}
CATEGORIES = {"warmup", "preset", "main", "kick", "cooldown"}
STROKES = {"free", "back", "breast", "fly", "im", "choice"}
TYPES = {"swim", "kick", "drill", "pull", "scull", None}
EQUIPMENT = {"fins", "paddles", "snorkel", "pull_buoy", "kickboard", "bungee"}
DRILLS = {"dressel", "over_under", "tiger_tumble", "tallahassee_tumble", None}
EFFORTS = {"easy", "social", "speed_play", "descend", "hvo", None}
BREATHING = {"count", "no_breath", None}
STARTS = {"off_blocks", None}
ROTATIONS = {"im_order", None}


def item_distance(item):
    if item.get("reps") is None:
        return None
    if "items" in item:
        child = [item_distance(c) for c in item["items"]]
        if None in child:
            return None
        return item["reps"] * sum(child)
    if item.get("distance") is None:
        return None
    return item["reps"] * item["distance"]


def is_pos_int(x):
    return isinstance(x, int) and not isinstance(x, bool) and x > 0


def check_item(item, where, errors, in_rotation=False):
    def err(msg):
        errors.append(f"{where}: {msg}")

    if not is_pos_int(item.get("reps")):
        err(f"reps must be a positive integer, got {item.get('reps')!r}")

    if "items" in item:
        rot = item.get("stroke_rotation")
        if rot not in ROTATIONS:
            err(f"unknown stroke_rotation {rot!r}")
        for i, child in enumerate(item["items"]):
            check_item(child, f"{where} > round item {i+1}", errors, in_rotation or rot is not None)
        return

    d = item.get("distance")
    if d is not None and not is_pos_int(d):
        err(f"distance must be a positive integer or null, got {d!r}")

    stroke = item.get("stroke")
    if stroke is None and not in_rotation:
        err("stroke is null outside a stroke_rotation round")
    elif stroke is not None and stroke not in STROKES:
        err(f"unknown stroke {stroke!r}")

    checks = [("type", TYPES), ("drill", DRILLS), ("effort", EFFORTS),
              ("breathing", BREATHING), ("start", STARTS)]
    for field, allowed in checks:
        if item.get(field) not in allowed:
            err(f"unknown {field} {item.get(field)!r}")

    if item.get("drill") is not None and item.get("type") != "drill":
        err("named drill requires type 'drill'")

    if item.get("interval_seconds") is not None and item.get("rest_seconds") is not None:
        err("cannot have both interval_seconds and rest_seconds")

    eq = item.get("equipment")
    if not isinstance(eq, list):
        err("equipment must be a list")
    else:
        for e in eq:
            if e not in EQUIPMENT:
                err(f"unknown equipment {e!r}")
        if len(eq) != len(set(eq)):
            err("duplicate equipment")

    b, pat, per = item.get("breathing"), item.get("breathing_pattern"), item.get("pattern_per")
    if b == "count":
        if not pat or per is None:
            err("breathing 'count' needs breathing_pattern and pattern_per")
        elif d is not None and d % (len(pat) * per) != 0:
            err(f"breathing pattern of {len(pat) * per} doesn't fit evenly into distance {d}")
    elif pat is not None or per is not None:
        err("breathing_pattern/pattern_per set but breathing is not 'count'")


def compare(label, stated, computed, results):
    if computed is None:
        results.append(f"  ⚠️  {label}: can't verify, some distances unknown")
    elif stated is None:
        results.append(f"  ✅ {label}: {computed} (no stated value)")
    elif stated == computed:
        results.append(f"  ✅ {label}: {computed}")
    else:
        results.append(f"  ❌ {label}: stated {stated}, computed {computed}")


def validate(path):
    with open(path) as f:
        p = json.load(f)
    errors, results = [], []

    if isinstance(p, list):
        print(f"\n{path}\n  ❌ file must contain one practice, not a list")
        return 1

    if "date" in p and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(p.get("date"))):
        errors.append(f"date must be YYYY-MM-DD, got {p.get('date')!r}")
    for field, allowed in [("group", GROUPS), ("focus", FOCUSES), ("phase", PHASES), ("unit", UNITS)]:
        if p.get(field) not in allowed:
            errors.append(f"unknown {field} {p.get(field)!r}")

    set_totals = []
    for s in p["sets"]:
        name = s["name"]
        if s.get("category") not in CATEGORIES:
            errors.append(f"{name}: unknown category {s.get('category')!r}")
        for i, item in enumerate(s["items"]):
            check_item(item, f"{name} > item {i+1}", errors)
        child = [item_distance(i) for i in s["items"]]
        computed = None if None in child else s["reps"] * sum(child)
        set_totals.append(computed)
        compare(name, s.get("set_distance"), computed, results)

    total = None if None in set_totals else sum(set_totals)
    compare("TOTAL", p.get("total_distance"), total, results)

    print(f"\n{path}")
    print("\n".join(results))
    for e in errors:
        print(f"  ❌ {e}")
    mismatches = sum(r.strip().startswith("❌") for r in results)
    return len(errors) + mismatches


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob("data/swim_workout_*.json"))
    problems = sum(validate(f) for f in files)
    print(f"\n{len(files)} file(s) checked, {problems} problem(s).")
    sys.exit(1 if problems else 0)
