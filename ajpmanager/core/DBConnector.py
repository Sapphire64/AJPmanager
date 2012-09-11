import redis

class DBConnection(object):

    def __init__(self, host='localhost', port=6379, db=0):
        from time import time
        t1 = time()
        self._connection = redis.StrictRedis(host=host, port=port, db=db)
        print ('Redis initialized: ' + str(time() - t1))

    @property
    def io(self):
        return self._connection
