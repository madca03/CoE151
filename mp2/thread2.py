import threading
import sys

def hello():
  print('Hello world')
  t = threading.Timer(2.0, hello)
  t.start()

t = threading.Timer(2.0, hello)
t.start()

try:
  while True:
    a = 1
except KeyboardInterrupt:
  t.cancel()
  t.join()
  sys.exit(0)