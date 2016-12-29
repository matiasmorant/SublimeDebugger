import threading
import time
import subprocess
import os
from Debugger.backends.comm_utils import TCPProcess,TCPServer, connect

def outeval(instruction): return eval(instruction)

class DBPython2():
	def __init__(self):
		self.sp = subprocess.Popen(["python2",os.path.dirname(__file__)+"/dbpy2_server.py"])
		self.breakpoints = {}
		time.sleep(.2)
		self.server = TCPServer(connect,5004)
		self.server.eval= outeval
		self.server_thread = threading.Thread(target=self.server.loop)
		self.server_thread.start()
		time.sleep(.2)
		self.proc         = TCPProcess(connect,5005)
		self.set_break    = self.proc.set_break
		self.clear_break  = self.proc.clear_break
		self.toggle_break = self.proc.toggle_break
		self.tryeval      = self.proc.tryeval
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
		self.sp.kill()
		self.sp.terminate()
		self.server_thread.join()
	parent = property(fset=set_parent, fget=get_parent)

parent=None

def get_cmd       (line,locals,globals,filename): return parent.get_cmd (line,locals,globals,filename)
def set_break     (filename,line, bpinfo       ): parent.set_break      (filename,line,bpinfo)
def clear_break   (filename,line               ): parent.clear_break    (filename,line)
def toggle_break  (filename,line               ): parent.toggle_break   (filename,line)
def show_help     (s                           ): parent.show_help      (s)
def show_exception(s                           ): parent.show_exception (s)
def finished      (                            ): parent.finished       ()