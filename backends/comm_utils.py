import socket
import json
import traceback
import threading
import time

def create_connection(port, ip="127.0.0.1"):
	print ("connecting",port)
	TCP_IP, TCP_PORT = ip, port
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((TCP_IP,TCP_PORT))
	s.listen(1)
	conn, addr = s.accept()
	s.close()
	print ("connected", addr)
	return conn

def connect(port, ip="127.0.0.1"):
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
			sock.connect((ip, port))
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
		if not message or message.endswith('$@#.'): break
	return data

class TCPClient(object):
	def __init__(self, port, ip="127.0.0.1", create= False):
		self.client_conn = (create_connection if create else connect)(port,ip=ip)
	def __getattr__(self,m):
		def f(*args):
			self.client_conn.send((m+"$@#"+json.dumps(args)+"$@#.").encode("UTF-8"))
			ans,ex,_ = recv_message(self.client_conn).split('$@#')
			return ans
		return f

class TCPServer(object):
	def __init__(self, port, ip="127.0.0.1" , create=False):
		self.client_conn = (create_connection if create else connect)(port,ip=ip)
	def __getitem__(self,m):
		instruction, parameters , _ = m.split('$@#')
		ret,ex = None,None
		try                  :
			ret = eval("self."+instruction)(*json.loads(parameters))
		except Exception as e:
			traceback.print_exc()
			ex  = e
		return str(ret) +'$@#'+str(ex)+'$@#.'
	def __call__(self):
		msg = recv_message(self.client_conn)
		ans = self[msg]
		self.client_conn.send((ans).encode("UTF-8"))
	def loop(self):
		try:
			while True: self()
		except Exception as e:
			traceback.print_exc()
			print ("connection down",e)
		self.client_conn.close()

class Peer(TCPServer):
	def __init__(self, port=(5004,5005), ip="127.0.0.1" , create=False):
		if create:
			super(Peer, self).__init__(port[0],ip=ip, create=create)
			self.client =  TCPClient(  port[1],ip=ip, create=create)
		else:
			self.client =  TCPClient(  port[0],ip=ip, create=create)
			time.sleep(.2)
			super(Peer, self).__init__(port[1],ip=ip, create=create)
		self.server_thread = threading.Thread(target=self.loop)
		self.server_thread.start()
		time.sleep(.2)
	def __getattr__(self, m):
		return getattr(self.client, m)
	def __del__(self):
		self.server_thread.join()