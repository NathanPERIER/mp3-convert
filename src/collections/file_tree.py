

from datetime import datetime

from typing import Final, Sequence


class FilesystemLeaf :

    def __init__(self, filename: str, extension: str, modification: datetime) :
        self.filename: Final[str] = filename
        self.extensions: dict[str, datetime] = { extension: modification }
    
    def add_extension(self, extension: str, modification: datetime) :
        self.extensions[extension] = modification


class FilesystemNode :

    def __init__(self, name: str) :
        self.name = name
        self.subfolders: dict[str, FilesystemNode] = {}
        self.files: dict[str, FilesystemLeaf] = {}
        self.file_count = 0
    
    def list_files(self) -> "Sequence[FilesystemLeaf]" :
        res = list(self.files.values())
        res.sort(key = lambda n: n.filename)
        return res
    
    def list_folders(self) -> "Sequence[FilesystemNode]" :
        res = list(self.subfolders.values())
        res.sort(key = lambda n: n.name)
        return res

    def _add_subfolder(self, name: str) -> "FilesystemNode" :
        self.file_count += 1
        if name not in self.subfolders :
            res = FilesystemNode(name)
            self.subfolders[name] = res
            return res
        return self.subfolders[name]
    
    def _add_file(self, filename: str, extension: str, modification: datetime) :
        self.file_count += 1
        if filename in self.files :
            self.files[filename].add_extension(extension, modification)
            return
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
