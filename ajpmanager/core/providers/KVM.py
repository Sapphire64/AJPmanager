# coding: utf-8
from multiprocessing.process import Process
from uuid import uuid4
from ajpmanager.core.MiscTools import safe_join
from xml.dom import minidom

import os
import libvirt
import random
import shutil



KVM_PATH = '/kvm'

PRESETS = safe_join(KVM_PATH, 'presets')
IMAGES = safe_join(KVM_PATH, 'images')


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

    @staticmethod
    def check_availability():
        try:
            import libvirt
        except ImportError:
            return False
        else:
            return True

    def __init__(self, dbcon):
        print ('Using KVM as a virtual machines server and libvirt for virtualization')
        self.connection = libvirt.open('qemu:///system')
        assert self.connection, 'Failed to open Qemu/KVM connection'
        self.db = dbcon
        self._prepare_database()


    def _clone(self, id, preset_name, machine_name, session):
        # PUSH / POP <- redis
        print ('cloning')
        if self.db.get('copy') == '1':
            print ('Return!')
            return {'answer': False, 'message': 'Copying operation already in progress'}
        self.db.set('copy', '1')

        # Path preparations
        src = safe_join(PRESETS, preset_name)
        dst = safe_join(IMAGES, machine_name)

        if not os.path.exists(dst):
            os.makedirs(dst)

        # Prepare XML file

        with open(safe_join(src, 'config.xml')) as f:
            dom = minidom.parse(f)

            # <TOTAL_MADNESS>
            dom.getElementsByTagName('name')[0].childNodes[0].data = machine_name
            dom.getElementsByTagName('uuid')[0].childNodes[0].data = generate_uuid()
            for num, tag in enumerate(dom.getElementsByTagName('interface')):
                if tag.attributes.get('type').value == 'network':
                    dom.getElementsByTagName('interface')[num].getElementsByTagName('mac')[0].attributes.get('address').value = generate_mac()

            # Write to file
            dom.writexml(open(safe_join(dst, 'config.xml'), 'w'), encoding='utf-8')
            # </TOTAL_MADNESS>

        # XML ready

        for file in ['description.txt', 'image.img']:
            try:
                shutil.copy2(safe_join(src, file), dst)
            except OSError as exc: # python >2.5
                print ('Exception')
                if exc.errno == 17:
                    return {'answer': False, 'message': 'VM with such name already exists'}
                if exc.errno == 28:
                    return {'answer': False, 'message': 'No space left on device'}
                print (exc.errno)
        print ('I am here')
        self.db.set('copy', '0')

        # Prepare message to client
        message = 'Sucessfully copied'
        return {'answer': True, 'message': message}


    def _prepare_database(self, soft=False):
        # Set flags in DB and also prepare list of preset domains
        if not soft:
            self.db.set('copy', '0')
            self.db.set('provider', 'kvm')

        # Cleaning lists
        self.db.expire('images', 0)
        self.db.expire('presets', 0)

        # Find presets & images names
        for slug, list_ in [('presets', PRESETS),
                            ('images', IMAGES)]:
            for directory in os.listdir(list_):
                directory_ = safe_join(list_, directory)                          # Building full path
                with open(safe_join(directory_, 'config.xml')) as f:              # Open config.xml in full path
                    dom = minidom.parse(f)                                        # Parsing it
                    name = dom.getElementsByTagName('name')[0].childNodes[0].data # Get name of the VM
                    self.db.rpush(slug.decode('utf-8'), name)                     # Append list to REDIS

        self.get_machines_list()

    def _list_domains(self):
        return self.connection.listDomainsID()


    def _lookup_by_id(self, id, info=False):
        if isinstance(id, list):
            answer = [self.connection.lookupByID(id_) for id_ in id]
            if info:
                answer = [obj.info() for obj in answer]
            return answer
        else:
            answer = self.connection.lookupByID(id)
            if info:
                return answer.info()
            else:
                return answer

    def _transform_state_to_text(self, info):
        state = info[0]
        if state == 1:
            return 'Running'
        elif state == 2:
            return 'Blah'
        else:
            return 'Unknown'


    def get_machines_list(self):
        # Read from Redis cache:
        #dbonline = self.db.lrange("online", 0, -1)
        #dboffline = self.db.lrange("offline", 0, -1)


        offline = self._get_offline_machines()
        online_ids = self._get_online_machines()

        presets = self.db.lrange("presets", 0, -1) # IMPORTANT

        online = []

        for id in online_ids:
            machine = self._lookup_by_id(id)
            name = machine.name()
            if name in presets:
                continue
            info = machine.info()
            answer = [id, name] + info
            online.append(answer)

        #online = [item for item in online if item not in presets]
        offline = [item for item in offline if item not in presets]

        #online = list(set(presets) - set(online))

        # Caching instruments
        self.db.rpush('online', online)
        self.db.expire('online', 30)
        self.db.rpush('offline', offline)
        self.db.expire('offline', 30)

        return {'offline': offline, 'online': online}

    def _get_offline_machines(self):
        return self.connection.listDefinedDomains()

    def _get_online_machines(self):
        return self.connection.listDomainsID()


    def run_machine(self, machine_name):
        path = safe_join(IMAGES, machine_name)
        f = open(safe_join(path, 'config.xml')).read()
        self.connection.createXML(f, 0)


    def clone_machine(self, preset_name, machine_name, session):
        id = 1
        p = Process(target=self._clone, args=(id, preset_name, machine_name, session)) # In different process
        p.start()
        print ('Cloned!')




    """
    f = open('/etc/libvirt/qemu/Web-apache.xml')
    f = f.read()
    conn.createXML(f, 0)


    conn.getCPUStats(cpuNum, lags)
    .getFreeMemory()
    .getCapabilities()
    .getHostname()
    .getInfo()
    getLibVersion()
    getType() # maybe like 'Xen'
    getVersion()
    interfaceLookupByName(self, name)
    isAlive(self) # connection to hypervisor

     listDefinedDomains(self)
 |      list the defined domains, stores the pointers to the names in @names
 |
 |  listDefinedInterfaces(self)
 |      list the defined interfaces, stores the pointers to the names in @names
 |
 |  listDefinedNetworks(self)
 |      list the defined networks, stores the pointers to the names in @names
 |
 |  listDefinedStoragePools(self)
 |      list the defined storage pool, stores the pointers to the names in @names
 |
 |  listDevices(self, cap, flags)
 |      list the node devices
 |
 |  listDomainsID(self)
 |      Returns the list of the ID of the domains on the hypervisor
   listDevices(self, cap, flags)
 |      list the node devices
 |
 |  listDomainsID(self)
 |      Returns the list of the ID of the domains on the hypervisor
 |
 |  listInterfaces(self)
 |      list the running interfaces, stores the pointers to the names in @names
 |
 |  listNWFilters(self)
 |      List the defined network filters
 |
 |  listNetworks(self)
 |      list the networks, stores the pointers to the names in @names
 |
 |  listSecrets(self)
 |      List the defined secret IDs
 |
 |  listStoragePools(self)
 |      list the storage pools, stores the pointers to the names in @names

 virDomain:
    reboot
    save
    create
    name
    shutdown
    suspend
    state
    screenshot

    """