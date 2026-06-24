from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urlparse
import os
session = requests.Session()
token = os.getenv("GITAUTH")
if token:
    session.headers.update({"Authorization": f"Bearer {token}"})




def fetchAll(paths, owner, repo, branch, workers, fetchFn):
    out = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {
            ex.submit(fetchFn, owner, repo, branch, p): p
            for p in paths
        }

        for f in as_completed(futs):
            out[futs[f]] = f.result()

    return out



def filePartial(own, rep, wBranch, path, maxBytes=512):
    u = f"https://raw.githubusercontent.com/{own}/{rep}/{wBranch}/{path}"

    r = session.get(
        u,
        headers={"Range": f"bytes=0-{maxBytes-1}"}
    )

    if r.status_code not in (200, 206):
        print('error')
        return None

    return r.text


def fileCode(own, rep, wBranch, path, maxBytes=300_000):
    u = f"https://raw.githubusercontent.com/{own}/{rep}/{wBranch}/{path}"
    r = session.get(u)
    if r.status_code != 200:
        return None
    if len(r.content) > maxBytes:
        print('big size')
        return r.text[:maxBytes]
    return r.text


def getTree(own, rep, wBranch):
    u = f"https://api.github.com/repos/{own}/{rep}/git/trees/{wBranch}?recursive=1"
    d = session.get(u).json()
    if d.get("truncated"):
       print("tree truncated")

    return d["tree"]


def fromUrl(url):
    parts = urlparse(url).path.strip("/").split("/")
    owner = parts[0]
    repo  = parts[1]
    return owner, repo

