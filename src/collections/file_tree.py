
from datetime import datetime

from src.metadata.keep import ConvertKeep

from typing import Final, Optional, Sequence, Callable


class LeafMetadata :

    def __init__(self, keep: ConvertKeep) :
        self.keep: Final[ConvertKeep] = keep


class FilesystemLeaf :

    def __init__(self, name: str, extension: str, modification: datetime) :
        self.name: Final[str] = name
        self.extension: Final[str] = extension
        self.modification: Final[datetime] = modification
        self.metadata: Optional[LeafMetadata] = None

    def filename(self) -> str :
        return f"{self.name}.{self.extension}"


class FilesystemNode :

    def __init__(self, name: str) :
        self.name = name
        self.subfolders: dict[str, FilesystemNode] = {}
        self.files: dict[str, FilesystemLeaf] = {}
        self.file_count = 0
    
    def list_files(self) -> "Sequence[FilesystemLeaf]" :
        res = list(self.files.values())
        res.sort(key = lambda n: n.name)
        return res
    
    def list_folders(self) -> "Sequence[FilesystemNode]" :
        res = list(self.subfolders.values())
        res.sort(key = lambda n: n.name)
        return res

    def drop_file(self, name: str) -> bool :
        if name not in self.files :
            return False
        del self.files[name]
        self.file_count -= 1
        return True
    
    def drop_folder(self, name: str) -> bool :
        if name not in self.subfolders :
            return False
        del self.subfolders[name]
        return True

    def _add_subfolder(self, name: str) -> "FilesystemNode" :
        self.file_count += 1
        if name not in self.subfolders :
            res = FilesystemNode(name)
            self.subfolders[name] = res
            return res
        return self.subfolders[name]
    
    def _add_file(self, filename: str, extension: str, modification: datetime) :
        if filename not in self.files :
            self.file_count += 1
        self.files[filename] = FilesystemLeaf(filename, extension, modification)

    def push_file(self, path: str, filename: str, extension: str, modification: datetime) :
        folders = path.split('/')
        node = self
        for folder in folders :
            node = node._add_subfolder(folder)
        node._add_file(filename, extension, modification)

    def push_subfolder(self, name: str) -> "FilesystemNode" :
        if name in self.subfolders :
            raise Exception('Tried to push a folder that already existed')
        res = FilesystemNode(name)
        self.subfolders[name] = res
        return res
    
    def get_file(self, path: str, filename: str) -> "Optional[FilesystemLeaf]" :
        folders = path.split('/')
        node = self
        for folder in folders :
            if folder not in node.subfolders :
                return None
            node = node.subfolders[folder]
        if filename in node.files :
            return node.files[filename]
        return None
    
    def walk_leaves(self, func: "FilesystemLeaf[[str, str], None]") :
        for leaf in self.files.values() :
            func(leaf)
        for child in self.subfolders.values() :
            child.walk_leaves(func)
