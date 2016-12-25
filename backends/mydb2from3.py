import os
import json
import socket
import threading
import time
import subprocess

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

def b(s): return bytes(s,'UTF-8')

class TCPProcess(object):
	def __init__(self, port):
		self.client_conn = connect(port)
	def __getattr__(self,m):
		def f(*args):
			self.client_conn.send(b(m+"@"+json.dumps(args)+"@."))
			ans,ex,_ = recv_message(self.client_conn).split('@')
			return ans
		return f

class TCPServer(object):
	def __init__(self, port):
		print("server __init__",port)
		self.client_conn = connect(port)
	def __getitem__(self,m):
		instruction, parameters , _ = m.split('@')
		ret,ex = None,None
		try                  : ret = eval(instruction)(*json.loads(parameters))
		except Exception as e: ex  = e
		return str(ret) +'@'+str(ex)+'@.'
	def __call__(self):
		msg = recv_message(self.client_conn)
		ans = self[msg]
		self.client_conn.send(b(ans))
	def loop(self):
		try:
			while True: self()
		except Exception as e:
			print ("connection down",e)
		self.client_conn.close()

class MyDB2from3():
	def __init__(self):
		self.sp = subprocess.Popen(["python2",os.path.dirname(__file__)+"/mydb2.py"])#,universal_newlines=True,bufsize=1,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		print("pid",self.sp.pid)
		self.breakpoints = []
		time.sleep(.2)
		self.server = TCPServer(5004)
		self.server_thread = threading.Thread(target=self.server.loop)
		self.server_thread.start()
		time.sleep(.2)
		self.proc        = TCPProcess(5005)
		self.set_break   = self.proc.set_break
		self.clear_break = self.proc.clear_break
		self.tryeval     = self.proc.tryeval
		print("fully connected")
	def runscript(self, filename):
		self.proc.set_breakpoints(self.breakpoints)
		self.proc.runscript(filename)
	def set_parent(self,p):
		global parent
		parent = p
	def get_parent(self):
		return parent
	def __del__(self):
		print("__del__")
		self.sp.kill()
		self.sp.terminate()
		print("waiting fon thread to join")
		self.server_thread.join()
		print("__del__ done")
	parent = property(fset=set_parent, fget=get_parent)

parent=None

def get_cmd  (line,locals,globals,filename): return parent.get_cmd  (line,locals,globals,filename)
def set_break(filename,line               ): parent.set_break(filename,line)
def show_help(s                           ): parent.show_help(s)
def finished (                            ): parent.finished ()