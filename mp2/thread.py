#!/usr/bin/python
import threading
import Queue
import time

# http://stackoverflow.com/questions/15461413/how-to-share-a-variable-between-2-threads
def func1(num, q):
  while num < 100000000:
    num = num ** 2
    q.put(num)
    time.sleep(2)

def func2(num, q):
  while num < 100000000:
    num = q.get()   # Queue.get() method blocks until the queue becomes non-empty
    print(num)

num = 2
q = Queue.Queue()
thread1 = threading.Thread(target=func1,args=(num,q))
thread2 = threading.Thread(target=func2,args=(num,q))
# print('setup')
thread1.start()
thread2.start()