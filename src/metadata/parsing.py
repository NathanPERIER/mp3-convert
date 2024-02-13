
import os
import functools
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from io import BytesIO

from src.collections.file_tree import ConvertKeep, LeafMetadata, FilesystemLeaf

from typing import Optional


def parse_keep(keep_rep: str) -> Optional[ConvertKeep] :
    try:
        return ConvertKeep[keep_rep.upper()]
    except ValueError:
        return None


class RawMetadata :
    def __init__(self) :
        self.keep: Optional[str] = None


def __read_mp3_for_tags(filepath: str) -> MP3 :
    with open(filepath, 'rb') as f :
        begin = f.read(10)
        f.seek(0)
        if begin[0:3] != b'ID3' :
            return MP3(f)
		
        size_encoded = bytearray(begin[-4:])
        size = functools.reduce(lambda a,b: a*128 + b, size_encoded, 0) + 2881
        data = f.read(size)

    stream = BytesIO()
    stream.write(data)
    stream.seek(0)
    return MP3(stream)

def metadata_mp3(path: str, leaf: FilesystemLeaf) -> RawMetadata :
    filepath = os.path.join(path, leaf.filename())
    res = RawMetadata()

    tags = __read_mp3_for_tags(filepath).tags
    if tags is not None and 'TXXX:Convert-Keep' in tags :
        res.keep = tags['TXXX:Convert-Keep'].text[0].strip()
    
    return res


def metadata_mpeg4(path: str, leaf: FilesystemLeaf) :
    filepath = os.path.join(path, leaf.filename())
    res = RawMetadata()

    with open(filepath, 'rb') as f :
        tags = MP4(f).tags
    
    if tags is not None and 'CONVERT-KEEP' in tags :
        res.keep = tags['CONVERT-KEEP'][0].strip()
    
    return res


def metadata_flac(path: str, leaf: FilesystemLeaf) :
    filepath = os.path.join(path, leaf.filename())
    res = RawMetadata()

    with open(filepath, 'rb') as f :
        tags = FLAC(f).tags
    
    if tags is not None and 'CONVERT-KEEP' in tags :
        res.keep = tags['CONVERT-KEEP'][0].strip()
    
    return res


def read_metadata(path: str, leaf: FilesystemLeaf, default_keep: ConvertKeep) :
    raw = RawMetadata()
    if leaf.extension == 'mp3' :
        raw = metadata_mp3(path, leaf)
    elif leaf.extension == 'flac' :
        raw = metadata_flac(path, leaf)
    elif leaf.extension == 'm4a' :
		rax = metadata_mpeg4(path, leaf)
    else :
        print(f"Unsupported extension for metadata parsing : {leaf.extension}")
    
    keep = default_keep
    if raw.keep is not None :
        parsed_keep = parse_keep(raw.keep)
        if parsed_keep is None :
            print(f"Bad Convert-Keep tag : {raw.keep}, ({os.path.join(path, leaf.filename())})")
        else :
            keep = parsed_keep
    
    leaf.metadata = LeafMetadata(keep)

