from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from reviewers.architecture import architectureReview
from reviewers.documentation import documentationReview
from reviewers.codeQuality import codeQualityReview
from reviewers.dependency import dependencyReview
from reviewers.testing import testingReview
from reviewers.aggregator import aggregateReview

from tokenMax import enforceBudget


class ReviewState(TypedDict):
    architecture_context: dict
    documentation_context: dict
    codeQuality_context: dict
    dependency_context: dict
    testing_context: dict

    architecture_review: dict
    documentation_review: dict
    codeQuality_review: dict
    dependency_review: dict
    testing_review: dict

    final_review: dict


import asyncio


async def architectureNode(state: ReviewState):
    context = enforceBudget(state["architecture_context"], "architecture")
    return {
        "architecture_review": architectureReview(context)
    }

async def documentationNode(state: ReviewState):
    context = enforceBudget(state["documentation_context"], "documentation")
    await asyncio.sleep(1.5)
    return {
        "documentation_review": documentationReview(context)
    }

async def codeNode(state: ReviewState):
    context = enforceBudget(state["codeQuality_context"], "codeQuality")
    await asyncio.sleep(3.0)
    return {
        "codeQuality_review": codeQualityReview(context)
    }

async def dependencyNode(state: ReviewState):
    context = enforceBudget(state["dependency_context"], "dependency")
    await asyncio.sleep(4.5)
    return {
        "dependency_review": dependencyReview(context)
    }

async def testingNode(state: ReviewState):
    context = enforceBudget(state["testing_context"], "testing")
    await asyncio.sleep(6.0)
    return {
        "testing_review": testingReview(context)
    }



def aggregatorNode(state: ReviewState):
    reviews = {
        "architecture": state["architecture_review"],
        "documentation": state["documentation_review"],
        "codeQuality": state["codeQuality_review"],
        "dependency": state["dependency_review"],
        "testing": state["testing_review"],
    }

    trimmedReviews = enforceBudget(reviews, "aggregator")

    return {
        "final_review": aggregateReview(trimmedReviews)
    }



builder = StateGraph(ReviewState)
builder.add_node("architecture", architectureNode)
builder.add_node("documentation", documentationNode)
builder.add_node("codeQuality", codeNode)
builder.add_node("dependency", dependencyNode)
builder.add_node("testing", testingNode)
builder.add_node("aggregator", aggregatorNode)

builder.add_edge(START, "architecture")
builder.add_edge(START, "documentation")
builder.add_edge(START, "codeQuality")
builder.add_edge(START, "dependency")
builder.add_edge(START, "testing")

builder.add_edge("architecture", "aggregator")
builder.add_edge("documentation", "aggregator")
builder.add_edge("codeQuality", "aggregator")
builder.add_edge("dependency", "aggregator")
builder.add_edge("testing", "aggregator")

builder.add_edge("aggregator", END)

graph = builder.compile()