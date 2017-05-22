import socket
import threading
import time
import Queue
import sys

class CustomThread(threading.Thread):
  """Thread class with a stop() method. The thread itself has to check
  regularly for the stopped() condition."""

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._stop = threading.Event()

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()

def message_writer(thread_stop):
  stop = 0
  while not stop:
    if not thread_stop.empty():
      stop = thread_stop.get()

    print('sending message {}'.format(stop))
    sock.sendto('WORLD', ('192.168.1.4', 3000))

    time.sleep(2)
    # for i in range(2*10):
    #   if stop:
    #     break
    #   time.sleep(0.1)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 3010))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

writer_thread_stop = Queue.Queue()

writer_thread = threading.Thread(target=message_writer, args=(writer_thread_stop,))
writer_thread.start()

while True:
  try:
    data, addr = sock.recvfrom(1024)
    print("received message: {}".format(data))
  except:
    print('hello')
    writer_thread_stop.put(1)
    writer_thread.join()
    sys.exit(0)