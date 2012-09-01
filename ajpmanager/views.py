from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import view_config
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

    @view_config(route_name='main', renderer='templates/main.jinja2')
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

        return {'text': 'AJPmanager', 'username': 'Vortex'}



class JSONprocessor(object):

    def __init__(self, request):
        self.request = request
        self.session = self.request.session.get_csrf_token()
        self.json = request.json_body

    @view_config(renderer="json", route_name="engine.ajax") #permission='admin') # << auth tag to implement later
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
        vms = VMC.get_vms_list()
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

    def run_machine(self):
        name = self.json.get('data')
        if not name:
            return {'status': False, 'answer': 'No name provided'}
        answer = VMC.run_machine(name)
        return {'status': answer[0], 'answer': answer[1]}


    functions = { # This dictionary is used to implement factory run of the requested functions
                  'verify_new_vm_name': verify_new_vm_name,
                  'get_vms_list': get_vms_list,
                  'get_presets_list': get_presets_list,
                  'run_machine': run_machine,
                  }

