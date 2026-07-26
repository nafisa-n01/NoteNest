# app_paths.py
#
# The single, shared answer to "where does this app's writable,
# private data live." Used by anything that needs to read/write a
# real file on disk that isn't the SQLite database itself.
#
# Deliberately a LAZY function, not a module-level constant computed
# at import time -- on Android, imports happen before the Kivy App
# instance exists, so anything computed at import time can't safely
# ask App.get_running_app() yet. Calling this only at actual
# read/write time (well after the app is running) sidesteps that.

import os
from kivy.utils import platform

_cached_app_data_dir = None


def get_app_data_dir():
    """
    Returns a writable, app-private directory path.
    - On Android: the app's real user_data_dir (private internal
      storage), via Kivy's own cross-platform API for this.
    - On desktop: the project root.
    Cached after the first successful call.
    """
    global _cached_app_data_dir
    if _cached_app_data_dir is not None:
        return _cached_app_data_dir

    if platform == "android":
        from kivy.app import App
        app = App.get_running_app()
        if app is None:
            raise RuntimeError(
                "get_app_data_dir() called before the Kivy App has "
                "started. This should only be called after build() "
                "is underway, not at module import time."
            )
        _cached_app_data_dir = app.user_data_dir
        return _cached_app_data_dir

    _cached_app_data_dir = os.path.dirname(os.path.abspath(__file__))
    return _cached_app_data_dir