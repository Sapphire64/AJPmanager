from ajpmanager.core.providers.KVM import KVMProvider

class VMConnector(object):
    " Interface for VM daemons "

    providers = {#'xen': None,
                 'kvm': KVMProvider}

    conn = None

    def __init__(self):
        self.db = DBConnection()
        self.db.io.set('provider', 'kvm')
        self.__select_vm_provider()
        self.conn = self.conn(self.db.io)
        assert self.conn, 'No connector found'


    def __select_vm_provider(self):
        " This functino recognizes - which VM provider we must use - Xen or Qemu+KVM (or any else)"
        if self.conn:
            return True

        provider = self.db.io.get('provider')

        if self.providers[provider].check_availability():
                self.conn = self.providers[provider]

        if self.conn:
            return True
        else:
            return False


    def clone(self, base, new_name):
        if not self.__select_vm_provider():
            return
        self.conn.clone_machine(base, new_name)


    def get_vms_list(self):
        if not self.__select_vm_provider():
            return
        return self.conn.get_machines_list()



    def prr(self):
        print ('HI!!!')




class DBConnection(object):

    def __init__(self, host='localhost', port=6379, db=0):
        import redis
        self._connection = redis.StrictRedis(host=host, port=port, db=db)

    @property
    def io(self):
        return self._connection

    """
        >>> r.set('foo', 'bar')
        True
        >>> r.get('foo')
        'bar'

        r.expire('foo', 10)


    """