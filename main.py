#Socket client example in python
 
import socket
import sys
import threading
import time
import datetime
import random

def client(remote_ip, port):
	print 'Running client..'
	try:
		#create an AF_INET, STREAM socket (TCP)
		global s_client
		s_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
		sys.exit();
	 
	print 'Client Socket Created'
	 
	s_client.connect((remote_ip , port))
	print 'Socket Connected to ' + remote_ip

	global message
	global send_port
	message = None
	send_port = None
	
	while 1:
		if (message and send_port == port):
		
			delay_t = threading.Thread(target=delay, args = (3, 0))

			print 'Sent \"' + str(message) + '\" to port ' + str(port) + '. The system time is ' + str(datetime.datetime.now())

			delay_t.start()
			delay_t.join()

			try :
				s_client.sendall(message)
			except socket.error:
				print 'Send failed'

			## reset the message flag			 
			message = None
			send_port = None

	s_client.close()

def server(host, port):
	global s_server
	s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print 'Socket created'
	 
	try:
		s_server.bind(('', port))
	except socket.error , msg:
		print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
		 
	print 'Socket bind complete'
	s_server.listen(10)
	print 'Socket listening'

	conn, addr = s_server.accept()
	print 'Connected with ' + addr[0] + ':' + str(addr[1])

	while 1:
		data = conn.recv(1024)
		if data != "":
			print 'Received \"' + data + '\" from port ' + str(port) + ', Max delay is ? s, ' + ' system time is ' + str(datetime.datetime.now())

	conn.close()
	s_server.close()

def delay(duration, g):
	time.sleep(duration * random.random())


while(1):

	userInput = raw_input('>>> ');
	cmd = userInput.split(' ');

	if cmd[0] == "run":
		if cmd[1] == "client":
			client_t = threading.Thread(target=client, args = ("localhost", int(cmd[2])))
			client_t.start()
		elif cmd[1] == "server":
			server_t = threading.Thread(target=server, args = ("", int(cmd[2])))
			server_t.start()

	elif cmd[0] == "Send" or cmd[0] == "send":
		message = cmd[1]
		send_port = cmd[2]

	elif cmd[0] == "quit":
		break
	elif userInput == "":
		continue
	else:
		print 'Invalid command'

