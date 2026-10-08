"""OpenSpec selection policy applied to an explicit classifier scope."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classify_changes import Scope


def valid_name(name: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) is not None


def add_related_changes(capability: str, scope: Scope) -> None:
    inventory = Path("openspec/changes")
    if not inventory.is_dir() or inventory.is_symlink():
        scope.require_full_test_and_type()
        return
    for directory in sorted(inventory.iterdir()):
        if directory.is_symlink():
            scope.require_full_test_and_type()
            continue
        if not directory.is_dir() or directory.name == "archive":
            continue
        related = directory / "specs" / capability
        if related.is_symlink() or (related.exists() and not related.is_dir()):
            scope.require_full_test_and_type()
        elif related.is_dir():
            if valid_name(directory.name):
                if directory.name not in scope.openspec_change_targets:
                    scope.openspec_change_targets.append(directory.name)
            else:
                scope.require_full_test_and_type()


def classify_openspec_path(path: str, scope: Scope) -> None:
    parts = path.split("/")
    if parts[0] != "openspec" or len(parts) < 2:
        return
    scope.openspec = True
    if parts[1] == "specs" and len(parts) >= 4:
        scope.require_full_test_and_type()
        capability = parts[2]
        if valid_name(capability) and Path(f"openspec/specs/{capability}").is_dir():
            if capability not in scope.openspec_spec_targets:
                scope.openspec_spec_targets.append(capability)
            add_related_changes(capability, scope)
        else:
            scope.openspec_bulk = True
    elif parts[1] == "changes" and len(parts) >= 5 and parts[2] == "archive":
        scope.openspec_archived = True
    elif parts[1] == "changes" and len(parts) >= 4:
        change = parts[2]
        if valid_name(change) and Path(f"openspec/changes/{change}").is_dir():
            if change not in scope.openspec_change_targets:
                scope.openspec_change_targets.append(change)
        else:
            scope.openspec_bulk = True
    else:
        scope.openspec_bulk = True
