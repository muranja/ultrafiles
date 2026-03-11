# SPDX-License-Identifier: GPL-3.0-or-later
"""Main entry point for UltraFiles"""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio

from .application import UltraFilesApplication


def main(version: str) -> int:
    """Main entry point"""
    app = UltraFilesApplication(version=version)
    return app.run(sys.argv)


if __name__ == "__main__":
    from . import __version__

    sys.exit(main(__version__))
