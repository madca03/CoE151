import select
import socket
import sys
import queue
import signal

def sigint_handler(signal, frame):
    print('Closing the server...')
    server.close()
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(0)

# Bind the socket to the port
server_address = ''
# server_port = input('Input port number: ')
server_port = 10000
server_address = (server_address, server_port)
print('starting up on %s port %s' % server_address)
server.bind(server_address)

# Listen for incoming connections
server.listen(5)

# Sockets from which we expect to read
inputs = [server]

# Sockets to which we expect to write
outputs = []

# Outgoing message queues (socket:Queue)
message_queues = {}

while inputs:

    # Wait for at least one of the sockets to be ready for processing
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    # Handle inputs
    for s in readable:

        if s is server:
            # A 'readable' server socket is ready to accept a connection
            connection, client_address = s.accept()
            print('new connection from', client_address)
            connection.setblocking(0)
            inputs.append(connection)
            outputs.append(connection)

            # Give the connecion a queue for data we wamt tp semd
            message_queues[connection] = queue.Queue()
        else:
            data = s.recv(1024).decode('utf-8')

            # A readable client socket has data
            if data:
                print('received "%s" from %s' % (data, s.getpeername()))

                if data == "/quit":
                    peername = s.getpeername()
                    outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    del message_queues[s]

                    print(peername)
                    for key in message_queues:
                        message_queues[key].put('%s:%s left the chat' % (peername[0], peername[1]))

                else:
                    # broadcast to all clients
                    for key in message_queues:
                        # if s is the sender, don't put his message in the message queue
                        if s is not key:
                            message = '%s: %s' % (s.getpeername(),data)
                            message_queues[key].put(message)
            else:
                # Interpret empty result as closed connection
                print('Closing', client_address, 'after reading no data')
                # stop listening for input on the connection
                outputs.remove(s)
                inputs.remove(s)
                s.close()

                # Remove message queue
                del message_queues[s]

    # Handle outputs
    for s in writable:
        if s in message_queues:
            try:
                next_msg = bytearray(message_queues[s].get_nowait(), 'utf-8')    ###
            except queue.Empty:
                pass
                # No messages waiting so stop checking for writability.
                # print('output queue for', s.getpeername(), 'is empty')
                # outputs.remove(s) # don't remove client from output list
            else:
                print('sending "%s" to %s' % (next_msg, s.getpeername()))
                s.send(next_msg)

    # Handle "exceptional conditions"
    for s in exceptional:
        print('handling exceptional condition for', s.getpeername())
        # Stop listening for input on the connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

        # Remove message queue
        del message_queue[s]
