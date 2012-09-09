import redis

host = '127.0.0.1'
port = 6379
db = 0

def run_terminal():
    dbcon = redis.StrictRedis(host=host, port=port, db=db)
    import pdb; pdb.set_trace()

if __name__ == '__main__':
    run_terminal()