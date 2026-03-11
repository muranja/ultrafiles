# Tests for SearchService
import unittest
from unittest.mock import MagicMock, call
import sys
import os

# Assume mocks are setup by runner.
# But if running standalone, we need to handle it? 
# For now, assume runner or manual setup.

# Standard import
from src.services.search_service import SearchService

class TestSearchService(unittest.TestCase):
    def setUp(self):
        self.tags_service = MagicMock()
        self.tags_service.search_by_theme.return_value = []
        self.meme_metadata_service = MagicMock()
        self.meme_metadata_service.search_captions.return_value = []
        self.service = SearchService(
            tags_service=self.tags_service,
            meme_metadata_service=self.meme_metadata_service,
        )
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

    def test_search_includes_captions_and_themes(self):
        self.service._rg_path = None
        self.tags_service.search_by_theme.return_value = ["file:///theme.mp4"]
        self.meme_metadata_service.search_captions.return_value = ["file:///caption.mp4"]

        gio_mock = sys.modules["gi.repository.Gio"]
        gfile_theme = MagicMock()
        gfile_theme.get_uri.return_value = "file:///theme.mp4"
        gfile_caption = MagicMock()
        gfile_caption.get_uri.return_value = "file:///caption.mp4"

        def new_for_uri(uri):
            if uri == "file:///theme.mp4":
                return gfile_theme
            return gfile_caption

        gio_mock.File.new_for_uri.side_effect = new_for_uri

        self.service.search(self.mock_dir, "funny")

        self.service.emit.assert_any_call("search-result", gfile_theme)
        self.service.emit.assert_any_call("search-result", gfile_caption)

if __name__ == '__main__':
    unittest.main()
