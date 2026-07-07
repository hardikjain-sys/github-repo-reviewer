import json

charsPerTokenEstimate = 4

defaultReviewerBudgets = {
    "architecture": 300,
    "documentation": 300,
    "codeQuality": 300,
    "dependency": 300,
    "testing": 300,
    "aggregator": 300,
}


def estimateTokens(value):
    serialized = json.dumps(value, default=str)
    return len(serialized) // charsPerTokenEstimate


def trimToBudget(context, maxTokens):
    trimmed = json.loads(json.dumps(context, default=str))
    maxChars = maxTokens * charsPerTokenEstimate

    if isinstance(trimmed, dict):
        keys = list(trimmed.keys())
        for key in keys:
            if key == "repoStats":
                continue

            if estimateTokens(trimmed) <= maxTokens:
                break

            val = trimmed[key]
            if isinstance(val, list) and len(val) > 1:
                while len(val) > 1 and estimateTokens(trimmed) > maxTokens:
                    val.pop()
                trimmed[key] = val
            elif isinstance(val, dict) and len(val) > 1:
                sub_keys = list(val.keys())
                for sk in reversed(sub_keys):
                    if estimateTokens(trimmed) <= maxTokens or len(val) <= 1:
                        break
                    del val[sk]
                trimmed[key] = val
            elif isinstance(val, str) and len(val) > 50:
                while len(val) > 20 and estimateTokens(trimmed) > maxTokens:
                    val = val[:len(val) // 2]
                trimmed[key] = val + "..."

    if estimateTokens(trimmed) > maxTokens:
        c = json.dumps(trimmed, default=str)[:maxChars]
        trimmed = {
            "notice": "Data shrunk to fit token limit.",
            "leftContext": c + "..."
        }

    trimmed["_tokenBudget"] = {
        "maxTokens": maxTokens,
        "estimatedTokens": estimateTokens(trimmed),
        "wasTrimmed": True,
    }
    return trimmed


def enforceBudget(context, reviewerName):
    maxTokens = defaultReviewerBudgets.get(reviewerName, 100)
    return trimToBudget(context, maxTokens)