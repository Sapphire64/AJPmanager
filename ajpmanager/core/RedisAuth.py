from passlib.hash import bcrypt
from ajpmanager.core.DBConnector import DBConnection

dbcon = DBConnection()


class User(object):
    global dbcon

    def __init__(self, username, password, dbcon=dbcon):
        self.username = username
        self.password = bcrypt.encrypt(password)
        self.db = dbcon
        if not self.db:
            raise Exception ('No redis connection provided')
        self.__add_to_redis()

    def __add_to_redis(self):
        uid = db.io.incr('global:nextUserId')
        self.db.io.set('uid:' + uid + ':username', self.username)
        self.db.io.set('uid:' + uid + ':password', self.password)
        self.db.io.set('username:' + self.username + ':uid', uid)
        self.db.io.rpush('users:list', uid)

    @classmethod
    def authenticate(cls, username, password):
        uid = dbcon.io.get('username:' + username + ':uid')
        if not uid:
            return False
        password_hash = dbcon.io.get('uid:' + uid + ':password')
        return bcrypt.verify(password, password_hash)



GROUPS = {'admin':['group:admins']}

def groupfinder(userid, request):
    return GROUPS.get(userid, ['group:users']) # special group or default one