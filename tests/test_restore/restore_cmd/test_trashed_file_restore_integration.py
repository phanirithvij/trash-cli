import os
import unittest

from mock import Mock
from six import StringIO

from tests.support.files import make_empty_file
from tests.support.my_path import MyPath
from trashcli.restore.file_system import RealRestoreWriteFileSystem, \
    FakeReadCwd, RealRestoreReadFileSystem
from trashcli.restore.restore_cmd import RestoreCmd
from trashcli.restore.trashed_file import TrashedFile, TrashedFiles


class TestTrashedFileRestoreIntegration(unittest.TestCase):
    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.input_value = None
        self.input = lambda _: self.input_value
        self.temp_dir = MyPath.make_temp_dir()
        cwd = self.temp_dir
        self.logger = Mock(spec=[])
        self.trashed_files = Mock(spec=TrashedFiles)
        self.cmd = RestoreCmd.make(stdout=self.stdout,
                                   stderr=self.stderr,
                                   exit=lambda _: None,
                                   input=self.input,
                                   version="0.0.0",
                                   trashed_files=self.trashed_files,
                                   read_fs=RealRestoreReadFileSystem(),
                                   write_fs=RealRestoreWriteFileSystem(),
                                   read_cwd=FakeReadCwd(cwd))

    def test_restore(self):
        trashed_file = TrashedFile(self.temp_dir / 'parent/path',
                                   None,
                                   self.temp_dir / 'info_file',
                                   self.temp_dir / 'orig')
        make_empty_file(self.temp_dir / 'orig')
        make_empty_file(self.temp_dir / 'info_file')
        self.input_value = '0'

        self.trashed_files.all_trashed_files.return_value = [trashed_file]
        self.cmd.run(['trash-restore'])

        assert os.path.exists(self.temp_dir / 'parent/path')
        assert not os.path.exists(self.temp_dir / 'info_file')
        assert not os.path.exists(self.temp_dir / 'orig')

    def test_restore_over_existing_file(self):
        trashed_file = TrashedFile(self.temp_dir / 'path', None, None, None)
        make_empty_file(self.temp_dir / 'path')
        self.input_value = '0'

        self.trashed_files.all_trashed_files.return_value = [trashed_file]
        self.cmd.run(['trash-restore'])

        assert self.stderr.getvalue() == 'Refusing to overwrite existing file "path".\n'

    def tearDown(self):
        self.temp_dir.clean_up()
