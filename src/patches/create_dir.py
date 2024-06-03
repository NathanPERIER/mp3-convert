
import os

from .base import Patch

from typing import Final


class CreateDirPatch(Patch) :

    def __init__(self, directory_path: str) :
        self.directory_path : Final[str] = directory_path
    
    def apply(self) :
        os.mkdir(self.directory_path)

    def get_name(self) -> str :
        return 'mkdir'
    
    def describe(self) -> str :
        return f"CREATE {self.directory_path}"
