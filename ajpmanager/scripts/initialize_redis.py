from passlib.hash import bcrypt
import redis

# TODO: READ FROM COMMAND LINE OPTIONS

# Presets
host='localhost'
port=6379
db=0

# Redis connection
db = redis.StrictRedis(host=host, port=port, db=db)

# If you want to rewrite all the values in DB
force = False

def initialize_vm_settings():
    global db
    global force
    # WARNING! We have same functionality in VMConnector class
    # Any changes here should by applied there
    # o you can always reset this values via admin interface
    if force or not db.get('XEN_PATH'):
        db.set('XEN_PATH', '/xen')

    if force or db.get('KVM_PATH'):
        db.set('KVM_PATH', '/kvm')

    if force or db.get('PRESETS'):
        db.set('PRESETS','presets')

    if force or db.get('IMAGES'):
        db.set('IMAGES', 'images')

    if force or db.get('CONFIG_NAME'):
        db.set('CONFIG_NAME', 'config.xml')

    if force or db.get('VMIMAGE_NAME'):
        db.set('VMIMAGE_NAME', 'image.img')

    if force or db.get('DESCRIPTION_NAME'):
        db.set('DESCRIPTION_NAME', 'description.txt')

    if force or db.get('VMMANAGER_PATH'):
        db.set('VMMANAGER_PATH', 'qemu:///system')
    # END of warning
    print ('Basic VM settings were added into Redis DB.\n')


def initialize_users():
    global db
    global force
    if force or not db.io.get('global:nextUserId') or not db.oi.get('uid:1:username'):
        db.set('global:nextUserId', 1)
        db.set('uid:1:username', 'admin')
        db.set('uid:1:password', bcrypt.encrypt('admin'))
        print ("Super user record was added, use next data to log in:\n - username: 'admin' \n - password: 'admin'\n")
    else:
        print ('Super user exists, change force to True to rewrite super user\'s password')



if __name__ == '__main___':
    initialize_vm_settings()
    initialize_users()
    print ('All done.')
    exit(0)