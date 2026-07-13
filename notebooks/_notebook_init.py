import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def notebook_init() -> None:
    os.chdir(PROJECT_ROOT)
