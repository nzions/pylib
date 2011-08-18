
import threading
import sys
from time import sleep

class ThreadQ:
    def __init__(self, max_threads):
        self.threads = []
        self.queue = []
        self.workerctl = {}

        self.qlock = threading.Lock()

        for i in range(max_threads):
            thr = threading.Thread(target=self._worker, args=(i,))
            self.threads.append(thr)
            self.workerctl[i] = True
            thr.start()

    def add_job(self, callback, func, *args, **kargs):
        self.qlock.acquire()
        self.queue.append( [callback, func, args, kargs] )
        self.qlock.release()

    def finish(self):
        for i in self.workerctl:
            self.workerctl[i] = False

        for thread in self.threads:
            thread.join()
        return()

    def pending_jobs(self):
        return(len(self.queue))

    def _get_job(self):
        callback = None
        func = None
        args = None
        kargs = None
        
        self.qlock.acquire()
        if ( len(self.queue) > 0 ):
            callback, func, args, kargs = self.queue.pop(0)
        self.qlock.release()
        
        return(callback, func, args, kargs)
        
    def _worker(self, myid, *args):
        """ the worker thread"""
        
        while self.workerctl[myid] == True:
            callback, func, args, kargs = self._get_job()
            if ( func != None ):
                try:
                    cb = (True, func(*args, **kargs) )
                except:
                    cb = (False, sys.exc_info())

                if callback != None: callback(*cb)
                
            else:
                sleep(0.1)


if __name__ == "__main__":
    """ Sample of thread q """

    def callback(*args):
        lock.acquire()
        print "Now in callback"
        print "-->" + repr(args)
        lock.release()

    def crashy(i):
        lock.acquire()
        print "Crashing number %d" % i
        lock.release()
        raise(Exception, "oops number %d crashed" % i)

    def myfunc(s,i):
        lock.acquire()
        print "Doing number %d" % i
        lock.release()
        return("you sent %s %d" % (s,i))

    q = ThreadQ(5)
    lock = threading.Lock()

    for i in range(10):
        q.add_job(callback, myfunc, "a", i)
        lock.acquire()
        print "Added %d" % i
        lock.release()
        
    for i in range(10,20):
        q.add_job(callback, crashy, i)
        lock.acquire()
        print "Added %d" % i
        lock.release()
    
    while q.pending_jobs() != 0:
        sleep(0.1)
    q.finish()
        
    
