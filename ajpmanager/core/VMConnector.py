from ajpmanager.core.DBConnector import DBConnection
from ajpmanager.core.MiscTools import PathGetter, get_storage_info, safe_join, calculate_flat_folder_size
from ajpmanager.core.RedisAuth import groupfinder, authenticate
from ajpmanager.core.providers.KVM import KVMProvider
from ajpmanager.models import User, email_pattern

try:
    import libvirt
except ImportError:
    print ('Please install libvirt from libs folder')
import socket
import re

localhost = '127.0.0.1' # Hardcoding localhost

FOLDERS_RE = re.compile(r'^[a-zA-Z0-9_-]+$')
FILES_RE = re.compile(r'^[a-zA-Z0-9_.-]+$')


class VMConnector(object):
    """ Interface to connect AJP with VM daemons.
     Also this class extend VMdaemons functionality with some additional methods
     like getting storage info, manipulations with users accounts, log online users.

     This :class: is created during initialization of views.py file and mostly executed from its classes,
     i.e. by ajax or web page handlers.
     """

    providers = {#'xen': None,
                 'kvm': KVMProvider}

    conn = None

    def __init__(self):
        self.db = DBConnection()
        self.pg = PathGetter(self.db.io)
        self._prepare_hypervisor_connection()

    def _prepare_hypervisor_connection(self, reload=False):
        """ Initializing VM provider connection by creating VM provider's object.

        In constructor of any VM provider we use DB object and PathGetter object from this function.
        `DBconnection` will be used for caching purposes,
        `PathGetter` will be used as abstract interface to filesystem & VM system path.
        """
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
        use - Xen or Qemu+KVM (or any else)

         FIXME: all the project is currently tested only with KVM.
         """
        if self.conn and not reload:
            return True

        provider = self.db.io.get('provider')

        if self.providers[provider].check_availability():
            return self.providers[provider]

        return False

    def clone(self, base, new_name):
        """
            Clone selected machine from presets
        """
        # TODO: add possibility to clone production machine, not only from presets.
        if not self.__select_vm_provider():
            return
        self.conn.clone_machine(base, new_name)

    def run_machine(self, username, name):
        """ Asks VM provider to run VM with provided name.
        """
        if not self.__select_vm_provider():
            return

        if not username:
            return
        user_machines = User.get_user_machines_by_name(username)
        if name not in user_machines:
            return

        return self.conn.run_machine(name)

    def stop_machine(self, username, name):
        """ Asks VM provider to stop VM with provided name.
        This can be ignored by target so UI after calling this method can call
        `destroy_machine` method to force stopping.
        """
        if not self.__select_vm_provider():
            return

        if not username:
            return
        user_machines = User.get_user_machines_by_name(username)
        if name not in user_machines:
            return

        return self.conn.stop_machine(name)

    def pause_machine(self, username, name):
        """ Asks VM provider to pause VM with provided name.
        TODO: This is not implemented yet by any VM provider, also we don't have unpause function.
        """
        if not self.__select_vm_provider():
            return

        if not username:
            return
        user_machines = User.get_user_machines_by_name(username)
        if name not in user_machines:
            return

        return self.conn.pause_machine(name)

    def destroy_machine(self, username, name):
        """ Asks VM provider to force stop of VM with provided name.
        This can be called by UI after calling `stop_machine` function, which can be ignored by VM.
        """
        if not self.__select_vm_provider():
            return

        if not username:
            return
        user_machines = User.get_user_machines_by_name(username)
        if name not in user_machines:
            return

        return self.conn.destroy_machine(name)

    def get_vms_list(self, username=None, no_cache=False):
        """ Asking VM provider to provide list of all non-presets VMs, then filtering by allowed.

            @param no_cache - clear machines list cache flag
        """
        if not self.__select_vm_provider():
            return
        if not username:
            return

        vms = self.conn.get_machines_list(no_cache)
        user_machines = User.get_user_machines_by_name(username)

        if user_machines is not None:
            vms['offline'] = filter(lambda x: x['name'] in user_machines, vms['offline'])
            vms['online'] = filter(lambda x: x['name'] in user_machines, vms['online'])

        return vms

    def get_presets_list(self):
        """
            Asking VM provider to provide list of all presets VMs.
        """
        if not self.__select_vm_provider():
            return
        return self.conn.get_presets_list()

    def install_from_preset(self, new_name, preset):

        if not new_name or not preset:
            return False, "No preset or no name provided"

        # Check for special signs (to avoid names like '*L()B$73R*')
        def special_match(strg, search=re.compile(r'[^A-Za-z0-9]').search):
            return not bool(search(strg))
        if not special_match(new_name) or (24 < len(new_name) < 4):
            import pdb; pdb.set_trace()
            return False, "Please provide better name"

        if preset not in map(lambda x: x['name'], self.get_presets_list()):
            return False, "Such preset does not exist"

        # Actual machines list for now
        # TODO: block concurrent operations
        vms = self.conn.get_machines_list(no_cache=True)

        vms = map(lambda x: x['name'], vms['online']) + map(lambda x: x['name'], vms['offline'])

        if new_name in vms:
            return False, "Such name already in use"

        free_space = self.get_storage_info(preset)

        if free_space[2] < free_space[3]:
            return False, "You don't have enough free disk space available to install from preset"

        # Looks like all good - continue
        try:
            self.clone(base=preset,  new_name=new_name)
        except Exception as e:
            print (e)
            return False, "Something went wrong: %s" % e
        else:
            return True, "New machine was successfully created"



    def get_storage_info(self, machine):
        """ Calculating storage info (total, free, used) for new VM:
        We are getting all storage info and then calculate how much space
         you need to copy selected VM.

        FIXME: we are calculating info only for presets, this should be fixed for cloning
            non-preset machines.
        """
        provider = self.db.io.get('provider')
        # TODO: optimize next, or maybe move it to VM provider.
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
        """ Interface to PathGetter :class: -> we are packing it's results into AJAX answer.
        """
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

    def get_users_list(self):
        """ Interface to User model :class: - asking for users list """
        return User.get_all_users()

    def get_groups_list(self):
        """ Interface to User model :class: - asking for groups list """
        return User.get_all_groups()

    def add_user(self, json, adder_username):
        """ Processing query for adding new user.
        All the registration data is provided by JSON body.

        TODO: Functional tests required!
        """

        # Prepare for permissions check
        info = User.get_user_info_by_name(adder_username)
        if not info[0] or not info[1]['username']: # if adder_username does not exists in DB (this is almost impossible)
           raise SystemError('Wrong adder username provided')
        adder_info = info[1]

        if adder_info['group'] not in ['group:admins', 'group:moderators']:
            raise SystemError("Non-privileged user have access to adding users!"
                              " Something wrong with JSONprocessor security or with DB!")

        selected_group = json['selected_group'].strip()
        new_group = json['new_group'].strip()
        # Pack groups information
        if new_group:
            group = new_group
        elif selected_group:
            group = selected_group
        else:
            return False, 'Wrong groups data'

        group = 'group:' + group

        # Check permissions to add such group (IMPORTANT!!!)
        if group in ['group:admins', 'group:moderators'] and adder_info['group'] != 'group:admins':
            return False, 'You don\'t have permissions to add new moderator or administrator'

        # All good. Continue to pack info.
        username = json['username'].strip()
        first_name = json['first_name'].strip()
        last_name = json['last_name'].strip()

        email = json['email'].strip()
        send_email = json['send_email']

        password = json['new_password'].strip()
        password_rpt = json['new_password_repeat'].strip()

        if not password or not password_rpt:
            return False, "Please repeat new password"

        if password != password_rpt:
            return False, 'Passwords does not match'

        user = User(username, password, email,
            first_name, last_name,
            group=group, expire=None)

        return user.add_to_redis()

    def update_user(self, json, updater_username):
        """
        TODO: Functional tests required!
        """

        # Step 0: prepare data
        username = json['username'].strip()
        first_name = json['first_name'].strip()
        last_name = json['last_name'].strip()
        group = json['group'].strip()

        machines = json['machines']

        if not group:
            return False, 'Bad group name provided'
        else:
            group = 'group:' + group

        email = json['email'].strip()

        if not email_pattern.match(email):
            return False, "Wrong email address!"

        old_password = json['old_password'].strip()
        password = json['change_password'].strip()
        password_rpt = json['change_password_confirm'].strip()

        #

        # Step 1: getting updater user permissions
        info = User.get_user_info_by_name(updater_username)
        if not info[0] or not info[1]['username']: # if updater_username does not exists in DB (this is almost impossible)
            raise SystemError('Wrong updater username provided')
        updater_info = info[1]

        # Step 2: collecting info about editing user
        info = User.get_user_info_by_name(username)
        if not info[0] or not info[1]['username']: # if editing_username does not exists in DB (but this IS possible :)
            return False, 'Wrong changing username provided'
        changing_user_info = info[1]

        # Step 3: setting vars
        change_password = False
        if any([password, password_rpt]) and not all([password, password_rpt]):
            return False, "To change password please fill all fields"
        elif all([password, password_rpt]):
            if password != password_rpt:
                return False, "New passwords does not match"
            elif not 4 <= len(password) <= 16:
                return False, 'Wrong password length! 4 <= x <= 16'
            else:
                change_password = True

        # Step 4: testing permissions and applying update
        # There are many cases which must be implemented
        new_password = None
        if updater_info['username'] == changing_user_info['username']:
            # Regular user or superuser changing himself
            if change_password:
                if not old_password:
                    return False, "To change password please fill all fields"
                if not authenticate(updater_info['username'], old_password):
                    return False, "Wrong old password provided"
                new_password = password


            group = None # Disabled change of self group

            User.update_user(username=updater_info['username'], first_name=first_name,
                last_name=last_name, group=group, email=email, password=new_password)

        elif updater_info['group'] not in ['group:admins', 'group:moderators']:
            # Non-privileged user trying to change somebody else
            return False, "You don't have permissions to change this user"

        else:
            # Superuser changing somebody else
            if changing_user_info['username'] == 'admin':
                return False, 'Nobody except admin himself can change superadmin profile'

            if updater_info['group'] == 'group:moderators':
                if changing_user_info['group'] in ['group:admins', 'group:moderators']:
                    return False, "You don't have permissions to change this user"
                # IMPORTANT
                if group in ['group:admins', 'group:moderators']:
                    return False, 'You don\'t have permissions to add new moderator or administrator'

            if change_password:
                new_password = password

            User.update_user(username=changing_user_info['username'], first_name=first_name,
                last_name=last_name, group=group, email=email, password=new_password, machines=machines)

        return True, ''


    def delete_user(self, id, deleter_username):
        """ Processing query for deleting user.

        @param `id` - removing user ID.
        @param `deleter_username` - username of the person who
            tries to delete user with provided `id`.

        This will be used to check deleter's permissions.
        Please make sure you are using authenticated_userid() to get deleter_username.
        """
        # Determining deleter uid and group
        info = User.get_user_info_by_name(deleter_username)
        if not info[0] or not info[1]['username']: # if updater_username does not exists in DB (this is almost impossible)
            raise SystemError('Wrong deleter username provided')
        deleter_info = info[1]

        # Step 2: collecting info about editing user
        info = User.get_user_info_by_id(id)
        if not info[0] or not info[1]['username']: # if editing_username does not exists in DB (but this IS possible :)
            return False, 'Wrong deleting id provided'
        deleting_user_info = info[1]

        if deleter_info['username'] == deleting_user_info['username']:
            return False, "You can't delete yourself"


        deleter_group = deleter_info['group']
        deleted_user_group = deleting_user_info['group']

        if deleter_group not in ['group:admins', 'group:moderators']:
            return False, 'You don\'t have permissions to delete users'

        if deleted_user_group in ['group:admins', 'group:moderators']:
            if deleter_group != 'group:admins':
                return False, 'You don\'t have permissions to delete admins or moderators'

        return User.remove_user(id)

    def get_user_info(self, ident, by_name):
        """ Function to get user info by name or by id (depends on who you are getting it in UI).
        """
        if by_name is True:
            return User.get_user_info_by_name(ident)
        else:
            return User.get_user_info_by_id(ident)

    def apply_settings(self, data):
        """ Save settings into DB """
        # TODO: implement it in PathGetter
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
        """ Restoring project's recommended settings including file paths """
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

    def vnc_connection(self, username, machine_name, local_user=False):
        """ Function to prepare proxy VNC connection for VM provider """
        global localhost

        # Step 1: can user view this machine at all?
        if not username:
            return
        user_machines = User.get_user_machines_by_name(username)
        if machine_name not in user_machines:
            return

        # Step 2: Finding your IP to bind to it (this allows remote users to connect)
        if not local_user: # This was added because local user does not store cookies for WAN IP connection.
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('yandex.ru', 0))
            hostname = sock.getsockname()[0]
        else:
            hostname = localhost

        # Step 3: Finding but not binding free port to run
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((hostname, 0)) # Asking OS to bind free port on your WAN IP
        except Exception:
            sock.bind(('', 0)) # If failed - on local IP.
            hostname = localhost
        finally:
            listen_port = sock.getsockname()[1] # << Here it is
        del(sock)

        # Step 4: Processing by VM manager
        answer = self.conn.vnc_connection(user_groups=groupfinder(username, None),
                                            machine_name=machine_name,
                                            listen_port=listen_port,
                                            listen_host=hostname,
                                            target_host=localhost)

        # Step 5: Pack answer to client
        return answer

    def release_vnc_connection(self, username, hash):
        """ Closing VNC proxy connection """

        # Step 1: getting machine name with security cookie
        machine_name = self.conn.get_machine_name_by_hash(hash)

        if not machine_name:
            return (False, 'No machine found for such hash')

        # Step 2: can user control this machine at all? TODO
        #if username != 'admin' and machine_name not in self.db.io.get(username + ':machines'):
        #    return (False, 'Access denied')

        # Step 3: Processing by VM manager
        answer = self.conn.disable_vnc_connection(machine_name=machine_name, session = hash)

        # Step 4: Pack answer to client
        return answer

    def log_active(self, username):
        """ Add info to redis that user is online
        """
        self.db.io.set('username:' + username + ':online', True)
        # 5 minutes w/o activity will say that user is offline
        # This is not accurate (vnc session for example can much longer)
        # but anyway ... ;)
        self.db.io.expire('username:' + username + ':online', 300)

