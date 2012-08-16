from pyramid.view import view_config

class MainPage(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='main', renderer='templates/main.jinja2')
    def __call__(self):
        return {'text': 'Hi!', 'username': 'Vortex'}



class PresetsPage(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='presets', renderer='templates/test.jinja2')
    def __call__(self):
        return {'text': 'Hi!', 'username': 'Vortex'}