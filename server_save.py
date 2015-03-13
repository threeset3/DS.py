#Central Server
 
import socket
import sys
import threading
import thread
import time
import datetime
import random
import ConfigParser
server_port = None

A_socket = None
B_socket = None
C_socket = None
D_socket = None
# Parses the configuration file
def parse_config():
	global server_port
	configParser = ConfigParser.RawConfigParser()
	ConfigFilePath = r'configurationfile.txt'
	configParser.read(ConfigFilePath)

	#get the server port to use later
	server_port = configParser.get('server','port')
def clientThread(conn):
	global done_reg, A_socket, B_socket, C_socket, D_socket
	while 1:
		data = conn.recv(1024)
		if(data == 'A'):
			#don't allow multiple instances of the same client
			if(A_socket == None):
				#store A's socket descriptor
				A_socket = conn
				print 'received A\'s regisration'
				break;
			else:
				print 'this client already exists'
				conn.send("bye")
				conn.close()
				break;
		elif(data == 'B'):
			if(B_socket == None):
				#store A's socket descriptor
				B_socket = conn
				print 'received B\'s regisration'
			else:
				print 'this client already exists'
				conn.close()
				break;
		elif(data == 'C'):
			if(A_socket == None):
				#store C's socket descriptor
				C_socket = conn
				print 'received C\'s regisration'
			else:
				print 'this client already exists'
				conn.close()
				break;
		elif(data == 'D'):
			if(D_socket == None):
				#store D's socket descriptor
				D_socket = conn
				print 'received D\'s regisration'
			else:
				print 'this client already exists'
				conn.close()
				break;
		elif data != "":
			print 'Received \"' + data + '\" from server_port ' + str(server_port) + ', Max delay is ? s, ' + ' system time is ' + str(datetime.datetime.now())
			
			#create a new socket to talk with the final destination client
			buf = data.split(' ');
			if buf[1] == 'A':
				#send to A
				print 'sending to A'
				if(A_socket != None):
					if(A_socket.sendall(buf[0])==None):
						print 'Sent \"' + str(buf[0]) + '\" to A ' + '. The system time is ' + str(datetime.datetime.now())
					else:
						print 'message send failure'
				else:
					print 'Client doesn\'t exist'
			elif buf[1] =='B':
				#send to B
				print 'sending to B'
				if(B_socket != None):
					if(B_socket.sendall(buf[0])==None):
						print 'Sent \"' + str(buf[0]) + '\" to B ' + '. The system time is ' + str(datetime.datetime.now())
					else:
						print 'message send failure'
				else:
						print 'Client doesn\'t exist'
			elif buf[1] =='C':
				#send to C
				print 'sending to C'
				if(C_socket != None):
					if(C_socket.sendall(buf[0])==None):
						print 'Sent \"' + str(buf[0]) + '\" to C ' + '. The system time is ' + str(datetime.datetime.now())
					else:
						print 'message send failure'
				else:
					print 'Client doesn\'t exist'
			elif buf[1] =='D':
				#send to D
				print 'sending to D'
				if(D_socket != None):
					if(D_socket.sendall(buf[0])==None):
						print 'Sent \"' + str(buf[0]) + '\" to D' + '. The system time is ' + str(datetime.datetime.now())
					else:
						print 'message send failure'
				else:
					print 'Client doesn\'t exist'
			else:
				print 'incorrectly formatted message!'
def server():
	global s_server, server_port, A_socket, B_socket, C_socket, D_socket, done_reg
	s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print 'Socket created'
		 
	try:
		if(server_port):
			s_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s_server.bind(('', int(server_port)))
		else:
			print 'server port not given'
			sys.exit()
	except socket.error , msg:
		print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
		 
	print 'Socket bind complete'
	s_server.listen(10)
	print 'Socket listening'

	while 1:
		conn, addr = s_server.accept()
		print 'Connected With '  + addr[0] + ':' + str(addr[1])
		thread.start_new_thread(clientThread, (conn,))

	conn.close()
	s_server.close()

global done_reg
done_reg = 0;
parse_config()
server()