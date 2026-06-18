from pathlib import Path
from rules import RULES

PRIORITY = [
    "ci_cd",
    "tests",
    "dependencies",
    "configuration",
    "documentation",
    "source_code",
    "skip"
]

def category(path: str) -> str:
    p = Path(path)

    name = p.name
    name_lower = name.lower()

    suffix = p.suffix.lower()

    path_lower = path.lower()

    parts = [part.lower() for part in p.parts]

    for cat in PRIORITY:
        rules = RULES[cat]

        for exact in rules["exact_names"]:
            if name_lower == exact.lower():
                return cat

        for folder in rules["folder_prefixes"]:
            folder_parts = [
                part.lower()
                for part in Path(folder.strip("/")).parts
            ]

            if len(folder_parts) <= len(parts):
                for i in range(len(parts) - len(folder_parts) + 1):
                    if parts[i:i + len(folder_parts)] == folder_parts:
                        return cat

        for sfx in rules["suffixes"]:
            if name_lower.endswith(sfx.lower()):
                return cat

        for sub in rules["contains"]:
            if sub.lower() in path_lower:
                return cat
        if suffix in [ext.lower() for ext in rules["extensions"]]:
            return cat

    return "other"



