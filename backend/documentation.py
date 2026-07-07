import re

from fetch import fetchAll, fileCode, filePartial


maxDocBytes = 1000
maxConfigBytes = 600

headingPattern = re.compile(r"^#{1,3}\s+(.+)", re.MULTILINE)

keySectionKeywords = {
    "install": "installation",
    "setup": "installation",
    "getting started": "installation",
    "quickstart": "installation",
    "quick start": "installation",
    "prerequisite": "installation",
    "requirements": "installation",
    "usage": "usage",
    "example": "usage",
    "how to use": "usage",
    "tutorial": "usage",
    "guide": "usage",
    "contribut": "contributing",
    "development": "contributing",
    "developing": "contributing",
    "code of conduct": "contributing",
    "pull request": "contributing",
    "test": "testing",
    "ci": "testing",
    "continuous integration": "testing",
    "license": "license",
    "copyright": "license",
    "api": "apiReference",
    "reference": "apiReference",
    "documentation": "apiReference",
    "configuration": "configurationDocs",
    "config": "configurationDocs",
    "environment variable": "configurationDocs",
    "deploy": "deployment",
    "docker": "deployment",
    "faq": "faq",
    "troubleshoot": "faq",
    "changelog": "changelog",
    "roadmap": "roadmap",
    "architecture": "architecture",
    "security": "security",
}

skipConfigNames = {
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

maxConfigFilesDetailed = 10
maxDocFilesDetailed = 8


def extractHeadings(content):
    return [h.strip() for h in headingPattern.findall(content)]


def classifySections(headings):
    found = set()

    for heading in headings:
        lowered = heading.lower()

        for keyword, label in keySectionKeywords.items():
            if keyword in lowered:
                found.add(label)

    return sorted(found)


def excerptBody(content, maxChars=maxDocBytes):
    stripped = content.strip()

    if len(stripped) <= maxChars:
        return stripped

    return stripped[:maxChars] + "..."


def summarizeDocFile(path, content):
    headings = extractHeadings(content)

    return {
        "path": path,
        "lengthChars": len(content),
        "headings": headings,
        "sectionsPresent": classifySections(headings),
        "excerpt": excerptBody(content),
    }


def rankDocFiles(documentation):
    def priority(file):
        name = file["path"].lower()

        if "readme" in name:
            return 0
        if "contributing" in name:
            return 1
        return 2

    return sorted(documentation, key=priority)


def summarizeConfigFile(path, content):
    return {
        "path": path,
        "lengthChars": len(content),
        "excerpt": excerptBody(content, maxConfigBytes),
    }


def buildDocumentationContext(repoData):
    documentation = repoData["categories"].get("documentation", [])
    configuration = repoData["categories"].get("configuration", [])

    rankedDocs = rankDocFiles(documentation)
    detailedDocs = rankedDocs[:maxDocFilesDetailed]
    remainingDocs = rankedDocs[maxDocFilesDetailed:]

    detailedDocPaths = [f["path"] for f in detailedDocs]

    documentationContents = fetchAll(
        detailedDocPaths,
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        lambda o, r, b, p: filePartial(o, r, b, p, maxBytes=4000)
    )

    documentationSummaries = []

    for file in detailedDocs:
        content = documentationContents.get(file["path"])

        if content is None:
            continue

        documentationSummaries.append(summarizeDocFile(file["path"], content))

    filteredConfigs = [
        f for f in configuration
        if f["path"].split("/")[-1] not in skipConfigNames
    ]

    skippedConfigs = [
        f["path"] for f in configuration
        if f["path"].split("/")[-1] in skipConfigNames
    ]

    detailedConfigs = filteredConfigs[:maxConfigFilesDetailed]
    remainingConfigs = filteredConfigs[maxConfigFilesDetailed:]

    detailedConfigPaths = [f["path"] for f in detailedConfigs]

    configurationContents = fetchAll(
        detailedConfigPaths,
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        lambda o, r, b, p: filePartial(o, r, b, p, maxBytes=maxConfigBytes)
    )

    configurationSummaries = []

    for file in detailedConfigs:
        content = configurationContents.get(file["path"])

        if content is None:
            continue

        configurationSummaries.append(summarizeConfigFile(file["path"], content))

    return {
        "documentation": documentationSummaries,
        "documentationFilesOmitted": [f["path"] for f in remainingDocs],
        "configuration": configurationSummaries,
        "configurationFilesOmitted": [f["path"] for f in remainingConfigs],
        "configurationFilesSkippedAsLockfiles": skippedConfigs,
        "repoStats": repoData["fingerprint"],
    }