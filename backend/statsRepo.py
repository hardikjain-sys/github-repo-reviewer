from collections import Counter

fingerprint = {}

def stats(repoData):
    fingerprint["total_files"] = sum(
        len(files) for files in repoData["categories"].values()
    )

    fingerprint["source_files"] = len(repoData["categories"].get("source_code", []))
    fingerprint["test_files"] = len(repoData["categories"].get("tests", []))
    fingerprint["documentation_files"] = len(repoData["categories"].get("documentation", []))
    fingerprint["dependency_files"] = len(repoData["categories"].get("dependencies", []))
    fingerprint["config_files"] = len(repoData["categories"].get("configuration", []))
    fingerprint["ci_cd_files"] = len(repoData["categories"].get("ci_cd", []))

    fingerprint["has_tests"] = fingerprint["test_files"] > 0
    fingerprint["has_docs"] = fingerprint["documentation_files"] > 0
    fingerprint["has_ci"] = fingerprint["ci_cd_files"] > 0

    languages = Counter()

    for file in repoData["categories"].get("source_code", []):
        languages[file.get("language", "unknown")] += 1

    fingerprint["languages"] = dict(languages)

    return fingerprint

