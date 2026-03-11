import gi

gi.require_version("Adw", "1")
from gi.repository import Adw

print(f"Adw version: {Adw.get_major_version()}.{Adw.get_minor_version()}")
try:
    print(f"Adw.Dialog available: {hasattr(Adw, 'Dialog')}")
except:
    pass
