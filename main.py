import requests
import json
from pathlib import Path
from urllib.parse import urlparse
import divideInCategory
import othersCategory
import batch

def fromUrl(url):
    parts = urlparse(url).path.strip("/").split("/")
    owner = parts[0]
    repo  = parts[1]
    return owner, repo


def fileCode(own, rep, wBranch, path):
    u = f"https://raw.githubusercontent.com/{own}/{rep}/{wBranch}/{path}"
    r = requests.get(u)
    return r.text if r.status_code == 200 else None


url = "https://github.com/hardikjain-sys/github-repo-reviewer"

owner, repo = fromUrl(url)
urlForRequest = f"https://api.github.com/repos/{owner}/{repo}"
response = requests.get(urlForRequest)
data = response.json()
branch = data["default_branch"]
print(branch)
# language    = data["language"]
# stars       = data["stargazers_count"]
# forks       = data["forks_count"]
# issues      = data["open_issues_count"]
# created     = data["created_at"]
# lastPush   = data["pushed_at"]

def getTree(own, rep, wBranch):
    u = f"https://api.github.com/repos/{own}/{rep}/git/trees/{wBranch}?recursive=1"
    d = requests.get(u).json()
    return d["tree"]

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

for path in files:
    if path['type'] == "blob":
        parts = Path(path['path']).parts
        if (Path(path['path']).suffix in filesToSkip) or (any(folder in foldersToSkip for folder in parts)):
            # print("skipped", path['path'])
            continue
        else:
            x = divideInCategory.category(path['path'])
            if x == "other":
                goodContent.append({
                    'path': path['path'],
                    'category': x,
                    'content': fileCode(owner, repo, branch, path['path'])
                })
            else:
                goodContent.append({
                    'path': path['path'],
                    'category': x,
                })
            # print(path['path'])


# print(goodContent)

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

print(goodContent)