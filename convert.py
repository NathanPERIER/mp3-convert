#!/usr/bin/python3

import sys

from src.conversion import conversion


def help() :
    print(f"{sys.argv[0]} [--dry-run] [--no-remove] <source> <destination>")


def main() :

    i = 1

    if i < len(sys.argv) and sys.argv[i] in ['-h', '--help'] :
        help()
        sys.exit(0)

    dry_run = False
    if i < len(sys.argv) and sys.argv[i] == '--dry-run' :
        dry_run = True
        i += 1
    
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

    conversion(source_dir, dest_dir, can_remove, dry_run)


if __name__== '__main__' :
    main() 
