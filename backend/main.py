
from rules import LANG
from pathlib import Path
import divideInCategory
import othersCategory
import batch
import statsRepo
import architecture

from fetch import fetchAll, filePartial,fileCode, getTree, fromUrl, session

url = "https://github.com/hardikjain-sys/bitboard-chess-engine"


owner, repo = fromUrl(url)
urlForRequest = f"https://api.github.com/repos/{owner}/{repo}"
response = session.get(urlForRequest)
data = response.json()
branch = data["default_branch"]
print(branch)

files = getTree(owner,repo,branch)

filesToSkip = [
    ".png",
    ".jpg",
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


print(t, others, sep="\n")
print(category_counts)


batches = batch.makeBatch(otherList, 50000)
newCategories = []
for b in batches:
    newCategories.extend(othersCategory.othersC(b))
print(newCategories)

i = 0
for file in goodContent:
    if file["category"] == "other":
        file["category"] = newCategories[i]
        i += 1
    if file["category"] == "source_code":
        suffix = Path(file["path"]).suffix.lower()
        file["language"] = LANG.get(suffix, "unknown")
        # print(file["language"], file["size"])



repoData = {
    "metadata": {
        "owner": owner,
        "repo": repo,
        "branch": branch
    },
    "categories": {}
}

for file in goodContent:
    category = file["category"]

    if category not in repoData["categories"]:
        repoData["categories"][category] = []

    repoData["categories"][category].append(file)



repoData["fingerprint"] = statsRepo.stats(repoData)

for file in goodContent:
    if file['category'] == 'source_code':
        break


context = architecture.build_architecture_context(repoData)

from pprint import pprint
pprint(context)
# print(architecture.build_architecture_context(repoData))

