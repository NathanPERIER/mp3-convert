
import re
import logging
import subprocess
from datetime import datetime

from typing import Sequence

from src.collections.file_tree import FilesystemNode


logger = logging.getLogger(__name__)


def __make_extension_filter(extensions: Sequence[str]) -> Sequence[str] :
    if len(extensions) == 0 :
        return []
    res = ['-name', f"*.{extensions[0]}"]
    for ext in extensions[1:] :
        res.extend(['-o', '-name', f"*.{ext}"])
    return res


find_line_reg = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+ ([+-]\d{4}) (.+)/([^/]+)\.([^/.]+)')

def scan_directory(directory: str, extensions: Sequence[str]) :
    command = ['find', directory, '-type', 'f', '-a', '(', *__make_extension_filter(extensions), ')', '-printf', '%TF %TT %Tz %p\\n']
    r = subprocess.run(command, check=True, capture_output=True)

    res = FilesystemNode(directory)

    prefix_len = len(directory) + 1
    lines = r.stdout.decode('utf8').rstrip('\n').split('\n')
    if len(lines[0]) <= 1 : # Basically if there are no matching files in the directory
        return res

    for line in lines :
        m = find_line_reg.fullmatch(line)
        if m is None :
            logger.warn(f"Bad format for line : \"{line}\"")
            continue
        date_repr = f"{m.group(1)} {m.group(2)}"
        directory = m.group(3)[prefix_len:]
        filename = m.group(4)
        extension = m.group(5)
        dt = datetime.strptime(date_repr, '%Y-%m-%d %H:%M:%S %z')
        res.push_file(directory, filename, extension, dt)
        logger.debug("(%s) %s/%s.%s", date_repr, directory, filename, extension)

    return res
