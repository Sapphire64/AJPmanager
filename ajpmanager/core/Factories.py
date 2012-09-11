from pyramid.security import (
    Allow,
    Everyone,
    )



class RootFactory(object):
    __acl__ = [ (Allow, 'group:admins', 'admin'),
                (Allow, 'group:users', 'admin')]

    def __init__(self, request):
        pass