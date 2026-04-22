import os
import json
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = Path(__file__).parent /"data" / "topics.json"

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def load_topics():
    with open(DATA_PATH) as f:
        return json.load(f)

def save_topics(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def suggest_topics():
    data = load_topics()
    history = data["used_topics"]

    prompt = f"""
You are helping a tech blogger plan their next article.

Previously written topics:
{json.dumps(history, indent=2) if history else "None yet"}

Suggest atleast 6 more topics to choose from. Instructions about choosing topics:
- It can be an intuitive topic. For example, 'how pressing a key on the keyboard is translated to the screen.' 
Because typing is something everyone does, but not many know how it goes to the screen internally. 
- It can be an abstract/generalised but accurate fact. For example, 'An LLM is not intelligent in the cognitive sense, it merely predicts based on probablity.'
Because it is an accurate fact and still requires an interesting way of thought. 
- It can be a book quote. For example, 'Hardware: the parts of a computer that can be kicked' or 'Any problem in computer science can be solved with another layer of indirection'
Because, these topics catch your attention but at the same time can branch out into multiple approahces of thought. 
- You may occasionally also suggest topics from other fields that can be written in the lens of Computer Science. For example, 'The Ship of Thesus' from psychology can be interpreted as/applied to: 1. The company Meta (originally FB) 2. The way compiters have evolved from a room size ot a microchip. Is it still the same.
Because this evokes creative thought. 
Best example: 'all a computer can do is addition.' Because, it sounds like a perfect thought provoking title. It can go in various directions like talking about hardware or gates and adders and how tasks flow in a computer internally, and so on.
Bad example: 'The cloud is just someone else's computer.' — Everyone already knows this. No creative direction.
Bad example: 'Why do computers have bugs?' — Too generic, no surprising angle.
- Most importantly, for all the suggestions, they must induce creative thought or give something to think about. 


Other notes:
Before suggesting a topic, ask yourself: would a developer already know this and shrug? If yes, discard it.
The goal is to make someone stop and think "wait... actually, how does that work?" or "I never thought about it that way."

Return ONLY a list of titles, no explanation. 
"""

    response = model.generate_content(prompt)
    print("\n--- Suggested Topics ---")
    print(response.text)

    choice = input("\nPick a number (1-6) or type your own topic: ").strip()

    # Parse numbered choice or free text
    lines = [l.strip() for l in response.text.strip().split("\n") if l.strip()]
    if choice.isdigit() and 1 <= int(choice) <= len(lines):
        selected = lines[int(choice) - 1]
        # Strip the leading "1. " etc
        selected = selected.split(". ", 1)[-1]
    else:
        selected = choice

    data["suggested_topics"].append(selected)
    save_topics(data)

    print(f"\n✅ Selected: {selected}")
    return selected

if __name__ == "__main__":
    suggest_topics()

