from .llmcall import review


def testingReview(context):
    return review("testing.txt", context)