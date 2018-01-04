from dbpy2 import MyDB

##############
import threading

from comm_utils import PingPong #Peer

DB = MyDB()

class DebuggerPeer(PingPong):
	def D_set_breakpoints(self, bps          ):
		for ldict in bps.values():
			for k in ldict.keys():
				ldict[int(k)] = ldict[k]
				ldict.pop(k)
		DB.breakpoints = bps
	def D_set_break      (self, filename,line,bpinfo): DB.set_break    (filename,line,bpinfo)
	def D_clear_break    (self, filename,line       ): DB.clear_break  (filename,line)
	def D_toggle_break   (self, filename,line       ): DB.toggle_break (filename,line)
	def D_tryeval        (self, expr                ): return DB.tryeval(expr)
	def D_runscript      (self, filename            ): threading.Timer(.1, DB.runscript, args=[filename]).start()


print ("debugger ready")
DB.parent = DebuggerPeer(create=True)
print ("parent ready")

