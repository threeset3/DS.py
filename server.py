#Central Server
 
import socket
import sys
import threading
import thread
import time
import datetime
import random
import ConfigParser
from collections import deque

# Globals
server_port = None
sock = [None] * 4
queue = [deque(), deque(), deque(), deque()]
server_ip = None
delay = [0] * 4

# message class
class Msg:
	def __init__(self, msg, dest, delay):
		self.msg = msg
		self.dest = dest
		self.regtime = time.time()
		self.delay = float(delay) * random.random()

# return index of socket letter
def idx(char):
	if char == None:
		return None

	char = char.upper()
	if char[0] == 'A':
		return 0
	elif char[0] == 'B':
		return 1
	elif char[0] == 'C':
		return 2
	elif char[0] == 'D':
		return 3
	else: return None

# Parses the configuration file
def parse_config():
	global server_ip, server_port, delay
	configParser = ConfigParser.RawConfigParser()
	ConfigFilePath = r'config.txt'
	configParser.read(ConfigFilePath)


	# get the max delay of each server
	delay[0] = configParser.get('A', 'delay')
	delay[1] = configParser.get('B', 'delay')
	delay[2] = configParser.get('C', 'delay')
	delay[3] = configParser.get('D', 'delay')
	server_ip = configParser.get('server', 'ip')
	server_port = configParser.get('server','port')

	# output server configuration
	print '-- Communication delays: '
	print delay
	print "-- Server_port: %s" % server_port


def sendThread(client_name, client_idx):
	while 1:

		# if out_queue has messages waiting to be delivered
		if len(queue[client_idx]) != 0:
			
			# retrieve the message
			msg = queue[client_idx][0]

			# if time to send the message 
			if time.time() >= (msg.regtime + msg.delay):

				# pop message from queue
				queue[client_idx].popleft()
				
				# send the message
				if(sock[idx(msg.dest)].sendall(msg.msg + ' ' + client_name) == None):
					print 'Sent \"' + str(msg.msg) + '\" to ' + msg.dest + '. The system time is ' + str(datetime.datetime.now())
				else:
					print 'message send failure'


# Client receiving thread
def clientThread(conn, unique):
	global sock, delay
	client_name = None

	while 1:
		# continuously receive data from a client
		data = conn.recv(1024)

		# if data is identifying msg
		if(data == 'A' or data == 'B' or data == 'C' or data == 'D'):
			# store client name in the local scope
			client_name = data

			# calculate client idx
			client_idx = idx(client_name)

			# store connection to global array of sockets
			sock[client_idx] = conn

			# start new thread for sending messages in FIFO
			send_thread = threading.Thread(target=sendThread, args=(client_name, client_idx))
			send_thread.start()

			print unique + ' identified as ' + data

		# if received actual data
		elif data != "":
			# print receipt and explode for processing
			print 'Received \"' + data + '\" from ' + client_name + ', Max delay is ' + delay[client_idx] + ' s, ' + ' system time is ' + str(datetime.datetime.now())
			buf = data.split(' ');

			# check destination
			if(buf[1] != 'A' and buf[1] != 'B' and buf[1] != 'C' and buf[1] != 'D'):
				print '[[ Received invalid message: ' + data + ' ]]'
				continue

			# check if the destination socket is registered
			if(sock[idx(buf[1])] == None):
				print '[[ Client ' + buf[1] + 'doesn\'t exist. Do \"run client ' + buf[1] + '\" first.]]'
				continue
	
			# build message object
			myMsg = Msg(buf[0], buf[1], delay[client_idx])

			# if sent to self, no delay
			if buf[1] == client_name:
				myMsg.delay = 0

			# attach msg to ORIGIN/SENDER's queue
			queue[client_idx].append(myMsg)


def server():
	global s_server, server_port, sock, server_ip
	s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print 'Socket created'
		 
	## setup server socket
	try:
		if(server_port):
			s_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s_server.bind((server_ip, int(server_port)))
		else:
			print '[[ Server port not given ]]'
			sys.exit()
	except socket.error , msg:
		print '[[ Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1] + ' ]]'
		sys.exit()
		 
	print 'Socket bind complete.'
	s_server.listen(10)
	print 'Socket listening..'

	while 1:
		conn, addr = s_server.accept()
		print 'Connected With '  + addr[0] + ':' + str(addr[1])
		thread.start_new_thread(clientThread, (conn, str(addr[1])))

	conn.close()
	s_server.close()
	
parse_config()
server()
