
import os

from .base import Patch

from typing import Final


class ClearDirPatch(Patch) :

    def __init__(self, dir_path: str) :
        self.dir_path : Final[str] = dir_path

    def apply(self) :
        try:
            os.rmdir(self.dir_path)
        except Exception :
            pass

    def describe(self) -> str :
        return f"CLEAR {self.dir_path}"
