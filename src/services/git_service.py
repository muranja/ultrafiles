# SPDX-License-Identifier: GPL-3.0-or-later
"""
Git Service
Retrieves git status for files in a directory.
Adheres to strict async rails (Gio.Subprocess).
"""

import gi
from typing import Dict, Optional

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib, GObject

class GitStatus:
    UNMODIFIED = "unmodified"
    MODIFIED = "modified"
    STAGED = "staged"
    UNTRACKED = "untracked"
    IGNORED = "ignored"
    CONFLICT = "conflict"

class GitService(GObject.Object):
    """
    Service for git operations.
    signals:
        status-ready: (path, status_dict)
    """
    
    __gsignals__ = {
        'status-ready': (GObject.SignalFlags.RUN_FIRST, None, (str, object)), # object = PyObject (dict)
    }

    def __init__(self):
        super().__init__()

    def get_repo_root(self, path: str) -> Optional[str]:
        """Check if path is in a git repo and return root"""
        # Synchronous check implies blocking?
        # Use simple check for .git provided we are already in a thread or 
        # accept slight delay. 
        # Better: assume yes and try running git status, if fails, not a repo.
        return None # TODO: Implement if needed.

    def fetch_status(self, directory: str):
        """
        Async fetch git status for directory.
        Emit 'status-ready' with dict of {filename: GitStatus}.
        """
        # git status --porcelain -z --ignored
        # -z for null termination (safe parsing)
        
        try:
            # Use Gio.SubprocessLauncher to set CWD
            launcher = Gio.SubprocessLauncher()
            launcher.set_cwd(directory)
            launcher.set_flags(Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE)
            subprocess = launcher.spawnv(["git", "status", "--porcelain", "-z", "--ignored", "."])
            
            subprocess.communicate_utf8_async(None, None, self._on_status_output, directory)
            
        except GLib.Error:
            # Likely not a git repo or git missing
            self.emit('status-ready', directory, {})

    def _on_status_output(self, proc, result, directory):
        try:
            success, stdout, stderr = proc.communicate_utf8_finish(result)
            if not success or not stdout:
                self.emit('status-ready', directory, {})
                return

            status_map = {}
            # Parse porcelain output
            # XY PATH\0
            # or XY PATH1 -> PATH2\0
            
            parts = stdout.split('\0')
            for part in parts:
                if not part or len(part) < 4:
                    continue
                    
                xy = part[:2]
                path = part[3:]
                
                # Determine status
                status = GitStatus.UNMODIFIED
                if xy == "??":
                    status = GitStatus.UNTRACKED
                elif xy == "!!":
                    status = GitStatus.IGNORED
                elif 'M' in xy:
                    status = GitStatus.MODIFIED
                elif 'A' in xy:
                    status = GitStatus.STAGED
                elif 'U' in xy:
                    status = GitStatus.CONFLICT
                    
                status_map[path] = status
                
            self.emit('status-ready', directory, status_map)
            
        except GLib.Error:
            self.emit('status-ready', directory, {})
