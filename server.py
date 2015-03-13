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

server_port = None
sock = [None] * 4

# return index of socket letter
def idx(char):
	return ord(char[0].lower()) - 98

# Parses the configuration file
def parse_config():
	configParser = ConfigParser.RawConfigParser()
	ConfigFilePath = r'config.txt'
	configParser.read(ConfigFilePath)

	#get the server port to use later
	global server_port
	server_port = configParser.get('server','port')
	print "Server_port: %s" % server_port

# Client receiving thread
def clientThread(conn, unique):
	global sock
	while 1:
		# continuously receive data from a client
		data = conn.recv(1024)

		# if data is identifying msg
		if(data == 'A' or data == 'B' or data == 'C' or data == 'D'):
			sock[idx(data)] = conn
			print unique + ' identified as ' + data

		# if received actual data
		elif data != "":
			print 'Received \"' + data + '\" from server_port ' + str(server_port) + ', Max delay is ? s, ' + ' system time is ' + str(datetime.datetime.now())

			#create a new socket to talk with the final destination client
			buf = data.split(' ');

			if(buf[1] == 'A' or buf[1] == 'B' or buf[1] == 'C' or buf[1] == 'D'):
				if(sock[idx(buf[1])] != None):
					if(sock[idx(buf[1])].sendall(buf[0]) == None):
						print 'Sent \"' + str(buf[0]) + '\" to A ' + '. The system time is ' + str(datetime.datetime.now())
					else:
						print 'message send failure'
				else:
					print 'Client ' + data + 'doesn\'t exist'
			else:
				print 'Received invalid msg'


def server():
	global s_server, server_port, sock
	s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print 'Socket created'
		 
	## setup server socket
	try:
		if(server_port):
			s_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s_server.bind(('', int(server_port)))
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
	
parse_config()
server()
