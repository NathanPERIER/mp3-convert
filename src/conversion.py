
import os
import sys
import itertools
from datetime import datetime
from tqdm import tqdm

from typing import Final, Optional, Tuple, Iterable

from src.collections.file_tree import FilesystemNode, FilesystemLeaf
from src.utils.directory_analyser import scan_directory
from src.utils.errors import UnreachableCode
from src.patches import Patch, ConvertPatch, CopyPatch, CreateDirPatch, RemovePatch


INPUT_EXTENSIONS = ['flac', 'm4a', 'mp3']
OUTPUT_EXTENSION = 'mp3'


class Options :

    def __init__(self, can_remove: bool) :
        self.can_remove: Final[bool] = can_remove


def remove_file(leaf: FilesystemLeaf, path: str) -> Patch :
    return RemovePatch(os.path.join(path, f"{leaf.filename}.{leaf.extension}"))

def convert_file(leaf: FilesystemLeaf, source_folder: str, dest_folder: str, dest_dt: Optional[datetime] = None) -> Iterable[Patch] :
    source_file = os.path.join(source_folder, f"{leaf.filename}.{leaf.extension}")
    if dest_dt != None and dest_dt >= leaf.modification :
        return []
    if source_file.endswith(f".{OUTPUT_EXTENSION}") :
        return [ CopyPatch(source_file, dest_folder, dest_dt is not None) ]
    dest_file = os.path.join(dest_folder, f"{leaf.filename}.{OUTPUT_EXTENSION}")
    return [ ConvertPatch(source_file, dest_file, dest_dt is not None) ]


def add_directory(name: str, node: FilesystemNode, path: str) -> Tuple[FilesystemNode, Optional[Patch]] :
    subpath = os.path.join(path, name)
    res_node = node.push_subfolder(name)
    res_patch = None
    if not os.path.exists(subpath) :
        res_patch = CreateDirPatch(subpath)
    return (res_node, res_patch)
    

def recursive_remove(node: FilesystemNode, path: str) -> Iterable[Patch] :
    subfolder_path = os.path.join(path, node.name)
    return itertools.chain(
        (remove_file(file, subfolder_path) for file in node.files.values()),
        itertools.chain.from_iterable(recursive_remove(node, subfolder_path) for node in node.subfolders.values()),
    )



# Leaf
# - Source exists, destination doesn't => cp/ffmpeg
# - Source exists, destination exists  => cp/ffmpeg if source strictly older than destination
# - Destination exists, source doesn't => if can_remove, rm

def process_leaves(src_node: FilesystemNode, dst_node: FilesystemNode, options: Options, src_base_path: Optional[str] = None, dst_base_path: Optional[str] = None) -> list[Patch] :
    res: list[Patch] = []
    
    src_file_entries = src_node.list_files()
    dst_file_entries = dst_node.list_files()
    i_src = 0
    i_dst = 0

    while i_src < len(src_file_entries) and i_dst < len(dst_file_entries) :
        src_entry = src_file_entries[i_src]
        dst_entry = dst_file_entries[i_dst]
        if src_entry.filename == dst_entry.filename :
            res.extend(convert_file(src_entry, src_base_path, dst_base_path, dst_entry.modification))
            i_src += 1
            i_dst += 1
        elif src_entry.filename < dst_entry.filename : # input file doesn't exist in the destination tree
            res.extend(convert_file(src_entry, src_base_path, dst_base_path))
            i_src += 1
        else :                                         # output file doesn't exist in the source tree
            if options.can_remove :
                res.append(remove_file(dst_entry, dst_base_path))
            i_dst += 1
    
    # remaining files that exist only in the source tree
    while i_src < len(src_file_entries) :
        res.extend(convert_file(src_file_entries[i_src], src_base_path, dst_base_path))
        i_src += 1
    
    # remaining files that exist only in the destination tree
    if options.can_remove :
        while i_dst < len(dst_file_entries) :
            res.append(remove_file(dst_file_entries[i_dst], dst_base_path))
            i_dst += 1
    
    return res



# Node
# - Source exists, destination doesn't => mkdir, add empty node in the destination, keep going
# - Source exists, destination exists  => keep going
# - Destination exists, source doesn't => if can_remove, rm recursively (only files)

def process_nodes(src_node: FilesystemNode, dst_node: FilesystemNode, options: Options, src_base_path: Optional[str] = None, dst_base_path: Optional[str] = None) -> list[Patch] :
    res: list[Patch] = []

    src_folder_entries = src_node.list_folders()
    dst_folder_entries = dst_node.list_folders()
    i_src = 0
    i_dst = 0

    while i_src < len(src_folder_entries) and i_dst < len(dst_folder_entries) :
        src_entry = src_folder_entries[i_src]
        dst_entry = dst_folder_entries[i_dst]
        mkdir_patch = None
        if src_entry.name > dst_entry.name : # output folder doesn't exist in the source tree
            if options.can_remove :
                res.extend(recursive_remove(dst_entry, dst_base_path))
            i_dst += 1
            continue
        if src_entry.name < dst_entry.name : # input folder doesn't exist in the destination tree
            dst_entry, mkdir_patch = add_directory(src_entry.name, dst_node, dst_base_path)
        else :
            i_dst += 1
        i_src += 1
        patches = process(src_entry, dst_entry, options, src_base_path, dst_base_path)
        if len(patches) > 0 :
            if mkdir_patch is not None :
                res.append(mkdir_patch)
            res.extend(patches)
    
    # remaining folders that exist only in the source tree
    while i_src < len(src_folder_entries) :
        src_node = src_folder_entries[i_src]
        dst_node, mkdir_patch = add_directory(src_node.name, dst_node, dst_base_path)
        patches = process(src_node, dst_node, options, src_base_path, dst_base_path)
        if len(patches) > 0 :
            if mkdir_patch is not None :
                res.append(mkdir_patch)
            res.extend(patches)
        i_src += 1
    
    # remaining folders that exist only in the destination tree
    if options.can_remove :
        while i_dst < len(dst_folder_entries) :
            res.extend(recursive_remove(dst_folder_entries[i_dst], dst_base_path))
            i_dst += 1
    
    return res



def process(src_node: FilesystemNode, dst_node: FilesystemNode, options: Options, src_base_path: Optional[str] = None, dst_base_path: Optional[str] = None) -> list[Patch] :
    src_subfolder_path = src_node.name if src_base_path is None else os.path.join(src_base_path, src_node.name)
    dst_subfolder_path = dst_node.name if dst_base_path is None else os.path.join(dst_base_path, dst_node.name)
    return list(itertools.chain(
        # Files
        process_leaves(src_node, dst_node, options, src_subfolder_path, dst_subfolder_path),
        # Subfolders
        process_nodes(src_node, dst_node, options, src_subfolder_path, dst_subfolder_path)
    ))



def conversion(source_dir: str, dest_dir: str, can_remove: bool, dry_run: bool) :
    source_files = scan_directory(source_dir, INPUT_EXTENSIONS)
    print('Found', source_files.file_count, 'input files')

    dest_files = scan_directory(dest_dir, [OUTPUT_EXTENSION])
    print('Found', dest_files.file_count, 'files in the destination directory')

    patches = process(source_files, dest_files, options = Options(can_remove))

    if len(patches) == 0 :
        print("Nothing to do")
        return

    if dry_run :
        for p in patches :
            print(p.describe())
        return

    if os.isatty(sys.stdout.fileno()) :
        for p in tqdm(patches, desc='Progress', unit='patch') :
            p.apply()
        return
    
    for p in patches :
        p.apply()
        print(p.describe())
