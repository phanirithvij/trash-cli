import unittest

from trashcli.put.file_trasher import TopDirRelativePaths, AbsolutePaths
from trashcli.put.original_location import OriginalLocation, parent_realpath
from trashcli.put.path_maker import PathMakerType
from trashcli.put.trash_directory_for_put import TrashDirectoryForPut
from mock import Mock


class TestHowOriginalLocationIsStored(unittest.TestCase):

    def test_for_absolute_paths(self):
        fs = Mock()
        paths = AbsolutePaths()
        self.path_maker_type = PathMakerType.absolute_paths
        original_location = OriginalLocation(parent_realpath)
        self.dir = TrashDirectoryForPut('/volume/.Trash', '/volume', fs,
                                        paths, None, original_location)

        self.assert_path_for_trashinfo_is('/file', '/file')
        self.assert_path_for_trashinfo_is('/file', '/dir/../file')
        self.assert_path_for_trashinfo_is('/outside/file', '/outside/file')
        self.assert_path_for_trashinfo_is('/volume/file', '/volume/file')
        self.assert_path_for_trashinfo_is('/volume/dir/file',
                                          '/volume/dir/file')

    def test_for_relative_paths(self):
        paths = TopDirRelativePaths('/volume')
        self.path_maker_type = PathMakerType.relative_paths
        original_location = OriginalLocation(parent_realpath)
        self.dir = TrashDirectoryForPut('/volume/.Trash', '/volume', Mock(),
                                        paths, None, original_location)

        self.assert_path_for_trashinfo_is('/file', '/file')
        self.assert_path_for_trashinfo_is('/file', '/dir/../file')
        self.assert_path_for_trashinfo_is('/outside/file', '/outside/file')
        self.assert_path_for_trashinfo_is('file', '/volume/file')
        self.assert_path_for_trashinfo_is('dir/file', '/volume/dir/file')

    def assert_path_for_trashinfo_is(self, expected_value, file_to_be_trashed):
        result = self.dir.path_for_trash_info_for_file(file_to_be_trashed,
                                                       self.path_maker_type)
        assert expected_value == result
