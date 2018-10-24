import socket
import time
import filetype #用于判断非txt类型的其他文件类型
import struct
import os
import sys
import gzip

HOST = '127.0.0.1'
PORT = 50000
Addr = (HOST, PORT)
MAX_SIG_NUM = 50
HEAD_FORMAT = "!3sI" #定义文件信息大小，!表示我们要使用网络字节序顺序解析，s前面的数字表示几个字节长的字符串，I表示integer或long
HEAD_SIZE = struct.calcsize(HEAD_FORMAT)
Iscompress = 'c'

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect(Addr)

ID = socket.gethostname()

def recvFile(filename, is_compress):
	filename_utf8 = (filename + is_compress).encode(encoding='utf-8')
	clientSocket.send(filename_utf8)
	while True:
		if "has_file" == (clientSocket.recv(4096)).decode("utf-8"):
			print("start receiving file......")
			fileinfo_size = struct.calcsize('!20s128sI')
			cmd_head = clientSocket.recv(fileinfo_size)
			if cmd_head:
				fileType, filename, filesize = struct.unpack('!20s128sI', cmd_head)
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
				print("received successfully!")
			fp.close()
		elif "no_such_file" == (clientSocket.recv(4096)).decode("utf-8"):
			print((clientSocket.recv(4096)).decode("utf-8"))
		else:
			print("Invalid message from server!")
		break

def sendFile(cmd, filename):
	print("filename:", filename)
	if not os.path.isfile(filename):
		print("The file is not exist!")
		return
	else:
		info = (filename + "|" + Iscompress).encode()
		cmd_size = len(info)
		print("cmd_size:", cmd_size)
		cmd_head = struct.pack(HEAD_FORMAT, cmd.encode(), cmd_size) + info
		clientSocket.send(cmd_head)
	buf = clientSocket.recv(HEAD_SIZE)
	rpl, rest_pkt_size = struct.unpack(HEAD_FORMAT, buf)
	info = clientSocket.recv(rest_pkt_size)
	rpl = rpl.decode()
	info = info.decode()
	if 'PUT' == rpl and 'OK' == info:
		if filename.split(".")[-1] == 'txt':
			fileType = filename.split(".")[-1]
		else:
			fileType = (filetype.guess(filename)).extension
		file_base_name = os.path.basename(filename)
		if Iscompress == 'c':
			fp = open(filename, 'rb')
			compress_data = gzip.compress(fp.read(), compresslevel=9)
			filesize = len(compress_data)
		elif Iscompress == 'o':
			filesize = os.stat(filename).st_size
		else:
			print("Whether the file is compressed is unknown...")
		cmd_filesize = str(filesize)
		cmd_info = ID + "|" + fileType + "|" + file_base_name + "|" + cmd_filesize
		msg_len = len(cmd_info)
		msg_head = struct.pack(HEAD_FORMAT, 'MSG'.encode(), msg_len)
		clientSocket.send(msg_head + cmd_info.encode())
		print("start sending file......")
		if Iscompress == 'c':
			clientSocket.sendall(compress_data)
		else:
			data_send = 0
			send_filesize = filesize
			with open(filename, 'rb') as fp:
				while send_filesize:
					content = fp.read(4096)
					clientSocket.send(content)
					data_send += len(content)
					send_filesize -= len(content)
					rate = data_send / filesize
					rate_num = int(rate * 100)
					sig_num = int(MAX_SIG_NUM * rate)
					r = '\r[%-50s]%d%%' % ('#' * sig_num, rate_num, )
					sys.stdout.write(r)
					sys.stdout.flush()
				sys.stdout.write("\n")
		fp.close()
	else:
		print("The file is not exist!")

def operation1(filename, is_compress):
	if confirm('get'):
		recvFile(filename, is_compress)
	else:
		print("server error!")


try:
    while True:
        command = input(">>>")
        if not command:
            continue
        elif command == 'END':
            cmd_head = struct.pack(HEAD_SIZE, command.encode(), "END".encode())
            clientSocket.send(cmd_head)
            print("The connection is closed!")
            clientSocket.close()
            break
        else:
        	msg = command.split()
        	if len(msg) == 2 and msg[0] == 'GET':
        		is_compress = input("please choose the file transfer mode (o or c only (o for original) (c for compress)):")
        		if not is_compress == 'o' and not is_compress == 'c' and not is_compress:
        			continue
        		else:
        			recvFile(msg[1], is_compress)
        	elif len(msg) == 2 and msg[0] == 'PUT':
        		Iscompress = input("please choose the file transfer mode (o or c only (o for original) (c for compress)):")
        		if not Iscompress == 'o' and not Iscompress == 'c' and not Iscompress:
        			continue
        		else:
        			sendFile(msg[0], msg[1])
        	else:
        		print("Wrong command!")
except socket.error as e:
	print("error : ", e)
	print("An error ocurred!")
	clientSocket.close()