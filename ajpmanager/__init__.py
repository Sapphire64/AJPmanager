from pyramid import session
from pyramid.config import Configurator
from ajpmanager.core.Connector import VMConnector, DBConnection
from ajpmanager.core.VMdaemon import VMDaemon
from pyramid_beaker import set_cache_regions_from_settings


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    config.include('pyramid_jinja2')
    config.include("pyramid_beaker")

    set_cache_regions_from_settings(settings)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('main', '/')
    config.add_route('presets', '/presets')
    config.add_route('engine.ajax', '/engine.ajax')
    config.scan()


    prepare_database(settings)

    return config.make_wsgi_app()

def prepare_database(settings):
    db = DBConnection()
    allowed_ips = settings['ajp.allowed_ips'].split(',')
    db.io.expire('allowed_ips', 0)
    for ip in allowed_ips:
        db.io.rpush('allowed_ips', ip.strip())