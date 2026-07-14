import shutil
import subprocess
import sys


def check_command(cmd: str) -> bool:
    """Check if command exists in system PATH."""
    return shutil.which(cmd) is not None


def sync_dependencies():
    """Sync dependencies using uv."""
    if not check_command("uv"):
        print("[1/2] Warning: 'uv' command not found. Skipping dependency sync.")
        return
    print("[1/2] Syncing python dependencies with uv...")
    subprocess.run(["uv", "sync"], check=True)


def update_agent_skills():
    """Update project agent skills via npx."""
    if not check_command("npx"):
        print("[2/2] Warning: 'npx' command not found. Skipping skill updates.")
        return
    print("[2/2] Fetching latest agent skill updates...")
    try:
        subprocess.run(["npx", "skills", "update", "-p", "-y"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: skills update encountered an issue, skipping.")


def main():
    print("===========================================")
    print("  Initializing Workspace Session Environment")
    print("===========================================")
    try:
        sync_dependencies()
        update_agent_skills()
    except subprocess.CalledProcessError as e:
        print(
            f"\nError: Initialization failed during subprocess execution: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    print("===========================================")
    print("  Initialization Complete!")
    print("===========================================")


if __name__ == "__main__":
    main()
