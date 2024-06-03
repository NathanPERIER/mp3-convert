#!/usr/bin/python3

import sys
from collections import deque

from src.options import options as prog_options
from src.conversion import conversion
from src.metrics import ExitStatus
from src.metadata.keep import ConvertKeep


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
    
    if len(args) > 1 and args[0] == '--keep-threshold' :
        args.popleft()
        keep_repr = args.popleft().lower()
        if keep_repr != 'all' :
            keep = ConvertKeep.parse(keep_repr)
            if keep == None :
                print(f"Bad keep threshold : {keep_repr}")
                sys.exit(1)
            prog_options.keep_treshold = keep
    
    if len(args) > 1 and args[0] == '--default-keep' :
        args.popleft()
        keep = ConvertKeep.parse(args.popleft().lower())
        if keep == None :
            print(f"Bad default Convert-Keep value : {keep_repr}")
            sys.exit(1)
        prog_options.default_keep = keep

    
    if len(args) != 2 :
        help()
        sys.exit(1)

    source_dir = args.popleft()
    dest_dir = args.popleft()

    if source_dir.endswith('/') :
        source_dir = source_dir[:-1]
    if dest_dir.endswith('/') :
        dest_dir = dest_dir[:-1]

    metrics = conversion(source_dir, dest_dir)

    print()
    if prog_options.dry_run :
        print(' --- Metrics ---')
        metrics.print()
    else :
        metrics.summary()
    
    if metrics.status != ExitStatus.SUCCESS :
        sys.exit(1)


if __name__== '__main__' :
    main() 
