"""CLI wrapper forwarding contract tests."""

from __future__ import annotations

import runpy
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import FunctionType, ModuleType
from typing import cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load_script(
    monkeypatch: pytest.MonkeyPatch,
    script_name: str,
    commands_module: ModuleType,
) -> dict[str, object]:
    monkeypatch.setitem(sys.modules, "_commands", commands_module)
    return runpy.run_path(
        str(SCRIPTS_DIR / script_name),
        run_name=f"test_{script_name}",
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("script_name", "tool_name"),
    [("biome.py", "biome"), ("tombi.py", "tombi")],
)
def test_local_node_wrapper_forwards_tool_and_cli_args(
    monkeypatch: pytest.MonkeyPatch,
    script_name: str,
    tool_name: str,
) -> None:
    """Biome/Tombi wrappers preserve tool identity, argv, and repository cwd."""
    calls: list[tuple[str, tuple[str, ...], Path]] = []
    commands = ModuleType("_commands")

    def fake_run_local_node_tool(
        tool: str,
        args: Sequence[str],
        *,
        cwd: Path,
    ) -> int:
        calls.append((tool, tuple(args), cwd))
        return 17

    commands.__dict__["run_local_node_tool"] = fake_run_local_node_tool
    namespace = _load_script(monkeypatch, script_name, commands)
    monkeypatch.setattr(sys, "argv", [script_name, "check", "example.txt"])

    main = cast(Callable[[], int], namespace["main"])
    assert main() == 17
    assert calls == [(tool_name, ("check", "example.txt"), REPO_ROOT)]


@pytest.mark.unit
def test_rulesync_wrapper_forwards_package_binary_and_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rulesync wrapper preserves package, binary, args, and repository cwd."""
    calls: list[tuple[str, str, tuple[str, ...], Path]] = []
    commands = ModuleType("_commands")

    def fake_run_npm_exec(
        package: str,
        binary: str,
        args: Sequence[str],
        *,
        cwd: Path,
    ) -> int:
        calls.append((package, binary, tuple(args), cwd))
        return 23

    commands.__dict__["run_npm_exec"] = fake_run_npm_exec
    namespace = _load_script(monkeypatch, "rulesync.py", commands)

    run = cast(Callable[[Sequence[str]], int], namespace["_run"])
    assert run(("generate", "--check")) == 23
    assert calls == [
        ("rulesync@latest", "rulesync", ("generate", "--check"), REPO_ROOT)
    ]


def _configure_rulesync_namespace(
    namespace: dict[str, object],
    tmp_path: Path,
) -> tuple[Path, Path]:
    config_path = tmp_path / "rulesync.jsonc"
    lock_path = tmp_path / "rulesync.lock"
    script_globals = _script_globals(namespace)
    script_globals["REPO_ROOT"] = tmp_path
    script_globals["RULESYNC_CONFIG"] = config_path
    script_globals["RULESYNC_LOCK"] = lock_path
    script_globals["SKILLS_LOCK"] = tmp_path / "skills-lock.json"
    script_globals["SKILLS_ROOT"] = tmp_path / ".rulesync" / "skills"
    return config_path, lock_path


def _make_target_skill(root: Path, name: str) -> Path:
    skill_path = root / name
    skill_path.mkdir(parents=True)
    (skill_path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test\n---\n",
        encoding="utf-8",
    )
    return skill_path


def _load_rulesync(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    commands = ModuleType("_commands")
    commands.__dict__["run_npm_exec"] = lambda *_args, **_kwargs: 0
    return _load_script(monkeypatch, "rulesync.py", commands)


def _script_globals(namespace: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], cast(FunctionType, namespace["_run"]).__globals__)


@pytest.mark.unit
def test_generate_prunes_stale_target_skills_and_preserves_declared_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Generate prunes only stale Skill directories in generated target roots."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text(
        '{\n  // source declaration\n  "sources": '
        '[{"skills": ["configured-skill"]}]\n}\n',
        encoding="utf-8",
    )
    lock_path.write_text(
        '{"sources": {"owner/assets": {"skills": {"locked-skill": {}}}}}\n',
        encoding="utf-8",
    )

    local_root = tmp_path / ".rulesync" / "skills" / "local-skill"
    local_root.mkdir(parents=True)
    (local_root / "SKILL.md").write_text("local", encoding="utf-8")

    target_roots = [
        tmp_path / ".agents" / "skills",
        tmp_path / ".claude" / "skills",
        tmp_path / ".github" / "skills",
    ]
    for target_root in target_roots:
        target_root.mkdir(parents=True)
        _make_target_skill(target_root, "stale-skill")
        manual = target_root / "manual-directory"
        manual.mkdir()
        (manual / "README.md").write_text("keep", encoding="utf-8")

    _make_target_skill(target_roots[0], "configured-skill")
    _make_target_skill(target_roots[1], "LOCKED-SKILL")
    _make_target_skill(target_roots[2], "LOCAL-SKILL")

    run_generate = cast(Callable[[], int], namespace["_run_generate"])
    assert run_generate() == 0

    for target_root in target_roots:
        assert not (target_root / "stale-skill").exists()
        assert (target_root / "manual-directory" / "README.md").exists()
    assert (target_roots[0] / "configured-skill" / "SKILL.md").exists()
    assert (target_roots[1] / "LOCKED-SKILL" / "SKILL.md").exists()
    assert (target_roots[2] / "LOCAL-SKILL" / "SKILL.md").exists()


@pytest.mark.unit
def test_generate_preserves_symlinked_target_skill(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Prune never follows a target Skill symlink."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")
    generated_root = tmp_path / ".agents" / "skills"
    generated_root.mkdir(parents=True)
    outside_skill = _make_target_skill(tmp_path, "outside-skill")
    linked_skill = generated_root / "linked-skill"
    try:
        linked_skill.symlink_to(outside_skill, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"directory symlinks unavailable: {error}")

    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert linked_skill.is_symlink()
    assert outside_skill.exists()


@pytest.mark.unit
def test_generate_skips_prune_when_projection_root_ancestor_is_symlink(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Prune does not follow a target root ancestor outside the repository."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")

    outside_root = tmp_path / "outside" / "skills"
    outside_skill = _make_target_skill(outside_root, "stale-skill")
    linked_root = tmp_path / ".agents"
    try:
        linked_root.symlink_to(outside_root.parent, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"directory symlinks unavailable: {error}")

    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert outside_skill.exists()


@pytest.mark.unit
def test_generate_skips_prune_when_local_skill_root_is_symlink(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An unsafe canonical local source keeps all target projections intact."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")

    outside_source = tmp_path / "outside-source"
    _make_target_skill(outside_source, "shared-skill")
    local_parent = tmp_path / ".rulesync"
    local_parent.mkdir()
    try:
        (local_parent / "skills").symlink_to(outside_source, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"directory symlinks unavailable: {error}")

    target_skill = _make_target_skill(tmp_path / ".agents" / "skills", "shared-skill")
    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert target_skill.exists()


@pytest.mark.unit
def test_generate_skips_prune_when_local_skill_root_is_not_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An invalid canonical source type keeps target projections intact."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")

    local_parent = tmp_path / ".rulesync"
    local_parent.mkdir()
    (local_parent / "skills").write_text("invalid source", encoding="utf-8")
    target_skill = _make_target_skill(tmp_path / ".agents" / "skills", "stale-skill")
    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert target_skill.exists()


@pytest.mark.unit
def test_generate_skips_prune_when_local_skill_child_is_symlink(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An unsafe local Skill child makes the canonical source unknown."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")

    outside_skill = _make_target_skill(tmp_path / "outside", "linked-skill")
    local_root = tmp_path / ".rulesync" / "skills"
    local_root.mkdir(parents=True)
    try:
        (local_root / "linked-skill").symlink_to(
            outside_skill,
            target_is_directory=True,
        )
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"directory symlinks unavailable: {error}")

    target_skill = _make_target_skill(tmp_path / ".agents" / "skills", "linked-skill")
    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert target_skill.exists()


@pytest.mark.unit
def test_generate_preserves_skills_cli_owned_target_skill(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Skills CLI lock names are outside Rulesync prune ownership."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")
    skills_lock = _script_globals(namespace)["SKILLS_LOCK"]
    assert isinstance(skills_lock, Path)
    skills_lock.write_text(
        '{"skills": {"external-skill": {"sourceType": "github", '
        '"source": "owner/repo", "ref": "main", "skillPath": "skill"}}}\n',
        encoding="utf-8",
    )

    external_skill = _make_target_skill(
        tmp_path / ".agents" / "skills",
        "external-skill",
    )
    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert external_skill.exists()


@pytest.mark.unit
def test_generate_skips_prune_when_skills_cli_lock_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Invalid optional ownership state disables destructive pruning."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")
    skills_lock = _script_globals(namespace)["SKILLS_LOCK"]
    assert isinstance(skills_lock, Path)
    skills_lock.write_text('{"skills": []}', encoding="utf-8")

    stale = _make_target_skill(tmp_path / ".agents" / "skills", "stale-skill")
    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert stale.exists()


@pytest.mark.unit
def test_generate_prunes_skill_created_after_generate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The after-generate observation catches a newly created stale directory."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")
    generated_root = tmp_path / ".agents" / "skills"
    generated_root.mkdir(parents=True)

    def fake_run(_args: Sequence[str]) -> int:
        _make_target_skill(generated_root, "created-during-generate")
        return 0

    _script_globals(namespace)["_run"] = fake_run
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert not (generated_root / "created-during-generate").exists()


@pytest.mark.unit
def test_generate_failure_preserves_stale_target_skills(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A failed generate does not turn observation into a destructive prune."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")
    stale = _make_target_skill(tmp_path / ".claude" / "skills", "stale-skill")

    _script_globals(namespace)["_run"] = lambda _args: 17
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 17
    assert stale.exists()


@pytest.mark.unit
def test_generate_skips_prune_when_lock_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Unknown lock state keeps target files untouched while generate runs."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    stale = _make_target_skill(tmp_path / ".github" / "skills", "stale-skill")

    _script_globals(namespace)["_run"] = lambda _args: 0
    run_generate = cast(Callable[[], int], namespace["_run_generate"])

    assert run_generate() == 0
    assert stale.exists()
    assert not lock_path.exists()


@pytest.mark.unit
def test_sync_sources_uses_generate_prune_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Install/update keeps its source step before the shared generate wrapper."""
    namespace = _load_rulesync(monkeypatch)
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_run(args: Sequence[str]) -> int:
        calls.append(("run", tuple(args)))
        return 0

    def fake_run_generate() -> int:
        calls.append(("generate", ()))
        return 29

    script_globals = _script_globals(namespace)
    script_globals["_run"] = fake_run
    script_globals["_run_generate"] = fake_run_generate
    sync_sources = cast(Callable[[Sequence[str]], int], namespace["_sync_sources"])

    assert sync_sources(("install", "--frozen")) == 29
    assert calls == [
        ("run", ("install", "--frozen")),
        ("generate", ()),
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("action", "checker_name"),
    [("preview", "_preview_claude_bridges"), ("check", "_check_claude_bridges")],
)
def test_inspection_actions_do_not_prune_target_skills(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    action: str,
    checker_name: str,
) -> None:
    """Preview/check keep their inspection-only behavior."""
    namespace = _load_rulesync(monkeypatch)
    config_path, lock_path = _configure_rulesync_namespace(namespace, tmp_path)
    config_path.write_text('{"sources": []}', encoding="utf-8")
    lock_path.write_text('{"sources": {}}', encoding="utf-8")
    stale = _make_target_skill(tmp_path / ".agents" / "skills", "stale-skill")
    script_globals = _script_globals(namespace)
    script_globals["_run"] = lambda _args: 0
    script_globals[checker_name] = lambda: 0
    main = cast(Callable[[], int], namespace["main"])
    monkeypatch.setattr(sys, "argv", ["rulesync.py", action])

    assert main() == 0
    assert stale.exists()


@pytest.mark.unit
def test_main_generate_uses_generate_prune_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public generate action uses the shared pruning wrapper."""
    namespace = _load_rulesync(monkeypatch)
    calls: list[str] = []
    script_globals = _script_globals(namespace)
    script_globals["_run"] = lambda _args: 0
    script_globals["_run_generate"] = lambda: calls.append("generate") or 31
    script_globals["_write_claude_bridges"] = lambda: calls.append("bridges")
    main = cast(Callable[[], int], namespace["main"])
    monkeypatch.setattr(sys, "argv", ["rulesync.py", "generate"])

    assert main() == 31
    assert calls == ["generate"]
