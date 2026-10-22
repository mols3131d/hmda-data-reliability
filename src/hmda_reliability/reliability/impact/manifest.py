"""dbt 매니페스트 계통(lineage) 그래프 파서 모듈."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from hmda_reliability.reliability.errors import ImpactAnalysisError


class DbtManifestGraph:
    """dbt 매니페스트 노드/소스 간 의존성 그래프."""

    def __init__(self, manifest: dict[str, Any]) -> None:
        self._resources = _resources(manifest)
        self._asset_index = _asset_index(self._resources)
        self._children = _children(self._resources)

    @classmethod
    def from_path(cls, path: Path) -> DbtManifestGraph:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            msg = f"dbt manifest를 읽을 수 없습니다: path={path}"
            raise ImpactAnalysisError(msg) from exc
        if not isinstance(manifest, dict):
            msg = f"dbt manifest root는 object여야 합니다: path={path}"
            raise ImpactAnalysisError(msg)
        return cls(manifest)

    def downstream_assets(self, upstream_asset: str) -> list[str]:
        """upstream asset의 transitive downstream asset 목록."""

        node_id = self._resolve_node_id(upstream_asset)
        if node_id is None:
            return []

        discovered: list[str] = []
        visited: set[str] = set()
        queue = deque(sorted(self._children.get(node_id, [])))
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            discovered.append(_asset_name(self._resources[current]))
            queue.extend(sorted(self._children.get(current, [])))
        return discovered

    def _resolve_node_id(self, asset_name: str) -> str | None:
        return self._asset_index.get(asset_name)


def _resources(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    resources: dict[str, dict[str, Any]] = {}
    for container_name in ("nodes", "sources"):
        container = manifest.get(container_name, {})
        if not isinstance(container, dict):
            msg = f"dbt manifest {container_name}는 object여야 합니다."
            raise ImpactAnalysisError(msg)
        resources.update(
            {
                str(node_id): node
                for node_id, node in container.items()
                if isinstance(node, dict)
            }
        )
    return resources


def _asset_index(resources: dict[str, dict[str, Any]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for node_id, node in resources.items():
        for key in _asset_keys(node_id, node):
            index.setdefault(key, node_id)
    return index


def _asset_keys(node_id: str, node: dict[str, Any]) -> set[str]:
    keys = {node_id}
    for field in ("name", "alias", "identifier", "relation_name"):
        value = node.get(field)
        if value:
            keys.add(str(value))
    schema = node.get("schema")
    name = node.get("name")
    if schema and name:
        keys.add(f"{schema}.{name}")
    return keys


def _children(resources: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    children: dict[str, set[str]] = defaultdict(set)
    for node_id, node in resources.items():
        depends_on = node.get("depends_on", {})
        if not isinstance(depends_on, dict):
            continue
        dependencies = depends_on.get("nodes", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            dependency_id = str(dependency)
            if dependency_id in resources:
                children[dependency_id].add(node_id)
    return children


def _asset_name(node: dict[str, Any]) -> str:
    return str(node.get("name") or node.get("unique_id") or "")
