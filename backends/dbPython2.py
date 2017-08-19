import threading
import time
import subprocess
import os
from SublimeDebugger.backends.comm_utils import TCPClient,TCPServer

class DBPython2():
	def __init__(self):
		self.sp = subprocess.Popen(["python2",os.path.dirname(__file__)+"/dbpy2_server.py"])
		self.breakpoints = {}
		time.sleep(.2)
		self.server = SublimeServer(5004)
		self.server_thread = threading.Thread(target=self.server.loop)
		self.server_thread.start()
		time.sleep(.2)
		self.proc         = TCPClient(5005)
		self.set_break    = self.proc.set_break
		self.clear_break  = self.proc.clear_break
		self.toggle_break = self.proc.toggle_break
		self.tryeval      = self.proc.tryeval
		print("fully connected")
	def runscript(self, filename):
		self.proc.set_breakpoints(self.breakpoints)
		self.proc.runscript(filename)
	def set_parent(self,p):
		self.server.parent = p
	def get_parent(self):
		return self.server.parent
	def __del__(self):
		self.sp.kill()
		self.sp.terminate()
		self.server_thread.join()
	parent = property(fset=set_parent, fget=get_parent)

class SublimeServer(TCPServer):
	def get_cmd       (self, line,locals,globals,filename): return self.parent.get_cmd (line,locals,globals,filename)
	def set_break     (self, filename,line, bpinfo       ): self.parent.set_break      (filename,line,bpinfo)
	def clear_break   (self, filename,line               ): self.parent.clear_break    (filename,line)
	def toggle_break  (self, filename,line               ): self.parent.toggle_break   (filename,line)
	def show_help     (self, s                           ): self.parent.show_help      (s)
	def show_exception(self, s                           ): self.parent.show_exception (s)
	def finished      (self,                             ): self.parent.finished       ()