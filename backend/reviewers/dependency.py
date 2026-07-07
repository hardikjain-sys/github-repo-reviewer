from .llmcall import review


def dependencyReview(context):
    return review("dependency.txt", context)