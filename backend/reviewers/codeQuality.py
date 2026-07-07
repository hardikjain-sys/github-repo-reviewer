from .llmcall import review


def codeQualityReview(context):
    return review("codeQuality.txt", context)