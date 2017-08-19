# SublimeDebugger

This is a graphical debugger for Sublime Text 3.
If this saves you some time with those nasty bugs of yours, feel free to buy me a coffee at PayPal.

![screenshot](http://i.imgur.com/W6KpC35.png)

## Features

* Setting breakpoints, using either keyboard shortcuts or the console.
* Local and Global Variables Inspector
* Expression Watcher
* Breakpoints Editor
* Step, Continue, Next, Outer/Inner frame through the console

## Languages Supported

* Python 2
* Python 3

## How to add support to your favourite Language

You've got to write a backend for the debugger. They are located in the backends folder.
Your backend should implement a class with the following members (Which will be called by the frontend):

* set_break(*filename*, *line*, *bpinfo*)

 Is called by the frontend to set a breakpoint. bppinfo is a dict containing info about the breakpoint (backend dependant).

* clear_break(*filename*, *line*)

 Is called by the frontend to clear a breakpoint.

* toggle_break(*filename*, *line*)

 Is called by the frontend to toggle a breakpoint.

* tryeval(*expr*)

 Is called by the frontend to evaluate an expression. It is needed to fill the Expression Watcher. Should return the result of the evaluated expression in the current context.

* runscript(*filename*)

 Is called by the frontend to start debugging a program.

* breakpoints

 A dict of breakpoints. The structure of the dict is the following:
 ```
 
 {
	filename1:
	{
		line1: bpinfo1,
		line2: bpinfo2,
		line3: bpinfo3,
		etc..
	},
	filename2:
	etc..
 }

 ```
where each bpinfo is a dict with backend dependant content.

* parent

 An member that will be set by the frontend, it will have the methods mentioned next.

Additionally, the following methods of the frontend should be called by your backend when relevant (accessed through the *parent* member of your backend):

* get_cmd(*line*, *locals*, *globals*, *filename*)

 Request a command from the user.

* set_break(*filename*, *line*, *bpinfo*)

 Set a breakpoint in the Sublime GUI

* clear_break(*filename*,*line*)

 Clear a breakpoint of the Sublime GUI

* toggle_break(*filename*,*line*)

 Toggle a breakpoint in the Sublime GUI

* show_help(*help_str*)

 Show the help message *help_str* in Sublime

* show_exception(*message*)

 Show an exception *message* in Sublime

Then import the backend from mydebugger.py. Add your language to Main.sublime-menu and to languageCommand in mydebugger.py

The Python3 backend (dbPython3.py) is the simpler one, take a look at that for guidance. Also, contact me if you really mean to implement one, I'll help you so we can include it here afterwards. wvlia5@live.com.ar

##TODO

* ST2 support?
* better exception handling (I think it can't be made better since it is managed by bdb)
* toggle hide special members 
* configuring breakpoints from Breakpoints Watcher?
* multifile support
* test on windows
* context key bindings with filename?