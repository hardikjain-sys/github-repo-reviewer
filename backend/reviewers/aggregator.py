from .llmcall import review


def aggregateReview(context):
    return review("aggregator.txt", context)