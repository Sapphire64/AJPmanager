from multiprocessing.process import Process
import random
import libvirt
import shutil
from uuid import uuid4
from ajpmanager.core.MiscTools import safe_join


KVM_PATH = '/kvm'


def generate_uuid():
    return str(uuid4())

def generate_mac():
    mac = [ 0x00, 0x33,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))



class KVMProvider(object):

    db = None

    def __init__(self, dbcon):
        print ('Using KVM as a virtual machines server and libvirt for virtualization')
        self.connection = libvirt.open('qemu:///system')
        assert self.connection, 'Failed to open Qemu/KVM connection'
        self.db = dbcon
        self.db.set('copy', '0')

    def list_domains(self):
        return self.connection.listDomainsID()

    def lookup_by_id(self, id, info=False):
        answer = self.connection.lookupByID(id)
        if info:
            return answer.info()
        else:
            return answer

    def clone_machine(self, preset_name, machine_name):
        src = safe_join(KVM_PATH + '/presets/', preset_name)
        dst = safe_join(KVM_PATH + '/images/', machine_name)

        print (src, dst)

        id = 1
        p = Process(target=self._clone, args=(id, src, dst)) # In different process
        p.start()


        print ('Cloned!')

    def _clone(self, id, src, dst):
        # PUSH / POP
        print ('cloning')
        if self.db.get('copy') == '1':
            print ('Return!')
            return {'answer': False, 'message': 'Copying operation already in progress'}
        self.db.set('copy', '1')
        try:
            shutil.copytree(src, dst)
        except OSError as exc: # python >2.5
            print ('Exception')
            if exc.errno == 17:
                return {'answer': False, 'message': 'VM with such name already exists'}
            if exc.errno == 28:
                return {'answer': False, 'message': 'No space left on device'}
            print (exc.errno)
        print ('I am here')
        self.db.set('copy', '0')
        return {'answer': True, 'message': ''}




    """
    f = open('/etc/libvirt/qemu/Web-apache.xml')
    f = f.read()
    conn.createXML(f, 0)

    """