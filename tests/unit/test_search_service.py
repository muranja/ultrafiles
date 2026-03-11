# Tests for SearchService
import unittest
from unittest.mock import MagicMock
import sys
import os

# Assume mocks are setup by runner.
# But if running standalone, we need to handle it? 
# For now, assume runner or manual setup.

# Standard import
from src.services.search_service import SearchService

class TestSearchService(unittest.TestCase):
    def setUp(self):
        self.service = SearchService()
        self.service.emit = MagicMock()
        self.mock_dir = MagicMock()
        self.mock_dir.get_path.return_value = "/test/path"

    def test_search_ripgrep_init(self):
        """Test ripgrep initialization and call"""
        self.service._rg_path = "/usr/bin/rg"
        
        # Get global mock
        gio_mock = sys.modules["gi.repository.Gio"]
        mock_proc = MagicMock()
        gio_mock.Subprocess.new.return_value = mock_proc
        
        # Call search
        self.service.search(self.mock_dir, "query")
        
        # Verify
        gio_mock.Subprocess.new.assert_called_once()
        args = gio_mock.Subprocess.new.call_args[0][0]
        self.assertIn("/usr/bin/rg", args)
        self.assertIn("*query*", args)

if __name__ == '__main__':
    unittest.main()
