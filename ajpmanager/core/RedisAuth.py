from ajpmanager.core.DBConnector import DBConnection
from passlib.hash import bcrypt

import re

dbcon = DBConnection()

email_pattern = re.compile('^[_.0-9a-z-]+@([0-9a-z][0-9a-z-]+.)+[a-z]{2,4}$')
groups_pattern = re.compile(r'group:(\w+)')


class User(object):
    global dbcon

    def __init__(self, username, password, email,
                     first_name = None, last_name = None,
                         group='group:users', expire=None,
                            send_password=False, dbcon=dbcon):
        if 4 > len(password) > 16:
            raise ValueError ('Wrong password length!')
        if not email_pattern.match(email):
            raise ValueError ('Wrong email address!')

        self.db = dbcon
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = bcrypt.encrypt(password)
        self.email = email
        self.group = group
        self.expire = expire # So you can make temporary account
        self.send_password = send_password

    def __check_provided_data(self):
        # Primitive checks block
        if not self.username or not self.group or not self.password:
            return False, 'Form data is not completely filled'
        if len(self.username) < 5:
            return False, 'Too short user name'
        if len(self.password) < 6:
            return False, 'Wrong password length'
        if not email_pattern.match(self.email):
            return False, 'Wrong Email address: Email address does not match email pattern'
        # Redis checks block
        if self.db.io.get('username:' + self.username + ':uid') is not None:
            return False, 'Such username already registered'
        if self.email in self.db.io.smembers('users:emails'):
            return False, 'Such email address already registered'

        return True,

    def add_to_redis(self, force=False):
        proceed = force
        if not force:
            proceed = self.__check_provided_data()
        if not proceed[0]:
            return proceed



        uid = str(self.db.io.incr('global:nextUserId'))
        self.db.io.set('uid:' + uid + ':username', self.username)
        self.db.io.set('uid:' + uid + ':first_name', self.first_name)
        self.db.io.set('uid:' + uid + ':last_name', self.last_name)
        self.db.io.set('uid:' + uid + ':password', self.password)
        self.db.io.set('uid:' + uid + ':email', self.email)
        self.db.io.set('uid:' + uid + ':group', self.group)

        if self.expire:
            self.db.io.expire('uid:' + uid + ':password', self.expire)

        self.db.io.set('username:' + self.username + ':uid', uid)

        self.db.io.sadd('users:list', uid)
        self.db.io.sadd('users:email', self.email)
        self.db.io.sadd('users:groups', self.group)

        if self.send_password:
            self._send_email()

        return True, ''

    def _send_email(self):
        pass # Dummy

    @classmethod
    def authenticate(cls, username, password):
        uid = dbcon.io.get('username:' + username + ':uid')
        if uid is None:
            return False
        password_hash = dbcon.io.get('uid:' + uid + ':password')
        if not password_hash:
            return (False, 'Password expired.')
        return bcrypt.verify(password, password_hash)

    @classmethod
    def change_password(cls, username, new_password, new_password_repeat, old_password=None, force=False):
        global dbcon
        if new_password != new_password_repeat:
            raise ValueError ('Entered passwords does not match')

        if 4 > len(new_password) > 16:
            raise ValueError ('Wrong password length!')

        uid = dbcon.io.get('username:' + username + ':uid')
        if not uid:
            raise ValueError ('Wrong username provided')

        if not force:
            if not old_password or not cls.authenticate(username, old_password):
                raise ValueError ('Wrong old password provided')
        dbcon.io.set('uid:' + uid + ':password', bcrypt.encrypt(new_password))
        return True


    @classmethod
    def get_all_users(cls):
        global dbcon
        users = []
        for uid in dbcon.io.smembers('users:list'):
            username = dbcon.io.get('uid:' + uid + ':username')
            first_name = dbcon.io.get('uid:' + uid + ':first_name')
            last_name = dbcon.io.get('uid:' + uid + ':last_name')
            group = dbcon.io.get('uid:' + uid + ':group')
            email = dbcon.io.get('uid:' + uid + ':email')
            users.append({'uid': uid, 'group': group, 'username': username, 'email': email,
                          'first_name': first_name, 'last_name': last_name,
                          'status':  dbcon.io.get('uid:' + username + ':online')})
        return sorted(users)

    @classmethod
    def get_all_groups(cls):
        global dbcon
        global groups_pattern
        groups = list(dbcon.io.smembers('users:groups'))
        answer = []
        for item in groups:
            try:
                # We're getting only `value` from "groups:{value}" pattern
                answer.append(groups_pattern.search(item).groups()[0]) # Welcome to hell
            except Exception:
                pass
        return answer


def groupfinder(userid, request):
    global dbcon
    uid = dbcon.io.get('username:' + userid + ':uid')
    if not uid:
        return None
    group = dbcon.io.get('uid:' + uid + ':group')
    if group:
        return [group]
    else:
        return []
