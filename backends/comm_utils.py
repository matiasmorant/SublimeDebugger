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

class Msg(object):
	def __init__(self, *args):
		formt = lambda *args: ("{}$@#{}$@#{}$@#{}$@#{}$@#.".format(*args)).encode("UTF-8")
		parse = lambda s: s.split(b'$@#')[:5]
		self.bstr = formt(*args) if len(args) == 5 else tobytes(args[0])
		self.fields = parse(self.bstr)
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


class Stream(object):
	def __init__(self, *args):
		self.args =  args
		self.running = True
		self.thread = threading.Thread(target=self.loop)
		self.thread.start()
		time.sleep(.2)
	def loop(self):
		try:
			while self.running:
				self.do(*self.args)
				time.sleep(.02)
		except Exception as e:
			traceback.print_exc()
		self.end(*self.args)
	def stop(self):
		self.running = False
		self.thread.join()
	def __del__(self):
		self.running = False
		self.thread.join()
	def do (self,*args): pass
	def end(self,*args): pass

class StreamIn(Stream,list):
	def do(self, connection):
		self.append(recv_message(connection).encode("UTF-8"))
	def end(self, connection):
		connection.close()
	
class FilterStream(Stream,list): # filtering stream
	def do(self, f, stream):
		match = list(filter(f, stream)) # doesn't work without "list". why??
		self.extend(match)
		for m in match: stream.remove(m)


class PingPong(Stream):
	def __init__(self, port=5005, ip="127.0.0.1", create= False):
		self.client_conn = (create_connection if create else connect)(port,ip=ip)
		self.streamin = StreamIn(self.client_conn)
		super(PingPong, self).__init__(FilterStream(lambda msg: msg.startswith(b"Q"), self.streamin))
	def __getattr__(self,m):
		def f(*args):
			mmsg = Msg('Q',datetime.now().microsecond, m, json.dumps(args), None)
			self.client_conn.send(mmsg.bstr)
			# print("__getattr__ sent", msg.bstr)
			pred = lambda m: is_QA_pair(Msg(m),mmsg)
			ans = FilterStream(pred, self.streamin)
			while not ans: time.sleep(.02)
			# print ("ans:", ans)
			# ans.stop() # ans doesn't seem to get deleted, why? loop running?
			return json.loads(Msg(ans.pop(0)).dres)
		return f
	def ans(self,m):
		m = Msg(m)
		ret,ex = None,None
		try:
			ret = eval("self."+m.dfun)(*json.loads(m.dres))
		except Exception as e:
			traceback.print_exc()
			ex  = e
		return Msg('A', m.dsig, m.dfun, json.dumps(ret), ex).bstr #is dumps necessary?
	def do(self, questions):
		if questions:
			self.client_conn.send(self.ans(questions.pop(0)))
	def end(self):
		self.client_conn.close()