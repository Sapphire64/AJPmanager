from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import view_config
from pyramid.security import authenticated_userid, Allow, Authenticated, Everyone
from ajpmanager.core.RedisAuth import groupfinder
from ajpmanager.core.VMConnector import VMConnector
from ajpmanager.security import verify_ip

VMC = VMConnector()

class MainPage(object):
    """ Class for loading admin's menu view.
    """
    def __init__(self, request):
        # Pyramid's class-based view
        # This part is required
        self.request = request

    @view_config(route_name='main', renderer='templates/main.jinja2', permission='registered')
    def __call__(self):
        # Actual function to run by framework (CBV)
        # TODO: display server IP and maybe some other info which can be loaded only once (will not change during run)
        if not verify_ip(self.request['REMOTE_ADDR']):
            return HTTPForbidden()
        show_settings = False
        username = authenticated_userid(self.request)
        user_groups = groupfinder(username, self.request)
        return {'username': username, 'show_settings': show_settings, 'user_groups': user_groups}


class JSONprocessor(object):
    """ This block is project's workhorse. All user requests are passing this block.

    TODO: implement more RESTful approach.
    """
    def __init__(self, request):
        self.request = request
        self.session = self.request.session.get_csrf_token()
        self.json = request.json_body

    def __check_permissions(self, accepted_group, match_if_all=False):
        """ A function to check user's permission in
        internal factory functions. Accepts `accepted_group` parameter
        must be without `group:` lead part.
        Like: `admins`
        """
        username = authenticated_userid(self.request)
        groups = groupfinder(username, self.request)

        type_ = type(accepted_group)
        if type_ is str: # single STR group
            if 'group:' + accepted_group in groups:
                return True
            else:
                return False
        elif type_ is list: # multiple permissions
            if match_if_all: # Match all
                for item in accepted_group:
                    if 'group:' + item not in groups:
                        return False
                return True
            else:
                for item in accepted_group:
                    if 'group:' + item in groups:
                        return True
                return False
        else:
            raise TypeError ("Wrong accepted_groups type provided!")


    @view_config(renderer="json", route_name="engine.ajax", permission='registered')
    def mainline(self):

        if not verify_ip(self.request['REMOTE_ADDR']):
            return HTTPForbidden()

        # Add to redis info that user is online
        VMC.log_active(authenticated_userid(self.request))

        # Factory to answer for JSON requests
        try:
            return self.functions[self.json['query']](self)
        except KeyError:
            # If we have wrong JSON request
            print ('Wrong JSON request: ' + str(self.json['query']))
            return {'status': False, 'answer': 'Wrong query'}

    def get_vms_list(self):
        # Here we are reading all virtual machines and packing them into answer:
        no_cache = self.json.get('no_cache')
        vms = VMC.get_vms_list(no_cache=no_cache)
        return {'status': True, 'data': vms}

    def get_users_list(self):
        users = VMC.get_users_list()
        return {'status': True, 'data': users}

    def get_groups_list(self):
        if not self.__check_permissions(['admins', 'moderators']):
            return {'status': False, 'answer': 'You are not authorized to get groups list'}
        groups = VMC.get_groups_list()
        return {'status': True, 'data': groups}

    def get_presets_list(self):
        if not self.__check_permissions(['admins', 'moderators']):
            return {'status': False, 'answer': 'You are not authorized to get presets list'}
        presets = VMC.get_presets_list()
        return {'status': True, 'data': presets}

    def get_active_operations(self):
        # Connect to redis and get list
        return {'status': True, 'answer': None}

    def verify_new_vm_name(self):
        if not self.__check_permissions(['admins', 'moderators']):
            return {'status': False, 'answer': 'You are not authorized to verify vms name'}
        name = self.json.get('data')
        if not name:
            return {'status': False, 'answer': 'No name provided'}
        vms = self.get_vms_list()['message']
        if name.strip() in vms:
            return {'status': False, 'answer': 'VM with such name already exists'}
        else:
            return {'status': True}

    def get_storage_info(self):
        if not self.__check_permissions(['admins', 'moderators']):
            return {'status': False, 'answer': 'You are not authorized to get storage info'}
        machine = self.json.get('machine')
        if not machine:
            return {'status': False, 'answer': 'No machine name provided to calculate allocated storage'}
        total, used, free, preset_size = VMC.get_storage_info(machine)
        return {'status': True, 'data': {'free': free, 'used': used, 'total': total, 'preset_size': preset_size}}

    @view_config(permission='admins')
    def get_settings(self):
        if not self.__check_permissions('admins'):
            return {'status': False, 'answer': 'You are not authorized to get settings info'}
        settings = VMC.get_settings()
        return {'status': True, 'data': settings}


    def apply_settings(self):
        if not self.__check_permissions('admins'):
            return {'status': False, 'answer': 'You are not authorized to get settings info'}
        data = self.json.get('data')
        if not data:
            return {'status': False, 'answer': 'No settings data provided'}
        try:
            VMC.apply_settings(data)
        #except ValueError:
            #return {'status': False, 'answer': 'Wrong values provided'}
        except NotImplementedError:
            pass
        else:
            return {'status': True}

    def restore_default_settings(self):
        if not self.__check_permissions('admins'):
            return {'status': False, 'answer': 'You are not authorized to get settings info'}
        VMC.restore_default_settings()
        return {'status': True}

    def machines_control(self):
        name = self.json.get('data')
        operation = self.json.get('operation')

        operations = {
            'run': VMC.run_machine,
            'stop': VMC.stop_machine,
            'pause': VMC.pause_machine,
            'destroy': VMC.destroy_machine,
            }

        if not name:
            return {'status': False, 'answer': 'No name provided'}
        if not operation:
            return {'status': False, 'answer': 'No operation provided'}
        function = operations.get(operation)
        if not function:
            return {'status': False, 'answer': 'No function found for "%s" request' % operation}
        else:
            answer = function(name)
            return {'status': answer[0], 'answer': answer[1]}

    def create_vnc_connection(self):
        username = authenticated_userid(self.request)
        print ('create VNC')
        answer = VMC.vnc_connection(username=username, machine_name=self.json.get('machine'))
        return {'status': answer[0], 'data': answer[1]}

    def release_vnc_connection(self):
        username = authenticated_userid(self.request)
        print ('release VNC')
        cookie = self.request.cookies['ajpvnc_key']
        answer = VMC.release_vnc_connection(username=username, hash=cookie)
        return {'status': answer}

    def add_user(self):
        if not self.__check_permissions(['admins', 'moderators']):
            return {'status': False, 'answer': 'You are not authorized to add user'}
        data = self.json['data']
        answer = VMC.add_user(data)
        return {'status': answer[0], 'answer': answer[1]}

    def get_user_info(self):
        ident = self.json['data'][0]
        by_name = self.json['data'][1]
        answer = VMC.get_user_info(ident, by_name)
        return {'status': answer[0], 'answer': answer[1]}

    def delete_user(self):
        if not self.__check_permissions(['admins', 'moderators']):
            return {'status': False, 'answer': 'You are not authorized to delete user'}
        id = self.json['data']
        answer = VMC.delete_user(id, authenticated_userid(self.request))
        return {'status': answer[0], 'answer': answer[1]}


    # This dictionary is used to implement factory run of the requested functions
    functions = {
        # VM lists
        'get_vms_list': get_vms_list,
        'get_presets_list': get_presets_list,
        # VM control
        'machines_control': machines_control,
        # Presets modal
        'get_storage_info': get_storage_info,
        'verify_new_vm_name': verify_new_vm_name,
        # Settings
        'get_settings': get_settings,
        'apply_settings': apply_settings,
        'restore_default_settings': restore_default_settings,
        # VNC
        'create_vnc_connection': create_vnc_connection,
        'release_vnc_connection': release_vnc_connection,
        # Users
        'get_user_info': get_user_info,
        'get_users_list': get_users_list,
        'get_groups_list': get_groups_list,
        'add_user': add_user,
        'delete_user': delete_user,
        }

