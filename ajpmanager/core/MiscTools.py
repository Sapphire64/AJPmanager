from ajpmanager.core.utils.DiskUsage import disk_usage

import os
import posixpath
import shutil

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


def get_storage_info(path):
    total, used, free = disk_usage(path)
    return (total, used, free)

def calculate_flat_folder_size(path):
    # sum([os.path.getsize(f) for f in os.listdir(path) if os.path.isfile(f)]) # Short but doesn't work w/o safe_join
    sum = 0
    for f in os.listdir(path):
        fpath = safe_join(path, f)
        if os.path.isfile(fpath):
            sum += os.path.getsize(fpath)
    return sum




    
    
class PathGetter(object):

    def __init__(self, dbcon):
        self.db = dbcon

    @property
    def KVM_PATH(self):
        return self.db.get('KVM_PATH')

    @property
    def PRESETS(self):
        return self.db.get('PRESETS')

    @property
    def IMAGES(self):
        return self.db.get('IMAGES')

    @property
    def CONFIG_NAME(self):
        return self.db.get('CONFIG_NAME')

    @property
    def VMIMAGE_NAME(self):
        return self.db.get('VMIMAGE_NAME')

    @property
    def DESCRIPTION_NAME(self):
        return self.db.get('DESCRIPTION_NAME')

    @property
    def VMMANAGER_PATH(self):
        return self.db.get('VMMANAGER_PATH')