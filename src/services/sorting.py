# SPDX-License-Identifier: GPL-3.0-or-later
"""
Sorting Service
Implements natural sorting algorithms for file lists.
Adheres to strict performance rails (efficient key generation).
"""

import re
import locale
from typing import Any, List

class NaturalSorter:
    """
    Provides natural sorting functionality.
    Splits strings into text and numeric parts for human-friendly sorting.
    """

    @staticmethod
    def _natural_key(text: str) -> List[Any]:
        """
        Generates a key for natural sorting.
        Splits text into chunks of text and numbers.
        Numbers are converted to integers for numeric comparison.
        Text is converted to lowercase for case-insensitive comparison.
        Each chunk is wrapped in a (type_flag, value) tuple so that
        int and str chunks are never compared directly (Python 3 TypeError).
        """
        if not text:
            return []
            
        def convert(text):
            if text.isdigit():
                return (0, int(text))   # 0 = numeric, sorts before text
            return (1, text.lower())    # 1 = text

        return [convert(c) for c in re.split(r'(\d+)', text) if c]

    @staticmethod
    def compare(item1: Any, item2: Any, attribute_getter: callable) -> int:
        """
        Compare two items using natural sort on the attribute.
        Returns: -1 if item1 < item2, 0 if equal, 1 if item1 > item2.
        """
        val1 = attribute_getter(item1)
        val2 = attribute_getter(item2)
        
        # Handle None
        if val1 is None and val2 is None:
            return 0
        if val1 is None:
            return -1
        if val2 is None:
            return 1
            
        key1 = NaturalSorter._natural_key(str(val1))
        key2 = NaturalSorter._natural_key(str(val2))
        
        if key1 < key2:
            return -1
        elif key1 > key2:
            return 1
        return 0
