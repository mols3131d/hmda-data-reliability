"""조사 자료가 없는 상태에서 App Server의 세션과 실제 실행 제약을 검사한다."""

from pathlib import Path

from hmda_reliability.runtime_ai.codex_rpc import AppServer, Json

# App Server's personal subscription tiers. Metered, organization-specific and
# future account types need separate billing evidence before sending an input.
_SUBSCRIPTION_PLANS = frozenset({"go", "plus", "pro", "prolite", "promax"})
PROFILE = "hmda-investigation"
_DISABLED = (
    "shell_tool",
    "apps",
    "plugins",
    "hooks",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "multi_agent",
    "code_mode",
    "image_generation",
    "memories",
    "skill_search",
    "skill_mcp_dependency_install",
    "request_permissions_tool",
    "remote_plugin",
    "tool_suggest",
    "js_repl",
)
_CONFIG = (
    'approval_policy="never"',
    'web_search="disabled"',
    'forced_login_method="chatgpt"',
    'model_provider="openai"',
    'chatgpt_base_url="https://chatgpt.com/backend-api"',
    f'default_permissions="{PROFILE}"',
    f'permissions.{PROFILE}.filesystem={{":root"="deny"}}',
    f"permissions.{PROFILE}.network.enabled=false",
    "project_doc_max_bytes=0",
    "features.skip_host_skill_discovery=true",
)


class PreflightError(ValueError):
    """근거를 보낼 수 없는 인증 또는 격리 오류 코드."""


def server_command() -> list[str]:
    args = ["codex", "app-server", "--stdio", "--strict-config"]
    for setting in _CONFIG:
        args.extend(("-c", setting))
    for name in _DISABLED:
        args.extend(("--disable", name))
    return args


def verify_server(server: AppServer, cwd: Path, deadline: float) -> None:
    server.rpc(
        "initialize",
        {
            "clientInfo": {"name": "hmda_reliability", "version": "1"},
            "capabilities": {"experimentalApi": True},
        },
        deadline,
    )
    server.send({"method": "initialized"}, deadline)
    config = server.rpc("config/read", {"cwd": str(cwd)}, deadline)["config"]
    profile = config["permissions"][PROFILE]
    filesystem = {k: v for k, v in profile["filesystem"].items() if v is not None}
    network = {k: v for k, v in profile["network"].items() if v is not None}
    if (
        filesystem != {":root": "deny"}
        or network != {"enabled": False}
        or profile.get("extends")
        or profile.get("workspace_roots")
        or config.get("default_permissions") != PROFILE
        or config.get("approval_policy") != "never"
        or config.get("web_search") != "disabled"
        or config.get("forced_login_method") != "chatgpt"
        or config.get("chatgpt_base_url", "").rstrip("/")
        != "https://chatgpt.com/backend-api"
        or config.get("model_provider") != "openai"
        or any(
            config.get(k)
            for k in (
                "model_providers",
                "openai_base_url",
                "notify",
                "otel",
                "mcp_servers",
                "experimental_thread_store_endpoint",
                "model_instructions_file",
            )
        )
        or any(config["features"].get(k) is not False for k in _DISABLED)
        or config["features"].get("skip_host_skill_discovery") is not True
    ):
        raise PreflightError("codex_isolation_unverified")
    _verify_extensions(server, cwd, deadline, {})

    # 동일 프로세스·디렉터리의 정상 실행과 프로필에 의한 실행 차단을 대조한다.
    probe = {
        "command": ["/usr/bin/true"],
        "cwd": str(cwd),
        "timeoutMs": 2500,
        "outputBytesCap": 2048,
    }
    control = server.rpc(
        "command/exec",
        {**probe, "sandboxPolicy": {"type": "readOnly", "networkAccess": False}},
        deadline,
    )
    denied = server.rpc(
        "command/exec", {**probe, "permissionProfile": PROFILE}, deadline
    )
    if (
        control["exitCode"] != 0
        or denied["exitCode"] == 0
        or not any(
            marker in denied["stderr"]
            for marker in ("Permission denied", "No such file or directory")
        )
    ):
        raise PreflightError("codex_isolation_unverified")
    account = (
        server.rpc("account/read", {"refreshToken": False}, deadline).get("account")
        or {}
    )
    if (
        account.get("type") != "chatgpt"
        or account.get("planType") not in _SUBSCRIPTION_PLANS
    ):
        raise PreflightError("codex_subscription_required")


def _verify_extensions(
    server: AppServer, cwd: Path, deadline: float, scope: Json
) -> None:
    mcp = server.rpc("mcpServerStatus/list", scope, deadline)
    hooks = server.rpc("hooks/list", scope or {"cwds": [str(cwd)]}, deadline)
    plugins = server.rpc("plugin/installed", {"cwds": [str(cwd)]}, deadline)
    if (
        mcp["data"]
        or mcp.get("nextCursor")
        or len(hooks["data"]) != 1
        or hooks["data"][0]["cwd"] != str(cwd)
        or hooks["data"][0]["hooks"]
        or hooks["data"][0]["errors"]
        or plugins["marketplaceLoadErrors"]
        or any(p["enabled"] for m in plugins["marketplaces"] for p in m["plugins"])
    ):
        raise PreflightError("codex_isolation_unverified")


def start_thread(
    server: AppServer, cwd: Path, model: str, deadline: float
) -> tuple[str, str]:
    params: Json = {
        "modelProvider": "openai",
        "ephemeral": True,
        "cwd": str(cwd),
        "permissions": PROFILE,
        "approvalPolicy": "never",
        "environments": [],
        "dynamicTools": [],
        "selectedCapabilityRoots": [],
        "runtimeWorkspaceRoots": [str(cwd)],
        "baseInstructions": (
            "Use the supplied conversation and permitted lookup schemas. "
            "Reply in the JSON envelope. Put host lookups in tool_calls with "
            "unique id, function name and JSON arguments string. For a final "
            "report put JSON text in content and return an empty tool_calls array. "
            "Only propose lookups. The host executes them."
        ),
    }
    if model != "codex-default":
        params["model"] = model
    result = server.rpc("thread/start", params, deadline)
    thread = result["thread"]
    if (
        thread.get("ephemeral") is not True
        or thread.get("environments") != []
        or result.get("instructionSources") != []
        or result.get("cwd") != str(cwd)
        or result.get("approvalPolicy") != "never"
        or result.get("modelProvider") != "openai"
        or result.get("activePermissionProfile") != {"id": PROFILE, "extends": None}
        or result.get("sandbox") != {"type": "readOnly", "networkAccess": False}
        or not isinstance(thread.get("id"), str)
        or not thread["id"]
        or not isinstance(result.get("model"), str)
        or not result["model"]
    ):
        raise PreflightError("codex_isolation_unverified")
    _verify_extensions(server, cwd, deadline, {"threadId": thread["id"]})
    return thread["id"], result["model"]
