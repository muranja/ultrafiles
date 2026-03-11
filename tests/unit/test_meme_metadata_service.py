# Tests for MemeMetadataService
import unittest
from unittest.mock import MagicMock
import sys
import tempfile

from src.services.meme_metadata_service import MemeMetadataService


class TestMemeMetadataService(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        sys.modules["gi.repository.GLib"].get_user_config_dir = MagicMock(
            return_value=self.tmpdir.name
        )
        self.service = MemeMetadataService()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_caption_save_and_retrieve(self):
        uri = "file:///tmp/cat.mp4"
        self.assertEqual(self.service.get_caption(uri), "")
        ok = self.service.set_caption(uri, "Crying Cat")
        self.assertTrue(ok)
        self.assertEqual(self.service.get_caption(uri), "Crying Cat")

    def test_search_captions(self):
        uri_cat = "file:///tmp/cat.mp4"
        uri_dog = "file:///tmp/dog.mp4"
        self.service.set_caption(uri_cat, "Crying Cat")
        self.service.set_caption(uri_dog, "Happy Dog")

        results = self.service.search_captions("cat")
        self.assertIn(uri_cat, results)
        self.assertNotIn(uri_dog, results)


if __name__ == '__main__':
    unittest.main()
