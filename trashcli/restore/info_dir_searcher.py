from typing import NamedTuple, Iterable

from trashcli.restore.info_files import InfoFiles
from trashcli.restore.trash_directories import TrashDirectories


class InfoDirSearcher:
    def __init__(self,
                 trash_directories,  # type: TrashDirectories
                 info_files, # type: InfoFiles
                 ):
        self.trash_directories = trash_directories
        self.info_files = info_files

    def all_file_in_info_dir(self, trash_dir_from_cli): # type: (str) -> Iterable[FileFound]
        for path, volume in self.trash_directories.list_trash_dirs(
                trash_dir_from_cli):
            for type, path in self.info_files.all_info_files(path):
                yield FileFound(type, path, volume)


class FileFound(NamedTuple('Info', [
    ('type', 'str'),
    ('path', 'str'),
    ('volume', 'str'),
])):
    pass
