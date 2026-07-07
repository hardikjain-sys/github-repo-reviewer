from pathlib import Path
import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

PROMPT_DIR = Path(__file__).parent / "prompts"


def review(prompt_file: str,
           context: dict,
           model: str = "openai/gpt-oss-120b"):

    with open(PROMPT_DIR / prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": json.dumps(context, indent=2)
            }
        ]
    )

    return json.loads(response.choices[0].message.content)