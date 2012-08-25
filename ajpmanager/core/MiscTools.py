import os
import posixpath

_os_alt_seps = list(sep for sep in [os.path.sep, os.path.altsep]
    if sep not in (None, '/'))

def safe_join(directory, filename):
    """Safely join `directory` and `filename`.  If this cannot be done,
    this function returns ``None``.

    :param directory: the base directory.
    :param filename: the untrusted filename relative to that directory.
    """
    filename = posixpath.normpath(filename)
    for sep in _os_alt_seps:
        if sep in filename:
            return None
    if os.path.isabs(filename) or filename.startswith('.'):
        return None
    return os.path.join(directory, filename)