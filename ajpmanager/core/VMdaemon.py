from multiprocessing.process import Process
from time import sleep


class VMDaemon(object):
    """ Class for updating info in Redis by reading and processing VM provider data
    Also will be used as interface to DB
    """

    def __init__(self, connection):
        self.run_main_loop()


    def print_it(self):
        while True:
            print ('Hi!')
            sleep(3)


    def run_main_loop(self):
        p = Process(target=self.print_it, args=())
        p.start()
