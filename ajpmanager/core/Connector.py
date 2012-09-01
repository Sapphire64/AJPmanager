from ajpmanager.core.providers.KVM import KVMProvider

class VMConnector(object):
    " Interface for VM daemons "

    providers = {#'xen': None,
                 'kvm': KVMProvider}

    conn = None

    def __init__(self):
        self.db = DBConnection()
        self.db.io.set('provider', 'kvm')
        self.conn = self.__select_vm_provider()(self.db.io) # Raise if not found

    @property
    def dbcon(self):
        return self.db.io


    def __select_vm_provider(self):
        """ This function recognizes - which VM provider we must
        use - Xen or Qemu+KVM (or any else) """
        if self.conn:
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
        return self.conn.run_machine(name)


    def get_vms_list(self):
        if not self.__select_vm_provider():
            return
        return self.conn.get_machines_list()

    def get_presets_list(self):
        if not self.__select_vm_provider():
            return
        return self.conn.get_presets_list()


class DBConnection(object):

    def __init__(self, host='localhost', port=6379, db=0):
        from time import time
        t1 = time()
        import redis
        self._connection = redis.StrictRedis(host=host, port=port, db=db)
        print ('Redis: ' + str(time() - t1))

    @property
    def io(self):
        return self._connection
