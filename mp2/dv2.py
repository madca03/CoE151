#!/usr/bin/python

import sys
import socket
import time
import threading
import Queue
import fcntl
import struct
import math

def message_reader(thread_stop):
  stop = 0

  while not stop:
    if not thread_stop.empty():
      stop = thread_stop.get()

    try:
      data, addr = sock.recvfrom(1024)
      lines = data.split()

      if lines[0] == '/route':
        neighbor = lines[1]
        neighbor_ip, neighbor_port = lines[1].split(':')
        neighbor_port = int(neighbor_port)

        # empty the neighbor's forwarding table previously stores
        neighbor_table[neighbor] = {}


        # # update / store the neighbor's forwarding table
        for i in range(len(lines) - 2):
          neighbor_dest_node, neighbor_dest_node_cost = lines[i+2].split(',')
          neighbor_dest_node_cost = int(neighbor_dest_node_cost)
          neighbor_dest_node_ip, neighbor_dest_node_port = neighbor_dest_node.split(':')
          neighbor_dest_node_port = int(neighbor_dest_node_port)
          neighbor_table [neighbor] [neighbor_dest_node] = {'ip': neighbor_dest_node_ip , 'port': neighbor_dest_node_port , 'cost': neighbor_dest_node_cost }

          if not (neighbor_dest_node in forwarding_table):
            forwarding_table[neighbor_dest_node] = {'ip': neighbor_ip, 'port': neighbor_port, 'cost': (forwarding_table[neighbor]['cost'] + neighbor_dest_node_cost) }


      for dest_node in forwarding_table.keys():
        # destination node is itself so ignore
        if dest_node == host_addr:
          continue 

        dcost = inf_cost
        old_dcost = inf_cost
        neigh_index = 0

        for i in range(len(local_table)):
          neigh_addr =  local_table[i]['ip'] + ':' + str(local_table[i]['port'])

          # local_table[i]['ip'] + ':' + str(local_table['port']) -> neighbor node
          # dest_node -> actual destination node
          if neigh_addr in neighbor_table:  # check if a neighbor has sent a forwarding table or the neigh_addr points to host

            # check for self link cost change on neighbor nodes
            if neighbor_table[neigh_addr][neigh_addr]['cost'] > 0:
              local_cost = neighbor_table[neigh_addr][neigh_addr]['cost']
            else: # if link cost to node is zero, use the local link cost generated from config file
              local_cost = local_table[i]['cost']

            if dest_node in neighbor_table[neigh_addr]:  # check if a the dest node is in the neigbor's forwarding table
              old_dcost = dcost # store previous dcost for index comparison
            
              # Dx(y) = c(x,v) + Dv(y)
              dcost = min(dcost, local_cost + neighbor_table[neigh_addr][dest_node]['cost'])
              if old_dcost > dcost:
                neigh_index = i

        forwarding_table[dest_node]['ip'] = local_table[neigh_index]['ip']
        forwarding_table[dest_node]['port'] = local_table[neigh_index]['port']
        forwarding_table[dest_node]['cost'] = dcost
    except:
      pass

def get_ip_address(ifname, s):
  return socket.inet_ntoa(fcntl.ioctl(
      s.fileno(),
      0x8915,  # SIOCGIFADDR
      struct.pack('256s', ifname[:15])
  )[20:24])

def forwarding_table_to_str():
  ftstr = '/route ' + host_ip + ':' + str(host_port) + '\n'

  for key, value in forwarding_table.items():
    ftstr += key + ',' + str(value['cost']) + '\n'

  return ftstr

if len(sys.argv) < 3:
  print('Wrong number of arguments')
  sys.exit(0)


host_port = int(sys.argv[2])

# [ 
#   {'ip' (neigh): __ 'port' (neigh): ___, 'cost' (host-to-neigh): ___ },
#   {'ip' (neigh): __ 'port' (neigh): ___, 'cost' (host-to-neigh): ___ },
# ]
local_table = []

# {'ip:port' (dest): {'ip' (neigh): __ , 'port' (neigh): __ , 'cost' (host-to-dest): },
#  'ip:port' (dest): {'ip' (neigh): __ , 'port' (neigh): __ , 'cost' (host-to-dest): },
# }
forwarding_table = {}

# key: 'ip:port' (source)
# value: {
#           {'ip:port' (dest): {'ip': __ , 'port': __ , 'cost': __ },
#           {'ip:port' (dest): {'ip': __ , 'port': __ , 'cost': __ },
#         }
neighbor_table = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', host_port))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setblocking(False)

try:
  host_ip = get_ip_address('wlo1', sock)
except IOError:
  host_ip = '127.0.0.1'

host_addr = host_ip + ':' + str(host_port)

local_table.append({'ip': host_ip, 'port': host_port, 'cost': 0})
forwarding_table [ host_ip + ':' + str(host_port) ] = { 'ip': host_ip, 'port': host_port, 'cost': 0 }

# http://stackoverflow.com/questions/8009882/how-to-read-large-file-line-by-line-in-python
with open(sys.argv[1]) as f:
  for line in f:
    neighbor_ip, neighbor_port, neighbor_cost = line.rstrip().split(',')
    neighbor_port = int(neighbor_port)
    neighbor_cost = int(neighbor_cost)
    local_table.append( {'ip': neighbor_ip, 'port': neighbor_port, 'cost': neighbor_cost } )
    forwarding_table[ neighbor_ip + ':' + str(neighbor_port) ] = { 'ip': neighbor_ip, 'port': neighbor_port, 'cost': neighbor_cost }

for entry in local_table:
  print(entry)
print('port: {}\n'.format(host_port))

message_reader_stop = Queue.Queue()

reader_thread = threading.Thread(target=message_reader,args=(message_reader_stop,))
reader_thread.start()

inf_cost = 1000
sleep_time = 0.5

# try:
#   time.sleep(sleep_time)
# except KeyboardInterrupt:
#   message_reader_stop.put(1)
#   reader_thread.join()
#   sys.exit(0)

while True:
  try:
    for key, value in neighbor_table.items():
      print('neighbor table ({})'.format(key))
      for key2, value2 in neighbor_table[key].items():
        print(key2,value2['cost'])
    print("host's table ({}:{})".format(host_ip, host_port))
    for key, value in forwarding_table.items():
      print(key,value)
    print('\n')

    for entry in local_table:
      if (entry['ip'] == host_ip) and (entry['port'] == host_port): 
        continue
      else:
        try:
          sock.sendto(forwarding_table_to_str(), (entry['ip'], entry['port']))
        except socket.error:
          pass
        time.sleep(sleep_time)
  except KeyboardInterrupt:
    local_table[0]['cost'] = inf_cost
    forwarding_table[host_addr]['cost'] = inf_cost

    print("sending infinite self cost")
    for entry in local_table:
      if (entry['ip'] == host_ip) and (entry['port'] == host_port): 
        continue
      else:
        try:
          sock.sendto(forwarding_table_to_str(), (entry['ip'], entry['port']))
        except socket.error:
          pass

    message_reader_stop.put(1)
    reader_thread.join()
    sys.exit(0)