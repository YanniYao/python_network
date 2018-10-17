import socket
import os
import sys
import time
import struct
import time
import signal
import filetype
import threading

HOST = '127.0.0.1'
PORT = 50000
ThreadNum = 0
Addr = (HOST, PORT)
LOG_FOPMAT = "[{TIME}] {OUT}"
terminate = False
kill_str = {
	'linux': "kill -9 {PID}",
	'win32': "taskkill /f /pid {PID}"
}
NO_SUCH_FILE = "no_such_file"
HAS_FILE = "has_file"

def signal_handling(signum,frame):           
    global terminate
    terminate = True
signal.signal(signal.SIGINT,signal_handling)


def log(*args):
    cur_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    output = ''.join(args).replace('\n', ' ')
    print(LOG_FOPMAT.format(TIME=cur_time, OUT=output))

def recvFile(clientSocket):
	msg = 'no problem'
	msg_utf8 = msg.encode("utf-8")
	clientSocket.send(msg_utf8)
	fileinfo_size = struct.calcsize('!3s5s128sI')
	cmd_head = clientSocket.recv(fileinfo_size)
	while True:
	    if cmd_head:
	    	clientID, fileType, filename, filesize = struct.unpack('!3s5s128sI', cmd_head)
	    	fn = (filename.decode('utf-8')).strip('\00')
	    	filelocalname = os.path.join('./Desktop/', 'new_' + fn)
	    	recvd_size = 0 #已接收文件大小
	    	data = b''
	    	fp = open(filelocalname, 'wb')
	    	print("from client ", clientID.decode('utf-8')  + ":[fileType]:", fileType.decode('utf-8') + ",[filename]:", (filename.decode('utf-8')).strip('\00') + ",[filesize]:", filesize)
	    	log("start receiving file......")
	    	while recvd_size < filesize:
	    		recv_data = clientSocket.recv(1024)
	    		data += recv_data
	    		recvd_size += len(recv_data)
	    	fp.write(data)
	    	log("received successfully!")
	    fp.close()
	    break

def sendFile(clientSocket):
	msg = 'no problem'
	msg_utf8 = msg.encode('utf-8')
	clientSocket.send(msg_utf8)
	filename_utf8 = clientSocket.recv(4096)
	filename = filename_utf8.decode("utf-8")
	if os.path.isfile(filename):
		clientSocket.send(HAS_FILE.encode("utf-8"))
		if filename.split(".")[-1] == 'txt':
			fileType = filename.split(".")[-1]
		else:
			fileType = (filetype.guess(filename)).extension
		fileinfo_size = struct.calcsize('!5s128sI')
		cmd_head = struct.pack('!5s128sI', fileType.encode('utf-8'), os.path.basename(filename).encode('utf-8'), os.stat(filename).st_size)
		clientSocket.send(cmd_head)
		log("start sending file......")
		'''
		fp = open(filename, 'rb')
		while True:
			data = fp.read(1024)
			if not data:
				break
			clientSocket.sendall(data)
			break
		'''
		cmd_filesize = os.stat(filename).st_size
		send_filesize = cmd_filesize
		with open(filename, 'rb') as fp:
			while send_filesize:
				content = fp.read(4096)
				clientSocket.send(content)
				send_filesize -= len(content)
		fp.close()
		log("send file successfully!")
	else:
		clientSocket.send(NO_SUCH_FILE.encode("utf-8"))

def acc_link(clientSocket, addr):
	while True:
		msg_utf8 = clientSocket.recv(4096)
		msg = msg_utf8.decode()
		if msg == 'exit':
			log("The client requests to close the connection.")
			clientSocket.close()
			log("The connection from %s:%s closed." % addr)
			break
		elif msg == 'get':
			sendFile(clientSocket)
		elif msg == 'put':
			recvFile(clientSocket)
		else:
			print("client error!")
			clientSocket.close()
			log("The connection from %s:%s closed." % addr)
			break
	clientSocket.close()
	log("The connection from %s:%s closed." % addr)


if __name__ == '__main__':
	log("SERVER UP")
	socketListener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socketListener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	socketListener.bind(Addr)
	socketListener.listen(5)
	log("server is listening: %s:%d" % (HOST, PORT))
	while True:
		clientSocket, (client_ip, client_port) = socketListener.accept()
		log("connection from : %s : %d" % (client_ip, client_port))
		t = threading.Thread(target=acc_link, args=(clientSocket, (client_ip, client_port)))
		t.start()