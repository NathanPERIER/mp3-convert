
import os

from .base import Patch

from typing import Final


class RemovePatch(Patch) :

    def __init__(self, dest_file: str) :
        self.dest_file : Final[str] = dest_file
    
    def apply(self) :
        os.remove(self.dest_file)
    
    def get_name(self) -> str :
        return 'remove'
    
    def describe(self) -> str :
        return f"REMOVE {self.dest_file}"
