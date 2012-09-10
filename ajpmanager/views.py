from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import view_config
from pyramid.security import authenticated_userid


from ajpmanager.core.Connector import VMConnector

VMC = VMConnector()
dbcon = VMC.dbcon # Wrong way? Maybe this can lead to more slow work with DB


class MainPage(object):
    """ Class for loading admin's menu view.
    """

    def __init__(self, request):
        # Pyramid's class-based view
        # This part is required
        self.request = request

    @view_config(route_name='main', renderer='templates/main.jinja2', permission='admin')
    def __call__(self):
        # Actual function to run by framework (CBV)
        # Here we return only user's name and user's settings
        # TODO: auth
        # TODO: display username
        # TODO: settings loading
        # TODO: display server IP and maybe some other info which can be loaded only once (will not change during run)

        allowed_ips = dbcon.lrange("allowed_ips", 0, -1)

        if '*' not in allowed_ips and self.request['REMOTE_ADDR'] not in allowed_ips:
            return HTTPForbidden()

        show_settings = False
        username = authenticated_userid(self.request)

        return {'username': username, 'show_settings': show_settings}



class JSONprocessor(object):

    def __init__(self, request):
        self.request = request
        self.session = self.request.session.get_csrf_token()
        self.json = request.json_body

    @view_config(renderer="json", route_name="engine.ajax", permission='admin')
    def mainline(self):

        allowed_ips = dbcon.lrange("allowed_ips", 0, -1)

        if '*' not in allowed_ips and self.request['REMOTE_ADDR'] not in allowed_ips:
            return HTTPForbidden()

        # Factory to answer for JSON requests
        # TODO: auth and other things are to be implemented. currently they have low priority.
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

    def get_presets_list(self):
        presets = VMC.get_presets_list()
        return {'status': True, 'data': presets}

    def get_active_operations(self):
        # Connect to redis and get list
        return {'status': True, 'answer': None}

    def verify_new_vm_name(self):
        name = self.json.get('data')
        if not name:
            return {'status': False, 'answer': 'No name provided'}
        vms = self.get_vms_list()['message']
        if name.strip() in vms:
            return {'status': False, 'answer': 'VM with such name already exists'}
        else:
            return {'status': True}

    def get_storage_info(self):
        machine = self.json.get('machine')
        if not machine:
            return {'status': False, 'answer': 'No machine name provided to calculate allocated storage'}
        total, used, free, preset_size = VMC.get_storage_info(machine)
        return {'status': True, 'data': {'free': free, 'used': used, 'total': total, 'preset_size': preset_size}}

    def get_settings(self):
        settings = VMC.get_settings()
        return {'status': True, 'data': settings}


    def apply_settings(self):
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


    functions = { # This dictionary is used to implement factory run of the requested functions
                  'verify_new_vm_name': verify_new_vm_name,
                  'get_vms_list': get_vms_list,
                  'get_presets_list': get_presets_list,
                  'machines_control': machines_control,
                  'get_storage_info': get_storage_info,
                  'get_settings': get_settings,
                  'apply_settings': apply_settings,
                  'restore_default_settings': restore_default_settings,
                  'create_vnc_connection': create_vnc_connection,
                  'release_vnc_connection': release_vnc_connection,
                  }

