from groq import Groq
import ast
import json

from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")


def othersC(otherList):

    client = Groq(
        api_key=api_key
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": f"""
                You are a repository file classifier.
                Classify each file into exactly one category:
                documentation
                source_code
                tests
                dependencies
                configuration
                ci_cd
                skip
                
                Return ONLY a valid Python list of category strings.
                Requirements:
                Output length must equal input length
                Preserve input order
                No explanations
                No markdown
                No code fences
                No extra text
                Skip means file is worthless in data
                
                Input:
                {json.dumps(otherList, indent=2)}
                """
            }
        ],
        temperature=0
    )

    categories = ast.literal_eval(
        response.choices[0].message.content
    )

    return categories