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
queue = [deque(), deque(), deque(), deque(), deque()]
server_ip = None
delay = [0] * 4
# key = ack_id, value = ack_counter
ack_dict = {}
server_send = 0
num_clients = 0
# message class
class Msg:
	def __init__(self, msg, source, dest, delay):
		self.msg = msg
		self.dest = dest
		self.regtime = time.time()
		self.delay = float(delay) * random.random()
		self.source = source

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
	elif char[0] == 'S':
		return 4
	else: return None

def idx_to_char(idx):
	if idx == 0:
		return 'A'
	elif idx == 1:
		return 'B'
	elif idx == 2:
		return 'C'
	elif idx == 3:
		return 'D'
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

#Handles receipt of send request
def recv_send(client_name, client_idx, data):
	global queue
	buf = data.split(' ')
	# print receipt and explode for processing
	print 'Received \"' + data + '\" from ' + client_name + ', Max delay is ' + delay[client_idx] + ' s, ' + ' system time is ' + str(datetime.datetime.now())

	# build message object
	myMsg = Msg(buf[1], client_name, buf[2], delay[idx(buf[2])]) # delay[client_index] changed to buf[2] because client_index is sender's index

	# if sent to self, no delay
	if buf[2] == client_name:
		myMsg.delay = 0

	# attach msg to ORIGIN/SENDER's queue
	queue[client_idx].append(myMsg)

# Handles receipt of ACK message
# data = "ACK <operation message> <sender> <operation requester>"
def recv_ACK(data):
	global queue, ack_dict
	buf = data.split(' ')
	if(ack_dict[buf[1]] != None):
		print 'ACK received from ' + buf[2] + ' for Requester: ' + buf[3]
		#keep track of the number of ACKs received for a given operation
		ack_dict[buf[1]] = ack_dict[buf[1]] + 1
		print "ACK counter: " + str(ack_dict[buf[1]])
		#if every client sent ACK, server sends ACK to the requester
		if(ack_dict[buf[1]] == num_clients):
			server_send = 1
			print 'Original Requester is ' + buf[3]
			myMsg = Msg("ACK" +' ' + buf[1], str(buf[3]), str(buf[3]), delay[idx(buf[3])]) #changed from buf[2], buf[2] to buf[3] buf[3]
			queue[4].append(myMsg)
			print ' ACK message appended'
			#REMOVE ACK ENTRY FROM THE DICTIONARY
#Handles receipt of insert operation
#data = "command(0) key(1) value(2) model(3) source(4) dest(5)"
def recv_insert(data):
	global queue, ack_dict
	#print the request
	buf = data.split(' ')
	print buf[4] + ' requested insert ' + buf[1] + ' ' + buf[2] + ' ' + buf[3]
	# Linearizibility Model
	if(buf[3] =="1"):
		print 'server handling Linearizibility Insert! receiver is ' + buf[5]
		#build operation message object: buf[4] - source ; buf[5] - dest
		myOpMsg = Msg(buf[0] +' '+buf[1]+' '+buf[2]+' '+buf[3], buf[4], buf[5], delay[idx(buf[5])])

		#use requester's queue to send message
		queue[client_idx].append(myOpMsg)
		#keep track of how many ACKs we get from clients + original operation requester
		ack_dict[buf[0]+buf[1]+buf[2]+buf[3]] =  0

#Handles receipt of update operation
#data = "command(0) key(1) value(2) model(3) source(4) dest(5)"
def recv_update(data):
	print 'recv_update called'

def sendThread(client_name, client_idx):
	global server_send
	while 1:
		if(server_send == 1):
			client_idx = 4
		# if out_queue has messages waiting to be delivered
		if len(queue[client_idx]) != 0:
			if(server_send == 1):
				server_send = 0
			# retrieve the message
			msg = queue[client_idx][0]

			# if time to send the message 
			if time.time() >= (msg.regtime + float(msg.delay)):

				# pop message from queue
				queue[client_idx].popleft()

				# send the message
				if(sock[idx(msg.dest)] == None):
					print 'INVALID MSG>DEST IS ' + msg.dest
					sys.exit()
				if(sock[idx(msg.dest)].sendall(msg.msg + ' ' + msg.source) == None):
					print 'Sent \"' + str(msg.msg) + '\" to ' + msg.dest + '. The system time is ' + str(datetime.datetime.now())
				else:
					print 'message send failure'


# Client receiving thread
def clientThread(conn, unique):
	global sock, delay, ack_dict, server_send

	#the current client communicating with the server
	client_name = None

	while 1:
		# continuously receive data from a client
		data = conn.recv(1024)

		# if data is identifying msg
		if(data == 'A' or data == 'B' or data == 'C' or data == 'D'):
			# store client name in the local scope
			# I wanna see if client_name is being modified when it shouldn't be
			print 'changing CLIENT name to ' + data
			client_name = data

			# calculate client idx
			client_idx = idx(client_name)

			# store connection to global array of sockets
			sock[client_idx] = conn

			# start new thread for sending messages in FIFO
			send_thread = threading.Thread(target=sendThread, args=(client_name, client_idx))
			send_thread.start()

			print unique + ' identified as ' + data
		
		buf = data.split(' ')

		#if insert operation should be executed
		if(buf[0] == "insert"):
			recv_Insert(data)
		#if update operation should be executed
		elif(buf[0] == "update"):
			recv_update(data)
		#if a client sends ACK upon completion of a task
		elif(buf[0] == "ACK"):
			recv_ACK(data)
		# if received: send <message> <destination>
		elif(buf[0] == "send"):
			# check if the destination socket is registered
			if(sock[idx(buf[2])] == None):
				print '[[ Client ' + buf[2] + 'doesn\'t exist. Do \"run client ' + buf[2] + '\" first.]]'
				continue
			recv_send(client_name, client_idx, data)

def server():
	global s_server, server_port, sock, server_ip, num_clients
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

		#keep track of the number of clients connected to server
		num_clients = num_clients + 1

	conn.close()
	s_server.close()

parse_config()
server()
