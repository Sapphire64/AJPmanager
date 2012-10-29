from time import sleep
from ajpmanager.core.DBConnector import DBConnection
from passlib.hash import bcrypt
import re
from ajpmanager.core.RedisAuth import authenticate

dbcon = DBConnection()

email_pattern = re.compile('^[_.0-9a-z-]+@([0-9a-z][0-9a-z-]+.)+[a-z]{2,4}$')
groups_pattern = re.compile(r'group:(\w+)')

class User(object):

    def __init__(self, username, password, email,
                 first_name = None, last_name = None,
                 group='group:users', expire=None,
                 send_password=False):
        if not 4 <= len(password) <= 16:
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
    def get_user_info_by_id(cls, uid):
        pack = dict()

        pack['username'] = dbcon.io.get('uid:' + uid + ':username')
        if not pack['username']:
            return False, 'Wrong user id'
        pack['first_name'] = dbcon.io.get('uid:' + uid + ':first_name')
        pack['last_name'] = dbcon.io.get('uid:' + uid + ':last_name')
        pack['email'] = dbcon.io.get('uid:' + uid + ':email')
        pack['group'] = dbcon.io.get('uid:' + uid + ':group')
        pack['online'] =  dbcon.io.get('username:' + pack['username'] + ':online')

        pack['machines'] = list(dbcon.io.smembers('uid:' + uid + ":machines"))

        return True, pack

    @classmethod
    def get_user_info_by_name(cls, name):
        uid = dbcon.io.get('username:' + str(name) + ':uid')
        if not uid:
            return False, "User does not exists"
        else:
            return cls.get_user_info_by_id(uid)

    @classmethod
    def _update_groups_list(cls):
        """ Removing from users:groups unused groups
        """
        groups_list = dbcon.io.smembers('users:groups')
        used_groups = set(['group:admins', 'group:moderators', 'group:users']) # Set with non-deleting default groups
        for i in range(2, int(dbcon.io.get('global:nextUserId'))+1):
            group = dbcon.io.get('uid:' + str(i) + ':group')
            if group:
                used_groups.add(group)
        # TODO: optimize next algorithm
        # Removing unused groups from groups list
        for group in groups_list:
            if group not in used_groups:
                dbcon.io.srem('users:groups', group)
        # Adding new groups not listed in groups list
        for group in used_groups:
            if group not in groups_list:
                dbcon.io.sadd('users:groups', group)

    @classmethod
    def remove_user(cls, deleting_uid):
        " Please make sure that deleter_username was checked by authenticated_userid() function! "
        if int(deleting_uid) == 1:
            return False, 'Cannot delete superadmin\'s account'

        username = dbcon.io.get('uid:' + deleting_uid + ':username')
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

        cls._update_groups_list()

        # Say farewell...
        print ("Farewell, %s" % username)
        return True, 'Farewell ' + str(username)

    @classmethod
    def update_user(cls, username, first_name=None, last_name=None,
                    group=None, email=None, password=None, machines=None):
        """ Function which applies provided username's new information.
        Only granted users can change user information and nobody can change username.
        """
        uid = dbcon.io.get('username:' + username + ':uid')
        if not uid:
            raise SystemError ('UID for provided username not found!')

        update_password = False
        if password is not None:
            if not 4 <= len(password) <= 16:
                raise ValueError ('Wrong password length!')
            password = bcrypt.encrypt(password)
            update_password = True

        update_email = False
        if email is not None:
            if not email_pattern.match(email):
                raise ValueError ('Wrong email address!')
            else:
                update_email = True

        # Applying changes
        if first_name is not None:
            dbcon.io.set('uid:' + uid + ':first_name', first_name)
        if last_name is not None:
            dbcon.io.set('uid:' + uid + ':last_name', last_name)
        if group is not None:
            old_group = dbcon.io.get('uid:' + uid + ':group')
            dbcon.io.set('uid:' + uid + ':group', group)
            cls._update_groups_list()
        if update_email:
            dbcon.io.set('uid:' + uid + ':email', email)
        if update_password:
            dbcon.io.set('uid:' + uid + ':password', password)

        if machines is not None:
            dbcon.io.expire('uid:' + uid + ':machines', 0)
            for machine in machines:
                dbcon.io.sadd('uid:' + uid + ':machines', machine)

        # All done.