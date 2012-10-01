from pyramid.security import (
    Allow,
    Authenticated,
    )



class RootFactory(object):
    __acl__ = [ (Allow, Authenticated, 'registered'),
                (Allow, 'group:admins', 'admin')]

    def __init__(self, request):
        self.request = request