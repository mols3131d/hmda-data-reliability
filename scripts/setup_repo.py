import shutil
import subprocess
import sys


def check_command(cmd: str) -> bool:
    """Check if command exists in system PATH."""
    return shutil.which(cmd) is not None


def sync_dependencies():
    """Sync dependencies using uv, fail fast if missing."""
    if not check_command("uv"):
        print(
            "[1/3] Error: 'uv' command not found. Please install uv first (https://astral.sh/uv).",
            file=sys.stderr,
        )
        sys.exit(1)
    print("[1/3] Syncing python dependencies with uv...")
    subprocess.run(["uv", "sync"], check=True)


def install_git_hooks():
    """Install Git hooks via lefthook."""
    print("[2/3] Installing Git hooks via lefthook...")
    subprocess.run(["uv", "run", "lefthook", "install"], check=True)


def fetch_initial_skills():
    """Perform initial update of project skills."""
    if not check_command("npx"):
        print("[3/3] Warning: 'npx' command not found. Skipping initial skill updates.")
        return
    print("[3/3] Fetching initial agent skills...")
    try:
        subprocess.run(["npx", "skills", "update", "-p", "-y"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: skills update encountered an issue.")


def main():
    print("===========================================")
    print("  Setting Up Repository for the First Time")
    print("===========================================")
    try:
        sync_dependencies()
        install_git_hooks()
        fetch_initial_skills()
    except subprocess.CalledProcessError as e:
        print(f"\nError: Repository setup failed: {e}", file=sys.stderr)
        sys.exit(1)
    print("===========================================")
    print("  Setup Complete! You can now start coding.")
    print("===========================================")


if __name__ == "__main__":
    main()
