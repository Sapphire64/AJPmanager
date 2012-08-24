from pyramid.config import Configurator
from ajpmanager.core.Connector import VMConnector
from ajpmanager.core.VMdaemon import VMDaemon

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    config.include('pyramid_jinja2')

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('main', '/')
    config.add_route('presets', '/presets')
    config.add_route('engine.ajax', '/engine.ajax')
    config.scan()

    VMConnector()

    return config.make_wsgi_app()

