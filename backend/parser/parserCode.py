import re
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_go
import tree_sitter_c
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_rust
import tree_sitter_typescript


def _lang(module, name="language"):
    return Language(getattr(module, name)())


LANGUAGES = {
    "python": _lang(tree_sitter_python),
    "javascript": _lang(tree_sitter_javascript),
    "go": _lang(tree_sitter_go),
    "c": _lang(tree_sitter_c),
    "cpp": _lang(tree_sitter_cpp),
    "java": _lang(tree_sitter_java),
    "rust": _lang(tree_sitter_rust),
    "typescript": Language(tree_sitter_typescript.language_typescript()),
}

_parsers = {}


def getParser(language: str) -> Parser:
    if language not in _parsers:
        _parsers[language] = Parser(LANGUAGES[language])
    return _parsers[language]


BRANCH_TYPES = {
    "if_statement", "if_expression", "switch_statement", "match_expression",
    "case_statement", "switch_case", "conditional_expression", "ternary_expression"
}
LOOP_TYPES = {
    "for_statement", "while_statement", "do_statement", "for_in_statement",
    "for_of_statement", "loop_expression", "while_expression", "for_expression"
}
TRY_TYPES = {"try_statement", "try_expression", "try_block"}
CALL_TYPES = {"call_expression", "method_invocation"}

LANGUAGE_CONFIG = {
    "python": {
        "function": {"types": ["function_definition"], "nameField": "name"},
        "class": {"types": ["class_definition"], "nameField": "name"},
        "import": {"types": ["import_statement", "import_from_statement"]},
    },
    "javascript": {
        "function": {"types": ["function_declaration", "method_definition", "arrow_function", "function"],
                     "nameField": "name"},
        "class": {"types": ["class_declaration"], "nameField": "name"},
        "import": {"types": ["import_statement"]},
    },
    "typescript": {
        "function": {"types": ["function_declaration", "method_definition", "arrow_function"], "nameField": "name"},
        "class": {"types": ["class_declaration", "interface_declaration"], "nameField": "name"},
        "import": {"types": ["import_statement"]},
    },
    "go": {
        "function": {"types": ["function_declaration", "method_declaration"], "nameField": "name"},
        "struct": {"types": ["type_declaration"]},
        "import": {"types": ["import_declaration"]},
    },
    "c": {
        "function": {"types": ["function_definition"]},
        "struct": {"types": ["struct_specifier"]},
        "import": {"types": ["preproc_include"]},
    },
    "cpp": {
        "function": {"types": ["function_definition"]},
        "class": {"types": ["class_specifier", "struct_specifier"]},
        "import": {"types": ["preproc_include"]},
    },
    "java": {
        "function": {"types": ["method_declaration", "constructor_declaration"], "nameField": "name"},
        "class": {"types": ["class_declaration", "interface_declaration", "enum_declaration"], "nameField": "name"},
        "import": {"types": ["import_declaration"]},
    },
    "rust": {
        "function": {"types": ["function_item"], "nameField": "name"},
        "struct": {"types": ["struct_item", "enum_item", "trait_item", "impl_item"], "nameField": "name"},
        "import": {"types": ["use_declaration"]},
    },
}


def extractName(node, nameField):
    if nameField:
        nameNode = node.child_by_field_name(nameField)
        if nameNode:
            return nameNode.text.decode("utf-8", errors="ignore")
    stack = list(node.children)
    while stack:
        cur = stack.pop(0)
        if cur.type in ("identifier", "type_identifier", "field_identifier"):
            return cur.text.decode("utf-8", errors="ignore")
        stack.extend(cur.children)
    return None


def analyzeBodyTelemetry(node, language: str) -> dict:
    metrics = {
        "pCount": 0,
        "cc": 1,
        "nest": 0,
        "br": 0,
        "lp": 0,
        "try": False,
        "hooks": 0
    }

    for child in node.children:
        if "parameter" in child.type or child.type == "parameters":
            metrics["pCount"] = len([c for c in child.children if c.is_named])
            break

    def walk(currNode, currentDepth):
        isControlStructure = False

        if currNode.type in BRANCH_TYPES:
            metrics["br"] += 1
            metrics["cc"] += 1
            isControlStructure = True
        elif currNode.type in LOOP_TYPES:
            metrics["lp"] += 1
            metrics["cc"] += 1
            isControlStructure = True
        elif currNode.type in TRY_TYPES:
            metrics["try"] = True
            isControlStructure = True
        elif currNode.type in CALL_TYPES:
            if language in ("javascript", "typescript"):
                fn = currNode.child_by_field_name("function")
                if fn and fn.type == "identifier":
                    fName = fn.text.decode("utf-8", errors="ignore")
                    if fName.startswith("use") and len(fName) > 3 and fName[3].isupper():
                        metrics["hooks"] += 1

        elif currNode.type in ("binary_expression", "logical_expression"):
            opNode = currNode.child_by_field_name("operator")
            if opNode:
                opText = opNode.text.decode("utf-8", errors="ignore")
                if opText in ("&&", "||", "and", "or"):
                    metrics["cc"] += 1

        nextDepth = currentDepth + (1 if isControlStructure else 0)
        metrics["nest"] = max(metrics["nest"], nextDepth)

        for child in currNode.children:
            walk(child, nextDepth)

    walk(node, 0)
    return metrics


def isMinified(content: str) -> bool:
    lines = content.splitlines()
    sampleLines = [l for l in lines[:15] if l.strip()]
    for line in sampleLines:
        if len(line) > 500:
            return True
    return False


def parseCode(content: str, language: str, filePath: str = "") -> dict | None:
    normalizedPath = filePath.lower().replace("\\", "/")
    ignoredPatterns = ["node_modules/", "dist/", "build/", "public/", ".next/", "vendor/", "bundle.js"]
    if any(pattern in normalizedPath for pattern in ignoredPatterns):
        return None

    if language not in LANGUAGE_CONFIG:
        return None

    if isMinified(content):
        return None

    config = LANGUAGE_CONFIG[language]
    parser = getParser(language)
    tree = parser.parse(bytes(content, "utf8"))
    lines = content.splitlines()

    result = {
        "language": language,
        "filePath": filePath,
        "totalLines": len(lines),
        "imports": [],
        "chunks": [],
    }

    typeToCategory = {}
    for category, spec in config.items():
        for t in spec["types"]:
            typeToCategory[t] = (category, spec)

    def visit(node, classCtx=None):
        catSpec = typeToCategory.get(node.type)

        if catSpec:
            category, spec = catSpec

            if category == "import":
                text = node.text.decode("utf-8", errors="ignore").strip()
                result["imports"].append(text)
                return

            name = extractName(node, spec.get("nameField")) or "anonymous"
            startLine = node.start_point[0] + 1
            endLine = node.end_point[0] + 1
            loc = endLine - startLine + 1

            chunk = {
                "type": category,
                "name": name,
                "startLine": startLine,
                "endLine": endLine,
                "loc": loc,
            }

            if classCtx:
                chunk["parentClass"] = classCtx

            if category == "function":
                if node.type.startswith("async"):
                    chunk["isAsync"] = True

                metrics = analyzeBodyTelemetry(node, language)

                if name == "anonymous" and loc <= 3 and metrics["cc"] <= 1:
                    return

                if loc <= 5 and metrics["cc"] <= 1 and metrics["nest"] <= 1:
                    return

                filteredMetrics = {
                    k: v
                    for k, v in metrics.items()
                    if v not in (0, False)
                }

                if filteredMetrics:
                    chunk["metrics"] = filteredMetrics

                if loc > 35 or metrics["cc"] > 6 or metrics["nest"] > 3:
                    preview = (
                            lines[node.start_point[0]: node.start_point[0] + 10]
                            + ["..."]
                            + lines[
                                max(node.end_point[0] - 4, node.start_point[0] + 10):
                                node.end_point[0] + 1
                            ]
                    )
                    chunk["preview"] = "\n".join(preview)

                result["chunks"].append(chunk)
                return

            elif category == "class":

                methodCount = 0

                if "function" in config:

                    functionTypes = set(config["function"]["types"])

                    for child in node.children:

                        if child.type in functionTypes:
                            methodCount += 1

                if methodCount:
                    chunk["methodCount"] = methodCount

                result["chunks"].append(chunk)

                for child in node.children:
                    visit(child, classCtx=name)

                return

        for child in node.children:
            visit(child, classCtx=classCtx)

    visit(tree.root_node)

    if len(result["chunks"]) > 50:
        result["chunks"] = [
            c
            for c in result["chunks"]
            if c.get("type") != "function"
               or c.get("metrics", {}).get("cc", 0) > 1
        ]

    return result