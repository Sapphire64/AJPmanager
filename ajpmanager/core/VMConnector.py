from ajpmanager.core.MiscTools import PathGetter, get_storage_info, safe_join, calculate_flat_folder_size
from ajpmanager.core.providers.KVM import KVMProvider

import libvirt
import socket
import re



localhost = '127.0.0.1' # Hardcoding localhost

FOLDERS_RE = re.compile(r'^[a-zA-Z0-9_-]+$')
FILES_RE = re.compile(r'^[a-zA-Z0-9_.-]+$')

class VMConnector(object):
    " Interface for VM daemons "

    providers = {#'xen': None,
                 'kvm': KVMProvider}

    conn = None

    def __init__(self):
        self.db = DBConnection()
        self.pg = PathGetter(self.db.io)
        self._prepare_hypervisor_connection()

    def _prepare_hypervisor_connection(self, reload=False):
        try:
            self.conn = self.__select_vm_provider(reload)(self.db.io, self.pg) # Raise if not found
        except libvirt.libvirtError as e:
            print ('Cannot create hypervisor connection')
            self.conn = None


    @property
    def dbcon(self):
        return self.db.io

    def __select_vm_provider(self, reload=False):
        """ This function recognizes - which VM provider we must
        use - Xen or Qemu+KVM (or any else) """
        if self.conn and not reload:
            return True

        provider = self.db.io.get('provider')

        if self.providers[provider].check_availability():
                return self.providers[provider]

        return False

    def clone(self, base, new_name):
        if not self.__select_vm_provider():
            return
        self.conn.clone_machine(base, new_name)

    def run_machine(self, name):
        if not self.__select_vm_provider():
            return
        return self.conn.run_machine(name)

    def stop_machine(self, name):
        if not self.__select_vm_provider():
            return
        return self.conn.stop_machine(name)

    def pause_machine(self, name):
        if not self.__select_vm_provider():
            return
        return self.conn.pause_machine(name)

    def destroy_machine(self, name):
        if not self.__select_vm_provider():
            return
        return self.conn.destroy_machine(name)

    def get_vms_list(self, no_cache):
        if not self.__select_vm_provider():
            return
        return self.conn.get_machines_list(no_cache)

    def get_presets_list(self):
        if not self.__select_vm_provider():
            return
        return self.conn.get_presets_list()

    def get_storage_info(self, machine):
        provider = self.db.io.get('provider')
        if provider == 'kvm':
            root = self.pg.KVM_PATH
        elif provider == 'xen':
            root = self.pg.XEN_PATH
        else:
            raise NotImplementedError

        path = safe_join(root, self.pg.IMAGES)
        preset_path = safe_join(root, self.pg.PRESETS)

        total, used, free = get_storage_info(path)
        preset_storage = calculate_flat_folder_size(safe_join(preset_path, machine))
        return (total, used, free, preset_storage)

    def get_settings(self):
        provider = self.db.io.get('provider')
        answer = {}

        if provider == 'kvm':
            answer['path'] = self.pg.KVM_PATH
        elif provider == 'xen':
            answer['path'] = self.pg.XEN_PATH
        else:
            raise NotImplementedError

        answer['provider'] = provider
        answer['images'] = self.pg.IMAGES
        answer['presets'] = self.pg.PRESETS
        answer['config'] = self.pg.CONFIG_NAME
        answer['vmimage'] = self.pg.VMIMAGE_NAME
        answer['description'] = self.pg.DESCRIPTION_NAME
        answer['vmmanager'] = self.pg.VMMANAGER_PATH

        return answer

    def apply_settings(self, data):
        provider = self.db.io.get('provider')

        if not data['path']:
            raise ValueError

        if provider == 'kvm':
            self.db.io.set('KVM_PATH', data['path'])
        elif provider == 'xen':
            self.db.io.set('XEN_PATH', data['path'])
        else:
            raise NotImplementedError

        if not data['presets'] or not FOLDERS_RE.search(data['presets']): # check for only letters and digits, no /
            raise ValueError
        self.db.io.set('PRESETS',data['presets'])

        if not data['images'] or not FOLDERS_RE.search(data['images']):
            raise ValueError
        self.db.io.set('IMAGES', data['images'])   # like 'images'

        if not data['config'] or not FILES_RE.search(data['config']):
            raise ValueError
        self.db.io.set('CONFIG_NAME', data['config']) # like 'config.xml'

        if not data['vmimage'] or not FILES_RE.search(data['vmimage']):
            raise ValueError
        self.db.io.set('VMIMAGE_NAME', data['vmimage'])

        if not data['description'] or not FILES_RE.search(data['description']):
            raise ValueError
        self.db.io.set('DESCRIPTION_NAME', data['description'])

        if not data['vmmanager']:
            raise ValueError
        self.db.io.set('VMMANAGER_PATH', data['vmmanager'])

        self._prepare_hypervisor_connection(reload=True)



    def restore_default_settings(self):
        # Warning! FIXME: we have same functionality in ajpmanager/__init__ module
        # Any changes here must by applied there
        self.db.io.set('XEN_PATH', '/xen')
        self.db.io.set('KVM_PATH', '/kvm')
        self.db.io.set('PRESETS','presets')
        self.db.io.set('IMAGES', 'images')
        self.db.io.set('CONFIG_NAME', 'config.xml')
        self.db.io.set('VMIMAGE_NAME', 'image.img')
        self.db.io.set('DESCRIPTION_NAME', 'description.txt')
        self.db.io.set('VMMANAGER_PATH', 'qemu:///system')

        self._prepare_hypervisor_connection(reload=True)