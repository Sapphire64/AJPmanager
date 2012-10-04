from pyramid.security import (
    Allow,
    Authenticated,
    )



class RootFactory(object):
    __acl__ = [ (Allow, Authenticated, 'registered'),
                (Allow, 'group:admins', 'admins'),
                (Allow, 'group:moderators', 'moderators')]

    def __init__(self, request):
        self.request = request