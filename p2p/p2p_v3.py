import select
import socket
import queue
import threading
import sys
import signal
from datetime import datetime

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

class P2P:
  def __init__(self, port, address=''):
    self.port = port
    self.address = address
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.msg_buflength = 1024

    self.reader_thread = CustomThread(target=self._message_reader)
    self.reader_thread.daemon = True

    self.writer_thread = CustomThread(target=self._message_writer)
    self.writer_thread.daemon = True

    self.initiated_close = False

  def bind(self):
    self.socket.bind((self.address, self.port))
    # sockname = self.socket.getsockname()
    # print(self.socket.getsockname())
    # print('P2P started on %s port %s' % (sockname[0], sockname[1]))

  def set_connection_limit(self, limit):
    self.connection_limit = limit

  def listen(self):
    # check if connection_limit attribute has been set
    if hasattr(self, 'connection_limit') and self.connection_limit > 0:
      self.socket.listen(self.connection_limit)
    self.socket.listen()

  def connect(self, ip, port):
    print('Connecting to %s:%s...' % (ip, port))
    self.socket.connect( (ip, int(port)) )
    print('Connected!')

    self.peer_socket = self.socket

    self._send_username()
    self._get_peer_username()
    print('*** You are now chatting with %s ***\n' % (self.peer_username))

  def accept_connection(self):
    self.peer_socket, self.peer_address = self.socket.accept()
    self._get_peer_username()
    self._send_username()
    print('*** You are now chatting with %s ***\n' % (self.peer_username))
    return True

  def send_message(self, data):
    # message = '<%s>: %s' % (self.username, data)
    # message = bytearray(message, 'utf-8')
    message = bytearray(data, 'utf-8')
    self.peer_socket.send(message)

  def get_message(self):
    return self.peer_socket.recv(self.msg_buflength).decode('utf-8')

  def set_username(self, username):
    self.username = username

  def set_peer_username(self, peer_username):
    self.peer_username = peer_username

  def has_initiated_connection(self):
    return self.peer_socket == self.socket

  def remove_peer(self):
    if self.has_initiated_connection():
      self.peer_socket = None
      self.peer_username = None

  def close(self):
    print('*** Closing connection ***')
    self.socket.close()

  ### Private ###

  def _message_reader(self):
    while not self.reader_thread.stopped():
      try:
        data = self.get_message()
        data_cmd = data.split(' ')

        # data_cmd[0] -> peer username
        # data_cmd[1] -> possible command
        # data_cmd[2] -> data for command
        if data_cmd[0] == '/changename':
          if (data_cmd[1]):
            self.set_peer_username(data_cmd[1])
            continue
        elif data_cmd[0] == '/quit':
          self.peer_socket.close()

          if not self.has_initiated_connection():
            self.socket.close()

          # stop the threads
          self.writer_thread.stop()
          self.reader_thread.stop()
          break

        if not data:
          self.close()

          if not self.writer_thread.stopped():
            self.writer_thread.stop()
           
          if not self.reader_thread.stopped(): 
            self.reader_thread.stop()
          
          os._exit(0)
          break

        print('<%s>: %s' % (self.peer_username, data))
      except:
        pass

  def _message_writer(self):
    while not self.writer_thread.stopped():
      data = input()

      if data:
        data_cmd = data.split(' ')

        if (data_cmd[0][0] == '/'):
          if (len(data_cmd) == 1):
            if (data_cmd[0] == '/whoami'):
              print('Your username is: %s' % sock.username)
              continue
            elif data_cmd[0] == '/quit':
              sock.send_message(data)
              self.reader_thread.stop()
              self.writer_thread.stop()
              break

          elif (len(data_cmd) == 2):
            if (data_cmd[0] == '/changename'):
              if (data_cmd[1]):
                sock.set_username(data_cmd[1])

        sock.send_message(data)

  def _send_username(self):
    message = '/changename %s' % (self.username)
    message = bytearray(message, 'utf-8')
    self.peer_socket.send(message)

  def _get_peer_username(self):
    data = self.get_message()
    data = data.split(' ')
    # # handle errors here
    self.peer_username = data[1]


def sigint_handler(signal, frame):
  try:
    sock.send_message('/quit')
  except AttributeError: # ctrl-c occured but sock doesn't have any peer yet
    sock.close()
    sys.exit(0)
  except NameError: # ctrl-c occured but sock hasn't been declared
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

try:
  port = int(input('Enter port number to use: '))
except ValueError:
  print('Error: Port should be an integer value.')
  sys.exit(0)

username = input('What is your name: ')

sock = P2P(port)
sock.set_username(username)
sock.bind()

print('Would you like to:')
print('1 - Listen for connections')
print("2 - Connect to a friend's IP:port")
print('3 - Quit')

mode = int(input('> '))

if mode == 1:
  print('Waiting for connection...')
  sock.listen()
  has_new_connection = False
  while not has_new_connection:
    has_new_connection = sock.accept_connection()

elif mode == 2:
  while True:
    peer_info = input("What is your friend's IP:port? ")
    peer_info = peer_info.split(':')
    if (len(peer_info) == 2) and (len(peer_info[0].split('.'))) == 4:
      break
    else:
      print('Usage: <IP>:<PORT>')
  sock.connect( peer_info[0], int(peer_info[1]) )

elif mode == 3:
  sock.close()
  sys.exit(0)

sock.reader_thread.start()
sock.writer_thread.start()

while True:
  if sock.reader_thread.stopped() and sock.writer_thread.stopped():
    print('*** Closing connection ***')
    break