import os
import re
import ast
import time
import requests

API_KEY   = "AIzaSyAod2ZMaNhWBbJZideqLHB1cP5KWCq0pLw"
WORDLIST  = "Filenames_or_Directories_Common.txt"
CHUNK_SIZE = 1
API_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

PROMPT_TEMPLATE = """You are a file categorization expert. Categorize every entry in the wordlist below into exactly one of these 6 categories:
- ci_cd
- tests
- dependencies
- configuration
- documentation
- source_code

If nothing fits, skip it.

Return ONLY a valid Python dict called RULES with exactly this structure — no explanation, no markdown, no backticks, just raw Python:

RULES = {{
    "ci_cd":          {{"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []}},
    "tests":          {{"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []}},
    "dependencies":   {{"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []}},
    "configuration":  {{"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []}},
    "documentation":  {{"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []}},
    "source_code":    {{"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []}}
}}

Rules:
- ci_cd: CI/CD pipelines, release automation (.github/workflows, Jenkinsfile, .travis.yml)
- tests: test files, spec files, test folders, fixtures, mocks (*.test.js, *.spec.ts, pytest.ini)
- dependencies: package managers, lockfiles, manifests (package.json, Cargo.toml, requirements.txt)
- configuration: build tools, linters, env files, dotfiles, infra (vite.config.js, .eslintrc, Dockerfile, .env)
- documentation: readme, changelog, license, guides (README.md, docs/, *.rst)
- source_code: actual code — use extension rules (.js, .py, .go, src/, lib/)

Priority if ambiguous (first wins): ci_cd > tests > dependencies > configuration > documentation > source_code

Wordlist:
{wordlist}"""


EMPTY_RULES = {
    "ci_cd":         {"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []},
    "tests":         {"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []},
    "dependencies":  {"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []},
    "configuration": {"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []},
    "documentation": {"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []},
    "source_code":   {"exact_names": [], "folder_prefixes": [], "extensions": [], "suffixes": [], "contains": []},
}


def merge(base, chunk):
    for cat in base:
        if cat not in chunk:
            continue
        for key in base[cat]:
            if key in chunk[cat]:
                base[cat][key] = list(set(base[cat][key] + chunk[cat][key]))
    return base


def call_gemini(prompt: str, retries: int = 3) -> str:
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    for attempt in range(retries):
        r = requests.post(API_URL, json=body, timeout=60)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(f"  HTTP {r.status_code} — retrying ({attempt+1}/{retries})...")
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Gemini failed after {retries} retries: {r.text}")


def parse_rules(text: str) -> dict:
    # strip markdown fences if model disobeys
    text = re.sub(r"```python|```", "", text).strip()
    # grab everything from RULES = { ... }
    match = re.search(r"RULES\s*=\s*(\{.*\})", text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find RULES dict in response:\n{text[:500]}")
    return ast.literal_eval(match.group(1))


def main():
    with open(WORDLIST, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]

    # filter out pure-number lines (noise in the wordlist)
    lines = [l for l in lines if not re.fullmatch(r"[\d.]+", l)]

    chunks = [lines[i:i+CHUNK_SIZE] for i in range(0, len(lines), CHUNK_SIZE)]
    total  = len(chunks)
    print(f"Total entries: {len(lines)} | Chunk size: {CHUNK_SIZE} | Chunks: {total}\n")

    combined = {cat: {k: list(v) for k, v in rules.items()} for cat, rules in EMPTY_RULES.items()}

    for i, chunk in enumerate(chunks, 1):
        print(f"[{i}/{total}] Sending {len(chunk)} entries...", end=" ", flush=True)
        prompt = PROMPT_TEMPLATE.format(wordlist="\n".join(chunk))

        try:
            raw   = call_gemini(prompt)
            rules = parse_rules(raw)
            combined = merge(combined, rules)
            total_rules = sum(len(v) for cat in combined.values() for v in cat.values())
            print(f"ok — {total_rules} rules so far")
        except Exception as e:
            print(f"FAILED — {e}")

        if i < total:
            time.sleep(1)

    # deduplicate everything
    for cat in combined:
        for key in combined[cat]:
            combined[cat][key] = sorted(set(combined[cat][key]))

    # write output
    out = "RULES = " + repr(combined)
    with open("rules_output.py", "w") as f:
        f.write(out)

    print(f"\nDone! Rules written to rules_output.py")
    print("Summary:")
    for cat, rules in combined.items():
        total_cat = sum(len(v) for v in rules.values())
        print(f"  {cat}: {total_cat} rules")


if __name__ == "__main__":
    main()