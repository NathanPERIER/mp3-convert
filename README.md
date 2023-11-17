# mp3-convert

This is a script I made to convert my music library to MP3. 

```
usage: ./convert.py [--no-remove] [--dry-run] <source> <destination>
```

The idea is that we have a bunch of audio files organised in a directory, for example like this :

```
source_directory
 +- Artist1
 |   +- Album1
 |   |   +- music1.flac
 |   |   +- music2.flac
 |   |   +- album.png
 |   +- Album2
 |   |   +- music1.flac
 |   |   +- music2.flac
 |   |   +- album.jpg
 +- Artist2
 |   +- Album1
 |   |   +- music1.m4a
 |   |   +- music2.m4a
 |   |   +- music3.m4a
 +- random_song.mp3
```

> Note: the folder depth doesn't really matter, audio files can be found in any directory under the source directory, as long as they have a valid extension.

This script can then be used to convert all the files to MP3, while retaining the folder structure :

```
destination_directory
 +- Artist1
 |   +- Album1
 |   |   +- music1.mp3
 |   |   +- music2.mp3
 |   +- Album2
 |   |   +- music1.mp3
 |   |   +- music2.mp3
 +- Artist2
 |   +- Album1
 |   |   +- music1.mp3
 |   |   +- music2.mp3
 |   |   +- music3.mp3
 +- random_song.mp3
```

This conversion typically takes a substantial amount of time for big libraries. In order to avoid doing unnecessary work, the musics will only be converted if there is no equivalent in the destination directory with a higher modification date. Also, the musics that are already in MP3 are directly copied. Hence, when changes are made to the source directory, one simply has to call the script again so that these changes are transposed to the MP3 library. If a music file in the destination directory has no counterpart in the source directory, it will be removed by default (we consider that it was there before but has been removed since the last conversion). This can be prevented with the `--no-remove` argument.

Any file that is not recognised as being an audio file will not be taken into account at all.

For the conversion, the script uses `ffmpeg`, which must be installed on the system. So far, the script has only be tested on a Linux-based OS. 

Edge cases that are currently not taken into account : 
 - node is a folder in the source tree but a file in the destination tree (or the other way around)
 - filesystem naming errors in the destination folder (e.g. source FS is EXT4, destination FS is NTFS)
