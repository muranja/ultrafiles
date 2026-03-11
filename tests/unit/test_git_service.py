# Tests for GitService
import unittest
from unittest.mock import MagicMock
import sys
import os

from src.services.git_service import GitService, GitStatus

class TestGitService(unittest.TestCase):
    def setUp(self):
        self.service = GitService()
        self.service.emit = MagicMock()
        self.GitStatus = GitStatus

    def test_fetch_status_success(self):
        gio_mock = sys.modules["gi.repository.Gio"]
        
        # Correctly mock SubprocessLauncher class and instance
        mock_launcher_instance = MagicMock()
        gio_mock.SubprocessLauncher.return_value = mock_launcher_instance
        
        mock_proc = MagicMock()
        mock_launcher_instance.spawnv.return_value = mock_proc
        
        # Trigger fetch
        self.service.fetch_status("/test/repo")
        
        # Verify
        mock_launcher_instance.set_cwd.assert_called_with("/test/repo")
        mock_proc.communicate_utf8_async.assert_called_once()
        
        # Simulate callback
        callback = mock_proc.communicate_utf8_async.call_args[0][2]
        stdout = "M  file1.txt\0?? file2.txt\0"
        mock_proc.communicate_utf8_finish.return_value = (True, stdout, "")
        
        callback(mock_proc, None, "/test/repo")
        
        self.service.emit.assert_called_with('status-ready', "/test/repo", {
            "file1.txt": self.GitStatus.MODIFIED,
            "file2.txt": self.GitStatus.UNTRACKED
        })

if __name__ == '__main__':
    unittest.main()
