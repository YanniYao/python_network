import socket
import time
import filetype #用于判断非txt类型的其他文件类型
import struct
import os
import sys

HOST = '127.0.0.1'
PORT = 50000
Addr = (HOST, PORT)
ID = '001'
MAX_SIG_NUM = 50

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect(Addr)

def recvFile(filename):
	filename_utf8 = filename.encode(encoding='utf-8')
	clientSocket.send(filename_utf8)
	while True:
		if "has_file" == (clientSocket.recv(4096)).decode("utf-8"):
			print("start receiving file......")
			fileinfo_size = struct.calcsize('!5s128sI')
			cmd_head = clientSocket.recv(fileinfo_size)
			if cmd_head:
				fileType, filename, filesize = struct.unpack('!5s128sI', cmd_head)
				print("from server: [fileType]:", fileType.decode('utf-8') + ",[filename]:", (filename.decode('utf-8')).strip('\00') + ",[filesize]:", filesize)
				fn = (filename.decode('utf-8')).strip('\00')
				filelocalname = os.path.join('./Desktop/', 'new_' + fn)
				print("start receiving file......")
				fp = open(filelocalname, 'wb')
				recvd_size = 0 #已接收文件大小
				while not recvd_size == filesize:
					if filesize - recvd_size > 1024:
						data = clientSocket.recv(1024)
						recvd_size += len(data)
					else:
						data = clientSocket.recv(filesize - recvd_size)
						recvd_size = filesize
					fp.write(data)
					rate = recvd_size / filesize
					rate_num = int(rate * 100)
					sig_num = int(MAX_SIG_NUM * rate)
					r = '\r[%-50s]%d%%' % ('#' * sig_num, rate_num, )
					sys.stdout.write(r)
					sys.stdout.flush()
				sys.stdout.write("\n")
				'''
				while recvd_size < filesize:
					print("11111111")
					recv_data = clientSocket.recv(1024)
					data += recv_data
					recvd_size += len(recv_data)
				fp.write(data)
				'''
				print("received successfully!")
			fp.close()
		elif "no_such_file" == (clientSocket.recv(4096)).decode("utf-8"):
			print((clientSocket.recv(4096)).decode("utf-8"))
		else:
			print("Invalid message from server!")
		break

def sendFile(filename):
	if os.path.isfile(filename):
		if filename.split(".")[-1] == 'txt':
			fileType = filename.split(".")[-1]
		else:
			fileType = (filetype.guess(filename)).extension
		#定义文件信息大小，!表示我们要使用网络字节序顺序解析，s前面的数字表示几个字节长的字符串，I表示integer或long
		fileinfo_size = struct.calcsize('!3s5s128sI')
		cmd_clientID = ID.encode('utf-8')
		cmd_fileType = fileType.encode('utf-8')
		cmd_filename = os.path.basename(filename).encode('utf-8')
		cmd_filesize = os.stat(filename).st_size
		cmd_head = struct.pack('!3s5s128sI', cmd_clientID, cmd_fileType, cmd_filename, cmd_filesize)
		clientSocket.send(cmd_head)
		print("start sending file......")
		data_send = 0
		send_filesize = cmd_filesize
		with open(filename, 'rb') as fp:
			while send_filesize:
				content = fp.read(4096)
				clientSocket.send(content)
				data_send += len(content)
				send_filesize -= len(content)
				rate = data_send / cmd_filesize
				rate_num = int(rate * 100)
				sig_num = int(MAX_SIG_NUM * rate)
				r = '\r[%-50s]%d%%' % ('#' * sig_num, rate_num, )
				sys.stdout.write(r)
				sys.stdout.flush()
			sys.stdout.write("\n")
		print("send file successfully!")
		fp.close()
	else:
		print("The file is not exist!")

def confirm(confirm_command):
	confirm_command_utf8 = confirm_command.encode(encoding='utf-8')
	clientSocket.sendall(confirm_command_utf8)
	msg_utf8 = clientSocket.recv(4096)
	msg = msg_utf8.decode()
	print("receive message : ", msg)
	if msg == 'no problem':
		return True
	else:
		return False

def operation1(filename):
	if confirm('get'):
		recvFile(filename)
	else:
		print("server error!")

def operation2(filename):
	if confirm('put'):
		sendFile(filename)
	else:
		print("server error!")

try:
    while True:
        command = input(">>>")
        if not command:
            continue
        elif command == 'exit':
            command_utf8 = command.encode(encoding='utf-8')
            clientSocket.sendall(command_utf8)
            print("The connection is closed!")
            clientSocket.close()
            break
        msg = command.split()
        if len(msg) == 2 and msg[0] == 'get':
    	    operation1(msg[1])
        elif len(msg) == 2 and msg[0] == 'put':
    	    operation2(msg[1])
        else:
    	    print("Wrong command!")
except socket.error as e:
	print("error : ", e)
	print("An error ocurred!")
	clientSocket.close()