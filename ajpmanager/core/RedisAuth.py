from ajpmanager.core.DBConnector import DBConnection
from passlib.hash import bcrypt

import re

dbcon = DBConnection()

email_pattern = re.compile('^[_.0-9a-z-]+@([0-9a-z][0-9a-z-]+.)+[a-z]{2,4}$')
groups_pattern = re.compile(r'group:(\w+)')


class User(object):

    def __init__(self, username, password, email,
                     first_name = None, last_name = None,
                         group='group:users', expire=None,
                            send_password=False, dbcon=dbcon):
        if 4 > len(password) > 16:
            raise ValueError ('Wrong password length!')
        if not email_pattern.match(email):
            raise ValueError ('Wrong email address!')

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
        if dbcon.io.get('username:' + self.username + ':uid') is not None:
            return False, 'Such username already registered'
        if self.email in dbcon.io.smembers('users:emails'):
            return False, 'Such email address already registered'
        return True,

    def add_to_redis(self, force=False):
        proceed = force
        if not force:
            proceed = self.__check_provided_data()
        if not proceed[0]:
            return proceed

        uid = str(dbcon.io.incr('global:nextUserId'))
        dbcon.io.set('uid:' + uid + ':username', self.username)
        dbcon.io.set('uid:' + uid + ':first_name', self.first_name)
        dbcon.io.set('uid:' + uid + ':last_name', self.last_name)
        dbcon.io.set('uid:' + uid + ':password', self.password)
        dbcon.io.set('uid:' + uid + ':email', self.email)
        dbcon.io.set('uid:' + uid + ':group', self.group)

        if self.expire:
            dbcon.io.expire('uid:' + uid + ':password', self.expire)

        dbcon.io.set('username:' + self.username + ':uid', uid)

        dbcon.io.sadd('users:list', uid)
        dbcon.io.sadd('users:email', self.email)
        dbcon.io.sadd('users:groups', self.group)

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
            return (False, 'Your user account has expired. Please contact your supervisor.')
        return bcrypt.verify(password, password_hash)

    @classmethod
    def change_password(cls, username, new_password, new_password_repeat, old_password=None, force=False):
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
        users = []
        for uid in dbcon.io.smembers('users:list'):
            username = dbcon.io.get('uid:' + uid + ':username')
            first_name = dbcon.io.get('uid:' + uid + ':first_name')
            last_name = dbcon.io.get('uid:' + uid + ':last_name')
            group = dbcon.io.get('uid:' + uid + ':group')
            email = dbcon.io.get('uid:' + uid + ':email')
            users.append({'uid': uid, 'group': group, 'username': username, 'email': email,
                          'first_name': first_name, 'last_name': last_name,
                          'status':  dbcon.io.get('username:' + username + ':online')})
        return sorted(users)

    @classmethod
    def get_all_groups(cls):
        groups = list(dbcon.io.smembers('users:groups'))
        answer = []
        for item in groups:
            try:
                # We're getting only `value` from "groups:{value}" pattern
                answer.append(groups_pattern.search(item).groups()[0]) # Welcome to hell
            except Exception:
                pass
        return answer

    @classmethod
    def remove_user(cls, deleting_uid, deleter_username):
        " Please make sure that deleter_username was checked by authenticated_userid() function! "
        if int(deleting_uid) == 1:
            return False, 'Cannot delete superadmin\'s account'
        # Determining deleter uid and group
        deleter_uid = dbcon.io.get('username:' + deleter_username + ':uid')
        deleter_group = dbcon.io.get('uid:' + deleter_uid + ':group')
        
        username = dbcon.io.get('uid:' + deleting_uid + ':username')
        deleted_user_group = dbcon.io.get('uid:' + deleting_uid + ':group')

        if deleter_group not in ['group:admins', 'group:moderators']:
            return False, 'You don\'t have permissions to delete users'

        if deleted_user_group in ['group:admins', 'group:moderators']:
            if deleter_group != 'group:admins':
                return False, 'You don\'t have permissions to delete admins or moderators'

        # Making deletion
        dbcon.io.expire('uid:' + deleting_uid + ':username', 0)
        dbcon.io.expire('uid:' + deleting_uid + ':first_name', 0)
        dbcon.io.expire('uid:' + deleting_uid + ':last_name', 0)
        dbcon.io.expire('uid:' + deleting_uid + ':password', 0)

        email = dbcon.io.get('uid:' + deleting_uid + ':email')
        dbcon.io.expire('uid:' + deleting_uid + ':email', 0)
        dbcon.io.srem('users:email', email)

        dbcon.io.expire('uid:' + deleting_uid + ':group', 0)
        dbcon.io.expire('username:' + username + ':uid', 0)
        dbcon.io.srem('users:list', deleting_uid)

        # Say farewell...
        return True, 'Farewell ' + str(username)




def groupfinder(userid, request):
    global dbcon
    uid = dbcon.io.get('username:' + userid + ':uid')
    if not uid:
        return None
    group = dbcon.io.get('uid:' + uid + ':group')
    return [group]
