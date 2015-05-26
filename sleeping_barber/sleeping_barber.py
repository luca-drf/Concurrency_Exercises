import multiprocessing as mp
import Queue
import time
import random
import argparse


POISON_PILL = object()


class Barber(mp.Process):
    def __init__(self, q, s):
        self._sleeping = False
        self._quitting = False
        self.q = q
        self.s = s
        super(Barber, self).__init__(name='Barber')

    def is_sleeping(self):
        return self._sleeping
    
    def cut_hair(self, customer):
        print 'Barber is cutting {}'.format(customer)
        time.sleep(0.001 * random.randint(1, 10))

    def sleep(self):
        self._sleeping = True
        print 'Barber is sleeping'

    def awake(self):
        self._sleeping = False

    def run(self):
        while True:
            try:
                self.s.get_nowait()
                self._quitting = True
            except Queue.Empty:
                pass

            try:
                customer = self.q.get_nowait()
                self.awake()
                self.cut_hair(customer)        
            except Queue.Empty:
                if self._quitting:
                    break
                if not self.is_sleeping():
                    self.sleep()


class Customer(mp.Process):
    def __init__(self, number, q):
        self.number = number
        self.q = q
        super(Customer, self).__init__(name='Customer %d' % number)

    def enter_shop(self):
        try:
            self.q.put_nowait(self.number)
        except Queue.Full:
            print 'Customer {} leaves'.format(self.number)

    def run(self):
        time.sleep(0.001 * random.randint(1, 100))
        self.enter_shop()
        

def create_customer(CUSTOMERS, q):
    processes = []
    for i in xrange(CUSTOMERS):
        processes.append(Customer(i, q))    
    for p in processes:
        p.start()
    for p in processes:
        p.join()


if __name__ == '__main__':
    def uint_type(x):
        x = int(x)
        if x < 0:
            raise argparse.ArgumentTypeError('Must be a non-negative integer')
        return x
    parser = argparse.ArgumentParser(description='Sleeping Barber Problem')
    parser.add_argument('-b', '--buffer', action="store", default=3,
                        type=uint_type,
                        help='Number of chairs (buffer size)')
    parser.add_argument('-c', '--customers', action="store", default=20,
                        help='Number of concurrent customers', type=uint_type)    
    args = parser.parse_args()


    q = mp.Queue(maxsize=args.buffer)
    s = mp.Queue()
    barber = Barber(q, s)
    barber.start()
    create_customer(args.customers, q)
    s.put(POISON_PILL)
    barber.join()
