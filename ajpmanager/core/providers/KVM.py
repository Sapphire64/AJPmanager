# coding: utf-8
from multiprocessing.process import Process
from uuid import uuid4
from ajpmanager.core.MiscTools import safe_join
from xml.dom import minidom

import os
import libvirt
import random
import shutil


KVM_PATH = '/kvm' # This should be get from Redis and setted by config on page
PRESETS = safe_join(KVM_PATH, 'presets')
IMAGES = safe_join(KVM_PATH, 'images')

# Also will be read from Redis:
CONFIG_NAME = 'config.xml'
VMIMAGE_NAME = 'image.img'
DESCRIPTION_NAME = 'description.txt'


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
        print ('init')
        #self.clone_machine('WheezyBasic', 'test_1', 111, force=True)


    def _clone(self, id, preset_name, machine_name, session, force=False):
        # PUSH / POP <- redis
        print ('cloning')
        if self.db.get('copy'):
            print ('Copy operation in progress')
            return {'answer': False, 'message': 'Copy operation already in progress'}
        self.db.set('copy', session)

        # Path preparations
        src = safe_join(PRESETS, preset_name)
        dst = safe_join(IMAGES, machine_name)

        if not os.path.exists(dst):
            os.makedirs(dst)
        else:
            if not force and os.path.\
                exists(CONFIG_NAME) or os.path.\
                exists(VMIMAGE_NAME) or os.path.\
                exists(DESCRIPTION_NAME):
                return {'answer': False, 'message': 'Folder exists, use force to rewrite content'}



        # Prepare XML file
        additional_images = [] # File images (as additional partition files)
        with open(safe_join(src, CONFIG_NAME)) as f:
            # Now we are updating info in memory copy of preset's config file
            dom = minidom.parse(f)

            # <TOTAL_MADNESS>
            dom.getElementsByTagName('name')[0].childNodes[0].data = machine_name
            dom.getElementsByTagName('uuid')[0].childNodes[0].data = generate_uuid()

            for num, tag in enumerate(dom.getElementsByTagName('interface')):
                if tag.attributes.get('type').value == 'network':
                    dom.getElementsByTagName('interface')[num].getElementsByTagName('mac')[0].attributes.get('address').value = generate_mac()

            # Change path of the images in config
            # Add to list of images additional disks
            for num, element in enumerate(dom.getElementsByTagName('disk')):
                if element.attributes.get('device').value == 'disk':
                    path = element.getElementsByTagName('source')[0].attributes.get('file').value
                    image_name = os.path.basename(path)
                    if image_name != 'image.img':
                        additional_images.append(image_name)
                    dom.getElementsByTagName('disk')[num].\
                        getElementsByTagName('source')[0].\
                        attributes.get('file').value = safe_join(dst, image_name)

            # Write to file
            dom.writexml(open(safe_join(dst, CONFIG_NAME), 'w'), encoding='utf-8')
            # </TOTAL_MADNESS>

        # XML ready

        for file in [DESCRIPTION_NAME, VMIMAGE_NAME] + additional_images:
            try:
                shutil.copy2(safe_join(src, file), dst)
            except OSError as exc: # python >2.5
                print ('Exception')
                if exc.errno == 28:
                    return {'answer': False, 'message': 'No space left on device'}
                print (exc.errno)

        self.db.expire('copy', 0)

        # Prepare message to client
        print ('Files copied!')
        message = 'Sucessfully copied'
        return {'answer': True, 'message': message}


    def _prepare_database(self, soft=False):
        # Set flags in DB and also prepare list of preset domains
        if not soft:
            self.db.expire('copy', 0)
            self.db.set('provider', 'kvm')

        # Cleaning lists
        self.db.expire('images', 0)
        self.db.expire('presets', 0)

        # Find presets & images names
        for slug, list_ in [('presets', PRESETS),
                            ('images', IMAGES)]:
            for directory in os.listdir(list_):
                directory_ = safe_join(list_, directory)                          # Building full path
                try:
                    with open(safe_join(directory_, CONFIG_NAME)) as f:           # Open config.xml in full path
                        dom = minidom.parse(f)                                    # Parsing it
                except IOError:
                    pass                                                          # No config file in folder
                else:
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
        try:
            online = self.db.lrange("online", 0, -1)
            offline = self.db.lrange("offline", 0, -1)
        except Exception:
            pass
        else:
            if online and offline:
                print ('Cache used') # Leave it for some time
                return {'offline': offline, 'online': online}


        presets = ['DEBUGG'] # Change for debug
        #presets = self.db.lrange("presets", 0, -1) # IMPORTANT

        # Online
        online = []
        online_ids = self._get_online_machines()

        for id in online_ids:
            machine = self._lookup_by_id(id)
            name = machine.name()
            if name in presets:
                continue
            type, memory = self._get_xml_type_memory(name)
            info = machine.info()
            answer = [id, name, type, memory] + [info]
            online.append(answer)

        # Offline
        offline = []
        offline_names = self._get_offline_machines()

        for machine in offline_names:
            if machine in presets:
                continue
            type, memory = self._get_xml_type_memory(machine)
            answer = ['-', machine, type, memory]
            offline.append(answer)

        #offline = [item for item in offline if item not in presets]

        # Caching instruments
        for item in online:
            self.db.rpush('online', item)
        self.db.expire('online', 30)

        for item in offline:
            self.db.rpush('offline', item)
        self.db.expire('offline', 30)

        # Downside: if there are no online or offline machines it will not use cache
        # but it is better than have at the same time single machine in online and offline state.

        return {'offline': offline, 'online': online}


    def _get_xml_type_memory(self, machine_name, presets=False):
        source = IMAGES if not presets else PRESETS
        path = safe_join(source, machine_name)
        # Maybe this code is too indian-styled
        try:
            with open(safe_join(path, CONFIG_NAME)) as f:

                dom = minidom.parse(f)
        except IOError:
            type = 'unknown'
            memory = -1
        else:
            type = dom.getElementsByTagName('ajptype')[0].childNodes[0].data
            memory = int(dom.getElementsByTagName('memory')[0].
                         childNodes[0].data)/1024 # In MB
        finally:
            if not type:
                type = 'not specified'
            if not memory:
                memory = 0
        return (type, memory)



    def _get_offline_machines(self):
        return self.connection.listDefinedDomains()

    def _get_online_machines(self):
        return self.connection.listDomainsID()


    def run_machine(self, machine_name):
        path = safe_join(IMAGES, machine_name)
        f = open(safe_join(path, CONFIG_NAME)).read()
        self.connection.createXML(f, 0)


    def clone_machine(self, preset_name, machine_name, session, force=False):
        id = 1
        p = Process(target=self._clone, args=(id, preset_name, machine_name, session, force)) # In different process
        p.start()
        #self._clone(id, preset_name, machine_name, session, force) # for debugging




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