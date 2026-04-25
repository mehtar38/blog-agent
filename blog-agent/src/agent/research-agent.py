import json
import os
from pathlib import Path
import dotenv
import google.generativeai as genai
from tavily import TavilyClient

TOPICS_PATH = Path(__file__).parent /"data" / "topics.json"
RESEARCH_PATH = Path(__file__).parent /"data" / "research.json"

dotenv.load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def get_topic():
    with open(TOPICS_PATH) as f:
        topic = json.load(f)
        return topic["current_topic"]

def generate_queries(topic):
    
    prompt = f"""
You are helping a tech blogger research for their next article.

Given the topic:{topic}, think about what the researcher would require to help guide writing this article.
You have to give targeted search queries that could be fed to the Tavily API to fetch results.
Suggest research that would cover questions like:
- What information would be needed to prove this topic?
- Is there any trustable evidence that would support the topic? (not just articles but research papers or official documentations)
- What directions could this topic branch into?

Return ONLY a JSON array, no explanation, no markdown backticks:
[
  {{"query": "your search query here", "source_type": "technical explainer"}},
  {{"query": "another query", "source_type": "research paper"}}
]

source_type can be: "research paper", "technical explainer", "historical", "official documentation", "counterargument"
"""
    
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Removing markdown code just in case
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw)


def fetch_sources(queries: list[dict]) -> list[dict]:
    results = []
    for q in queries:
        print(f"  Searching: {q['query']}")
        response = tavily.search(
            query=q["query"],
            search_depth="advanced",
            max_results=5
        )
        for r in response["results"]:
            results.append({
                "title": r["title"],
                "url": r["url"],
                "content": r["content"],
                "source_type": q["source_type"]
            })
    return results

def filter_and_summarize(topic: str, sources: list[dict]) -> list[dict]:
    # A condensed version of sources to fit in the prompt
    sources_text = ""
    for i, s in enumerate(sources, 1):
        sources_text += f"""
{i}. Title: {s['title']}
   URL: {s['url']}
   Type: {s['source_type']}
   Content: {s['content'][:500]}
---"""

    prompt = f"""
You are a research editor helping a tech blogger write about: "{topic}"

Here are {len(sources)} raw search results. Your job is to:
1. Drop low quality sources (SEO farms, listicles, outdated content, paywalled with no preview)
2. Keep the best 8-10 sources that are actually citable and useful
3. Prioritize: research papers, official docs, reputable technical blogs
4. Make sure the kept sources cover different angles of the topic, not just the same point repeated

For each source you keep, write:
- A 2-3 sentence summary of what it covers
- Why it is useful for this article
- A citable label: "background", "evidence", "technical depth", "historical", "counterargument"

Raw results:
{sources_text}

Return ONLY a JSON array, no markdown, no explanation:
[
  {{
    "title": "source title",
    "url": "source url",
    "summary": "2-3 sentence summary",
    "why_useful": "one sentence",
    "cite_as": "background | evidence | technical depth | historical | counterargument"
  }}
]
"""
    response = model.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw)

# def get_direction_note() -> str:
#     print("\nReview the sources above.")
#     print("Give a direction note — what angle are you taking? What to emphasize? What to skip?")
#     note = input("\nYour direction: ").strip()
#     return note


def save_research(topic: str, queries: list, sources: list, curated: list):
    with open(RESEARCH_PATH) as f:
        data = json.load(f)

    session = {
        "topic": topic,
        "queries": queries,
        "raw_source_count": len(sources),
        "curated_sources": curated,
        # "direction_note": direction
    }

    data["sessions"].append(session)

    with open(RESEARCH_PATH, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    topic = get_topic()
    queries = generate_queries(topic)
    sources = fetch_sources(queries)
    curated = filter_and_summarize(topic, sources)
    for i, s in enumerate(curated, 1):
        print(f"{i}. {s['title']}")
        print(f"{s['url']}")
        print(f"{s['cite_as'].upper()}")
        print(f"{s['summary']}")
        print()
    save_research(topic, queries, sources, curated)

