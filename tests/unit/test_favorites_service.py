# Tests for FavoritesService
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Assume global mocks from run_tests.py

# Standard imports
from src.services.favorites_service import FavoritesService

class TestFavoritesService(unittest.TestCase):
    def setUp(self):
        # Configure env
        config_mock = MagicMock(return_value="/tmp/config")
        sys.modules["gi.repository.GLib"].get_user_config_dir = config_mock
        
        # Patch file ops
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()
        
        self.patcher_open = patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='{"favorites": []}')
        self.mock_open = self.patcher_open.start()
        
        self.service = FavoritesService()
        self.service.emit = MagicMock()

    def tearDown(self):
        self.patcher_exists.stop()
        self.patcher_open.stop()

    def test_add_favorite(self):
        self.service.add_favorite("/path/to/fav")
        self.assertIn("/path/to/fav", self.service.get_favorites())
        self.service.emit.assert_called_with('changed')

if __name__ == '__main__':
    unittest.main()
