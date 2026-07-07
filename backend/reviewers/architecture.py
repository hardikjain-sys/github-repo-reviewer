from .llmcall import review


def architectureReview(context):
    return review("architecture.txt", context)