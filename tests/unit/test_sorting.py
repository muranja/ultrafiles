# Tests for Sorting Service
# Adheres to testing_rails: Isolation

import unittest
import sys
import os

# Add project root path logic
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.services.sorting import NaturalSorter

class TestNaturalSorter(unittest.TestCase):
    
    def test_natural_key_numbers(self):
        # 2 should come before 10
        key2 = NaturalSorter._natural_key("file2.txt")
        key10 = NaturalSorter._natural_key("file10.txt")
        self.assertLess(key2, key10)
        
    def test_natural_key_mixed(self):
        # file1 < file2 < file10
        files = ["file10.txt", "file1.txt", "file2.txt"]
        files.sort(key=NaturalSorter._natural_key)
        self.assertEqual(files, ["file1.txt", "file2.txt", "file10.txt"])

    def test_compare_objects(self):
        class Item:
            def __init__(self, name):
                self.name = name
        
        items = [Item("Track 10.mp3"), Item("Track 2.mp3"), Item("Track 1.mp3")]
        
        # Sort using compare
        # Python's list.sort expects a key, simplified here using key wrapper mechanism or functools.cmp_to_key
        # But for Gtk.CustomSorter, we use the compare return value (-1, 0, 1) directly.
        # We'll verify basic comparisons manually.
        
        # Track 2 < Track 10
        res = NaturalSorter.compare(items[1], items[0], lambda x: x.name)
        self.assertEqual(res, -1)
        
        # Track 10 > Track 1
        res = NaturalSorter.compare(items[0], items[2], lambda x: x.name)
        self.assertEqual(res, 1)

    def test_complex_names(self):
        # "z1.txt" > "a10.txt" based on letter
        # "file 2" < "file 20"
        
        self.assertLess(NaturalSorter._natural_key("a2"), NaturalSorter._natural_key("a10"))
        self.assertLess(NaturalSorter._natural_key("file 2.txt"), NaturalSorter._natural_key("file 20.txt"))
        
        # Version numbers
        self.assertLess(NaturalSorter._natural_key("v1.2.3"), NaturalSorter._natural_key("v1.2.10"))

if __name__ == '__main__':
    unittest.main()
