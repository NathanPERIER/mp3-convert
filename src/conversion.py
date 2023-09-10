
import os
import subprocess
from datetime import datetime

from typing import Final, Optional, Tuple

from src.collections.file_tree import FilesystemNode, FilesystemLeaf
from src.utils.directory_analyser import scan_directory
from src.utils.errors import UnreachableCode


INPUT_EXTENSIONS = ['flac', 'm4a', 'mp3']
OUTPUT_EXTENSION = 'mp3'


class Options :

    def __init__(self, can_remove: bool) :
        self.can_remove: Final[bool] = can_remove


def select_input_file(leaf: FilesystemLeaf, path: str) -> Tuple[str, datetime] :
    for ext in INPUT_EXTENSIONS :
        if ext in leaf.extensions :
            return (os.path.join(path, f"{leaf.filename}.{ext}"), leaf.extensions[ext])
    raise UnreachableCode()

def remove_file(leaf: FilesystemLeaf, path: str) :
    for ext in leaf.extensions :
        filepath = os.path.join(path, f"{leaf.filename}.{ext}")
        os.remove(filepath)
        print('REMOVE', filepath)

def convert_file(leaf: FilesystemLeaf, source_folder: str, dest_folder: str, dest_dt: Optional[datetime] = None) :
    source_file, source_dt = select_input_file(leaf, source_folder)
    if dest_dt != None and dest_dt >= source_dt :
        return
    dest_file = os.path.join(dest_folder, f"{leaf.filename}.{OUTPUT_EXTENSION}")
    if source_file.endswith(f".{OUTPUT_EXTENSION}") :
        print('COPY' if dest_dt is None else 'UPDATE', dest_file)
        subprocess.run(['cp', source_file, dest_folder], check=True, capture_output=True)
    else :
        print('CONVERT' if dest_dt is None else 'UPDATE', dest_file)
        command = ['ffmpeg', '-y', '-i', source_file, '-q:a', '2', dest_file]
        subprocess.run(command, check=True, capture_output=True)


def add_directory(name: str, node: FilesystemNode, path: str) -> FilesystemNode :
    subpath = os.path.join(path, name)
    if not os.path.exists(subpath) :
        print('CREATE', subpath)
        os.mkdir(subpath)
    return node.push_subfolder(name)

def recursive_remove(node: FilesystemNode, path: str) :
    subfolder_path = os.path.join(path, node.name)
    for file in node.files.values() :
        remove_file(file, subfolder_path)
    for node in node.subfolders.values() :
        recursive_remove(node, subfolder_path)



# Leaf
# - Source exists, destination doesn't => cp/ffmpeg
# - Source exists, destination exists  => cp/ffmpeg if source strictly older than destination
# - Destination exists, source doesn't => if can_remove, rm

def process_leaves(src_node: FilesystemNode, dst_node: FilesystemNode, options: Options, src_base_path: Optional[str] = None, dst_base_path: Optional[str] = None) :
    src_file_entries = list(src_node.files.values())
    dst_file_entries = list(dst_node.files.values())
    src_file_entries.sort(key = lambda n: n.filename)
    dst_file_entries.sort(key = lambda n: n.filename)
    i_src = 0
    i_dst = 0

    while i_src < len(src_file_entries) and i_dst < len(dst_file_entries) :
        src_entry = src_file_entries[i_src]
        dst_entry = dst_file_entries[i_dst]
        if src_entry.filename == dst_entry.filename :
            convert_file(src_entry, src_base_path, dst_base_path, dst_entry.extensions[OUTPUT_EXTENSION])
            i_src += 1
            i_dst += 1
        elif src_entry.filename < dst_entry.filename : # input file doesn't exist in the destination tree
            convert_file(src_entry, src_base_path, dst_base_path)
            i_src += 1
        else :                                         # output file doesn't exist in the source tree
            if options.can_remove :
                remove_file(dst_entry, dst_base_path)
            i_dst += 1
    
    # remaining files that exist only in the source tree
    while i_src < len(src_file_entries) :
        convert_file(src_file_entries[i_src], src_base_path, dst_base_path)
        i_src += 1
    
    # remaining files that exist only in the destination tree
    if options.can_remove :
        while i_dst < len(dst_file_entries) :
            remove_file(dst_file_entries[i_dst], dst_base_path)
            i_dst += 1



# Node
# - Source exists, destination doesn't => mkdir, add empty node in the destination, keep going
# - Source exists, destination exists  => keep going
# - Destination exists, source doesn't => if can_remove, rm recursively (only files)

def process_nodes(src_node: FilesystemNode, dst_node: FilesystemNode, options: Options, src_base_path: Optional[str] = None, dst_base_path: Optional[str] = None) :
    src_folder_entries = list(src_node.subfolders.values())
    dst_folder_entries = list(dst_node.subfolders.values())
    src_folder_entries.sort(key = lambda n: n.name)
    dst_folder_entries.sort(key = lambda n: n.name)
    i_src = 0
    i_dst = 0

    while i_src < len(src_folder_entries) and i_dst < len(dst_folder_entries) :
        src_entry = src_folder_entries[i_src]
        dst_entry = dst_folder_entries[i_dst]
        if src_entry.name > dst_entry.name : # output folder doesn't exist in the source tree
            if options.can_remove :
                recursive_remove(dst_entry, dst_base_path)
            i_dst += 1
            continue
        if src_entry.name < dst_entry.name : # input folder doesn't exist in the destination tree
            dst_entry = add_directory(src_entry.name, dst_node, dst_base_path)
        else :
            i_dst += 1
        i_src += 1
        process(src_entry, dst_entry, options, src_base_path, dst_base_path)
    
    # remaining folders that exist only in the source tree
    while i_src < len(src_folder_entries) :
        src_node = src_folder_entries[i_src]
        dst_node = add_directory(src_node.name, dst_node, dst_base_path)
        process(src_node, dst_node, options, src_base_path, dst_base_path)
        i_src += 1
    
    # remaining folders that exist only in the destination tree
    if options.can_remove :
        while i_dst < len(dst_folder_entries) :
            recursive_remove(dst_folder_entries[i_dst], dst_base_path)
            i_dst += 1



def process(src_node: FilesystemNode, dst_node: FilesystemNode, options: Options, src_base_path: Optional[str] = None, dst_base_path: Optional[str] = None) :
    src_subfolder_path = src_node.name if src_base_path is None else os.path.join(src_base_path, src_node.name)
    dst_subfolder_path = dst_node.name if dst_base_path is None else os.path.join(dst_base_path, dst_node.name)
    # Files
    process_leaves(src_node, dst_node, options, src_subfolder_path, dst_subfolder_path)
    # Subfolders
    process_nodes(src_node, dst_node, options, src_subfolder_path, dst_subfolder_path)


def conversion(source_dir: str, dest_dir: str, can_remove: bool) :
    source_files = scan_directory(source_dir, INPUT_EXTENSIONS)
    print('Found', source_files.file_count, 'input files')

    dest_files = scan_directory(dest_dir, [OUTPUT_EXTENSION])
    print('Found', dest_files.file_count, 'files in the destination directory')

    process(source_files, dest_files, options = Options(can_remove))
