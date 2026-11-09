import json
import os
import random
from convert import call_llm, parse_json

random.seed(0)
train = [json.loads(line) for line in open("train.jsonl")]
test = [json.loads(line) for line in open("test.jsonl")]
vocab = open("vocabulary.md").read()

def build_prompt(request):
    examples = random.sample(train, 3)
    shots = "\n\n".join(
        f"REQUEST: {ex['input']}\nPRACTICE:\n{json.dumps(ex['output'])}" for ex in examples
    )
    return f"""You are a swim coach. Write a practice as JSON.

### RULES
{vocab}

### EXAMPLES
{shots}

### INSTRUCTIONS
- Output only the JSON object.
- Use realistic intervals and yardage for the group.
- Make set_distance and total_distance match the actual sets.

### REQUEST
{request}
"""

os.makedirs("baseline", exist_ok=True)

for i, ex in enumerate(test):
    out_path = f"baseline/gen_{i:02d}.json"
    if os.path.exists(out_path):
        continue
    try:
        practice = parse_json(call_llm(build_prompt(ex["input"])))
        practice["request"] = ex["input"]
        with open(out_path, "w") as f:
            json.dump(practice, f, indent=2)
        print("saved", out_path)
    except Exception as e:
        print("FAILED", i, e)