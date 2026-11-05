from dotenv import load_dotenv
import anthropic
import json
import os
import sys
import glob

load_dotenv()
client = anthropic.Anthropic()

def call_llm(prompt):
    msg = client.messages.create(
        model = "claude-sonnet-5-5",
        max_tokens = 8000,
        messages = [{"role": "user", "content": prompt}]
    )
    return "".join(b.text for b in msg.content if b.type == "text")

def build_prompt(chunk_text):
    vocab = open("vocabulary.md").read()
    example_in = open("chunks/2026-10-28_competitive.txt").read()
    example_out = open("data/swim_workout_2026-10-28.json").read()

    return f"""Convert swim practice text into JSON.

#Rules:
Follow this vocabulary and structure exactly:
{vocab}

#Example Input:
{example_in}

#Example Output:
{example_out}

#Instructions:
- Output only the JSON file. No explanation, markdown fences, or anything else.
- Use null for anything not written in the text. Never guess or estimate.
- Keep the coach's set names exactly as written.
- set_distance and total_distance are only numbers the coach wrote.
- Put anything that doesn't fit a field into notes.
- Turn practice reps use type: "drill".
- Choose category using the category rules in the vocabulary.
- With bungee work, type follows the activity (kick, pull, or swim); equipment is ["bungee"].
- "Bungee pull" means a resisted full-stroke sprint: type "swim".

#Input to Convert:
{chunk_text}
"""

def parse_json(reply):
    text = reply.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)
 
 
def convert(chunk_path, out_path):
    chunk = open(chunk_path).read()
    reply = call_llm(build_prompt(chunk))
    practice = parse_json(reply)
    with open(out_path, "w") as f:
        json.dump(practice, f, indent=2)
    print(f"Saved {out_path}")
 
 
if __name__ == "__main__":
    os.makedirs("converted", exist_ok=True)
    chunks = sys.argv[1:] or sorted(glob.glob("chunks/*.txt"))

    for chunk_path in chunks:
        name = os.path.splitext(os.path.basename(chunk_path))[0]
        out_path = f"converted/swim_workout_{name}.json"

        if "all_groups" in name:
            print(f"skip (multi-group page): {name}")
            continue
        if os.path.exists(out_path):
            print(f"skip (already done): {name}")
            continue

        try:
            convert(chunk_path, out_path)
        except Exception as e:
            print(f"FAILED {name}: {e}")