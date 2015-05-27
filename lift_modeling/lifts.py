import argparse
import time
import Queue
import random
import threading

POISON_PILL = object()

class Lift(threading.Thread):
    def __init__(self, lift, queue, update_q, floors):
        super(Lift, self).__init__(name='Lift%d' % lift)
        self.lift = lift
        self.call_q = queue
        self.update_q = update_q
        self.floor = 0
        self.floors = floors
        self.total_travel = 0

    def move(self, floor):
        time.sleep(0.001 * abs(floor - self.floor))
        floor, self.floor = self.floor, floor
        return floor

    def run(self):
        while 1:
            floor = self.call_q.get()
            if floor is POISON_PILL:
                break
            next_floor = random.randrange(0, self.floors)
            old_floor = self.move(floor)
            self.move(next_floor)
            update_q.put((self.lift, next_floor))
            #print '%s called from %d gone to %d' % (
                #self.name, floor, next_floor)
            self.total_travel += abs(old_floor - floor)


class Dispatcher(threading.Thread):
    def __init__(self, floors, calls_q, lifts_q, update_q):
        super(Dispatcher, self).__init__(name='Dispatcher')
        self.floors = floors
        self.calls_q = calls_q
        self.lifts_q = lifts_q
        self.update_q = update_q
        self.lifts_pos = [0 for _ in xrange(len(lifts_q))]
        
    def get_closer_lift(self, call):
        for _ in xrange(len(self.lifts_pos)):
            if not self.update_q.empty():
                lift, floor = self.update_q.get_nowait()
                self.lifts_pos[lift] = floor
        
        dist = self.floors
        closer = random.randrange(0, len(self.lifts_pos))
        for i in xrange(len(self.lifts_pos)):
            if self.lifts_pos[i]:
                curr_dist = abs(self.lifts_pos[i] - call)
                if curr_dist < dist:
                    closer = i
                    dist = curr_dist
        return closer

    def shut_down(self):
        for i in self.lifts_q:
            i.put(POISON_PILL)

    def run(self):
        while True:
            call = calls_q.get()
            if call is POISON_PILL:
                self.shut_down()
                break
            lift = self.get_closer_lift(call)
            self.lifts_q[lift].put(call)
            self.lifts_pos[lift] = None


def create_lifts(lifts, floors):
    lifts_q = []
    tlifts = []
    update_q = Queue.Queue()
    for i in xrange(lifts):
        q = Queue.Queue()
        lifts_q.append(q)
        lift = Lift(i, q, update_q, floors)
        tlifts.append(lift)        
        lift.start()
    return lifts_q, update_q, tlifts


def random_caller(queue, floors, iterations):
    for x in xrange(iterations):
        call = random.randrange(0, floors)
        queue.put(call)
    queue.put(POISON_PILL)
    

if __name__ == '__main__':
    def uint_type(x):
        x = int(x)
        if x < 0:
            raise argparse.ArgumentTypeError('Must be a non-negative integer')
        return x
    parser = argparse.ArgumentParser(description='Lifts Problem')
    parser.add_argument('-l', '--lifts', action="store", default=5,
                        type=uint_type,
                        help='Number of lifts')
    parser.add_argument('-f', '--floors', action="store", default=20,
                        help='Number of floors', type=uint_type)
    parser.add_argument('-c', '--calls', action="store", default=10,
                        help='Number of calls', type=uint_type)
    args = parser.parse_args()

    liftsn = args.lifts
    floorsn = args.floors
    iterationsn = args.calls

    calls_q = Queue.Queue()
    lifts_q, update_q, lifts = create_lifts(liftsn, floorsn)
    disp = Dispatcher(floorsn, calls_q, lifts_q, update_q)
    disp.start()
    random_caller(calls_q, floorsn, iterationsn)

    for lift in lifts:
        lift.join()
        print '%s travelled %d floors' % (lift.name, lift.total_travel)

    disp.join()
