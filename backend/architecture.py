import re
from pathlib import Path
from collections import Counter

from dependencyParser import finalDependencies
from parser.parse import parseCode
from fetch import fetchAll, filePartial


entryPointNames = {
    "main.py",
    "app.py",
    "server.py",
    "main.c",
    "main.cpp",
    "manage.py",
    "index.js",
    "index.ts",
    "server.js",
    "server.ts",
    "main.go",
    "main.rs",
}


importantConfigs = {
    "package.json",
    "package-lock.json",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}


includeGuardPattern = re.compile(r"^#define\s+\w+_H$")


def isIncludeGuard(macro):
    return bool(includeGuardPattern.match(macro.strip()))


def trimParsedFile(parsed):
    if not isinstance(parsed, dict):
        return parsed

    trimmedMacros = [
        macro for macro in parsed.get("macros", [])
        if not isIncludeGuard(macro)
    ]

    trimmedChunks = []

    for chunk in parsed.get("chunks", []):
        lineCount = chunk.get("line_count", 0)

        if lineCount <= 1 and chunk.get("type") not in ("function", "class"):
            continue

        trimmedChunks.append({
            "name": chunk.get("name"),
            "type": chunk.get("type"),
            "parentClass": chunk.get("parent_class"),
            "lineCount": lineCount,
        })

    return {
        "imports": parsed.get("imports", []),
        "macros": trimmedMacros,
        "chunks": trimmedChunks,
    }


def importantFileParsed(
    repoData,
    entryPoints,
    configs,
    centralModulesList
):
    importantPaths = set()

    importantPaths.update(entryPoints)
    importantPaths.update(configs)

    for item in centralModulesList[:5]:
        importantPaths.add(item["path"])

    contents = fetchAll(
        list(importantPaths),
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        lambda o, r, b, p: filePartial(o, r, b, p, maxBytes=4096)
    )

    parsed = {}
    languageLookup = {}

    for file in repoData["categories"].get("source_code", []):
        languageLookup[file["path"]] = file["language"]

    for path, content in contents.items():
        if content is None:
            continue

        language = languageLookup.get(path)

        if language is None:
            continue

        result = parseCode(content, language, path)

        if result is None:
            continue

        parsed[path] = trimParsedFile(result)

    return parsed


def centralModules(graph):
    incoming = Counter()

    for deps in graph.values():
        for dep in deps["structure"]:
            incoming[dep] += 1

    result = []

    for module, count in incoming.most_common(10):
        result.append({
            "path": module,
            "incomingDependencies": count
        })

    return result


def repoStats(repoData):
    stats = {
        "totalFiles": 0,
        "sourceFiles": 0,
        "testFiles": 0,
        "documentationFiles": 0,
        "configurationFiles": 0,
        "languages": Counter()
    }

    for category, files in repoData["categories"].items():
        stats["totalFiles"] += len(files)

        if category == "source_code":
            stats["sourceFiles"] = len(files)
        elif category == "tests":
            stats["testFiles"] = len(files)
        elif category == "documentation":
            stats["documentationFiles"] = len(files)
        elif category == "configuration":
            stats["configurationFiles"] = len(files)

        for file in files:
            if "language" in file:
                stats["languages"][file["language"]] += 1

    stats["languages"] = dict(stats["languages"])

    return stats


def buildModuleLookup(repoData):
    lookup = {}

    for file in repoData["categories"].get("source_code", []):
        path = file["path"]
        language = file["language"]

        if language == "python":
            module = path[:-3].replace("/", ".")
            lookup[module] = path

        elif language in ["javascript", "typescript"]:
            stem = Path(path).stem
            lookup[stem] = path

            parent = str(Path(path).with_suffix(""))
            lookup[parent.replace("/", "/")] = path

        elif language == "java":
            module = path[:-5].replace("/", ".")
            lookup[module] = path

        elif language in ["c", "cpp"]:
            filename = Path(path).name
            lookup[filename] = path

            stem = Path(path).stem
            lookup[stem] = path

    return lookup


def resolveDependencyGraph(importGraph, repoData):
    lookup = buildModuleLookup(repoData)
    graph = {}

    for file in repoData["categories"].get("source_code", []):
        path = file["path"]
        imports = importGraph.get(path, [])

        internalDeps = []

        for imp in imports:
            resolved = None

            if imp in lookup:
                resolved = lookup[imp]
            else:
                impLast = imp.split(".")[-1]

                if impLast in lookup:
                    resolved = lookup[impLast]

            if resolved:
                internalDeps.append(resolved)
            else:
                internalDeps.append(imp)

        graph[path] = {
            "structure": sorted(set(internalDeps))
        }

    return graph


def buildDependencyGraph(repoData, contents):
    graph = {}

    for file in repoData["categories"].get("source_code", []):
        content = contents.get(file["path"])

        if content is None:
            continue

        deps = finalDependencies(file["language"], content)
        graph[file["path"]] = deps

    return graph


def buildDirectoryTree(repoData):
    paths = []

    for category in repoData["categories"].values():
        for file in category:
            paths.append(file["path"])

    return sorted(paths)


def getEntryPoints(repoData):
    entryPoints = []

    for category in repoData["categories"].values():
        for file in category:
            name = Path(file["path"]).name

            if name in entryPointNames:
                entryPoints.append(file["path"])

    return sorted(entryPoints)


def getImportantConfigs(repoData):
    configs = []

    for category in repoData["categories"].values():
        for file in category:
            name = Path(file["path"]).name

            if name in importantConfigs:
                configs.append(file["path"])

    return sorted(configs)


def buildArchitectureContext(repoData):
    sourcePaths = [
        f["path"]
        for f in repoData["categories"].get("source_code", [])
    ]

    contents = fetchAll(
        sourcePaths,
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        filePartial
    )

    rawGraph = buildDependencyGraph(repoData, contents)
    dependencyGraph = resolveDependencyGraph(rawGraph, repoData)

    entryPoints = getEntryPoints(repoData)
    configs = getImportantConfigs(repoData)
    central = centralModules(dependencyGraph)

    return {
        "directoryTree": buildDirectoryTree(repoData),
        "entryPoints": entryPoints,
        "importantConfigs": configs,
        "repoStats": repoStats(repoData),
        "centralModules": central,
        "parsedFiles": importantFileParsed(
            repoData,
            entryPoints,
            configs,
            central
        )
    }