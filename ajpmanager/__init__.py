from pyramid import session
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from ajpmanager.core.Connector import VMConnector
from ajpmanager.core.VMdaemon import VMDaemon
from pyramid_beaker import set_cache_regions_from_settings
from ajpmanager.core.DBConnector import DBConnection
from ajpmanager.core.RedisAuth import groupfinder


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    prepare_database(settings)





    authn_policy = AuthTktAuthenticationPolicy(
            'sikret;)', callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings,
        root_factory='ajpmanager.factories.RootFactory')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.include('pyramid_jinja2')
    config.include("pyramid_beaker")

    set_cache_regions_from_settings(settings)


    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('main', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
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

    if not db.io.get('global:nextUserId'):
        raise SystemError ('No users data found, to start you must run scripts/initialize_redis.py script inside of project')
    elif not db.io.get('uid:1:username'):
        raise SystemError ('Super user entry not found. Run scripts/initialize_redis.py to set up default super user account')
    elif not db.io.get('uid:1:password'):
        raise SystemError ('Super user entry exists but has blank password, launch aborted. Check scripts/initialize_redis.py to restore default or any given password to super user')
    else:
        pass