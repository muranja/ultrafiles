import sys
import os

current = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(current, "../../.."))
src = os.path.join(root, "src")

print(f"Current: {current}")
print(f"Root: {root}")
print(f"Src: {src}")
print(f"Src exists: {os.path.exists(src)}")
print(f"Src listdir: {os.listdir(src)}")

sys.path.insert(0, root)
print(f"Sys path: {sys.path}")

try:
    import src
    print(f"Imported src: {src}")
    import src.services
    print(f"Imported src.services: {src.services}")
except ImportError as e:
    print(f"Import Error: {e}")
