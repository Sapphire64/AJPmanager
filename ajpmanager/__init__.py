from pyramid import session
from pyramid.config import Configurator
from ajpmanager.core.Connector import VMConnector, DBConnection
from ajpmanager.core.VMdaemon import VMDaemon
from pyramid_beaker import set_cache_regions_from_settings


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    prepare_database(settings)

    config = Configurator(settings=settings)

    config.include('pyramid_jinja2')
    config.include("pyramid_beaker")

    set_cache_regions_from_settings(settings)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('main', '/')
    config.add_route('presets', '/presets')
    config.add_route('engine.ajax', '/engine.ajax')
    config.scan()



    return config.make_wsgi_app()

def prepare_database(settings):
    db = DBConnection()

    db.io.set('provider', settings['ajp.vm_provider'])

    allowed_ips = settings['ajp.allowed_ips'].split(',')
    db.io.expire('allowed_ips', 0)
    for ip in allowed_ips:
        db.io.rpush('allowed_ips', ip.strip())

    # Applying default settings
    # Warning! FIXME: we have same functionality in VMConnector class
    # Any changes here must by applied there
    if not db.io.get('XEN_PATH'):
        db.io.set('XEN_PATH', '/xen')

    if not db.io.get('KVM_PATH'):
        db.io.set('KVM_PATH', '/kvm')

    if not db.io.get('PRESETS'):
        db.io.set('PRESETS','presets')

    if not db.io.get('IMAGES'):
        db.io.set('IMAGES', 'images')

    if not db.io.get('CONFIG_NAME'):
        db.io.set('CONFIG_NAME', 'config.xml')

    if not db.io.get('VMIMAGE_NAME'):
        db.io.set('VMIMAGE_NAME', 'image.img')

    if not db.io.get('DESCRIPTION_NAME'):
        db.io.set('DESCRIPTION_NAME', 'description.txt')

    if not db.io.get('VMMANAGER_PATH'):
        db.io.set('VMMANAGER_PATH', 'qemu:///system')