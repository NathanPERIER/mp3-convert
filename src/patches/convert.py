
import subprocess

from .base import Patch

from typing import Final


class ConvertPatch(Patch) :

    def __init__(self, source_file: str, dest_file: str, update: bool = False) :
        self.source_file : Final[str] = source_file
        self.dest_file   : Final[str] = dest_file
        self.update : Final[bool] = update
    
    def apply(self) :
        command = ['ffmpeg', '-y', '-i', self.source_file, '-q:a', '2', self.dest_file]
        subprocess.run(command, check=True, capture_output=True)
    
    def get_name(self) -> str :
        return 'convert'
    
    def describe(self) -> str :
        res = f"CONVERT {self.source_file}"
        if self.update :
            return f"{res} (update)"
        return res
