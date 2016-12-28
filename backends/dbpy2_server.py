from dbpy2 import MyDB

##############
import threading

from comm_utils import TCPProcess,TCPServer, create_connection
		
class DebuggerParent():
	def __init__(self):
		self.proc           = TCPProcess(create_connection,5004)
		self.get_cmd        = self.proc.get_cmd
		self.set_break      = self.proc.set_break
		self.clear_break    = self.proc.clear_break
		self.toggle_break   = self.proc.toggle_break
		self.show_help      = self.proc.show_help
		self.show_exception = self.proc.show_exception
		self.finished       = self.proc.finished

def set_breakpoints(bps          ):
	for ldict in bps.values():
		for k in ldict.keys():
			ldict[int(k)] = ldict[k]
			ldict.pop(k)
	DB.breakpoints = bps
def set_break      (filename,line,bpinfo): DB.set_break    (filename,line,bpinfo)
def clear_break    (filename,line       ): DB.clear_break  (filename,line)
def toggle_break   (filename,line       ): DB.toggle_break (filename,line)
def tryeval        (expr                ): return DB.tryeval(expr)
def runscript      (filename            ): threading.Timer(.1, DB.runscript, args=[filename]).start()

print "mydb2.py started"

DB = MyDB()
print "debugger ready"
DB.parent = DebuggerParent()
print "parent ready"
def outeval(instruction): return eval(instruction)
server=TCPServer(create_connection,5005)
server.eval= outeval
server.loop()