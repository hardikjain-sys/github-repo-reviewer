
from rules import LANG
from pathlib import Path
import divideInCategory
import othersCategory
import batch
import statsRepo
import architecture
import documentation
import codeQuality
import dependency
import testing
from fetch import fetchAll, fileCode, getTree, fromUrl, session
from graphlangchain import graph
# url = ""
import asyncio

async def reviewRepo(url: str, deep: bool = False):
    owner, repo = fromUrl(url)
    urlForRequest = f"https://api.github.com/repos/{owner}/{repo}"
    response = session.get(urlForRequest)

    if response.status_code == 404:
        raise ValueError("Repository not found")

    if response.status_code == 403:
        raise ValueError("GitHub rate limit")

    if response.status_code != 200:
        raise ValueError("Some error occoured")

    data = response.json()

    data = response.json()
    branch = data["default_branch"]
    name = data.get("full_name", f"{owner}/{repo}")
    stars = data.get("stargazers_count", 0)
    # print(branch)

    files = getTree(owner,repo,branch)

    filesToSkip = [
        ".png",
        ".jpg",
        ".pdf",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".mp3",
        ".mp4",
        ".mov",
        ".zip",
        ".tar",
        ".gz",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".pyc",
        ".class",
        ".log"
    ]

    foldersToSkip = [
        ".git",
        "node_modules",
        "dist",
        "build",
        "assets",
        "coverage",
        ".venv",
        "venv",
        "__pycache__",
        ".cache",
        "target"
    ]

    goodContent = []

    otherPaths = []

    for path in files:
        if path['type'] == "blob":
            parts = Path(path['path']).parts
            if (Path(path['path']).suffix in filesToSkip) or (any(folder in foldersToSkip for folder in parts)):
                continue

            x = divideInCategory.category(path['path'])
            if x == "other":
                otherPaths.append(path['path'])
                goodContent.append({'path': path['path'], 'category': x})
            else:
                goodContent.append({'path': path['path'], 'category': x, 'size': path['size']})


    fetched = fetchAll(otherPaths, owner, repo, branch, 10, fileCode)

    for file in goodContent:
        if file["category"] == "other":
            file["content"] = fetched.get(file["path"])


    # print(goodContent)
    #
    category_counts = {}
    for file in goodContent:
        cat = file["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    others = [
        file["path"]
        for file in goodContent
        if file["category"] == "other"
    ]

    t=0
    otherList = []
    maxLen = 10


    for file in goodContent:
        if file["category"] == "other":
            content = file['content'].splitlines()[:maxLen]
            otherList.append({'path': file["path"], 'content': content})
            t += 1

    #
    # print(t, others, sep="\n")
    # print(category_counts)


    batches = batch.makeBatch(otherList, 50000)
    newCategories = []
    for b in batches:
        newCategories.extend(othersCategory.othersC(b))
    # print(newCategories)

    i = 0
    for file in goodContent:
        if file["category"] == "other":
            file["category"] = newCategories[i]
            i += 1
        if file["category"] in ("source_code", "tests"):
            suffix = Path(file["path"]).suffix.lower()
            file["language"] = LANG.get(suffix, "unknown")
            # print(file["language"], file["size"])



    repoData = {
        "metadata": {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "name": name,
            "stars": stars
        },
        "categories": {}
    }

    for file in goodContent:
        category = file["category"]

        if category not in repoData["categories"]:
            repoData["categories"][category] = []

        repoData["categories"][category].append(file)



    repoData["fingerprint"] = statsRepo.stats(repoData)


    contextArch = architecture.buildArchitectureContext(repoData)
    contextDoc = documentation.buildDocumentationContext(repoData)
    contextCode = codeQuality.buildCodeQualityContext(repoData)
    contextDependency = dependency.buildDependencyContext(repoData)
    contextTest = testing.buildTestingContext(repoData, mode="auto")
    from pprint import pprint
    pprint(contextArch)
    print("------------------------------------------------------")
    pprint(contextDoc)
    print("------------------------------------------------------")
    pprint(contextCode)
    print("------------------------------------------------------")
    pprint(contextDependency)
    print("------------------------------------------------------")
    pprint(contextTest)
    print("------------------------------------------------------")
    print("now diff")


    state = {
        "architecture_context": contextArch,
        "documentation_context": contextDoc,
        "codeQuality_context": contextCode,
        "dependency_context": contextDependency,
        "testing_context": contextTest,
    }
    #
    #
    result = await graph.ainvoke(state)

    # print(result)
    return {
        "success": True,
        "data": {
            "final_review": result["final_review"],
            "architecture_review": result["architecture_review"],
            "documentation_review": result["documentation_review"],
            "codeQuality_review": result["codeQuality_review"],
            "dependency_review": result["dependency_review"],
            "testing_review": result["testing_review"],
        }
    }

# asyncio.run(reviewRepo("https://github.com/hardikjain-sys/attention-and-sparsity", False))

