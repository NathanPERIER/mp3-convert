
import os
import sys
import itertools
import traceback
from datetime import datetime
from tqdm import tqdm

from typing import Optional, Tuple, Iterable

from src.options import options as prog_options
from src.metrics import ConversionMetrics, ExitStatus
from src.metadata.keep import ConvertKeep
from src.collections.file_tree import FilesystemNode, FilesystemLeaf
from src.utils.directory_analyser import scan_directory
from src.utils.print_iterator     import PrintIterator
from src.metadata.parsing import read_metadata
from src.patches import Patch, ClearDirPatch, ConvertPatch, CopyPatch, CreateDirPatch, RemovePatch


INPUT_EXTENSIONS = ['flac', 'm4a', 'mp3']
OUTPUT_EXTENSION = 'mp3'


def remove_file(leaf: FilesystemLeaf, parent: FilesystemNode, path: str) -> Patch :
    res = RemovePatch(os.path.join(path, leaf.filename()))
    parent.drop_file(leaf.name)
    return res

def convert_file(leaf: FilesystemLeaf, source_folder: str, dest_folder: str, dest_dt: Optional[datetime] = None) -> Iterable[Patch] :
    source_file = os.path.join(source_folder, leaf.filename())
    if dest_dt != None and dest_dt >= leaf.modification :
        return []
    if leaf.extension == OUTPUT_EXTENSION :
        return [ CopyPatch(source_file, dest_folder, dest_dt is not None) ]
    dest_file = os.path.join(dest_folder, f"{leaf.name}.{OUTPUT_EXTENSION}")
    return [ ConvertPatch(source_file, dest_file, dest_dt is not None) ]


def add_directory(name: str, node: FilesystemNode, path: str) -> Tuple[FilesystemNode, Optional[Patch]] :
    subpath = os.path.join(path, name)
    res_node = node.push_subfolder(name)
    res_patch = None
    if not os.path.exists(subpath) :
        res_patch = CreateDirPatch(subpath)
    return (res_node, res_patch)
    

def recursive_remove(node: FilesystemNode, parent: FilesystemNode, path: str) -> Iterable[Patch] :
    subfolder_path = os.path.join(path, node.name)
    res = itertools.chain(
        (remove_file(file, node, subfolder_path) for file in list(node.files.values())),
        itertools.chain.from_iterable(recursive_remove(node, parent, subfolder_path) for node in list(node.subfolders.values())),
        [ ClearDirPatch(os.path.join(path, node.name)) ]
    )
    parent.drop_folder(node.name)
    return res



# Leaf
# - Source exists, destination doesn't => cp/ffmpeg
# - Source exists, destination exists  => cp/ffmpeg if source strictly older than destination
# - Destination exists, source doesn't => if can_remove, rm

def process_leaves(src_node: FilesystemNode, dst_node: FilesystemNode, metrics: ConversionMetrics, src_base_path: Optional[str], dst_base_path: Optional[str]) -> "list[Patch]" :
    res: list[Patch] = []

    if prog_options.keep_treshold != ConvertKeep.lowest() :
        for leaf in src_node.list_files() :
            read_metadata(src_base_path, leaf, prog_options.default_keep, metrics.convert_tags)
            if leaf.metadata is None or leaf.metadata.keep <= prog_options.keep_treshold :
                continue
            metrics.ignored_files.incr(leaf.extension)
            print(f"IGNORE ({leaf.metadata.keep.name.lower()}) {os.path.join(src_base_path, leaf.filename())}")
            src_node.drop_file(leaf.name)
    
    src_file_entries = src_node.list_files()
    dst_file_entries = dst_node.list_files()
    i_src = 0
    i_dst = 0

    while i_src < len(src_file_entries) and i_dst < len(dst_file_entries) :
        src_entry = src_file_entries[i_src]
        dst_entry = dst_file_entries[i_dst]
        if src_entry.name == dst_entry.name :
            res.extend(convert_file(src_entry, src_base_path, dst_base_path, dst_entry.modification))
            i_src += 1
            i_dst += 1
        elif src_entry.name < dst_entry.name : # input file doesn't exist in the destination tree
            res.extend(convert_file(src_entry, src_base_path, dst_base_path))
            i_src += 1
        else :                                         # output file doesn't exist in the source tree
            if prog_options.can_remove :
                res.append(remove_file(dst_entry, dst_node, dst_base_path))
            i_dst += 1
    
    # remaining files that exist only in the source tree
    while i_src < len(src_file_entries) :
        res.extend(convert_file(src_file_entries[i_src], src_base_path, dst_base_path))
        i_src += 1
    
    # remaining files that exist only in the destination tree
    if prog_options.can_remove :
        while i_dst < len(dst_file_entries) :
            res.append(remove_file(dst_file_entries[i_dst], dst_node, dst_base_path))
            i_dst += 1
    
    return res



# Node
# - Source exists, destination doesn't => mkdir, add empty node in the destination, keep going
# - Source exists, destination exists  => keep going
# - Destination exists, source doesn't => if can_remove, rm recursively (only files)

def process_nodes(src_node: FilesystemNode, dst_node: FilesystemNode, metrics: ConversionMetrics, src_base_path: Optional[str], dst_base_path: Optional[str]) -> "list[Patch]" :
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
            if prog_options.can_remove :
                res.extend(recursive_remove(dst_entry, dst_node, dst_base_path))
            i_dst += 1
            continue
        if src_entry.name < dst_entry.name : # input folder doesn't exist in the destination tree
            dst_entry, mkdir_patch = add_directory(src_entry.name, dst_node, dst_base_path)
        else :
            i_dst += 1
        i_src += 1
        patches = process(src_entry, dst_entry, metrics, src_base_path, dst_base_path)
        if len(patches) > 0 :
            if mkdir_patch is not None :
                res.append(mkdir_patch)
            res.extend(patches)
    
    # remaining folders that exist only in the source tree
    while i_src < len(src_folder_entries) :
        src_node = src_folder_entries[i_src]
        dst_node, mkdir_patch = add_directory(src_node.name, dst_node, dst_base_path)
        patches = process(src_node, dst_node, metrics, src_base_path, dst_base_path)
        if len(patches) > 0 :
            if mkdir_patch is not None :
                res.append(mkdir_patch)
            res.extend(patches)
        i_src += 1
    
    # remaining folders that exist only in the destination tree
    if prog_options.can_remove :
        while i_dst < len(dst_folder_entries) :
            res.extend(recursive_remove(dst_folder_entries[i_dst], dst_node, dst_base_path))
            i_dst += 1
    
    return res



def process(src_node: FilesystemNode, dst_node: FilesystemNode, metrics: ConversionMetrics, src_base_path: Optional[str] = None, dst_base_path: Optional[str] = None) -> "list[Patch]" :
    src_subfolder_path = src_node.name if src_base_path is None else os.path.join(src_base_path, src_node.name)
    dst_subfolder_path = dst_node.name if dst_base_path is None else os.path.join(dst_base_path, dst_node.name)
    return list(itertools.chain(
        # Files
        process_leaves(src_node, dst_node, metrics, src_subfolder_path, dst_subfolder_path),
        # Subfolders
        process_nodes(src_node, dst_node, metrics, src_subfolder_path, dst_subfolder_path)
    ))


def compute_patches(source_dir: str, dest_dir: str, metrics: ConversionMetrics) -> "list[Patch]" :
    source_files = scan_directory(source_dir, INPUT_EXTENSIONS)
    print('Found', source_files.file_count, 'input files')
    source_files.walk_leaves(lambda node: metrics.input_files.incr(node.extension))

    dest_files = scan_directory(dest_dir, [OUTPUT_EXTENSION])
    print('Found', dest_files.file_count, 'files in the destination directory')
    dest_files.walk_leaves(lambda node: metrics.output_files.incr(node.extension))

    print('Processing trees and metadata')
    return process(source_files, dest_files, metrics)


def dry_run(patches: "list[Patch]", metrics: ConversionMetrics) -> ConversionMetrics :
    print('\n --- Patch summary --- ')
    for p in patches :
        print(p.describe())
        metrics.patches.incr(p.get_name())
    return metrics.end()


def conversion(source_dir: str, dest_dir: str) -> ConversionMetrics :
    metrics = ConversionMetrics()

    try:
        patches = compute_patches(source_dir, dest_dir, metrics)

        if len(patches) == 0 :
            print("Nothing to do")
            return metrics.end()

        if prog_options.dry_run :
            return dry_run(patches, metrics)
        
        print('Applying patches')

        patches_it = tqdm(patches, desc='Progress', unit='patch') if os.isatty(sys.stdout.fileno()) else PrintIterator(patches)
        
        for p in patches_it :
            p.apply()
            metrics.patches.incr(p.get_name())
    except Exception :
        metrics.status = ExitStatus.ERROR
        traceback.print_exc(file = sys.stderr)
    
    return metrics.end()
