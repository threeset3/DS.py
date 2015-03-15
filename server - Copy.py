#Central Server
 
import socket
import sys
import threading
import thread
import time
import datetime
import random
import ConfigParser
import Queue

def init_vars():
	global server_port, sock, server_ip, client_replica
	server_port = None
	sock = [None] * 4

	#key-value storage for 4 clients
	client_replica = [{}] * 4

# return index of socket letter
def idx(char):
	return ord(char[0].lower()) - 98

# Parses the configuration file
def parse_config():
	global server_ip, server_port
	configParser = ConfigParser.RawConfigParser()
	ConfigFilePath = r'config.txt'
	configParser.read(ConfigFilePath)
	server_ip = configParser.get('server', 'ip')

	#get the server port to use later
	server_port = configParser.get('server','port')
	print "Server_port: %s" % server_port

# Client receiving thread
def clientThread(conn, unique):
	global sock, client_replica
	client_name = None
	while 1:
		# continuously receive data from a client
		data = conn.recv(1024)

		# if data is identifying msg
		if(data == 'A' or data == 'B' or data == 'C' or data == 'D'):
			sock[idx(data)] = conn
			print unique + ' identified as ' + data
			client_name = data

		# if received actual data
		elif data != "":
			print 'Received \"' + data + '\" from ' + client_name + ', Max delay is ? s, ' + ' system time is ' + str(datetime.datetime.now())

			#create a new socket to talk with the final destination client
			buf = data.split(' ');

			#handle : send <message> <destination>
			if(buf[1] == 'A' or buf[1] == 'B' or buf[1] == 'C' or buf[1] == 'D'):
				if(sock[idx(buf[1])] != None):
					if(sock[idx(buf[1])].sendall(buf[0] + ' ' + client_name) == None):
						print 'Sent \"' + str(buf[0]) + '\" to ' + buf[1] + '. The system time is ' + str(datetime.datetime.now())
					else:
						print 'message send failure'
				else:
					print 'Client ' + data + 'doesn\'t exist'
			#insert key-value pair to corresponding dictionaries
			elif(buf[0] == "insert" and buf[1] != None and buf[2] != None and buf[3] != None):
				print 'performing insert operation'
				if(buf[3] == "1"): # Linearizibility
					if(sock[idx(buf[4])] != None):
						#buf[1]: key; buf[2]: value
						client_replica[idx(buf[4])][buf[1]] = buf[2]
						print 'key-value stored successfully!'
					else:
						print 'Client ' + data + 'doesn\'t exist'
			else:
				print 'Received invalid msg'


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
			print 'Server port not given'
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
		thread.start_new_thread(clientThread, (conn, str(addr[1])))

	conn.close()
	s_server.close()
	
init_vars()
parse_config()
server()

#Linearizibility Implementation
	#Totally Ordered Broadcasts
		# each client keeps a replica of shared variable
			# dictionary
		# Read request / Get request
			#send broadcast containing request
			#return local replica value when own b-cast message arrives
		# Write Request / Insert request
			#send broadcast containing request
			#upon receipt, each process updates local value
			#when own message arrives, respond with "ACK"


