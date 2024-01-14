#!/usr/bin/python3

import sys
from collections import deque

from src.options import options as prog_options
from src.conversion import conversion


def help() :
    print(f"{sys.argv[0]} [--dry-run] [--no-remove] [--keep-threshold <keep>] [--default-keep <keep>] <source> <destination>")


def main() :

    args = deque(sys.argv[1:])

    if len(args) > 0 and args[0] in ['-h', '--help'] :
        help()
        sys.exit(0)

    if len(args) > 0 and args[0] == '--dry-run' :
        prog_options.dry_run = True
        args.popleft()
    
    if len(args) > 0 and args[0] == '--no-remove' :
        prog_options.can_remove = False
        args.popleft()
    
    if len(args) != 2 :
        help()
        sys.exit(1)

    source_dir = args.popleft()
    dest_dir = args.popleft()

    if source_dir.endswith('/') :
        source_dir = source_dir[:-1]
    if dest_dir.endswith('/') :
        dest_dir = dest_dir[:-1]

    conversion(source_dir, dest_dir)


if __name__== '__main__' :
    main() 
