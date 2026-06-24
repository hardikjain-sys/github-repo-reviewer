from pathlib import Path
from collections import defaultdict
from dependencyParser import finalDependencies


from fetch import fetchAll, filePartial



ENTRY_POINT_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "main.c",
    "main.cpp"
    "manage.py",
    "index.js",
    "index.ts",
    "server.js",
    "server.ts",
    "main.go",
    "main.rs",
}


IMPORTANT_CONFIGS = {
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




from pathlib import Path


from collections import Counter


def important_file_previews(
    repoData,
    entry_points,
    important_configs,
    central_modules_list
):

    important_paths = set()

    important_paths.update(entry_points)

    important_paths.update(important_configs)

    for item in central_modules_list[:5]:
        important_paths.add(item["path"])

    previews = fetchAll(
        list(important_paths),
        repoData["metadata"]["owner"],
        repoData["metadata"]["repo"],
        repoData["metadata"]["branch"],
        10,
        lambda o, r, b, p: filePartial(
            o,
            r,
            b,
            p,
            maxBytes=4096
        )
    )

    return previews

def central_modules(graph):
    incoming = Counter()

    for deps in graph.values():
        for dep in deps["structure"]:
            incoming[dep] += 1

    result = []

    for module, count in incoming.most_common(10):
        result.append({
            "path": module,
            "incoming_dependencies": count
        })

    return result

def repo_stats(repoData):
    stats = {
        "total_files": 0,
        "source_files": 0,
        "test_files": 0,
        "documentation_files": 0,
        "configuration_files": 0,
        "languages": Counter()
    }

    for category, files in repoData["categories"].items():

        stats["total_files"] += len(files)

        if category == "source_code":
            stats["source_files"] = len(files)

        elif category == "tests":
            stats["test_files"] = len(files)

        elif category == "documentation":
            stats["documentation_files"] = len(files)

        elif category == "configuration":
            stats["configuration_files"] = len(files)

        for file in files:
            if "language" in file:
                stats["languages"][file["language"]] += 1

    stats["languages"] = dict(stats["languages"])

    return stats

def build_module_lookup(repoData):
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


def resolve_dependency_graph(import_graph, repoData):
    lookup = build_module_lookup(repoData)

    graph = {}

    for file in repoData["categories"].get("source_code", []):
        path = file["path"]

        imports = import_graph.get(path, [])

        internal_deps = []
        external_deps = []

        for imp in imports:

            resolved = None

            if imp in lookup:
                resolved = lookup[imp]

            else:
                imp_last = imp.split(".")[-1]

                if imp_last in lookup:
                    resolved = lookup[imp_last]

            if resolved:
                internal_deps.append(resolved)
            else:
                internal_deps.append(imp)

        graph[path] = {
            "structure": sorted(set(internal_deps))
        }

    return graph

def build_dependency_graph(repoData, contents):

    graph = {}

    for file in repoData["categories"].get("source_code", []):

        content = contents.get(file["path"])

        if content is None:
            continue

        deps = finalDependencies(
            file["language"],
            content
        )

        graph[file["path"]] = deps

    return graph


def build_directory_tree(repoData):
    tree = {}

    for category in repoData["categories"].values():
        for file in category:
            current = tree

            for part in Path(file["path"]).parts:
                current = current.setdefault(part, {})

    return tree


def get_entry_points(repoData):
    entry_points = []

    for category in repoData["categories"].values():
        for file in category:
            name = Path(file["path"]).name

            if name in ENTRY_POINT_NAMES:
                entry_points.append(file["path"])

    return sorted(entry_points)


def get_important_configs(repoData):
    configs = []

    for category in repoData["categories"].values():
        for file in category:
            name = Path(file["path"]).name

            if name in IMPORTANT_CONFIGS:
                configs.append(file["path"])

    return sorted(configs)

def build_architecture_context(repoData):


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

    raw_graph = build_dependency_graph(
        repoData,
        contents
    )

    dependency_graph = resolve_dependency_graph(
        raw_graph,
        repoData
    )

    entry_points = get_entry_points(repoData)

    important_configs = get_important_configs(repoData)

    central = central_modules(
        dependency_graph
    )

    return {
        "directory_tree": build_directory_tree(repoData),

        "entry_points": entry_points,

        "important_configs": important_configs,

        "module_dependency_graph": dependency_graph,

        "repo_stats": repo_stats(repoData),

        "central_modules": central,

        "important_file_previews": important_file_previews(
            repoData,
            entry_points,
            important_configs,
            central
        )
    }

