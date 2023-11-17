
import subprocess

from .base import Patch

from typing import Final


class CopyPatch(Patch) :

    def __init__(self, source_file: str, dest_folder: str, update: bool = False) :
        self.source_file : Final[str] = source_file
        self.dest_folder : Final[str] = dest_folder
        self.update : Final[bool] = update
    
    def apply(self) :
        subprocess.run(['cp', self.source_file, self.dest_folder], check=True, capture_output=True)
    
    def describe(self) -> str :
        res = f"COPY {self.source_file}"
        if self.update :
            return f"{res} (update)"
        return res
