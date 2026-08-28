"""Architecture checks for Review AI, Runtime AI, and Reliability imports."""

from __future__ import annotations

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

pytestmark = pytest.mark.component

_PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "hmda_reliability"
_FORBIDDEN_IMPORTS = {
    "runtime_ai": (
        "hmda_reliability.review_ai",
        "hmda_reliability.reliability",
    ),
    "reliability": (
        "hmda_reliability.review_ai",
        "hmda_reliability.runtime_ai",
    ),
}


@pytest.mark.parametrize(("package", "forbidden"), _FORBIDDEN_IMPORTS.items())
def test_domain_import_direction_excludes_forbidden_dependencies(
    package: str,
    forbidden: tuple[str, ...],
) -> None:
    violations = [
        f"{source.relative_to(_PACKAGE_ROOT)} -> {imported}"
        for source in sorted(_PACKAGE_ROOT.joinpath(package).rglob("*.py"))
        for imported in sorted(_imported_modules(source))
        if any(
            imported == prefix or imported.startswith(f"{prefix}.")
            for prefix in forbidden
        )
    ]

    assert violations == []


def _imported_modules(source: Path) -> set[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    package = _containing_package(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        module = node.module or ""
        if node.level:
            module = resolve_name(f"{'.' * node.level}{module}", package)
        if not module:
            continue
        imported.add(module)
        imported.update(
            f"{module}.{alias.name}" for alias in node.names if alias.name != "*"
        )
    return imported


def _containing_package(source: Path) -> str:
    relative = source.relative_to(_PACKAGE_ROOT).with_suffix("")
    package_parts = relative.parts[:-1]
    if source.name == "__init__.py":
        package_parts = relative.parts[:-1]
    return ".".join(("hmda_reliability", *package_parts))
