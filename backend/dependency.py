import re

from fetch import fetchAll, fileCode


skipLockfileNames = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "go.sum",
    "composer.lock",
    "Gemfile.lock",
    "mix.lock",
    "flake.lock",
    "conda-lock.yml",
    "uv.lock",
    "packages.lock.json",
    "gradle.lockfile",
}

maxDepsPerFile = 15


requirementsLinePattern = re.compile(
    r"^([A-Za-z0-9_.\-]+)\s*([=<>!~^]{1,2}=?\s*[A-Za-z0-9_.\-]*)?"
)

packageJsonDepPattern = re.compile(r'"([A-Za-z0-9_./@-]+)"\s*:\s*"([^"]*)"')

pyprojectDepPattern = re.compile(
    r'^\s*([A-Za-z0-9_.\-]+)\s*=\s*"?([^"\n]*)"?', re.MULTILINE
)

cargoDepPattern = re.compile(
    r'^\s*([A-Za-z0-9_\-]+)\s*=\s*"?([^"\n{]*)', re.MULTILINE
)

goModRequirePattern = re.compile(
    r'^\s*([A-Za-z0-9_./\-]+)\s+(v[0-9][A-Za-z0-9.\-+]*)', re.MULTILINE
)

gemfileDepPattern = re.compile(
    r"^\s*gem\s+['\"]([A-Za-z0-9_.\-]+)['\"](?:,\s*['\"]([^'\"]+)['\"])?",
    re.MULTILINE,
)


def parseRequirementsTxt(content):
    deps = []

    for line in content.splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue

        match = requirementsLinePattern.match(stripped)

        if match:
            name = match.group(1)
            version = (match.group(2) or "").strip()
            deps.append({"name": name, "version": version or "unspecified"})

    return deps


def extractJsonDepBlock(content, blockName):
    marker = f'"{blockName}"'
    startIndex = content.find(marker)

    if startIndex == -1:
        return {}

    braceStart = content.find("{", startIndex)

    if braceStart == -1:
        return {}

    depth = 0
    endIndex = braceStart

    for index in range(braceStart, len(content)):
        if content[index] == "{":
            depth += 1
        elif content[index] == "}":
            depth -= 1

            if depth == 0:
                endIndex = index
                break

    block = content[braceStart:endIndex]

    return dict(packageJsonDepPattern.findall(block))


def parsePackageJson(content):
    deps = []

    for blockName in ("dependencies", "devDependencies", "peerDependencies"):
        found = extractJsonDepBlock(content, blockName)

        for name, version in found.items():
            deps.append({
                "name": name,
                "version": version or "unspecified",
                "scope": blockName,
            })

    return deps


def parsePyprojectToml(content):
    deps = []
    inDepsSection = False

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("["):
            inDepsSection = "dependencies" in stripped.lower()
            continue

        if not inDepsSection or not stripped or stripped.startswith("#"):
            continue

        match = pyprojectDepPattern.match(stripped)

        if match:
            name = match.group(1)
            version = match.group(2).strip()
            deps.append({"name": name, "version": version or "unspecified"})

    return deps


def parseCargoToml(content):
    deps = []
    inDepsSection = False

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("["):
            inDepsSection = "dependencies" in stripped.lower()
            continue

        if not inDepsSection or not stripped or stripped.startswith("#"):
            continue

        match = cargoDepPattern.match(stripped)

        if match:
            name = match.group(1)
            version = match.group(2).strip().strip(",")
            deps.append({"name": name, "version": version or "unspecified"})

    return deps


def parseGoMod(content):
    deps = []

    for name, version in goModRequirePattern.findall(content):
        deps.append({"name": name, "version": version})

    return deps


def parseGemfile(content):
    deps = []

    for name, version in gemfileDepPattern.findall(content):
        deps.append({"name": name, "version": version or "unspecified"})

    return deps


manifestParsers = {
    "requirements.txt": parseRequirementsTxt,
    "package.json": parsePackageJson,
    "pyproject.toml": parsePyprojectToml,
    "Cargo.toml": parseCargoToml,
    "go.mod": parseGoMod,
    "Gemfile": parseGemfile,
}


def parseManifest(fileName, content):
    parser = manifestParsers.get(fileName)

    if parser is None:
        return None

    return parser(content)[:maxDepsPerFile]


def buildDependencyContext(repoData):
    dependencyFiles = repoData["categories"].get("dependencies", [])

    parsableFiles = []
    skippedLockfiles = []
    unrecognizedFiles = []

    for file in dependencyFiles:
        fileName = file["path"].split("/")[-1]

        if fileName in skipLockfileNames:
            skippedLockfiles.append(file["path"])
        elif fileName in manifestParsers:
            parsableFiles.append(file)
        else:
            unrecognizedFiles.append(file["path"])

    parsablePaths = [f["path"] for f in parsableFiles]

    contents = fetchAll(
        parsablePaths,
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        fileCode
    )

    manifests = {}

    for file in parsableFiles:
        content = contents.get(file["path"])

        if content is None:
            continue

        fileName = file["path"].split("/")[-1]
        deps = parseManifest(fileName, content)

        if deps is not None:
            manifests[file["path"]] = {
                "dependencyCount": len(deps),
                "dependencies": deps,
            }

    return {
        "manifests": manifests,
        "lockfilesSkipped": skippedLockfiles,
        "unrecognizedDependencyFiles": unrecognizedFiles,
        "repoStats": repoData["fingerprint"],
    }