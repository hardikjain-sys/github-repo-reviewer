import re

from fetch import fetchAll, fileCode
from parser.parserCode import parseCode


metricNameMap = {
    "br": "branches",
    "cc": "cyclomaticComplexity",
    "lp": "loopCount",
    "nest": "nestingDepth",
}

headerExtensions = (".h", ".hpp")

topComplexLimit = 5

singleLetterParamPattern = re.compile(r"\(([^)]*)\)")


def renameMetrics(metrics):
    return {
        metricNameMap.get(key, key): value
        for key, value in metrics.items()
    }


def isHeaderLike(path, parsed):
    if not path.endswith(headerExtensions):
        return False

    return len(parsed.get("chunks", [])) == 0


def summarizeHeaders(headerEntries):
    if not headerEntries:
        return None

    paths = sorted(headerEntries.keys())
    lineCounts = [entry["totalLines"] for entry in headerEntries.values()]

    return {
        "count": len(paths),
        "files": paths,
        "minLines": min(lineCounts),
        "maxLines": max(lineCounts),
        "note": "include guard plus single include only, no logic to review",
    }


def extractSingleLetterParams(preview):
    if not preview:
        return []

    match = singleLetterParamPattern.search(preview)

    if not match:
        return []

    params = match.group(1).split(",")
    singleLetter = []

    for param in params:
        tokens = param.strip().split()

        if not tokens:
            continue

        name = tokens[-1].strip("[]*&")

        if len(name) == 1 and name.isalpha():
            singleLetter.append(name)

    return singleLetter


def buildFunctionEntry(path, chunk):
    entry = {
        "file": path,
        "name": chunk.get("name"),
        "loc": chunk.get("loc"),
        "metrics": renameMetrics(chunk.get("metrics", {})),
    }

    singleLetterParams = extractSingleLetterParams(chunk.get("preview"))

    if singleLetterParams:
        entry["singleLetterParams"] = singleLetterParams

    return entry


def buildSourceFileEntry(path, parsed):
    imports = [
        imp.replace("#include", "").strip().strip('"<>')
        for imp in parsed.get("imports", [])
    ]

    functions = [
        buildFunctionEntry(path, chunk)
        for chunk in parsed.get("chunks", [])
    ]

    for function in functions:
        function.pop("file", None)

    entry = {
        "totalLines": parsed.get("totalLines"),
        "language": parsed.get("language"),
        "imports": imports,
        "functions": functions,
    }

    return entry


def collectTopComplexFunctions(sourceEntries, limit):
    allFunctions = []

    for path, parsed in sourceEntries.items():
        for chunk in parsed.get("chunks", []):
            allFunctions.append((path, chunk))

    ranked = sorted(
        allFunctions,
        key=lambda item: item[1].get("metrics", {}).get("cc", 0),
        reverse=True,
    )

    topFunctions = []

    for path, chunk in ranked[:limit]:
        topFunctions.append({
            "file": path,
            "name": chunk.get("name"),
            "preview": chunk.get("preview"),
        })

    return topFunctions


def summarizeNaming(sourceEntries):
    allSingleLetterParams = set()

    for parsed in sourceEntries.values():
        for chunk in parsed.get("chunks", []):
            for param in extractSingleLetterParams(chunk.get("preview")):
                allSingleLetterParams.add(param)

    return {
        "singleLetterParamsFound": sorted(allSingleLetterParams),
    }


def simplifyRepoStats(fingerprint):
    return {
        "totalFiles": fingerprint.get("total_files"),
        "sourceFiles": fingerprint.get("source_files"),
        "testFiles": fingerprint.get("test_files"),
        "documentationFiles": fingerprint.get("documentation_files"),
        "configFiles": fingerprint.get("config_files"),
        "dependencyFiles": fingerprint.get("dependency_files"),
        "ciCdFiles": fingerprint.get("ci_cd_files"),
        "languages": fingerprint.get("languages", {}),
    }


largeRepoFileThreshold = 30
flaggedComplexityThreshold = 10
flaggedNestingThreshold = 4
maxFlaggedFunctions = 20


def summarizeFileStats(path, parsed):
    chunks = parsed.get("chunks", [])
    complexities = [c.get("metrics", {}).get("cc", 0) for c in chunks]

    return {
        "totalLines": parsed.get("totalLines"),
        "functionCount": len(chunks),
        "avgComplexity": round(sum(complexities) / len(complexities), 1) if complexities else 0,
        "maxComplexity": max(complexities) if complexities else 0,
    }


def collectFlaggedFunctions(sourceEntries, limit):
    flagged = []

    for path, parsed in sourceEntries.items():
        for chunk in parsed.get("chunks", []):
            metrics = chunk.get("metrics", {})
            cc = metrics.get("cc", 0)
            nest = metrics.get("nest", 0)

            if cc >= flaggedComplexityThreshold or nest >= flaggedNestingThreshold:
                flagged.append((path, chunk))

    ranked = sorted(
        flagged,
        key=lambda item: item[1].get("metrics", {}).get("cc", 0),
        reverse=True,
    )

    result = []

    for path, chunk in ranked[:limit]:
        entry = buildFunctionEntry(path, chunk)
        entry["file"] = path
        result.append(entry)

    return result


def buildAggregateContext(repoData, headerEntries, sourceEntries):
    fileStats = {
        path: summarizeFileStats(path, parsed)
        for path, parsed in sourceEntries.items()
    }

    return {
        "mode": "aggregate",
        "headerFilesSummary": summarizeHeaders(headerEntries),
        "fileStats": fileStats,
        "flaggedFunctions": collectFlaggedFunctions(sourceEntries, maxFlaggedFunctions),
        "topComplexFunctions": collectTopComplexFunctions(sourceEntries, topComplexLimit),
        "namingObservations": summarizeNaming(sourceEntries),
        "repoStats": simplifyRepoStats(repoData["fingerprint"]),
    }


def buildDetailedContext(repoData, headerEntries, sourceEntries):
    sourceFileContext = {
        path: buildSourceFileEntry(path, parsed)
        for path, parsed in sourceEntries.items()
    }

    return {
        "mode": "detailed",
        "headerFilesSummary": summarizeHeaders(headerEntries),
        "sourceFiles": sourceFileContext,
        "topComplexFunctions": collectTopComplexFunctions(sourceEntries, topComplexLimit),
        "namingObservations": summarizeNaming(sourceEntries),
        "repoStats": simplifyRepoStats(repoData["fingerprint"]),
    }


def buildCodeQualityContext(repoData):
    sourceFiles = repoData["categories"].get("source_code", [])

    sourcePaths = [f["path"] for f in sourceFiles]

    contents = fetchAll(
        sourcePaths,
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        fileCode
    )

    headerEntries = {}
    sourceEntries = {}

    for file in sourceFiles:
        content = contents.get(file["path"])

        if content is None:
            continue

        parsed = parseCode(content, file["language"], file["path"])

        if parsed is None:
            continue

        if isHeaderLike(file["path"], parsed):
            headerEntries[file["path"]] = parsed
        else:
            sourceEntries[file["path"]] = parsed

    if len(sourceEntries) > largeRepoFileThreshold:
        return buildAggregateContext(repoData, headerEntries, sourceEntries)

    return buildDetailedContext(repoData, headerEntries, sourceEntries)