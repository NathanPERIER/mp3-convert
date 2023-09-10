#!/usr/bin/python3

import sys

from src.utils.directory_analyser import scan_directory


def help() :
    print(f"{sys.argv[0]} [--no-remove] <source> <destination>")


def main() :

    i = 1

    if i < len(sys.argv) and sys.argv[i] in ['-h', '--help'] :
        help()
        sys.exit(0)
    
    can_remove = True
    if i < len(sys.argv) and sys.argv[i] == '--no-remove' :
        can_remove = False
        i += 1
    
    if i + 1 >= len(sys.argv) :
        help()
        sys.exit(1)

    source_dir = sys.argv[i]
    dest_dir = sys.argv[i+1]

    if source_dir.endswith('/') :
        source_dir = source_dir[:-1]
    if dest_dir.endswith('/') :
        dest_dir = dest_dir[:-1]

    source_files = scan_directory(source_dir, ['mp3', 'flac', 'm4a'])
    print('Found', source_files.file_count, 'input files')

    dest_files = scan_directory(dest_dir, ['mp3'])
    print('Found', dest_files.file_count, 'files in the destination directory')


if __name__== '__main__' :
    main() 
