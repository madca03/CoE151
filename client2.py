import socket
import sys
import threading
import signal
import os

# class StoppableThread(threading.Thread):
#     def __init__(self):
#         super(StoppableThread, self).__init__()
#         self._stop = threading.Event()
#
#     def stop(self):
#         self._stop.set()
#
#     def stopped(self):
#         return self._stop.isSet()

def sigint_handler(signal, frame):
    print('Closing the client socket...')
    # message_reader_stop.set()
    csock.close()
    sys.exit(0)

def reader():
    """ thread worker function """
    # while not stop_event.is_set(:
    while True:
        try:
            data = csock.recv(1024).decode('utf-8')
            print(data)
            # print(data, end='/r')
            # print('%s: received "%s"' % (csock.getsockname(), data))
            if not data:
                print('closing socket', csock.getsockname())
                csock.close()
                os._exit(0)
                # thread.interrupt_main()
                # thread.exit()
        except:
            pass

signal.signal(signal.SIGINT, sigint_handler)

server_ip = input('Input server IP address: ')
server_port = int(input('Input server port number: '))

csock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Connecting to %s port %s', (server_ip, server_port))
csock.connect((server_ip, server_port))
print('Connected. IP address = %s, Port = %s' % csock.getpeername())


# message_reader_stop = threading.Event()
message_reader = threading.Thread(target=reader)
message_reader.daemon = True
message_reader.start()


while True:
    cdata = input()
    cdata = bytearray(cdata, 'utf-8')
    csock.send(cdata)
