#Socket client example in python
 
import socket
import sys
import threading

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

	#Send some data to remote server
	message = "GET / HTTP/1.1\r\n\r\n"
	 
	try :
		#Set the whole string
		s_client.sendall(message)
	except socket.error:
		#Send failed
		print 'Send failed'
		sys.exit()
	 
	print 'Message send successfully'
	 
	#Now receive data
	reply = s_client.recv(4096)

	print reply

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

	while 1:
		conn, addr = s_server.accept()
		print 'Connected with ' + addr[0] + ':' + str(addr[1])

		data = conn.recv(1024)
		print data

	conn.close()
	s_server.close()


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

	elif cmd[0] == "quit":
		break
	elif userInput == "":
		continue
	else:
		print 'Invalid command'

