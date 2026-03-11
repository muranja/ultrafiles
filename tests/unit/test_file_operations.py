# Tests for FileOperations
import unittest
from unittest.mock import MagicMock
import sys
import os

# Assume global mocks from run_tests.py
# Configure specifics for this test module if needed, but not overwriting module
gio = sys.modules["gi.repository.Gio"]
gio.FileCopyFlags.NONE = 0
gio.Cancellable = MagicMock
gio.File = MagicMock

gio.File = MagicMock

from src.services.file_operations import FileOperationsService

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.service = FileOperationsService()
        self.service.emit = MagicMock() # Mock the emit method

    def test_delete_files(self):
        file_mock = MagicMock()
        file_mock.trash_async = MagicMock()
        
        self.service.trash_files([file_mock])
        
        file_mock.trash_async.assert_called()

if __name__ == '__main__':
    unittest.main()
