from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.view import (
    view_config,
    forbidden_view_config,
    )

from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )

from ajpmanager.core.DBConnector import DBConnection
from ajpmanager.core.RedisAuth import authenticate

dbcon = DBConnection().io

def verify_ip(ip):
    allowed_ips = dbcon.lrange("allowed_ips", 0, -1)
    if '*' not in allowed_ips and ip not in allowed_ips:
        return False
    return True


@view_config(route_name='login', renderer='templates/login.jinja2')
@forbidden_view_config(renderer='templates/login.jinja2')
def login(request):

    if not verify_ip(request['REMOTE_ADDR']):
        return HTTPForbidden()

    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    username = ''
    password = ''
    if 'form.submitted' in request.params:
        username = request.params['login']
        password = request.params['password']
        if authenticate(username, password):
            headers = remember(request, username)
            return HTTPFound(location = '/',
                headers = headers)
        message = 'Failed login'

    return dict(
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = username,
        password = password,
    )


@view_config(route_name='logout')
def logout(request):
    if not verify_ip(request['REMOTE_ADDR']):
        return HTTPForbidden()

    headers = forget(request)
    return HTTPFound(location = request.route_url('main'),
        headers = headers)
