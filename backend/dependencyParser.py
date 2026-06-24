from pathlib import Path
import ast
import re


def python_dependencies(content):
    deps = []

    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    deps.append(name.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    deps.append(node.module)

    except Exception:
        pass

    return deps


def c_dependencies(content):
    return re.findall(r'#include\s+"([^"]+)"', content)


def cpp_dependencies(content):
    return re.findall(r'#include\s+"([^"]+)"', content)


def js_dependencies(content):
    deps = []

    deps.extend(
        re.findall(
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            content
        )
    )

    deps.extend(
        re.findall(
            r'require\([\'"]([^\'"]+)[\'"]\)',
            content
        )
    )

    return deps


def java_dependencies(content):
    return re.findall(
        r'import\s+([a-zA-Z0-9_.]+);',
        content
    )


LANGUAGE_PARSERS = {
    "python": python_dependencies,
    "c": c_dependencies,
    "cpp": cpp_dependencies,
    "javascript": js_dependencies,
    "typescript": js_dependencies,
    "java": java_dependencies,
}


def finalDependencies(language, content):
    parser = LANGUAGE_PARSERS.get(language)

    if parser is None:
        return []

    return parser(content)