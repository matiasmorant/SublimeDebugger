from dbpy2 import MyDB

##############
import threading

from comm_utils import TCPClient,TCPServer

class DebuggerServer(TCPServer):
	def set_breakpoints(self, bps          ):
		for ldict in bps.values():
			for k in ldict.keys():
				ldict[int(k)] = ldict[k]
				ldict.pop(k)
		DB.breakpoints = bps
	def set_break      (self, filename,line,bpinfo): DB.set_break    (filename,line,bpinfo)
	def clear_break    (self, filename,line       ): DB.clear_break  (filename,line)
	def toggle_break   (self, filename,line       ): DB.toggle_break (filename,line)
	def tryeval        (self, expr                ): return DB.tryeval(expr)
	def runscript      (self, filename            ): threading.Timer(.1, DB.runscript, args=[filename]).start()

print "mydb2.py started"

DB = MyDB()
print "debugger ready"
DB.parent = TCPClient(5004, create=True)
print "parent ready"

DebuggerServer(5005, create=True).loop()