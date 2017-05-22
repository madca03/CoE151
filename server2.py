import select
import socket
import sys
import queue
import signal
from datetime import datetime

class Server:
    def __init__(self, port, address=''):
        self.port = port
        self.address = address
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.server_socket.setblocking(0)
        self.input_sockets = [self.server_socket]
        self.output_sockets = []
        self.msg_queues = {}
        self.usernames = {}

    def bind(self):
        print('starting up on %s port %s' % (self.address, self.port))
        self.server_socket.bind((self.address, self.port))

    def set_connection_limit(self, limit):
        self.connection_limit = limit
        self.server_socket.listen(limit)

    def listen(self):
      # check if connection_limit attribute has been set
      if hasattr(self, 'connection_limit') and self.connection_limit > 0:
        self.server_socket.listen(self.connection_limit)
      self.server_socket.listen()

    def has_inputs(self):
        return not not self.input_sockets

    def accept_connection(self):
        client_socket, client_address = self.server_socket.accept()
        print('new connection from', client_address)
        # client_socket.setblocking(0)
        self.input_sockets.append(client_socket)
        self.output_sockets.append(client_socket)
        self.msg_queues[client_socket] = queue.Queue()

        client_info = client_socket.getpeername()
        username = '%s:%s' % (client_info[0], client_info[1])
        self.usernames[client_socket] = username

        self.add_client_join_message_to_clients(client_socket)

    def get_client_data(self, client_socket):
        return client_socket.recv(1024).decode('utf-8')

    def remove_client(self, client_socket):

        client_name = client_socket.getpeername()
        print('Closing connection with %s:%s' % (client_name[0], client_name[1]))
        self.output_sockets.remove(client_socket)
        self.input_sockets.remove(client_socket)
        client_socket.close()
        del self.msg_queues[client_socket]

        self.add_client_quit_message_to_clients(client_socket)

    def add_client_quit_message_to_clients(self, client_socket):
        for key in self.msg_queues:
            message = "<server>: %s left the chat" % (self.usernames[client_socket])
            self.msg_queues[key].put(message)

    def add_broadcast_message_to_clients(self, client_socket, data):
        for key in self.msg_queues:
            if key is not client_socket:
                message = '<%s>: %s' % (self.usernames[client_socket], data)
                self.msg_queues[key].put(message)

    def send_message_to(self, client_socket):
        # Queue.get_nowait() -> doesn't block, returns queue.Empty exception if none is available
        #                    -> return an item if one is immediately available 
        try:
            next_msg = bytearray(self.msg_queues[client_socket].get_nowait(), 'utf-8')    ###
        except queue.Empty:
            pass
            # No messages waiting so stop checking for writability.
            # print('output queue for', s.getpeername(), 'is empty')
            # outputs.remove(s) # don't remove client from output list
        else:
            print('sending "%s" to %s' % (next_msg, client_socket.getpeername()))
            client_socket.send(next_msg)

    def change_client_username(self, client_socket, username):
        old_username = self.usernames[client_socket]
        if client_socket in self.usernames:
            self.usernames[client_socket] = username
            self.add_changed_username_message_to_clients(client_socket, old_username);


    # param: client socket - the client that changed username
    # client socket should not be given the message about its changing of username
    def add_changed_username_message_to_clients(self, client_socket, old_username):
        for key in self.msg_queues:
            if key is not client_socket:
                message = "<server>: '%s' changed its username to '%s'" % (
                    old_username, self.usernames[client_socket] )
                self.msg_queues[key].put(message)

    def add_user_info_message_to_client(self, client_socket, requested_client_username):
        requested_client_socket = self.get_client_by_username(requested_client_username)

        if (requested_client_socket):
            requested_client_info = requested_client_socket.getpeername()
            message = '<server>: username:%s, IP_address:%s, Port:%s' % (
                self.usernames[requested_client_socket],
                requested_client_info[0],
                requested_client_info[1] )
            self.msg_queues[client_socket].put(message)
        else:
            message = "<server>: username doesn't exist"
            self.msg_queues[client_socket].put(message)

    def get_client_by_username(self, username):
        for key in self.usernames:
            if self.usernames[key] == username:
                return key
        return None

    def add_time_message_to_client(self, client_socket):
        current_time = datetime.now()
        message = '<server>: current_time is %s' % (current_time.strftime('%I:%M:%S %p - %x'))
        self.msg_queues[client_socket].put(message)

    def add_client_join_message_to_clients(self, client_socket):
        for key in self.msg_queues:
            if key is not client_socket:
                message = '<server>: %s joined the chat' % (self.usernames[client_socket])
                self.msg_queues[key].put(message)

    def close(self):
        self.server_socket.close()

def sigint_handler(signal, frame):
    print('Closing the server...')
    sock.close()
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

# port = 10000
port = int(input('Enter port: '))
sock = Server(port)
sock.bind()
sock.set_connection_limit(5)
sock.listen()

while sock.has_inputs():
    # Wait for at least one of the sockets to be ready for processing
    readable, writable, exceptional = select.select(sock.input_sockets, sock.output_sockets, sock.input_sockets)

    # Handle inputs
    for s in readable:
        if s is sock.server_socket:
            # A 'readable' server socket is ready to accept a connection
            sock.accept_connection()
        else:
            data = sock.get_client_data(s)
            if data:
                if data[0] != '/':
                    print('received "%s" from %s' % (data, s.getpeername()))
                    sock.add_broadcast_message_to_clients(s, data)
                else:
                    data = data.split(' ', 1)

                    if len(data) > 1:
                        cmd = data[0]
                        data = data[1]

                        if cmd == '/changename':
                            sock.change_client_username(s, data)
                        elif cmd == '/userinfo':
                            sock.add_user_info_message_to_client(s, data)
                    
                    else:
                        cmd = data[0]

                        if cmd == '/quit':
                            sock.remove_client(s)
                        elif cmd == '/time':
                            sock.add_time_message_to_client(s)

                   

            else:
                # Interpret empty result as closed connection
                sock.remove_client(s)

    # Handle outputs
    for s in writable:
        if s in sock.msg_queues:
            sock.send_message_to(s)

    # Handle "exceptional conditions"
    for s in exceptional:
        sock.remove_client(s)
