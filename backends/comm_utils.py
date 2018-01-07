import socket
import json
import traceback
import threading
import time
from datetime import datetime
from functools import reduce

def compose(*funs):
	return reduce(lambda f,g: (lambda *args: f(g(*args))), funs)

def tobytes(s): return s if isinstance(s,bytes) else s.encode("UTF-8")

fmt = lambda *args: ("{}$@#{}$@#{}$@#{}$@#{}$@#.".format(*args)).encode("UTF-8")

class Msg(object):
	def __init__(self, *args):
		self.bstr = fmt(*args) if len(args) == 5 else tobytes(args[0])
		self.fields = self.bstr.split(b'$@#')[:5]
		self.QA, self.sig, self.fun, self.res, self.ex = self.fields
		self.dQA, self.dsig, self.dfun, self.dres, self.dex = [f.decode() for f in self.fields]

def is_QA_pair(m1, m2):
	return {m1.QA, m2.QA} == {b"Q",b"A"} and\
				   m1.sig == m2.sig      and\
				   m1.fun == m2.fun

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


class Peer(TCPServer): # trying to deprecate
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


class StreamIn(list):
	def __init__(self, connection):
		self.connection =  connection
		self.running = True
		self.thread = threading.Thread(target=self.loop)
		self.thread.start()
		time.sleep(.2)
	def loop(self):
		try:
			while self.running:
				msg = recv_message(self.connection).encode("UTF-8")
				self.append(msg)
				# print("StreamIn is:",self)
				time.sleep(.05)
		except Exception as e:
			traceback.print_exc()
			print ("connection down",e)
		self.connection.close()
	def stop(self):
		self.running = False
		self.thread.join()
	def __del__(self):
		self.running = False
		self.thread.join()

class FilterStream(list): # filtering stream
	def __init__(self, f, stream):
		self.f =  f
		self.stream = stream
		self.running = True
		self.thread = threading.Thread(target=self.loop)
		self.thread.start()
		print(id(self),"__init__ed")
	def loop(self):
		print(id(self),"entered loop",self.running)
		try:
			while self.running:
				match = list(filter(self.f, self.stream)) # doesn't work without "list". why??
				self.extend(match)
				for m in match: self.stream.remove(m)
				time.sleep(.05)
		except Exception as e:
			traceback.print_exc()
			print ("connection down ?",e)
	def stop(self):
		self.running = False
		self.thread.join()
	def __del__(self):
		self.running = False
		self.thread.join()
		print(id(self),"Stream __del__ed")


class PingPong(object):
	def __init__(self, port=5005, ip="127.0.0.1", create= False):
		self.client_conn = (create_connection if create else connect)(port,ip=ip)
		self.streamin = StreamIn(self.client_conn)
		self.questions = FilterStream(lambda msg: msg.startswith(b"Q"), self.streamin)
		self.server_thread = threading.Thread(target=self.loop)
		self.server_thread.start()
		time.sleep(.2)
	def __getattr__(self,m):
		def f(*args):
			msg = Msg('Q',datetime.now().microsecond, m, json.dumps(args), None)
			self.client_conn.send(msg.bstr)
			# print("__getattr__ sent", msg.bstr)
			pred = compose(lambda m: is_QA_pair(m,msg), Msg)
			ans = FilterStream(pred, self.streamin)
			while not ans: time.sleep(.05)
			# print ("ans:", ans)
			# ans.stop() # ans doesn't seem to get deleted, why? loop running?
			return Msg(ans.pop(0)).res
		return f
	def __getitem__(self,m):
		m = Msg(m)
		print ("__getitem__",m)
		ret,ex = None,None
		try:
			ret = eval("self."+m.dfun)(*json.loads(m.dres))
		except Exception as e:
			traceback.print_exc()
			ex  = e
		return fmt('A', m.dsig, m.dfun, ret, ex)
	def __call__(self):
		while not self.questions: time.sleep(.05)
		msg = self.questions.pop(0)
		print("__call__ recv",msg)
		# QA,sig,fun,res,ex,_ = msg.split(b'$@#')
		ans = self[msg]
		self.client_conn.send(ans)
		print("__call__ sent",ans)
	def loop(self):
		try:
			while True: self()
		except Exception as e:
			traceback.print_exc()
			print ("connection down",e)
		self.client_conn.close()
	def __del__(self):
		self.server_thread.join()