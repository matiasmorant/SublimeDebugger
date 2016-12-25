import socket
import json

def create_connection(port):
	print ("connecting",port)
	TCP_IP, TCP_PORT = "127.0.0.1", port
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((TCP_IP,TCP_PORT))
	s.listen(1)
	conn, addr = s.accept()
	s.close()
	print ("connected", addr)
	return conn

def connect(port):
	# def tryevalE(expr):
	# 	try:
	# 		eval(expr)
	# 		return True
	# 	except:
	# 		return False
	# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# for _ in range(10): #try to connect 10 times
	# 	if tryeval('sock.connect(("127.0.0.1", port))') : break
	# 	else: print ("doesn't want to connect",_)
	# return sock

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	connected = False
	for _ in range(10): #try to connect 10 times
		try:
			sock.connect(("127.0.0.1", port))
			connected = True
		except:
			connected = False
		if connected : break
		else: print ("doesn't want to connect",_,port)
	return sock

def recv_message(conn, BUFFER_SIZE = 1024):
	data = ''
	while True:
		message = conn.recv(BUFFER_SIZE).decode("UTF-8")
		data+=message
		if not message or message.endswith('@.'): break
	return data

class TCPProcess(object):
	def __init__(self, connect,port):
		self.client_conn = connect(port)
	def __getattr__(self,m):
		def f(*args):
			self.client_conn.send((m+"@"+json.dumps(args)+"@.").encode("UTF-8"))
			ans,ex,_ = recv_message(self.client_conn).split('@')
			return ans
		return f

class TCPServer(object):
	def __init__(self,connect, port):
		print("server __init__",port)
		self.client_conn = connect(port)
	def __getitem__(self,m):
		instruction, parameters , _ = m.split('@')
		ret,ex = None,None
		try                  : ret = self.eval(instruction)(*json.loads(parameters))
		except Exception as e: ex  = e
		return str(ret) +'@'+str(ex)+'@.'
	def __call__(self):
		msg = recv_message(self.client_conn)
		ans = self[msg]
		self.client_conn.send((ans).encode("UTF-8"))
	def loop(self):
		try:
			while True: self()
		except Exception as e:
			print ("connection down",e)
		self.client_conn.close()