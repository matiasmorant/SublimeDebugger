# SublimeDebugger

This is a graphical debugger for Sublime Text 3.
If this saves you some time with those nasty bugs of yours, feel free to buy me a coffee at PayPal.

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
Your backend should implement a class with the following methods:

* set_break
* clear_break
* runscript

These will be called by the frontend. Additionally, the following methods of the frontend should be called by your backend when relevant:

* set_break
* clear_break

Import the backend from mydebugger.py

Add your language to Main.sublime-menu and to languageCommand in mydebugger.py

The Python3 backend (dbPython3.py) is the simpler one, take a look at that for guidance. Also, contact me if you really mean to implement one, I'll help you so we can include it here afterwards. wvlia5@live.com.ar

##TODO

* better exception handling
* toggle special members 
* configuring breakpoints from Breakpoints Watcher
* multifile support
* test on windows
* context key bindings with filename?