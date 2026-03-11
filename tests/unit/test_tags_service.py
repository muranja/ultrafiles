# Tests for TagsService
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Assume global mocks from run_tests.py

# Standard imports
from src.services.tags_service import TagsService

class TestTagsService(unittest.TestCase):
    def setUp(self):
        # Configure env
        config_mock = MagicMock(return_value="/tmp/config")
        sys.modules["gi.repository.GLib"].get_user_config_dir = config_mock
        
        # Patch file ops
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()
        
        self.patcher_open = patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='{"file_tags": {}}')
        self.mock_open = self.patcher_open.start()
        
        self.service = TagsService()
        self.service.emit = MagicMock()

    def tearDown(self):
        self.patcher_exists.stop()
        self.patcher_open.stop()

    def test_toggle_tag(self):
        self.service.toggle_tag("/path/to/file", "Red")
        tags = self.service.get_tags_for_file("/path/to/file")
        self.assertIn("Red", tags)
        self.service.emit.assert_called()

if __name__ == '__main__':
    unittest.main()
