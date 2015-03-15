#Socket client example in python
 
import socket
import sys
import threading
import thread
import time
import datetime
import random
import ConfigParser
import Queue
from collections import namedtuple

global counter
counter = 0
# Parses the configuration file
def parse_config():
	configParser = ConfigParser.RawConfigParser()
	ConfigFilePath = r'config.txt'
	configParser.read(ConfigFilePath)
	global A, B, C, D, server_port, server_ip, client_delay

	#get the max delay of each server
	A = configParser.get('A', 'delay')
	B = configParser.get('B', 'delay')
	C = configParser.get('C', 'delay')
	D = configParser.get('D', 'delay')
	server_ip = configParser.get('server', 'ip')
	client_delay = configParser.get(client_ID, 'delay')

	#get the server port to use later
	server_port = configParser.get('server','port')
	print 'server_port: %d' % int(server_port)
	print 'A: %d' % int(A)
	print 'B: %d' % int(B)
	print 'C: %d' % int(C)
	print 'D: %d' % int(D)

def client_recv(remote_ip, socket_id):
	global registered, client_delay
	while 1:
		try :
			mailbox = socket_id.recv(1024)
			if(mailbox != None and mailbox != ""):
				if(mailbox == "bye"):
					print 'connection terminated'
					registered = 0;
					sys.exit()
				else:
					buf = mailbox.split(' ')
				print 'Received \"' + buf[0] + '\" ' + 'from ' + buf[1] + ', Max delay is ' + client_delay + 's' + ' system time is ' + str(datetime.datetime.now())
		except socket.error:
			print 'receive failed'

#This thread should not block
def client_send(remote_ip):
	print 'Running client..'
	global s_client, server_port, client_ID, msg_flag, dest_delay, message, msg_queue, prev_msg
	try:
		#create an AF_INET, STREAM socket (TCP)
		s_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
		sys.exit();
	 
	print 'Client Socket Created'
	if(int(server_port)):
		s_client.connect((remote_ip , int(server_port)))
		print 'Socket Connected to ' + remote_ip

		#register client to the server
		if(s_client.sendall(client_ID)==None):
			print '%s connected to server' % client_ID
		else:
			print 'client registration incomplete'
	else:
		print("server point not found in configuration file")
		print 'server_port: %d' % int(server_port)
		sys.exit();
	
	#thread for receiving from server
	client_r = threading.Thread(target=client_recv, args = (server_ip, s_client))
	client_r.start()

	message = None
	msg_flag = 0
	while 1:
		if(msg_flag == 1):
			if(not msg_queue.empty()):
				top_msg = msg_queue.get()
				msg_queue.task_done()
				print 'queue NOT empty'
			else:
				print 'queue EMPTY'
			print 'Sent \"' + str(top_msg[0]) + '\" to server_port ' + str(server_port) + '. The system time is ' + str(datetime.datetime.now())
			#if msg shouldn't be delivered yet, activate delay'
			print 'top_msg.del_time: %d' % top_msg.del_time
			print 'time.time()2: %d' % time.time()
		
			#if there is a message in the channel, current message should be delivered after
			if(prev_msg != None and prev_msg.del_time > top_msg.del_time):
				top_msg = msg_struct(msg_field = top_msg[0], del_time = prev_msg[1], queue_time = 0)
			#current message becomes previous for the next round
			prev_msg = top_msg

			#sleep if delivery time hasn't arrived yet
			if(top_msg.del_time > time.time()):
				delay_t = threading.Thread(target=delay, args = (top_msg.del_time - time.time(), s_client, top_msg))
				delay_t.start()
			else:
				print 'DON\' HAVE TO WAIT'
				try :
					if(s_client.sendall(str(top_msg[0])) != None):
						print 'MESSAGE LOST!'
				except socket.error:
					print 'Send failed'
			## reset the message flag			 
			message = None
			msg_flag = 0
			dest_delay = None
	s_client.close()

def delay(delay_time, send_socket, msg):
	time.sleep(delay_time)
	try :
		send_socket.sendall(str(msg[0]))
	except socket.error:
		print 'Send failed'
""" 
	Create a new key with the specified value
	update key if key already exists
"""
def insert_handler(command, key, value, model):
	write = command + ' ' + key + ' ' + value + ' ' + model

	#the messages will simulate writing to multiple replicas due to channel delay
	send_handler(write, 'A')
	send_handler(write, 'B')
	send_handler(write, 'C')
	send_handler(write, 'D')

#Update the value for the specified key
def update_handler(key, value, model):
	print 'update_handler called'
#Return the value corresponding to the given key
def get_handler(key, model):
	print 'get_handler called'
#Delete info related to key from all replicas
def delete_handler(key):
	print "delete_handler called"

def send_handler(msg_input, send_dest):
	global dest_delay, msg_flag, msg_queue, msg_struct
	if send_dest == 'A' :
		"""FIFO TEST CODE
		print 'counter: %d' % counter
		if(counter == 0):
			dest_delay = 10
			counter = 1
		else:
			dest_delay = 2
		"""
		dest_delay = random.randrange(0, int(A), 1)
	elif send_dest == 'B':
		dest_delay =  random.randrange(0, int(B), 1)
	elif send_dest == 'C':
		dest_delay =  random.randrange(0, int(C), 1)
	elif send_dest == 'D':
		dest_delay =  random.randrange(0, int(D), 1)
	else:
		dest_delay = None
		print("invalid destination")
	message = msg_input + ' ' + send_dest
	print 'my message: %s' % message

	#fill the namedtuple for the new message and enqueue
	msg_tuple = msg_struct(msg_field = message, del_time = (time.time() + float(dest_delay)), queue_time = datetime.datetime.now())
	print 'time.time() : %d' % time.time()
	print 'dest_delay: %s' % str(dest_delay) 
	#print 'del_time: %d' % (time.time() + float(dest_delay))
	msg_queue.put(msg_tuple)
	msg_flag = 1
def init_vars():
	global msg_queue, msg_struct, message, A, B, C, D, registered, server_ip, server_port
	global prev_msg
	#queue of size inifinite
	msg_queue = Queue.Queue(maxsize=0)
	#structure containing info about message to send
	msg_struct = namedtuple("msg_struct", "msg_field del_time queue_time")
	message = None
	server_port = 0
	A = None
	B = None
	C = None
	D = None
	registered = 0
	prev_msg = None
#Program execution starts HERE!!!
init_vars()
while(1):
	global dest_delay, client_ID, client_delay, msg_flag, server_ip, msg_queue, msg_struct

	#-----Run client <client-id>-----
	userInput = raw_input('>>> ');
	cmd = userInput.split(' ');
	if cmd[0] == "run":
		if cmd[1] == "client":
			if(cmd[2] == 'A' or cmd[2] == 'B' or cmd[2] == 'C' or cmd[2] == 'D'):
				if(registered == 1):
					print 'already registered'
					continue;
				client_ID = cmd[2]
				# parse the config file and store all the important data to global variables
				parse_config()
				print 'server_ip: %s' % server_ip

				# thread for sending to server
				client_s = threading.Thread(target=client_send, args = (server_ip,))
				client_s.start()
				registered = 1
			else:
				print 'invalid client id'
	#-----Send Message Destination-----
	elif cmd[0] == "Send" or cmd[0] == "send":
		#make sure parameters are given 
		if(cmd[1] != None and cmd[2] != None):
			#cmd[1]: message ; cmd[2]: destination client
			send_handler(cmd[1], cmd[2])
		else:
			print 'arguments not given!'
	# -----insert Key Value Model-----
	elif cmd[0] == "insert" and cmd[1] != None and cmd[2] != None and cmd[3] != None:
		insert_handler(cmd[0], cmd[1], cmd[2], cmd[3])
	# -----Update Key Value Model-----
	elif cmd[0] =="update" and cmd1[1] != None and cmd[2] != None and cmd[3] != None:
		update_handler(cmd[1], cmd[2], cmd[3])
	# -----get Key Value-----
	elif cmd[0] =="get" and cmd1[1] != None and cmd[2] != None:
		get_handler(cmd[1], cmd[2])
	# -----get Key-----
	elif cmd[0] =="delete" and cmd[1] != None:
		delete_handler(cmd[1])
	elif cmd[0] == "quit":
		break
	elif userInput == "":
		continue
	else:
		print 'Invalid command'
# QUESTIONS / CONCERNS
	#Should there be delay if A sends message to A?
