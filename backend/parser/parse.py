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
        p = Parser(LANGUAGES[language])
        _parsers[language] = p
    return _parsers[language]


LANGUAGE_CONFIG = {
    "python": {
        "function": {"types": ["function_definition"], "nameField": "name"},
        "class": {"types": ["class_definition"], "nameField": "name"},
        "import": {"types": ["import_statement", "import_from_statement"]},
        "global": {"types": ["assignment"], "topLevelOnly": True},
    },
    "javascript": {
        "function": {"types": ["function_declaration", "method_definition",
                               "arrow_function", "function"], "nameField": "name"},
        "class": {"types": ["class_declaration"], "nameField": "name"},
        "import": {"types": ["import_statement"]},
        "global": {"types": ["lexical_declaration", "variable_declaration"],
                   "topLevelOnly": True},
    },
    "typescript": {
        "function": {"types": ["function_declaration", "method_definition",
                               "arrow_function"], "nameField": "name"},
        "class": {"types": ["class_declaration", "interface_declaration"],
                  "nameField": "name"},
        "import": {"types": ["import_statement"]},
        "global": {"types": ["lexical_declaration"], "topLevelOnly": True},
    },
    "go": {
        "function": {"types": ["function_declaration", "method_declaration"],
                     "nameField": "name"},
        "struct": {"types": ["type_declaration"]},
        "import": {"types": ["import_declaration"]},
        "global": {"types": ["var_declaration", "const_declaration"],
                   "topLevelOnly": True},
    },
    "c": {
        "function": {"types": ["function_definition"]},
        "struct": {"types": ["struct_specifier"]},
        "enum": {"types": ["enum_specifier"]},
        "import": {"types": ["preproc_include"]},
        "macro": {"types": ["preproc_def"]},
        "global": {"types": ["declaration"], "topLevelOnly": True},
    },
    "cpp": {
        "function": {"types": ["function_definition"]},
        "class": {"types": ["class_specifier", "struct_specifier"]},
        "enum": {"types": ["enum_specifier"]},
        "import": {"types": ["preproc_include"]},
        "macro": {"types": ["preproc_def"]},
        "global": {"types": ["declaration"], "topLevelOnly": True},
    },
    "java": {
        "function": {"types": ["method_declaration", "constructor_declaration"],
                     "nameField": "name"},
        "class": {"types": ["class_declaration", "interface_declaration",
                            "enum_declaration"], "nameField": "name"},
        "import": {"types": ["import_declaration"]},
        "global": {"types": ["field_declaration"], "topLevelOnly": True},
    },
    "rust": {
        "function": {"types": ["function_item"], "nameField": "name"},
        "struct": {"types": ["struct_item", "enum_item", "trait_item",
                             "impl_item"], "nameField": "name"},
        "import": {"types": ["use_declaration"]},
        "global": {"types": ["static_item", "const_item"],
                   "topLevelOnly": True, "nameField": "name"},
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


def parseCode(content: str, language: str, filePath: str = "") -> dict | None:
    if language not in LANGUAGE_CONFIG:
        return None

    config = LANGUAGE_CONFIG[language]
    parser = getParser(language)
    tree = parser.parse(bytes(content, "utf8"))

    result = {
        "language": language,
        "filePath": filePath,
        "imports": [],
        "macros": [],
        "chunks": [],
    }

    typeToCategory = {}
    for category, spec in config.items():
        for t in spec["types"]:
            typeToCategory[t] = (category, spec)

    def isTopLevel(node):
        parent = node.parent
        return parent is not None and parent.parent is None

    def visit(node):
        catSpec = typeToCategory.get(node.type)

        if catSpec:
            category, spec = catSpec

            if spec.get("topLevelOnly") and not isTopLevel(node):
                pass
            elif category == "import":
                result["imports"].append(node.text.decode("utf-8", errors="ignore").strip())
                return
            elif category == "macro":
                result["macros"].append(node.text.decode("utf-8", errors="ignore").strip())
                return
            else:
                name = extractName(node, spec.get("nameField")) or "anonymous"

                parentClass = None
                currParent = node.parent
                while currParent:
                    if currParent.type in config.get("class", {}).get("types", []):
                        parentClass = extractName(currParent, config["class"].get("nameField"))
                        break
                    currParent = currParent.parent

                startLine = node.start_point[0] + 1
                endLine = node.end_point[0] + 1

                chunk = {
                    "type": category,
                    "name": name,
                    "parentClass": parentClass,
                    "startLine": startLine,
                    "endLine": endLine,
                    "lineCount": endLine - startLine + 1,
                }
                result["chunks"].append(chunk)

                if category == "class":
                    for child in node.children:
                        visit(child)
                return

        for child in node.children:
            visit(child)

    visit(tree.root_node)
    return result