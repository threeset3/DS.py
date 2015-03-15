#Socket client example in python
 
import socket
import sys
import threading
import thread
import time
import datetime
import ConfigParser

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

def init_vars():
	global client_replica, server_port, registered, server_ip, message
	server_port = 0
	message = None
	registered = 0

	#local replica
	client_replica = [{}] * 4
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
	global client_ID, client_delay, msg_flag, server_ip
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
	elif cmd[0] == "Send" or cmd[0] == "send":
		#make sure destination parameter is given
		if(cmd[1] != None and cmd[2] != None):
			send_handler(cmd[1], cmd[2])
		else:
			print 'arguments not given!'
	elif cmd[0] == "quit":
		break
	elif userInput == "":
		continue
	else:
		print 'Invalid command'
