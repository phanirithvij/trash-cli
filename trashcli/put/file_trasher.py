import os
import random
from datetime import datetime
from typing import Callable, Dict, Optional

from trashcli.fstab import Volumes
from trashcli.put.info_dir import InfoDir
from trashcli.put.my_logger import MyLogger
from trashcli.put.original_location import OriginalLocation, parent_realpath
from trashcli.put.reporter import TrashPutReporter
from trashcli.put.security_check import SecurityCheck
from trashcli.put.suffix import Suffix
from trashcli.put.trash_directories_finder import TrashDirectoriesFinder
from trashcli.put.real_fs import RealFs
from trashcli.put.trash_directory_for_put import TrashDirectoryForPut
from trashcli.put.trash_result import TrashResult
from trashcli.put.path_maker import PathMaker


class PossibleTrashDirectories:
    def __init__(self, trash_directories_finder, user_trash_dir,
                 environ, uid):
        self.trash_directories_finder = trash_directories_finder
        self.user_trash_dir = user_trash_dir
        self.environ = environ
        self.uid = uid

    def trash_directories_for(self, volume_of_file_to_be_trashed):
        return self.trash_directories_finder. \
            possible_trash_directories_for(volume_of_file_to_be_trashed,
                                           self.user_trash_dir, self.environ,
                                           self.uid)


class FileTrasher:

    def __init__(self,
                 fs,  # type: RealFs
                 volumes,  # type: Volumes
                 realpath,  # type: Callable[[str], str]
                 now,  # type: Callable[[], datetime]
                 trash_directories_finder,  # type: TrashDirectoriesFinder
                 parent_path,  # type: Callable[[str], str]
                 logger,  # type: MyLogger
                 reporter,  # type: TrashPutReporter
                 trash_file_in=None,  # type: TrashFileIn
                 ):  # type: (...) -> None
        self.fs = fs
        self.volumes = volumes
        self.realpath = realpath
        self.now = now
        self.trash_directories_finder = trash_directories_finder
        self.parent_path = parent_path
        self.logger = logger
        self.reporter = reporter
        self.trash_file_in = trash_file_in

    def trash_file(self,
                   path,  # type: str
                   forced_volume,
                   user_trash_dir,
                   result,  # type: TrashResult
                   environ,  # type: Dict[str, str]
                   uid,  # type: int
                   program_name,  # type: str
                   verbose,  # type: int
                   ):
        volume_of_file_to_be_trashed = forced_volume or \
                                       self.volume_of_parent(path)
        candidates = self.trash_directories_finder. \
            possible_trash_directories_for(volume_of_file_to_be_trashed,
                                           user_trash_dir, environ, uid)
        self.reporter.volume_of_file(volume_of_file_to_be_trashed, program_name,
                                     verbose)
        file_has_been_trashed = False
        for trash_dir_path, volume, path_maker, checker in candidates:
            file_has_been_trashed = self.trash_file_in.trash_file_in(path,
                                                                     trash_dir_path,
                                                                     volume,
                                                                     path_maker,
                                                                     checker,
                                                                     file_has_been_trashed,
                                                                     volume_of_file_to_be_trashed,
                                                                     program_name,
                                                                     verbose,
                                                                     environ)
            if file_has_been_trashed: break

        if not file_has_been_trashed:
            result = result.mark_unable_to_trash_file()
            self.reporter.unable_to_trash_file(path, program_name)

        return result

    def volume_of_parent(self, file):
        return self.volumes.volume_of(self.parent_path(file))


class TrashFileIn:
    def __init__(self, fs, realpath, volumes, now, parent_path,
                 reporter, info_dir, trash_dir):
        self.fs = fs
        self.realpath = realpath
        self.volumes = volumes
        self.now = now
        self.parent_path = parent_path
        self.reporter = reporter
        self.path_maker = PathMaker()
        self.security_check = SecurityCheck()
        self.info_dir = info_dir
        self.trash_dir = trash_dir

    def trash_file_in(self,
                      path,
                      trash_dir_path,
                      volume,
                      path_maker_type,
                      check_type,
                      file_has_been_trashed,
                      volume_of_file_to_be_trashed,
                      program_name,
                      verbose,
                      environ,
                      ):  # type: (...) -> bool
        info_dir_path = os.path.join(trash_dir_path, 'info')
        norm_trash_dir_path = os.path.normpath(trash_dir_path)
        trash_dir_is_secure, messages = self.security_check. \
            check_trash_dir_is_secure(norm_trash_dir_path,
                                      self.fs,
                                      check_type)
        for message in messages:
            self.reporter.log_info(message, program_name, verbose)

        if trash_dir_is_secure:
            volume_of_trash_dir = self.volumes.volume_of(
                self.realpath(norm_trash_dir_path))
            self.reporter.trash_dir_with_volume(norm_trash_dir_path,
                                                volume_of_trash_dir,
                                                program_name, verbose)
            if self._file_could_be_trashed_in(
                    volume_of_file_to_be_trashed,
                    volume_of_trash_dir):
                try:
                    self.fs.ensure_dir(trash_dir_path, 0o700)
                    self.fs.ensure_dir(os.path.join(trash_dir_path, 'files'),
                                       0o700)
                    self.trash_dir.trash2(path, self.now, program_name, verbose,
                                          path_maker_type, volume,
                                          info_dir_path)
                    self.reporter.file_has_been_trashed_in_as(
                        path,
                        norm_trash_dir_path,
                        program_name,
                        verbose,
                        environ)
                    file_has_been_trashed = True

                except (IOError, OSError) as error:
                    self.reporter.unable_to_trash_file_in_because(
                        path, norm_trash_dir_path, error, program_name, verbose,
                        environ)
        else:
            self.reporter.trash_dir_is_not_secure(norm_trash_dir_path,
                                                  program_name, verbose)
        return file_has_been_trashed

    def _file_could_be_trashed_in(self,
                                  volume_of_file_to_be_trashed,
                                  volume_of_trash_dir):
        return volume_of_trash_dir == volume_of_file_to_be_trashed