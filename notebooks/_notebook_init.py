import os
from pathlib import Path


def notebook_init():
    os.chdir(Path(__file__).parent.parent.resolve())


notebook_init()
