"""Guard: the shipped runtime surface of A11oy Factory is Python.

Two artifacts ship from this repository, and both are Python:

* the PyPI wheel ``a11oy-factory`` (pyproject.toml);
* the Hugging Face Space Docker image (Dockerfile).

The TanStack/React console under ``src/`` is not deployed by anything in this
repository. This module checks, from the checked-in files only, that:

* the Dockerfile builds from Python base images, installs and runs no Node
  toolchain, and COPYs no ``src/``, Node manifest or TypeScript/Node module;
* the wheel packages only ``a11oy_factory`` and that package holds no
  TypeScript/Node module;
* every ``src/lib/*.ts`` module (``*.test.ts`` excluded) is listed in
  ``TS_MODULE_INVENTORY`` with its ``a11oy_factory`` Python counterpart or
  marked ``TS_ONLY``.

The inventory is input to the owner decision on the console. A listed
counterpart means the same job has a Python home; behavioural parity is not
tested here.

Not checked: the image is not built, the published Space and PyPI release are
not read, and the Space repository upload (which still carries ``src/`` as
source files) is out of scope. Only the image built from the Dockerfile is.
"""

from __future__ import annotations

import json
import posixpath
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_NAME = "a11oy_factory"
PACKAGE_DIR = ROOT / PACKAGE_NAME
TS_LIB = ROOT / "src" / "lib"

# Executables and package sources that install or run a JavaScript runtime.
# Words are matched whole, after splitting on anything but letters, digits, "_" and "+".
NODE_TOOLS = frozenset(
    {
        "bun",
        "bunx",
        "corepack",
        "deno",
        "node",
        "nodeenv",
        "nodejs",
        "nodesource",
        "npm",
        "npx",
        "nvm",
        "pnpm",
        "pnpx",
        "tsx",
        "volta",
        "yarn",
        "yarnpkg",
    }
)
# Files that only a Node toolchain reads.
NODE_MANIFESTS = frozenset(
    {
        ".node_modules.lock",
        ".npmrc",
        ".nvmrc",
        "bun.lock",
        "bun.lockb",
        "npm-shrinkwrap.json",
        "package-lock.json",
        "package.json",
        "pnpm-lock.yaml",
        "tsconfig.json",
        "yarn.lock",
    }
)
# TypeScript sources and Node module formats. Plain .js and .css browser assets
# are not listed: a static file served by the Python server is not a Node runtime.
NODE_SOURCE_SUFFIXES = frozenset({".cjs", ".cts", ".jsx", ".mjs", ".mts", ".ts", ".tsx"})
# Directories whose contents must never reach the image.
EXCLUDED_DIRS = frozenset({"node_modules", "src"})

DOCKER_INSTRUCTIONS = frozenset(
    {
        "ADD",
        "ARG",
        "CMD",
        "COPY",
        "ENTRYPOINT",
        "ENV",
        "EXPOSE",
        "FROM",
        "HEALTHCHECK",
        "LABEL",
        "MAINTAINER",
        "ONBUILD",
        "RUN",
        "SHELL",
        "STOPSIGNAL",
        "USER",
        "VOLUME",
        "WORKDIR",
    }
)
# Instructions whose arguments are executed in the image.
EXECUTING_INSTRUCTIONS = frozenset({"CMD", "ENTRYPOINT", "HEALTHCHECK", "RUN", "SHELL"})
PYTHON_EXECUTABLE = re.compile(r"^python(?:3(?:\.\d+)?)?$")

PYTHON_COUNTERPART = "PYTHON_COUNTERPART"
TS_ONLY = "TS_ONLY"

# src/lib/<module>.ts -> (class, a11oy_factory counterpart or None, note).
# Classified by reading both trees at 4a5f2308. Add a row for every new module.
TS_MODULE_INVENTORY: dict[str, tuple[str, str | None, str]] = {
    "admission.ts": (TS_ONLY, None, "owner admission order and browser-stored approval receipts"),
    "compiler.ts": (
        TS_ONLY,
        None,
        "vertical-cell manifest compiler over src/lib/data/profile.json; "
        "a11oy_factory/compiler.py shares the name but is the Decision Cell Compiler",
    ),
    "db.ts": (TS_ONLY, None, "console database adapter (Neon or PGlite)"),
    "forge.ts": (TS_ONLY, None, "browser-stored scenario forge"),
    "frontier.ts": (TS_ONLY, None, "console frontier acceptance checks over vertical cells, ledger and forge"),
    "hash.ts": (
        PYTHON_COUNTERPART,
        "a11oy_factory/distribution_common.py",
        "canonical JSON and SHA-256 (canonical_bytes, digest_json); byte parity not tested",
    ),
    "hf-space-observation.ts": (TS_ONLY, None, "reads the generated Hub Space inventory"),
    "honest.ts": (TS_ONLY, None, "console honesty contract"),
    "ledger.ts": (TS_ONLY, None, "browser-stored hash-chained decision ledger"),
    "organ-ledger.ts": (TS_ONLY, None, "browser-stored organ receipts"),
    "organs.ts": (
        PYTHON_COUNTERPART,
        "a11oy_factory/organs.py",
        "same N-series organs, not parity: organs.ts lists N1-N25 with honesty LIVE, "
        "organs.py covers N1-N27 fail closed and never LIVE",
    ),
    "policy.ts": (TS_ONLY, None, "scenario policy evaluation (LOG_ONLY / ENFORCE)"),
    "preview-embedder-origin.ts": (TS_ONLY, None, "browser preview embedder allowlist"),
    "preview-host-bridge.ts": (TS_ONLY, None, "browser preview postMessage bridge"),
    "receipt-selection.ts": (TS_ONLY, None, "UI state helper"),
    "scenarios.ts": (TS_ONLY, None, "synthetic scenario fixtures for the console"),
    "spaces.ts": (TS_ONLY, None, "Space configuration and release plan"),
    "types.ts": (TS_ONLY, None, "type declarations"),
    "use-mount-snapshot.ts": (TS_ONLY, None, "React hook"),
    "utils.ts": (TS_ONLY, None, "UI formatting helpers"),
}


def dockerfile_instructions(text: str) -> list[tuple[str, str]]:
    """Return (INSTRUCTION, arguments) pairs with line continuations joined."""

    lines = text.splitlines()
    escape = "\\"
    for line in lines:
        directive = re.match(r"^\s*#\s*([A-Za-z]+)\s*=\s*(\S+)\s*$", line)
        if directive is None:
            break
        if directive.group(1).lower() == "escape":
            escape = directive.group(2)
    joined: list[str] = []
    pending = ""
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith(escape):
            pending += stripped[: -len(escape)] + " "
            continue
        joined.append(pending + stripped)
        pending = ""
    if pending.strip():
        joined.append(pending.strip())
    instructions: list[tuple[str, str]] = []
    for line in joined:
        keyword, _, arguments = line.partition(" ")
        keyword = keyword.upper()
        if keyword == "ONBUILD":
            keyword, _, arguments = arguments.strip().partition(" ")
            keyword = keyword.upper()
        instructions.append((keyword, arguments.strip()))
    return instructions


def split_flags(arguments: str) -> tuple[dict[str, str], str]:
    """Split leading --name=value flags from the rest of an instruction."""

    flags: dict[str, str] = {}
    rest = arguments.strip()
    while rest.startswith("--"):
        token, _, rest = rest.partition(" ")
        name, _, value = token[2:].partition("=")
        flags[name.lower()] = value
        rest = rest.lstrip()
    return flags, rest


def from_stages(instructions: list[tuple[str, str]]) -> list[tuple[str, str | None]]:
    """(image, stage alias) for every FROM, flags removed."""

    stages: list[tuple[str, str | None]] = []
    for keyword, arguments in instructions:
        if keyword != "FROM":
            continue
        words = split_flags(arguments)[1].split()
        image = words[0] if words else ""
        alias = words[2].lower() if len(words) >= 3 and words[1].lower() == "as" else None
        stages.append((image, alias))
    return stages


def command_words(arguments: str) -> list[str]:
    """Exec form (JSON array) or shell form, as argv-like words."""

    stripped = arguments.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
    return stripped.split()


def node_tool_hits(arguments: str) -> set[str]:
    words = {word.lower() for word in re.split(r"[^A-Za-z0-9_+]+", arguments) if word}
    return words & NODE_TOOLS


def shipped_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(
            item
            for item in path.rglob("*")
            if item.is_file() and "__pycache__" not in item.relative_to(ROOT).parts
        )
    return [path]


def console_or_node_reason(file: Path) -> str | None:
    rel = file.relative_to(ROOT)
    if rel.parts[0] in EXCLUDED_DIRS or "node_modules" in rel.parts:
        return f"{rel.as_posix()} (console or Node dependency source)"
    if file.name in NODE_MANIFESTS:
        return f"{rel.as_posix()} (Node manifest)"
    if file.suffix.lower() in NODE_SOURCE_SUFFIXES:
        return f"{rel.as_posix()} (TypeScript/Node module)"
    return None


class DockerImageIsPythonTests(unittest.TestCase):
    """The Space image built from the Dockerfile carries no Node runtime and no src/."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructions = dockerfile_instructions(DOCKERFILE.read_text(encoding="utf-8"))
        cls.stages = from_stages(cls.instructions)

    def test_dockerfile_uses_only_instructions_this_guard_reads(self) -> None:
        # Fails closed on syntax the parser does not follow, such as heredoc bodies.
        unknown = [keyword for keyword, _ in self.instructions if keyword not in DOCKER_INSTRUCTIONS]
        self.assertEqual(unknown, [], "Dockerfile has instructions this guard cannot read")
        self.assertTrue(self.stages, "Dockerfile has no FROM")

    def test_every_base_image_is_python(self) -> None:
        earlier_stages: set[str] = set()
        for image, alias in self.stages:
            self.assertTrue(image, "FROM without an image")
            if image.lower() not in earlier_stages:
                repository = image.split("@", 1)[0]
                name = repository.rsplit("/", 1)[-1].split(":", 1)[0].lower()
                self.assertEqual(name, "python", f"FROM {image}: the base image is not a Python image")
            if alias:
                earlier_stages.add(alias)

    def test_no_instruction_installs_or_runs_node(self) -> None:
        for keyword, arguments in self.instructions:
            if keyword in EXECUTING_INSTRUCTIONS:
                hits = node_tool_hits(arguments)
                self.assertFalse(hits, f"{keyword} {arguments!r} names a Node tool: {sorted(hits)}")

    def test_container_process_is_python(self) -> None:
        entrypoints = [arguments for keyword, arguments in self.instructions if keyword == "ENTRYPOINT"]
        commands = [arguments for keyword, arguments in self.instructions if keyword == "CMD"]
        final = entrypoints[-1] if entrypoints else (commands[-1] if commands else None)
        self.assertIsNotNone(final, "the image must declare its own CMD or ENTRYPOINT")
        argv = command_words(final)
        self.assertTrue(argv, "empty CMD/ENTRYPOINT")
        executable = posixpath.basename(argv[0])
        self.assertRegex(executable, PYTHON_EXECUTABLE, f"the container process {argv!r} is not Python")

    def test_copy_sources_exclude_src_and_node(self) -> None:
        stage_refs = {str(index) for index in range(len(self.stages))}
        stage_refs.update(alias for _, alias in self.stages if alias)
        copied_roots: set[str] = set()
        for keyword, arguments in self.instructions:
            if keyword not in {"ADD", "COPY"}:
                continue
            flags, rest = split_flags(arguments)
            words = command_words(rest)
            self.assertGreaterEqual(len(words), 2, f"{keyword} {arguments!r} has no source")
            if "from" in flags:
                self.assertIn(
                    flags["from"].lower(),
                    stage_refs,
                    f"{keyword} --from={flags['from']} copies from an image outside this Dockerfile",
                )
                continue
            for source in words[:-1]:
                self.assertNotRegex(
                    source, r"^[A-Za-z][A-Za-z0-9+.-]*://|^git@", f"{keyword} {source!r} fetches a remote source"
                )
                self.assertNotIn("$", source, f"{keyword} {source!r} uses a variable this guard cannot resolve")
                relative = source.lstrip("/")
                normalized = posixpath.normpath(relative) if relative else "."
                self.assertNotEqual(
                    normalized, ".", f"{keyword} {source!r} copies the whole build context, which holds src/"
                )
                self.assertFalse(normalized.startswith(".."), f"{keyword} {source!r} leaves the build context")
                if any(char in normalized for char in "*?["):
                    matches = sorted(ROOT.glob(normalized))
                else:
                    matches = [ROOT / normalized] if (ROOT / normalized).exists() else []
                self.assertTrue(matches, f"{keyword} {source!r} does not exist in the repository")
                for match in matches:
                    copied_roots.add(match.relative_to(ROOT).as_posix())
                    for file in shipped_files(match):
                        reason = console_or_node_reason(file)
                        self.assertIsNone(reason, f"{keyword} {source!r} ships {reason}")
        self.assertIn(PACKAGE_NAME, copied_roots, "the image must ship the a11oy_factory Python package")


class WheelIsPythonTests(unittest.TestCase):
    """The PyPI wheel packages only the a11oy_factory Python package."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    def test_wheel_packages_only_a11oy_factory(self) -> None:
        setuptools_config = self.pyproject.get("tool", {}).get("setuptools", {})
        packages = setuptools_config.get("packages")
        if isinstance(packages, dict):
            names = packages.get("find", {}).get("include")
        else:
            names = packages
        self.assertIsInstance(names, list, "pyproject.toml must name the wheel packages explicitly")
        self.assertTrue(names)
        allowed = {PACKAGE_NAME, f"{PACKAGE_NAME}*", f"{PACKAGE_NAME}.*"}
        for name in names:
            self.assertTrue(
                name in allowed or name.startswith(f"{PACKAGE_NAME}."),
                f"wheel package pattern {name!r} reaches outside {PACKAGE_NAME}",
            )

    def test_console_scripts_run_the_python_package(self) -> None:
        scripts = self.pyproject.get("project", {}).get("scripts", {})
        self.assertTrue(scripts)
        for name, target in scripts.items():
            module = target.split(":", 1)[0].strip()
            self.assertEqual(module.split(".", 1)[0], PACKAGE_NAME, f"console script {name} -> {target}")

    def test_package_holds_no_typescript_or_node_module(self) -> None:
        self.assertTrue((PACKAGE_DIR / "__init__.py").is_file())
        files = shipped_files(PACKAGE_DIR)
        self.assertTrue(any(file.suffix == ".py" for file in files))
        for file in files:
            self.assertIsNone(console_or_node_reason(file))


class TypeScriptModuleInventoryTests(unittest.TestCase):
    """Every src/lib/*.ts module is classified for the owner decision on the console."""

    def test_inventory_lists_every_src_lib_module(self) -> None:
        on_disk = {path.name for path in TS_LIB.glob("*.ts") if not path.name.endswith(".test.ts")}
        listed = set(TS_MODULE_INVENTORY)
        self.assertEqual(sorted(on_disk - listed), [], "classify new src/lib modules in TS_MODULE_INVENTORY")
        self.assertEqual(sorted(listed - on_disk), [], "remove inventory rows for modules no longer in src/lib")

    def test_inventory_rows_are_well_formed(self) -> None:
        for module, (kind, counterpart, note) in TS_MODULE_INVENTORY.items():
            self.assertIn(kind, {PYTHON_COUNTERPART, TS_ONLY}, module)
            self.assertTrue(note.strip(), module)
            if kind == TS_ONLY:
                self.assertIsNone(counterpart, module)
                continue
            self.assertIsNotNone(counterpart, module)
            self.assertTrue(counterpart.startswith(f"{PACKAGE_NAME}/"), f"{module} -> {counterpart}")
            self.assertTrue(counterpart.endswith(".py"), f"{module} -> {counterpart}")
            self.assertTrue((ROOT / counterpart).is_file(), f"{module} -> {counterpart} does not exist")


if __name__ == "__main__":
    unittest.main()
