import time
import threading
import SingletonType as SingletonType

class ThreadPool(metaclass=SingletonType.SingletonType):
    def __init__(self):
        self.setThreadCount(10)
        self.m_threads = []

    def setThreadCount(self, nCountThreads):
        self.m_nCountThreads = nCountThreads

    def checkAliveThreads(self):
        nCountAlive = 0
        for i in range(len(self.m_threads) - 1, -1, -1):
            thread = self.m_threads[i]
            if thread.is_alive():
                nCountAlive = nCountAlive + 1
            else:
                self.m_threads.remove(thread)
        return nCountAlive

    def Thread(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        while self.m_nCountThreads <= self.checkAliveThreads():
            time.sleep(0.2)
        t = threading.Thread(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.m_threads.append(t)

        return t