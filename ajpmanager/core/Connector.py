from ajpmanager.core.providers.KVM import KVMProvider

class VMConnector(object):
    " Interface for VM daemons "

    providers = {'xen': None,
                 'kvm': KVMProvider}

    _conn = None

    def __init__(self):
        self.db = DBConnection()
        self.__select_vm_provider()
        assert self._conn, 'No connector found'
        self.clone()

    def __select_vm_provider(self):
        " This functino recognizes - which VM provider we must use - Xen or Qemu+KVM (or any else)"

        # Part 1
        try:
            import XenAPI # If no xen api installed we can't work with Xen
            # do something, check, TODO and FIXME :)
            raise Exception
        except Exception:
            pass
        else:
            self._conn = self.providers['xen'](self.db.io)

        # Part 2
        try:
            import libvirt # for KVM & Qemu
            # etc etc...
        except Exception:
            pass
        else:
            self._conn = self.providers['kvm'](self.db.io)


        # PS: So it means that if we have Xen and KVM available we'll use KVM


    def clone(self):
        self._conn.clone_machine('base', 'blah')




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