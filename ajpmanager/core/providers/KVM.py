# coding: utf-8
from multiprocessing.process import Process
from time import sleep
from uuid import uuid4
from ajpmanager.core.MiscTools import safe_join, isOpen
from xml.dom import minidom

import os
try:
    import libvirt
except ImportError:
    print ('Please install libvirt from libs folder')
import random
import json
import shutil
from ajpmanager.core.sockets.websockify import WebSocketProxy


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
    vnc_proxies = dict()

    @staticmethod
    def check_availability():
        try:
            import libvirt
        except ImportError:
            return False
        else:
            return True

    def __init__(self, dbcon, pathgetter):
        print ('Using KVM as a virtual machines server and libvirt as frontend')
        self.db = dbcon
        self.pg = pathgetter

        self._prepare_database()

        self.connection = libvirt.open(self.VMMANAGER_PATH)
        assert self.connection, 'Failed to open Qemu/KVM connection'

        #self.clone_machine('WheezyBasic', 'test_1', 111, force=True)


    def _clone(self, id, preset_name, machine_name, session, force=False):
        print ('cloning')
        if self.db.get('copy'):
            print ('Copy operation in progress')
            return {'answer': False, 'message': 'Copy operation already in progress'}
        self.db.set('copy', session)

        # Path preparations
        src = safe_join(self.PRESETS, preset_name)
        dst = safe_join(self.IMAGES, machine_name)

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
        # Drop cache:
        self._prepare_database(soft=True)

        # Prepare message to client
        print ('Files copied!')
        message = 'Sucessfully copied'
        return {'answer': True, 'message': message}


    def drop_cache(self):
        self._prepare_database()


    def _prepare_database(self, soft=False): # aka drop cache
        # Set flags in DB and also prepare list of preset domains
        if not soft:
            self.db.expire('copy', 0)
            self.db.set('provider', 'kvm')

        self.KVM_PATH = self.pg.KVM_PATH
        self.PRESETS = safe_join(self.KVM_PATH, self.pg.PRESETS)
        self.IMAGES = safe_join(self.KVM_PATH, self.pg.IMAGES)

        self.CONFIG_NAME = self.pg.CONFIG_NAME
        self.VMIMAGE_NAME = self.pg.VMIMAGE_NAME
        self.DESCRIPTION_NAME = self.pg.DESCRIPTION_NAME

        self.VMMANAGER_PATH = self.pg.VMMANAGER_PATH

        # Cleaning cache lists
        self.db.expire('online', 0)
        self.db.expire('offline', 0)
        self.db.expire('presets', 0)


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

    def _lookup_by_name(self, name):
        return self.connection.lookupByName(name)

    def _transform_state_to_text(self, info):
        state = info[0]
        if state == 1:
            return 'Running'
        elif state == 2:
            return 'Blah'
        else:
            return 'Unknown'


    def get_machines_list(self, no_cache=False):
        # Read from Redis cache:
        from time import time
        t1 = time()

        if no_cache:
            self._prepare_database()
        else:
            try:
                online = self.db.lrange("online", 0, -1)
                offline = self.db.lrange("offline", 0, -1)
            except Exception:
                pass
            else:
                # Caching provides more than 30x faster processing
                if online and offline:
                    online_lst = []
                    for element in online:
                        try:
                            element = json.loads(element) # Load from JSON
                        except ValueError: # in case of 'Empty' elemenet or anything else
                            continue
                        else:
                            online_lst.append(element)

                    offline_lst = []
                    for element in offline:
                        try:
                            element = json.loads(element)
                        except ValueError:
                            continue
                        else:
                            offline_lst.append(element)

                    print ('Cache used: ' + str(time()-t1)) # Leave it for some time
                    return {'offline': sorted(offline_lst), 'online': online_lst}

        self._define_machines() # Add all machines from folders into libvirt

        #presets = ['DEBUGG'] # Changed for debug
        presets = self.get_presets_list()
        presets = [preset['name'] for preset in presets]

        # Online
        online = []
        online_names = []
        online_ids = self._get_online_machines()

        for id in online_ids:
            machine = self._lookup_by_id(id)
            name = machine.name()
            if name in presets: # Hiding presets from actual machines
                continue
            online_names.append(name)
            type, cpu, memory = self._get_xml_info(name)
            info = machine.info()
            answer = {'id': id, 'name': name, 'type': type, 'cpu': cpu, 'memory': memory, 'info': info}
            online.append(answer)

        # Offline
        offline = []

        # Getting VMs by libvirt
        offline_names = self._get_offline_machines()

        for machine in offline_names:
            if machine in presets or machine in online_names: # excluding presets and already started machines
                continue
            type, cpu, memory = self._get_xml_info(machine)
            answer = {'id': '-', 'name': machine, 'type': type, 'cpu': cpu, 'memory': memory, 'info': None}
            offline.append(answer)

        #offline = [item for item in offline if item not in presets]

        # Caching instruments
        # 10 minutes caching which will be disabled in case of any changes
        if online:
            for item in online:
                item = json.dumps(item)
                self.db.rpush('online', item)
        else:
            self.db.rpush('online', 'Empty')

        self.db.expire('online', 600)

        if offline:
            for item in offline:
                item = json.dumps(item)
                self.db.rpush('offline', item)
        else:
            self.db.rpush('offline', 'Empty')

        self.db.expire('offline', 600)

        print ('Cache not used: '  + str(time()-t1)) # Temp mini-bench
        print ('Results: %s and Online: %s and Presets: %s' % (offline_names, online, presets))

        return {'offline': offline, 'online': sorted(online)}


    def get_presets_list(self):
        presets = []
        try:
            presets_list = self.db.lrange("presets", 0, -1)
        except Exception:
            pass
        else:
            if presets_list:
                for element in presets_list:
                    try:
                        element = json.loads(element)
                    except ValueError:
                        continue
                    else:
                        presets.append(element)
                print ('Cached presets: %s' % presets)
                return presets

        # If not cache
        for directory in os.listdir(self.PRESETS):
            path = safe_join(self.PRESETS, directory)
            try:
                with open(safe_join(path, self.CONFIG_NAME)) as f:
                    dom = minidom.parse(f)
                #import pdb; pdb.set_trace()
            except IOError:
                continue
            else:
                name = dom.getElementsByTagName('name')[0].childNodes[0].data # Get name of the VM
                try:
                    with open(safe_join(path, self.DESCRIPTION_NAME)) as f:
                        description = f.read()
                except IOError:
                    continue
                else:
                    presets.append({'name': name, 'description': description})


        if presets:
            for preset in presets:
                item = json.dumps(preset)
                self.db.rpush('presets', item)
        else:
            self.db.rpush('presets', 'Empty')

        self.db.expire('presets', 600)
        print ('presets: ' + str(presets))
        return presets

    def get_machine_name_by_hash(self, hash):
        for key in self.vnc_proxies.keys():
            obj = self.vnc_proxies.get(key)
            if obj and obj[0] == hash:
                return str(key)
        return None


    def _get_xml_info(self, machine_name, presets=False):
        source = self.IMAGES if not presets else self.PRESETS
        path = safe_join(source, machine_name)
        # Maybe this code is too indian-styled
        try:
            with open(safe_join(path, self.CONFIG_NAME)) as f:

                dom = minidom.parse(f)
        except IOError:
            type = 'unknown'
            memory = -1
            cpu = '?'
        else:
            cpu = dom.getElementsByTagName('vcpu')[0].childNodes[0].data
            type = dom.getElementsByTagName('ajptype')[0].childNodes[0].data
            memory = int(dom.getElementsByTagName('memory')[0].
                         childNodes[0].data)/1024 # In MB
        finally:
            if not type:
                type = 'not specified'
            if not memory:
                memory = 0
            if not cpu:
                cpu = '?'
        return (type, cpu, memory)


    def _get_offline_machines(self):
        return self.connection.listDefinedDomains()


    def _get_online_machines(self):
        return self.connection.listDomainsID()


    def _define_machines(self):
        """ Adding VM into Libvirt. Also refreshing changed config files.
        """
        # Find preset's name & image name of the machine and add it into libvirt
        for category in [self.IMAGES, self.PRESETS]: # Scanning both images and presets
            for directory in os.listdir(category):
                directory_ = safe_join(category, directory)                          # Building full path
                if not os.path.isdir(directory_):
                    continue
                try:
                    with open(safe_join(directory_, CONFIG_NAME)) as f:
                        f = f.read()
                    self.connection.defineXML(f)
                    # vice versa -> undefine_XML
                except Exception:
                    continue


    def run_machine(self, machine_name, preset=False):
        if isinstance(machine_name, libvirt.virDomain): # Processing domain object itself
            try:
                self.machine_name.create()
            except Exception as e:
                error =  'Unknown error while trying to start machine by domain object: %s' % e
                print (error)
                return (False, error)
            else:
                self._prepare_database()
                return (True, 'Machine started')

        # Simple approach -> start by reading configuration file
        folder = self.PRESETS if preset else self.IMAGES
        path = safe_join(folder, machine_name)
        try:
            with open(safe_join(path, self.CONFIG_NAME)) as f:
                f = f.read()
        except IOError:
            return (False, 'Cannot open config name for %s machine' % machine_name)
        machines = self._get_online_machines()
        try:
            self.connection.createXML(f, 0)
        except libvirt.libvirtError as e:
            return (False, str(e))
        except Exception:
            return (False, 'Cannot run machine, but config file was found')
        else:
            # TODO: improve this algorithm
            cnt = 0
            while machines == self._get_online_machines() and cnt < 5:
                cnt += 1
                sleep(2)
            self._prepare_database()
            return (True, 'Machine started')

    def stop_machine(self, machine_name):
        machine = self.connection.lookupByName(machine_name)
        if not machine:
            return (False, 'No machine found with such name')
        try:
            machine.shutdown() # check exception
        except libvirt.libvirtError as e:
            return (False, str(e))
        except Exception as e:
            return (False, 'Cannot stop machine: %s' % e)
        else:
            cnt = 0
            while machine.isActive():
                if cnt > 10:
                    return (False, 'Machine is still running, please try to stop it again')
                cnt += 1
                sleep (1)
            return (True, 'Machine stopped')

    def destroy_machine(self, machine_name):
        machine = self.connection.lookupByName(machine_name)
        if not machine:
            return (False, 'No machine found with such name')
        try:
            machine.destroy() # check exception
        except libvirt.libvirtError as e:
            return (False, str(e))
        except Exception as e:
            return (False, 'Cannot stop machine: %s' % e)
        else:
            self._prepare_database()
            return (True, 'Machine destroyed')

    def pause_machine(self, machine_name):
        return (False, 'Not implemented yet')



    def clone_machine(self, preset_name, machine_name, session, force=False):
        id = 1
        p = Process(target=self._clone, args=(id, preset_name, machine_name, session, force)) # In different process
        p.start()
        #self._clone(id, preset_name, machine_name, session, force) # for debugging


    def _check_vnc_permissions(self, user_groups, accepted_group, match_if_all=False):
        """ A function to check user's permission in
        internal factory functions. Accepts `accepted_group` parameter
        must be without `group:` lead part.
        Like: `admins`

        TODO: refractoring (check views file for same function)
        """
        type_ = type(accepted_group)
        if type_ is str: # single STR group
            if 'group:' + accepted_group in user_groups:
                return True
            else:
                return False
        elif type_ is list: # multiple permissions
            if match_if_all: # Match all
                for item in accepted_group:
                    if 'group:' + item not in user_groups:
                        return False
                return True
            else:
                for item in accepted_group:
                    if 'group:' + item in user_groups:
                        return True
                return False
        else:
            raise TypeError ("Wrong accepted_groups type provided!")

    def vnc_connection(self, machine_name, target_host, listen_host, listen_port, user_groups=None, ssl_only=None, ssl_cert=None):
        """
        ================================================! WARNING !===================================================
        FIXME: If user will close browser tab, function 'disconnect' will not be run and we will have zombie connection
        with no chance for anybody else to connect. <- this gonna be fixed soon.

        TODO: loop to check unused and timeout socket listeners and close them.

        Edit this code with cautions. Non-closed connection can give access to VNC terminal even if it shouldn't,
            so some user can spy for another one:

        ----> Oh, exploitable! User can avoid our JS algorithms and by appending cookie and port from previous
            successful connection he can spy for another user connected right now. All he need to do - just avoid our
            "disconnect()" function, but send disconnect query to our server AJAX server. This will lead to release
            possibility to create new connection for another user BUT WILL NOT CLOSE ACTIVE PROXY TO VNC SERVER.
         ================================================! WARNING !===================================================

         Update: comments are quickly becoming outdated, I don't know, is this fixed or not, probably yes :)
        """
        is_super_user = self._check_vnc_permissions(user_groups, ['admins', 'moderators'])

        # TODO:
        # Can user manipulate this machine at all?
        if not is_super_user:
            pass # Do some checks

        # Finding target domain
        try:
            domain = self.connection.lookupByName(machine_name)
        except libvirt.libvirtError as e:
            return (False, "LibvirtError: %s" % e)

        if not domain:
            return (False, 'No machine found') # but I assume that previous try:except will catch such state

        if not domain.isActive():
            return (False, 'Run machine first')

        secondary_connection = False # Client-side JS won't disable connection if user does not initiated it.

        # This operation should block other server starts or it could cause problems
        if self.vnc_proxies.get(machine_name): # check if vnc session is running already
            if is_super_user:
                # Here SU can just spy for somebody else !!! :)
                # Please use for educational purposes only :P
                hash = self.vnc_proxies[machine_name][0]
                listen_host = self.vnc_proxies[machine_name][2]
                listen_port = self.vnc_proxies[machine_name][3]
                secondary_connection = True
            else:
                return (False, "VNC connection is already established")
        else:
            if ssl_only and not os.path.exists(ssl_cert):
                raise Exception ("SSL only and %s not found" % ssl_cert)
            else:
                # TODO: SSL support
                pass

            # Finding target machine's VNC port
            xml = domain.XMLDesc(0) # Getting XML description to find machine's VNC port
            dom = minidom.parseString(xml)
            graphics = dom.getElementsByTagName('graphics')

            for item in graphics:
                if item.attributes.get('type').value == 'vnc':
                    target_port = int(item.attributes.get('port').value)
                    break

            if not target_port:
                return (False, "Can't find VNC port for given machine")


            hash = os.urandom(16).encode('hex') + '00000' + machine_name # Generating random hash

            opts = dict(listen_host=listen_host, listen_port=listen_port, target_host=target_host, target_port=target_port,
                        session_id = hash, wrap_cmd = False, wrap_mode = False) # Dunno what this two do

            # Create and start the WebSockets proxy
            server = WebSocketProxy(**opts)
            p = Process(target=server.start_server, args=())

            # Memory db with info about connections
            # IMPORTANT: we are storing `is_super_user` flag so in future releases one can add
            # a toggle to show super user's session to other super users or not
            self.vnc_proxies[machine_name] = (hash, p, listen_host, listen_port, is_super_user)
            self.vnc_proxies[machine_name][1].start()

        data = {'cookie': hash, 'host': listen_host, 'port': listen_port, 'secondary_connection': secondary_connection}
        return (True, data)

    def disable_vnc_connection(self, machine_name, session):
        " Wow... "
        obj = self.vnc_proxies.get(machine_name)
        if obj and obj[0] == session and obj[1]:
            #import pdb; pdb.set_trace()
            #obj[1].active_children()
            obj[1].terminate()
            sleep(0.5)
            if isOpen(obj[2], obj[3]):
                return (False,
                        'Error - connection to the server is not closed.'
                        ' Must be used "rfb.disconnect()" method in JavaScript.')
            else:
                del(self.vnc_proxies[machine_name])

        return (True, '')





    """
    Some 'docs' as development reminder :)

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