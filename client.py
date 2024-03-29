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
	global client_delay, server_port, server_ip, client_ID
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

#Helper insert/update
def insert_update(mailbox):
	global client_replica

	buf = mailbox.split(' ')
	if(client_replica.has_key(int(buf[1])) == True):

		client_replica[int(buf[1])] = [int(buf[2]), time.time()]
		print 'updating key: %d' % int(buf[1])

	#if key doesn't exist AND operation is insert
	elif(buf[0] == "insert"):
		client_replica[int(buf[1])] = [int(buf[2]), time.time()]

	#if key doesn't exist AND operation is "update"
	elif(buf[0] == "update"):
		print '[[ERROR! Key: ' + buf[1] + 'doesn\'t exist]]'
		cmd_in_progress = None
		return -1

#If received command receipt
# receipt of ACK indicates end of operation at the client
def recv_insert(mailbox):
	global client_replica

	buf = mailbox.split(' ')

	#Linearizibility / Sequential insert receipt
	if(buf[3] == "1" or buf[3] == "2"):
		if(insert_update(mailbox) == -1):
			return
		#indicate that operation executed succesfully
		send_handler("ACK", buf[0]+buf[1]+buf[2]+buf[3]+buf[4] + ' ' + client_ID + ' '+buf[3], buf[4]) #buf[4] is requester
	
	#Eventual Consistency, W=1, R=1 / W=2, R=2
	elif(buf[3] == "3" or buf[3] == "4"):
		#make sure it's not self-broadcast message
		if(buf[4] != client_ID):
			if(insert_update(mailbox) == -1):
				return
			#model 4: clients other than self need to send ACK
			if(buf[3] == "4"):
				#indicate that operation executed succesfully
				send_handler("ACK", buf[0]+buf[1]+buf[2]+buf[3]+buf[4] + ' ' + client_ID + ' ' +buf[3], buf[4]) #buf[4] is requester

	print 'Received \"' + buf[0] + '\" ' + buf[1] + ' ' + buf[2] + ' ' + buf[3] + ' ' + 'from ' + buf[4] + ', Max delay is ' + client_delay + 's' + ' system time is ' + str(datetime.datetime.now())

#if client receives request update. Update the value of the given key if the key exists in local replica
# receipt of ACK indicates end of operation at the client
def recv_update(mailbox):
	recv_insert(mailbox)

#handle ACK messages from central server
def recv_ACK(mailbox):
	global cmd_in_progress, ACK_time

	buf = mailbox.split(' ')
	print 'Received ACK for ' + buf[1] #buf[1] is <operation message>
	ACK_time = time.time()

	#if Eventual Consistency ACK to get request
	if(buf[2] == "get"):
		print "EVENTUAL CONSISTENCY W=2, R=2 reading for KEY " + buf[4] + ':' + '[' + buf[5] + ']'
	cmd_in_progress = None

# delete request handler
# receipt of ACK indicates end of operation at the client
def recv_delete(mailbox):
	print 'recv_delete called'
	global client_replica, cmd_in_progress
	buf = mailbox.split(' ')

	#del key from local replica
	if(client_replica.has_key(int(buf[1]))):
		del client_replica[int(buf[1])]
		if(client_replica.has_key(int(buf[1]))== False):
			print 'delete from local replica SUCCESS!'
			#send ACK to indicate success of operation
			send_handler("ACK", buf[0]+buf[1] + ' ' + client_ID + ' ' + buf[2], buf[2]) #buf[2] is requester


#handle get requests
def recv_get(mailbox):
	global client_replica, cmd_in_progress
	buf = mailbox.split(' ')

	#Linearizibility get request
	if(buf[2] == "1"):
		#check if self broadcast message
		if(buf[3] == client_ID):
			if(client_replica.has_key(int(buf[1]))):
				print 'LINEARIZIBILITY Model Reading for KEY %s:' % str(buf[1]) +'[' + str(client_replica[int(buf[1])])+']'
				cmd_in_progress = None
			else:
				print 'Read failed. Key Not Found'

	#Eventual Consistency W=2, R=2
	elif(buf[2] == "4"):
		#read the replica with the latest timestamp out of 2 replicas
		if(client_replica.has_key(int(buf[1]))):
			#send ACK to indicate success of operation
			#msg format: "ACK(0) get_key_model(1) sender(2) command(3) key(4) local_replica(5) requester(6)"
			if(buf[3] != client_ID):
				send_handler("ACK", buf[0]+buf[1]+buf[2] + ' ' + client_ID + ' ' + buf[0]+' ' + buf[1] + ' ' + str(client_replica[int(buf[1])]) + ' ' + buf[3], buf[3]) 
				cmd_in_progress = None
		else:	
			print 'Read failed. Key Not Found'

	#Indicate end of 'get' request
	cmd_in_progress = None
# thread that receives messages from server
def client_recv(remote_ip):
	global registered, client_delay, cmd_in_progress, s_client, client_replica
	while 1:
		try :
			mailbox = s_client.recv(1024)
			if(mailbox != None and mailbox != ""):
				if(mailbox == "bye"):
					print 'connection terminated'
					registered = 0;
					sys.exit()
				else:
					buf = mailbox.split(' ')

					#message 'ACK' indicates end of current operation
					if(buf[0] == "ACK"):
						recv_ACK(mailbox)
					elif(buf[0] == "insert"):
						recv_insert(mailbox)
					elif(buf[0] == "update"):
						print 'update received'
						recv_update(mailbox)
					elif(buf[0] == "get"):
						recv_get(mailbox)
					elif(buf[0] == "delete"):
						recv_delete(mailbox)

				#if response from a send operation
				if(buf[0] != "insert" and buf[0] != "update" and buf[0] != "get" and buf[0] != "delete" and buf[0] != "ACK"):
					print 'Received \"' + buf[0] + '\" ' + 'from ' + buf[1] + ', Max delay is ' + client_delay + 's' + ' system time is ' + str(datetime.datetime.now())
		except socket.error:
			print 'receive failed'

def send_handler(operation, msg_input, send_dest):
	global msg_flag, msg_queue, msg_struct, message, dest
	dest = send_dest
	if send_dest == 'A' or send_dest =='B' or send_dest == 'C' or send_dest == 'D':
		message = operation + ' ' + msg_input + ' ' + send_dest
		msg_flag = 1
	else:
		print("invalid destination")

# thread that executes special operations
def cmd_handler():
	global cmd_in_progress, cmd_queue

	#execute only when no operation is executing and there are operations to execute
	while(1):
		while(cmd_in_progress == None and cmd_queue.empty()==0):
			top_command = cmd_queue.get()
			cmd_queue.task_done()
			if(top_command.command == "insert" or top_command.command == "update"):
				insert_update_handler(top_command[0], int(top_command[1]), int(top_command[2]), int(top_command[3]))
			elif(top_command.command == "get"):
				get_handler(top_command.command, int(top_command.key), int(top_command.model))
			elif(top_command.command == "delete"):
				delete_handler(top_command.command, int(top_command.key))
			elif(top_command.command == "delay"):
				delay_handler(top_command.value)


#if command "insert" should execute
def insert_update_handler(command, key, value, model):
	global cmd_in_progress

	if(model == 1 or model == 2 or model == 3 or model == 4):
		#eventual consistency modifies local replica right away
		if(model == 3 or model == 4):
			#insert key-value to local replica and we're done with the operation
			insert_update(command+' '+str(key)+' '+str(value)+' '+str(model))

		#only in model 3, modification of local replica marks end of operation
		if(model == 3):
			cmd_in_progress = None
		else:
			#indicate that an operation is in progress
			cmd_in_progress = "insert " + str(key)
		#notify other clients to insert new key-value pair
		# "insert(0) key(1) value(2) model(3) source(4) dest(5)"
		insert_msg = str(key) + ' ' + str(value) + ' ' + str(model) + ' ' + str(client_ID)
		send_handler(command, insert_msg, 'A')
		while(msg_flag == 1):
			pass
		send_handler(command, insert_msg, 'B')
		while(msg_flag == 1):
			pass
		send_handler(command, insert_msg, 'C')
		while(msg_flag == 1):
			pass
		send_handler(command, insert_msg, 'D')
	else:
		print 'Invalid input for model'
		return

#Return the value corresponding to the given key
def get_handler(command, key, model):
	global cmd_in_progress

	cmd_in_progress = command + str(key) + str(model)

	#Linearizibility, send broadcast to everyone
	if(model == 1 or model == 4):
		# "insert(0) key(1) model(2) source(3) dest(4)"
		get_request = str(key)  + ' ' + str(model) + ' ' + str(client_ID)
		send_handler(command, get_request, 'A')
		while(msg_flag == 1):
			pass
		send_handler(command, get_request, 'B')
		while(msg_flag == 1):
			pass
		send_handler(command, get_request, 'C')
		while(msg_flag == 1):
			pass
		send_handler(command, get_request, 'D')

	#Sequential consistency, immediately return value of local replica
	if(model == 2):
		if(client_replica.has_key(key)):
			print 'SEQUENTIAL CONSISTENCY Reading for KEY %s:' % str(key) +'[' + str(client_replica[key])+']'
			cmd_in_progress = None
		else:
			print 'Read failed. Key Not Found'
	
	#eventual consistency with R=1 reads local replica right away
	elif(model == 3):
		if(client_replica.has_key(key)):
			print 'EVENTUAL CONSISTENCY, W=1 R=1: reading for key %s:' % str(key) +'[' + str(client_replica[key])+']'
			cmd_in_progress = None
		else:
			print 'Read failed. Key Not Found'
#Delete info related to key from all replicas
def delete_handler(command, key):
	global client_replica, cmd_in_progress
	#indicate that an operation is in progress
	cmd_in_progress = "delete " + str(key)
	#tell other clients to delete the given key from their local replica
	
	send_handler(command, str(key) + ' ' + client_ID, 'A')
	while(msg_flag==1):
		pass
	send_handler(command, str(key) + ' ' + client_ID, 'B')
	
	while(msg_flag==1):
		pass
	send_handler(command, str(key) + ' ' + client_ID, 'C')
	
	while(msg_flag==1):
		pass
	send_handler(command, str(key) + ' ' + client_ID, 'D')

#Handles delay between commands
#if time passed since last ACK is less than delay time, then sleep the time difference
def delay_handler(delay_time):
	global ACK_time, cmd_in_progress
	cmd_in_progress = "delay"
	if(ACK_time != None):
		if(time.time() - ACK_time < delay_time):
			print '[DELAY time: ' + str(delay_time - (time.time() - ACK_time)) + ']'
			delay_t = threading.Thread(target=delay_thread, args = (delay_time - (time.time()-ACK_time),))
			delay_t.start()
			delay_t.join()
	cmd_in_progress = None

#thread that sends data to server	
def client_send(remote_ip):
	print 'Running client..'
	global s_client, server_port, client_ID, msg_flag, message, recv_started, dest
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
		sys.exit()
	if(not recv_started):
		#thread for receiving from server
		client_r = threading.Thread(target=client_recv, args = (server_ip,))
		client_r.start()

		#thread for executing operations
		cmd_thread = threading.Thread(target=cmd_handler, args= ())
		cmd_thread.start()
		recv_started = 1
	while 1:
		if(msg_flag):
			try :
				#message = "command key value model source dest"
				if(s_client.sendall(str(message)) == None):
					print 'Sent \"' + str(message) + '\" to client ' + str(dest) + '. The system time is ' + str(datetime.datetime.now())
				else:
					print 'Send failed'
			except socket.error:
				print 'Send failed'

			## reset the message flag			 
			msg_flag = 0
	s_client.close()

def init_vars():
	global client_replica, server_port, registered, server_ip, message, cmd_queue
	global cmd_in_progress, cmd_struct, recv_started, client_ID, msg_flag, ACK_time

	#queue of commands
	cmd_queue = Queue.Queue(maxsize=0)
	cmd_in_progress = None
	server_port = 0
	message = None
	registered = 0
	cmd_struct = namedtuple("cmd_struct_name", "command key value model")
	#local replica
	client_replica = {}
	recv_started = 0
	client_ID = None
	msg_flag = 0
	ACK_time = None
def delay_thread(s):
	time.sleep(float(s))

#Program execution starts here!
init_vars()
while(1):
	global client_ID, s_client, client_delay, msg_flag, server_ip, cmd_struct, cmd_queue, client_replica
	userInput = raw_input('>>> ');
	cmd = userInput.split(' ');
	if cmd[0] == "run":
		if(cmd[1] == 'A' or cmd[1] == 'B' or cmd[1] == 'C' or cmd[1] == 'D'):
			if(registered == 1):
				print 'already registered'
				continue;
			client_ID = cmd[1]
			# parse the config file and store all the important data to global variables
			parse_config()
			print 'server_ip: %s' % server_ip

			# thread for sending to server
			client_s = threading.Thread(target=client_send, args = (server_ip,))
			client_s.start()

			registered = 1
		else:
			print 'invalid client id'
	
	elif cmd[0] == "Send" or cmd[0] == "send" and (cmd[1] != None and cmd[2] != None):
		send_handler(cmd[0], cmd[1], cmd[2])
	
	# -----put the commands into a queue
	elif cmd[0] == "insert" or cmd[0] == "update" and (cmd[1] != None and cmd[2] != None and cmd[3] != None):
		cmd_tuple = cmd_struct(command = cmd[0], key = cmd[1], value = cmd[2], model = cmd[3])
		cmd_queue.put(cmd_tuple)
	
	elif cmd[0] == "get" and ( cmd[1] != None and cmd[2] != None):
		cmd_tuple = cmd_struct(command = cmd[0], key = cmd[1], value = -1, model = cmd[2])
		cmd_queue.put(cmd_tuple)
	
	elif cmd[0] == "delete" and cmd[1] != None:
		cmd_tuple = cmd_struct(command = cmd[0], key = cmd[1], value = -1, model = -1)
		cmd_queue.put(cmd_tuple)
	
	elif cmd[0] == "show-all":
		print client_replica
		print client_replica.values()
	
	elif cmd[0] == "delay":
		cmd_tuple = cmd_struct(command = cmd[0], key = -1, value = float(cmd[1]), model = -1)
		cmd_queue.put(cmd_tuple)
		
	elif cmd[0] == "quit":
		break
	elif userInput == "":
		continue
	else:
		print 'Invalid command'


