from ajpmanager.core.DBConnector import DBConnection
from passlib.hash import bcrypt
from time import sleep

dbcon = DBConnection()

def authenticate(username, password):
    sleep(1.2) # Slowing down attacks
    uid = dbcon.io.get('username:' + username + ':uid')
    if uid is None:
        return False
    password_hash = dbcon.io.get('uid:' + uid + ':password')
    if not password_hash:
        return False
        #return (False, 'Your user account has expired. Please contact your supervisor.')
    return bcrypt.verify(password, password_hash)


def groupfinder(userid, request):
    uid = dbcon.io.get('username:' + userid + ':uid')
    if not uid:
        return None
    group = dbcon.io.get('uid:' + uid + ':group')
    return [group]
