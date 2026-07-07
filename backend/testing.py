from pathlib import Path

from fetch import fetchAll, fileCode
from parser.parse import parseCode


MAX_TEST_FILES = 5
MAX_TEST_FUNCTIONS = 20


def buildTestingContext(repoData, mode="auto"):

    test_files = repoData["categories"].get("tests", [])

    test_paths = [
        f["path"]
        for f in test_files
    ]

    contents = fetchAll(
        test_paths,
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        fileCode
    )

    frameworks = set()

    summary = {
        "test_files": 0,
        "test_functions": 0,
        "test_classes": 0,
        "fixtures": 0
    }

    full_tests = {}
    compact_tests = {}

    for file in test_files:

        content = contents.get(file["path"])

        if content is None:
            continue

        parsed = parseCode(
            content,
            file["language"],
            file["path"]
        )

        if parsed is None:
            continue

        function_count = sum(
            1
            for chunk in parsed["chunks"]
            if chunk["type"] == "function"
        )

        class_count = sum(
            1
            for chunk in parsed["chunks"]
            if chunk["type"] == "class"
        )

        fixture = Path(file["path"]).name == "conftest.py"

        imports = " ".join(parsed["imports"]).lower()

        if "pytest" in imports:
            frameworks.add("pytest")

        if "unittest" in imports:
            frameworks.add("unittest")

        if "jest" in imports:
            frameworks.add("jest")

        if "mocha" in imports:
            frameworks.add("mocha")

        if "vitest" in imports:
            frameworks.add("vitest")

        summary["test_files"] += 1
        summary["test_functions"] += function_count
        summary["test_classes"] += class_count

        if fixture:
            summary["fixtures"] += 1

        compact_tests[file["path"]] = {
            "functions": function_count,
            "classes": class_count,
            "fixture_file": fixture
        }

        full_tests[file["path"]] = {
            "imports": parsed["imports"],
            "chunks": [
                {
                    "type": chunk["type"],
                    "name": chunk["name"]
                }
                for chunk in parsed["chunks"]
            ]
        }

    summary["frameworks"] = sorted(frameworks)

    if mode == "summary":
        tests = compact_tests

    elif mode == "full":
        tests = full_tests

    else:

        if (
            summary["test_files"] <= MAX_TEST_FILES
            and summary["test_functions"] <= MAX_TEST_FUNCTIONS
        ):
            tests = full_tests
        else:
            tests = compact_tests

    return {
        "summary": summary,
        "tests": tests,
        "repoStats": repoData["fingerprint"]
    }