# Tests for ClipboardService
import unittest
from unittest.mock import MagicMock
import sys
import os

# Assume global mocks from run_tests.py

# Standard imports
from src.services.clipboard_service import ClipboardService

class TestClipboardService(unittest.TestCase):
    def setUp(self):
        # Configure Gdk.Display.get_default().get_clipboard()
        self.mock_clipboard = MagicMock()
        self.mock_display = MagicMock()
        self.mock_display.get_clipboard.return_value = self.mock_clipboard
        
        gdk = sys.modules["gi.repository.Gdk"]
        gdk.Display.get_default.return_value = self.mock_display
        
        self.service = ClipboardService()
        self.service.emit = MagicMock()

    def test_copy_files(self):
        files = [MagicMock()]
        files[0].get_path.return_value = "/path/to/file"
        files[0].get_uri.return_value = "file:///path/to/file"
        
        self.service.set_files(files)
        
        # Verify set called with texture/string?
        # ClipboardService logic:
        # content = Gdk.ContentProvider.new_for_value(Gdk.FileList.new(files))
        # clipboard.set_content(content)
        
        self.mock_clipboard.set_content.assert_called()
        self.service.emit.assert_called_with('changed')

if __name__ == '__main__':
    unittest.main()
