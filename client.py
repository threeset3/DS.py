#Socket client example in python
 
import socket
import sys
import threading
import thread
import time
import datetime
import ConfigParser
import Queue
from collections import namedtuple

# Parses the configuration file
def parse_config():
	global client_delay, server_port, server_ip
	configParser = ConfigParser.RawConfigParser()
	ConfigFilePath = r'config.txt'
	configParser.read(ConfigFilePath)

	server_ip = configParser.get('server', 'ip')
	client_delay = configParser.get(client_ID, 'delay')

	#get the server port to use later
	server_port = configParser.get('server','port')
	print 'server_port: %d' % int(server_port)

# return index of socket letter
def idx(char):
	return ord(char[0].lower()) - 98

def client_recv(remote_ip, sock_id):
	global registered, client_delay, cmd_in_progress, s_client
	while 1:
		try :
			mailbox = s_client.recv(1024)
			if(mailbox != None and mailbox != ""):
				if(mailbox == "bye"):
					print 'connection terminated'
					registered = 0;
					sys.exit()
				elif(mailbox == "ack" or mailbox == "ACK"):
					print 'received ACK'
					#message 'ACK' indicates end of current operation
					cmd_in_progress = 0
				else:
					buf = mailbox.split(' ')
				print 'Received \"' + buf[0] + '\" ' + 'from ' + buf[1] + ', Max delay is ' + client_delay + 's' + ' system time is ' + str(datetime.datetime.now())
		except socket.error:
			print 'receive failed'

def client_send(remote_ip):
	print 'Running client..'
	global s_client, server_port, client_ID, msg_flag, message
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
		if(message!=None):
			try :
				s_client.sendall(str(message))
				print 'Sent \"' + str(message) + '\" to server_port ' + str(server_port) + '. The system time is ' + str(datetime.datetime.now())
			except socket.error:
				print 'Send failed'

			## reset the message flag			 
			message = None
			msg_flag = 0
	s_client.close()

""" 
	Create a new key with the specified value
	update key if key already exists
"""
def cmd_handler():
	global cmd_in_progress, cmd_queue
	#execute only when no operation is executing and there are operations to execute
	while(cmd_in_progress != 1 and (not cmd_queue.empty())):
		top_command = cmd_queue.get()
		if(top_command.command == "insert"):
			insert_handler(top_command[0], top_command[1], top_command[2], top_command[3])
		elif(top_command.command == "update"):
			update_handler(top_command[0], top_command[1], top_command[2], top_command[3])
		elif(top_command.command == "get"):
			get_handler(top_command.key, top_command.model)
		elif(top_command.command == "delete"):
			delete_handler(top_command.key)

def insert_handler(command, key, value, model):
	global client_replica
	if(model == 1): #linearizibility
		print 'insert linearizibility model'
		print 'before insert: ' + client_replica
		#insert key-value to local replica
		client_replica[key] = value
		print 'key-value stored successfully!'
		#notify other clients to insert new key-value pair
		insert_msg = command + ' ' + key + ' ' + value + ' ' + model
		send_handler(insert_msg, 'A')
		send_handler(insert_msg, 'B')
		send_handler(insert_msg, 'C')
		send_handler(insert_msg, 'D')
	elif(model == 2): #Sequential Consistency
		print 'insert Sequential Consistency model'
	elif(model == 3): #Eventual Consistency w=1 R=1
		print 'insert Eventual Consistency w=1 R=1 model'
	elif(model == 4): #Eventual Consistency w=2 R=2
		print 'insert Eventual Consistency w=2 R=2'
	#indicate that an operation is in progress
	cmd_in_progress = 1
	print 'inserted replica: ' + client_replica
#Update the value for the specified key
def update_handler(command, key, value, model):
	global client_replica
	print 'update_handler called'
	print 'before update: ' + client_replica
	if(model == 1): #linearizibility
		print 'insert update linearizibility model'
		#if key exists in local replica
		if(client_replica[key] != None):
			#update local replica
			client_replica[key] = value
			print 'key-value updated successfully!'
			#notify other clients to update their local replica
			update_msg = command + ' ' + key + ' ' + value + ' ' + model
			send_handler(update_msg, 'A')
			send_handler(update_msg, 'B')
			send_handler(update_msg, 'C')
			send_handler(update_msg, 'D')
	elif(model == 2): #Sequential Consistency
		print 'insert Sequential Consistency model'
	elif(model == 3): #Eventual Consistency w=1 R=1
		print 'insert Eventual Consistency w=1 R=1 model'
	elif(model == 4): #Eventual Consistency w=2 R=2
		print 'insert Eventual Consistency w=2 R=2'
	#indicate that an operation is in progress
	cmd_in_progress = 1
	print 'updated replica: ' + client_replica
#Return the value corresponding to the given key
def get_handler(command, key, model):
	print 'get_handler called'
#Delete info related to key from all replicas
def delete_handler(command, key):
	global client_replica
	print "delete_handler called"
	print 'before delete: ' + client_replica
	#delete key from local replica
	if(client_replica.has_key(key)):
		del client_replica[key]
	
	#tell other clients to delete the given key from their local replica
	#notify other clients to update their local replica
	delete_msg = command + ' ' + key
	send_handler(delete_msg, 'A')
	send_handler(delete_msg, 'B')
	send_handler(delete_msg, 'C')
	send_handler(delete_msg, 'D')
	#indicate that an operation is in progress
	cmd_in_progress = 1
	print 'deleted replica: ' + client_replica
def init_vars():
	global client_replica, server_port, registered, server_ip, message, cmd_queue
	global cmd_in_progress, cmd_struct

	#queue of commands
	cmd_queue = Queue.Queue(maxsize=0)
	cmd_in_progress = 0
	server_port = 0
	message = None
	registered = 0
	cmd_struct = namedtuple("command", "key value model")
	#local replica
	client_replica = {}

def send_handler(msg_input, send_dest):
	global msg_flag, msg_queue, msg_struct, message
	if cmd[2] == 'A' or cmd[2] =='B' or cmd[2] == 'C' or cmd[2] == 'D':
		message = msg_input + ' ' + send_dest
		print 'my message: %s' % message
		msg_flag = 1
	else:
		print("invalid destination")

#Program execution starts here!
init_vars()
while(1):
	global client_ID, s_client, client_delay, msg_flag, server_ip, cmd_struct, cmd_queue
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

				#thread for executing operations
				cmd_thread = threading.Thread(target=cmd_handler, args= ())
				cmd_thread.start()
				registered = 1
			else:
				print 'invalid client id'
	elif cmd[0] == "Send" or cmd[0] == "send" and (cmd[1] != None and cmd[2] != None):
		send_handler(cmd[1], cmd[2])
	# -----put the commands into a queue
	elif cmd[0] == "insert" or cmd[0] == "update" and (cmd[1] != None and cmd[2] != None and cmd[3] != None):
		cmd_tuple = cmd_struct(command = cmd[0], key = cmd[1], value = cmd[2], model = cmd[3])
		cmd_queue.put(cmd_tuple)
	elif cmd[0] == "get" and ( cmd[1] != None and cmd[2] != None):
		cmd_tuple = cmd_struct(command = cmd[0], key = cmd[1], model = cmd[3])
		cmd_queue.put(cmd_tuple)
	elif cmd[0] == "delete" and cmd[1] != None:
		cmd_tuple = cmd_struct(command = cmd[0], key = cmd[1])
		cmd_queue.put(cmd_tuple)
	elif cmd[0] == "quit":
		break
	elif userInput == "":
		continue
	else:
		print 'Invalid command'
