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
flag = 0
# key = ack_id, value = ack_counter
ack_dict = {}
num_clients = 0

# message class
class Msg:
	def __init__(self, msg, source, dest, delay):
		self.msg = msg
		self.dest = dest
		self.regtime = time.time()
		self.delay = float(delay) * random.random()
		self.source = source
		self.printed = 0
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

# handles send requests
def recv_send(client_name, client_idx, data):
	global queue
	buf = data.split(' ')
	# print receipt and explode for processing
	print 'Received \"' + data + '\" from ' + client_name + ', Max delay is ' + delay[client_idx] + ' s, ' + ' system time is ' + str(datetime.datetime.now())

	# build message object
	myMsg = Msg(buf[1], client_name, buf[2], delay[idx(buf[2])])

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

	#make sure ACK id exists
	if(ack_dict.has_key(buf[1])):
		print 'ACK received from ' + buf[2] + ' for Requester: ' + buf[4]

		#Count total number of ACKs received for the given ACK id
		ack_dict[buf[1]] = ack_dict[buf[1]] + 1
		
		#if every client sent ACK, server sends ACK to the requester
		if(ack_dict[buf[1]] == num_clients):
			myMsg = Msg("ACK" +' ' + buf[1], str(buf[4]), str(buf[4]), delay[idx(buf[4])])
			queue[4].append(myMsg)
			#REMOVE ACK ENTRY FROM THE DICTIONARY after final ACK is sent
			try:
				#make sure the dictionary is not being deleted more than once
				if(ack_dict.has_key(buf[1])):
					del ack_dict[buf[1]]
			except socket.error , msg:
				print "ack dict remove entry failed, error code: " + msg[0] + ' Message:' + msg[1]

		#model 4 special case - waits for only 1 ACK
		if(buf[3] == "4"):
			if(ack_dict[buf[1]] == 1):
				myMsg = Msg("ACK" +' '+ buf[1], str(buf[4]), str(buf[4]), delay[idx(buf[4])])
				queue[4].append(myMsg)
				try:
					#make sure the dictionary is not being deleted more than once
					if(ack_dict.has_key(buf[1])):
						del ack_dict[buf[1]]
				except socket.error , msg:
					print "ack dict remove entry failed, error code: " + msg[0] + ' Message:' + msg[1]

#Handles receipt of insert operation
#data = "command(0) key(1) value(2) model(3) source(4) dest(5)"
def recv_insert(client_idx, data):
	global queue, ack_dict
	#print the request
	buf = data.split(' ')
	print buf[4] + ' requested ' + buf[0] + ' ' + buf[1] + ' ' + buf[2] + ' ' + buf[3]
	if(int(buf[3]) > 4 ):
		print 'Invalid model'
		return
	#build operation message object: buf[4] - source ; buf[5] - dest
	myOpMsg = Msg(buf[0] +' '+buf[1]+' '+buf[2]+' '+buf[3], buf[4], buf[5], delay[idx(buf[5])])

	#use requester's queue to send message
	queue[client_idx].append(myOpMsg)

	#keep track of how many ACKs we get from clients + original operation requester
	ack_dict[buf[0]+buf[1]+buf[2]+buf[3]+buf[4]] =  0

#Handles receipt of update operation
#data = "command(0) key(1) value(2) model(3) source(4) dest(5)"
def recv_update(client_idx, data):
	recv_insert(client_idx, data)
def recv_get(data):
	print 'recv_get called'
def recv_delete(client_idx, data):
	global queue
	buf = data.split(' ')

	#show the request
	print buf[2] + ' requested delete ' + buf[1]

	#build operation message object: buf[2] - source ; buf[3] - dest
	myOpMsg = Msg(buf[0] +' '+buf[1], buf[2], buf[3], delay[idx(buf[3])])
	
	#use requester's queue to send message
	queue[client_idx].append(myOpMsg)

	#keep track of how many ACKs we get from clients + original operation requester
	ack_dict[buf[0]+buf[1]] =  0

# sendThread layer that sends data
def sendThread(client_name, client_idx):
	while 1:
		send_data(client_name, client_idx)
		send_data(client_name, 4)

#sendThread calls this function to send data
def send_data(client_name, client_idx):
	global queue, flag
	# if out_queue has messages waiting to be delivered

	if(not flag):
		flag=1
		if len(queue[client_idx]) != 0:
			# retrieve the message
			try:
				msg = queue[client_idx][0]
			except IndexError:
				return
			if(msg.printed == 0):
				print 'Sent \"' + str(msg.msg + ' ' + msg.source) + '\" to ' + msg.dest + '. The system time is ' + str(datetime.datetime.now())
				msg.printed = 1
			# if time to send the message 
			if time.time() >= (msg.regtime + float(msg.delay)):
				# check if client socket is registered
				if(sock[idx(msg.dest)] == None):
					print '[[ Invalid msg.dest of ' + msg.dest + ' not registered ]]'
					return

				# send message
				try:
					sock[idx(msg.dest)].sendall(msg.msg + ' ' + msg.source)
				except socket.error , msg2:
					print '[[ Send failed : ' + str(msg2[0]) + ' Message ' + msg2[1] + ' ]]'
					sys.exit()
				# pop message from queue
				if(len(queue[client_idx]) > 0):
					queue[client_idx].popleft()
				else:
					return
		flag=0
# Client receiving thread
def clientThread(conn, unique):
	global sock, delay, ack_dict

	#the current client communicating with the server
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
		
		# if not identifier, process message
		else:
			buf = data.split(' ')

			#if insert operation should be executed
			if(buf[0] == "insert"):
				recv_insert(client_idx, data)

			#if update operation should be executed
			elif(buf[0] == "update"):
				recv_update(client_idx, data)

			elif(buf[0] == "get"):
				recv_get(data)

			elif(buf[0] == "delete"):
				recv_delete(client_idx, data)

			#if a client sends ACK upon completion of a task
			elif(buf[0] == "ACK"):
				recv_ACK(data)

			# if received: send <message> <destination>
			elif(buf[0] == "send"):

				# make sure destination socket is registered
				if(sock[idx(buf[2])] == None):
					print '[[ Client ' + buf[2] + 'doesn\'t exist. Do \"run client ' + buf[2] + '\" first.]]'
					continue

				# call send handler
				recv_send(client_name, client_idx, data)
def server():
	global s_server, server_port, sock, server_ip, num_clients
	s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# exit if no port
	if(not server_port):
		print '[[ Server port not given ]]'
		sys.exit()

	try: # setup server socket
		s_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s_server.bind((server_ip, int(server_port)))
	
	# if server setup fail
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

#Program execution starts here!
parse_config()
server()
