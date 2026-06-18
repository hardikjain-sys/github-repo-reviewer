RULES = {
    "ci_cd": {
        "exact_names": [
            ".pre-commit-config.yaml", ".pre-commit-config.yml",
            "Jenkinsfile", "appveyor.yml", "bitbucket-pipelines.yml",
            "azure-pipelines.yml", "cloudbuild.yaml", "cloudbuild.yml",
            ".travis.yml", ".drone.yml", ".woodpecker.yml", "codeship-steps.yml",
            "circle.yml", ".gitlab-ci.yml", "gitlab-ci.yml",
            ".releaserc", ".releaserc.json", ".releaserc.yml",
            "release.config.js", "cliff.toml", "goreleaser.yml", "goreleaser.yaml"
        ],
        "folder_prefixes": [
            ".github/workflows/", ".github/actions/", ".github/ISSUE_TEMPLATE/",
            ".circleci/", ".buildkite/"
        ],
        "extensions": [],
        "suffixes": [".jenkinsfile"],
        "contains": []
    },
    "tests": {
        "exact_names": [
            "jest.setup.js", "jest.setup.ts", "vitest.setup.ts",
            "setupTests.js", "setupTests.ts", "cypress.json",
            "playwright.config.ts", "playwright.config.js", "pytest.ini"
        ],
        "folder_prefixes": [
            "test/", "tests/", "__tests__/", "spec/", "specs/",
            "e2e/", "integration/", "unit/", "cypress/", "playwright/",
            "jest/", "fixtures/", "mocks/", "__mocks__/"
        ],
        "extensions": [],
        "suffixes": [
            ".test.js", ".spec.js", ".test.ts", ".spec.ts",
            ".test.jsx", ".spec.jsx", ".test.tsx", ".spec.tsx",
            ".test.py", "_test.py", "_test.go", "Test.java", "Spec.rb"
        ],
        "contains": []
    },
    "dependencies": {
        "exact_names": [
            "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            ".npmrc", ".nvmrc", ".node-version",
            "requirements.txt", "requirements-dev.txt",
            "Pipfile", "Pipfile.lock", "pyproject.toml",
            "setup.py", "setup.cfg", "poetry.lock", "uv.lock",
            "Gemfile", "Gemfile.lock",
            "go.mod", "go.sum",
            "Cargo.toml", "Cargo.lock",
            "pom.xml", "build.gradle", "build.gradle.kts",
            "composer.json", "composer.lock", "packages.config",
            ".tool-versions", "mix.exs", "mix.lock",
            "pubspec.yaml", "pubspec.lock",
            "deno.json", "deno.lock",
            "Brewfile", "Brewfile.lock.json"
        ],
        "folder_prefixes": ["node_modules/"],
        "extensions": [],
        "suffixes": [".csproj", ".sln"],
        "contains": []
    },
    "configuration": {
        "exact_names": [
            "CMakeLists.txt",
            ".readthedocs.yaml", ".readthedocs.yml",
            "vite.config.js", "vite.config.ts",
            "webpack.config.js", "rollup.config.js",
            "babel.config.js", "babel.config.json", ".babelrc",
            "tsconfig.json", "jsconfig.json",
            "next.config.js", "next.config.ts",
            "nuxt.config.ts", "nuxt.config.js",
            "svelte.config.js", "astro.config.mjs",
            "eslint.config.js", ".eslintrc", ".eslintrc.js",
            ".eslintrc.json", ".eslintrc.yml", ".eslintignore",
            "prettier.config.js", ".prettierrc", ".prettierrc.js",
            ".prettierrc.json", ".prettierrc.yml", ".prettierignore",
            "stylelint.config.js", ".stylelintrc", "biome.json",
            ".editorconfig",
            ".env", ".env.example", ".env.sample", ".env.template",
            "tailwind.config.js", "tailwind.config.ts",
            "postcss.config.js", "postcss.config.ts",
            "jest.config.js", "jest.config.ts",
            "vitest.config.ts", "vitest.config.js",
            "app.config.js", "app.config.ts",
            "config.json", "config.yaml", "config.yml", "settings.json",
            "Dockerfile", ".dockerignore",
            "docker-compose.yml", "docker-compose.yaml",
            "serverless.yml", "serverless.yaml",
            "fly.toml", "render.yaml", "netlify.toml", "vercel.json",
            ".gitignore", ".gitattributes", ".gitmodules", ".npmignore",
            "Makefile", "makefile", "GNUmakefile",
            ".vscode/settings.json"
        ],
        "folder_prefixes": [".vscode/", ".idea/",".devcontainer/"],
        "extensions": [".conf", ".ini", ".cfg", ".hcl", ".tfvars"],
        "suffixes": [
            ".config.js", ".config.ts", ".config.mjs", ".config.cjs",
            ".tf", ".toml"
        ],
        "contains": [".env."]
    },
    "documentation": {
        "exact_names": [
            "README", "README.md", "README.rst", "README.txt",
            "CHANGELOG", "CHANGELOG.md", "CHANGELOG.rst",
            "CONTRIBUTING", "CONTRIBUTING.md",
            "LICENSE", "LICENSE.md", "LICENSE.txt",
            "CODE_OF_CONDUCT.md", "SECURITY.md", "NOTICE",
            "AUTHORS", "CODEOWNERS", "FUNDING.yml",
            "ARCHITECTURE.md", "ROADMAP.md", "FAQ.md",
            "INSTALL.md", "USAGE.md", "SUPPORT.md"
        ],
        "folder_prefixes": [
            "docs/", "doc/", "documentation/",
            "wiki/", "guides/", "manuals/", "pages/", "site/"
        ],
        "extensions": [".md", ".mdx", ".rst", ".adoc", ".wiki", ".pod"],
        "suffixes": [],
        "contains": []
    },
    "source_code": {
        "exact_names": [],
        "folder_prefixes": [
            "src/", "lib/", "app/", "core/", "internal/", "pkg/",
            "cmd/", "api/", "server/", "client/", "frontend/",
            "backend/", "services/", "contracts/", "scripts/"
        ],
        "extensions": [
            ".cu",
            ".cuh",
            ".hpp",
            ".hh",
            ".hxx",
            ".cc",
            ".cxx",
            ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
            ".vue", ".svelte", ".astro",
            ".py", ".rb", ".php", ".java", ".go", ".rs",
            ".cs", ".cpp", ".c", ".h", ".swift", ".kt",
            ".scala", ".ex", ".exs", ".clj", ".hs", ".lua",
            ".dart", ".r", ".m", ".jl",
            ".html", ".htm", ".css", ".scss", ".sass", ".less", ".styl",
            ".sol", ".vy",
            ".sh", ".bash", ".zsh", ".fish", ".ps1", ".psm1",
            ".sql", ".graphql", ".gql", ".proto"
        ],
        "suffixes": [],
        "contains": []
    },
    "skip": {
        "exact_names": [".DS_Store", "Thumbs.db"],
        "folder_prefixes": [
            "dist/", "build/", "out/", "target/", ".next/", ".nuxt/",
            "coverage/", "public/", "assets/", "static/",
            "images/", "fonts/", "media/"
        ],
        "extensions": [
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
            ".woff", ".woff2", ".ttf", ".otf", ".eot",
            ".csv", ".xml", ".parquet", ".db", ".sqlite", ".geojson",
            ".map", ".iml"
        ],
        "suffixes": [
            ".min.js", ".min.css", ".bundle.js",
            ".code-workspace", ".sublime-project"
        ],
        "contains": []
    }
}