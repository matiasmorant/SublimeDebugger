import bdb

class MyDB(bdb.Bdb):

	breakpoints = {}
	# def __init__(self,*args,**kwargs):
	#	 super(MyDB,self).__init__(*args,**kwargs)
	def user_call(self, frame, args):
		"""This method is called when there is the remote possibility
		that we ever need to stop in this function."""
		if self._wait_for_mainpyfile:
			return		
		print("--call--")
		if self.stop_here(frame):
			print ("call", function_name(frame), args)
			self.wait_cmd(frame)
		self.stack, self.curidx = self.get_stack(frame, None)

	def user_line(self, frame):
		print ("user_line")
		if self._wait_for_mainpyfile:
			if (self.mainpyfile != filename(frame) or frame.f_lineno<= 0):
				return
			self._wait_for_mainpyfile = False
		print ("--line--")
		print( "break at", filename(frame), line(frame), "in", function_name(frame))
		self.stack, self.curidx = self.get_stack(frame, None)
		self.wait_cmd(frame) # continue to next breakpoint

	def user_return(self, frame, value):
		if self._wait_for_mainpyfile:
			return		
		print ("--return--")
		print ("return from", function_name(frame), value)
		self.stack, self.curidx = self.get_stack(frame, None)
		self.wait_cmd(frame) # continue

	def user_exception(self, frame, exception):
		if self._wait_for_mainpyfile:
			return		
		print("--exception--")
		print("exception in", function_name(frame), exception)
		self.stack, self.curidx = self.get_stack(frame, exception)
		self.wait_cmd(frame) # continue

	def wait_cmd(self,frame):
		self.curframe = frame
		cmd = self.parent.get_cmd(line(frame),frame.f_locals,frame.f_globals, filename(frame))
		cmd = cmd or (self.last_cmd if hasattr(self, 'last_cmd') else '')
		self.last_cmd = cmd
		s,*args = cmd.split() or ['']
		if   s in ['c']: self.set_continue()
		elif s in ['n']: self.set_next(frame)
		elif s in ['b']:
			self.parent.set_break(self.mainpyfile, int(args[0]))
			# self.set_break
			self.wait_cmd(frame)
		elif s in ['s']: self.set_step()
		elif s in ['q']: self.set_quit()
		elif s in ['r']: self.set_return(frame)
		elif s in ['u']: self.set_until(frame, int(args[0]) if args else None)
		elif s in ['o']:
			self.curidx = self.curidx-1
			self.wait_cmd(self.stack[self.curidx][0])
		elif s in ['i']:
			self.curidx = self.curidx+1
			self.wait_cmd(self.stack[self.curidx][0])
		elif s in ['h']:
			self.show_help()
			self.wait_cmd(frame)
		else           : self.wait_cmd(frame)
	def show_help(self):
		self.parent.show_help("""
			Commands  Description
			c         Continue execution, only stop when a breakpoint is encountered.
			n         Continue execution until the next line in the current function
                      is reached or it returns.
			b [LINE]  Toggle break at LINE in the current file.
			s         Execute the current line, stop at the first possible occasion
                      (either in a function that is called or in the current
                      function).
			q         Quit the debugger.
			r         Continue execution until the current function returns.
			u [LINE]  Without argument, continue execution until the line with a
                      number greater than the current one is reached.  With a line
                      number, continue execution until a line with a number greater
                      or equal than LINE is reached.  In both cases, also stop when
                      the current frame returns.
			o         Move the current frame one level up in the stack trace (to an older frame).
			i         Move the current frame one level down in the stack trace (to a newer frame).
			h         Show this help.

			If no command is given, the previous command is repeated.
			""")
	def runscript(self,filename):
		# When bdb sets tracing, a number of call and line events happens
		# BEFORE debugger even reaches user's code (and the exact sequence of
		# events depends on python version). So we take special measures to
		# avoid stopping before we reach the main script (see user_line and
		# user_call for details).
		self._wait_for_mainpyfile = True
		self.mainpyfile = self.canonic(filename)
		self._user_requested_quit = False
		with open(filename, "rb") as fp:
			statement = "exec(compile(%r, %r, 'exec'))" % \
						(fp.read(), self.mainpyfile)
		self.clear_all_breaks()
		for filenam,lines in self.breakpoints.items():
			for l in lines:
				self.set_break(filenam, l)
		self.run(statement)
		self.parent.finished()
	def tryeval(self,expr):
		try:
			return eval(expr, self.curframe.f_locals, self.curframe.f_globals)
		except Exception as e:
			return e
def line(frame):
	return frame.f_lineno
def filename(frame):
	return bdb.Bdb().canonic(frame.f_code.co_filename)
def function_name(frame):
	return frame.f_code.co_name or "<unknown>"