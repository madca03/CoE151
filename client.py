import socket
import sys
import threading

messages = [ 'This is the message.',
             'It will be sent ',
             'in parts.',
          ]

server_ip = raw_input('Input server IP address: ')
server_port = int(raw_input('Input server port number: '))

# Create TCP/IP socket
socks = [socket.socket(socket.AF_INET, socket.SOCK_STREAM),
         socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ]

# Connect the socket to the port where the server is listening
print('connecting to %s port %s' % (server_ip, server_port))
for s in socks:
    s.connect((server_ip, server_port))

for message in messages:

    # Send messages on both Sockets
    for s in socks:
        print('%s: sending "%s"' % (s.getsockname(), message))
        s.send(message)

    # Read responses on both Sockets
    for s in socks:
        data = s.recv(1024)
        print('%s: received "%s"' % (s.getsockname(), data))
        if not data:
            print('closing socket', s.getsockname())
            s.close()
