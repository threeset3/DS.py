#Socket client example in python
 
import socket
import sys
import threading
import thread
import time
import datetime
import random
import ConfigParser

server_port = 0
server_ip = "localhost"
msg_flag = None
message = None
A = None
B = None
C = None
D = None

# Parses the configuration file
def parse_config():
	configParser = ConfigParser.RawConfigParser()
	ConfigFilePath = r'configurationfile.txt'
	configParser.read(ConfigFilePath)
	global A, B, C, D, server_port

	#get the max delay of each server
	A = configParser.get('A', 'delay')
	B = configParser.get('B', 'delay')
	C = configParser.get('C', 'delay')
	D = configParser.get('D', 'delay')
	client_delay = configParser.get(client_ID, 'delay')

	#get the server port to use later
	server_port = configParser.get('server','port')
	print 'server_port: %d' % int(server_port)
	print 'A: %d' % int(A)
	print 'B: %d' % int(B)
	print 'C: %d' % int(C)
	print 'D: %d' % int(D)
	
def client(remote_ip):
	print 'Running client..'
	global s_client, server_port, client_ID, message, msg_flag, dest_delay
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
	
	while 1:
		print 'inside while'
		s_client.sendall("Hi B")
		if(msg_flag != None):
			print 'before delay'
			delay_t = threading.Thread(target=delay, args = (dest_delay, 0))
			delay_t.start()
			#block until delay finishes executing
			delay_t.join()
			print 'about to send'
			try :
				if(s_client.sendall(message) == None):
					print 'Sent \"' + str(message) + '\" to server_port ' + str(server_port) + '. The system time is ' + str(datetime.datetime.now())
				else:
					print 'Send incomplete'
			except socket.error:
				print 'Send failed'

			## reset the message flag			 
			message = None
			msg_flag = 0
			dest_delay = None
		#always try to receive
		#delay_t = threading.Thread(target=delay, args = (client_delay, 0))
		#delay_t.start()
		#block until delay finishes executing
		#delay_t.join()
		try :
			mailbox = s_client.recv(1024)
			if(mailbox != None):
				print 'Received \"' + mailbox + '\" ' + ', Max delay is ? s, ' + ' system time is ' + str(datetime.datetime.now())
		except socket.error:
			print 'receive failed'

	s_client.close()

def delay(duration, g):
	time.sleep(duration * random.random())


while(1):
	global dest_delay, client_ID, client_delay, message, msg_flag
	#global msg_flag
	#global message
	userInput = raw_input('>>> ');
	cmd = userInput.split(' ');

	if cmd[0] == "run":
		if cmd[1] == "client":
			if(cmd[2] == 'A' or cmd[2] == 'B' or cmd[2] == 'C' or cmd[2] == 'D'):
				client_ID = cmd[2]
				# parse the config file and store all the important data to global variables
				parse_config()
				print 'server_ip: %s' % server_ip
				client_t = threading.Thread(target=client, args = ("localhost",))
				#thread.start_new_thread(client, (server_ip,))
				client_t.start()
			else:
				print 'invalid client id'

	elif cmd[0] == "Send" or cmd[0] == "send":
		#figure out max delay based on destination client
		if(cmd[1] != None and cmd[2] != None):
			if cmd[2] == 'A' :
				dest_delay = int(A)
			elif cmd[2] == 'B':
				dest_delay = int(B)
			elif cmd[2] == 'C':
				dest_delay = int(C)
			elif cmd[2] == 'D':
				dest_delay = int(D)
			else:
				dest_delay = None
				print("invalid destination")
			message = cmd[1] + ' ' + cmd[2]
			print 'my message: %s' % message
			msg_flag = 1
		else:
			print 'arguments not given!'

	elif cmd[0] == "quit":
		break
	elif userInput == "":
		continue
	else:
		print 'Invalid command'

