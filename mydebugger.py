import sublime, sublime_plugin
import threading
from Debugger.backends import mydb2from3
from Debugger.backends import mydb
import bdb
from contextlib import contextmanager
from time import sleep
from copy import deepcopy

breakpoints = {}
expressions = []
curlang = "Python2"
DB = mydb2from3.MyDB2from3()

class languageCommand(sublime_plugin.WindowCommand):
    def run(self,lang):
        global DB, curlang
        sublime.status_message("language: "+lang)
        print("language:",lang)
        if lang == curlang: return
        else: curlang = lang
        DB = mydb2from3.MyDB2from3() if lang == "Python2" else\
             mydb      .MyDB      () if lang == "Python3" else\
             None
    def is_checked(self,lang):
        return lang==curlang
class debugCommand(sublime_plugin.WindowCommand):
    input_panel  = None
    cmd_status = None    
    cmd = None
    def run(self):
        sublime.status_message("Started Debugging")
        print("Started Debugging")
        filename = bdb.Bdb().canonic(self.window.active_view().file_name())
        DB.parent = self
        DB.breakpoints = deepcopy(breakpoints)
        f = lambda: DB.runscript(filename)
        threading.Timer(.2,f).start()
    def show_empty_panel(self):
        self.window.show_input_panel("command (type h for help)","",self.success, self.cancel, self.open)
    def success(self,s):
        self.cmd_status = "success"
        self.cmd = s
    def cancel(self,s):
        self.cmd_status = "cancel"
    def open(self):
        self.cmd_status = "open"
    def get_cmd(self,line,locals,globals,filename):
        global expressions
        fill_view("Variables"   , watcher_content   (globals,locals))
        expressions = parse_expressions(get_view_content("Expression"))
        fill_view("Expression", expression_content())
        self.show_empty_panel()
        with highlight(filename,line):
            while not self.cmd_status == "success": sleep(.1)
        sublime.status_message("received cmd: "+self.cmd)
        cmd = self.cmd                
        self.cmd_status = None
        self.cmd = None
        return cmd
    def set_break(self, filename, line):
        toggle_breakGUI(filename, line)
    def show_help(self, s):
        view = self.window.create_output_panel("help")
        view.run_command("fill_view",{'text': s})
        self.window.run_command("show_panel",{"panel": "output.help"})
        p = self.window.active_panel()
        while self.window.active_panel()==p:pass
    def finished(self):
        pass

class toggle_breakpointCommand(sublime_plugin.WindowCommand):
    def run(self):
        filename, line = self.window.active_view().file_name(), get_curline()+1
        toggle_breakGUI(filename, line)
        toggle_breakDB(filename, line)

def toggle_breakGUI(filename, line):
    global breakpoints
    V = sublime.active_window().find_open_file(filename)
    if not filename in breakpoints: breakpoints.update({filename:[]})
    bps = breakpoints[filename]
    (bps.remove   if line in bps else bps.append    )(line)
    V.add_regions("bp",[get_line(V,l-1) for l in bps],"string","circle",sublime.DRAW_NO_FILL|sublime.DRAW_NO_OUTLINE)

def toggle_breakDB(filename,line):
    DB.toggle_break(filename,line)

# def update_breakDB(filename,line):
#     bps = breakpoints[filename]
#     (DB.set_break if line in bps else DB.clear_break)(filename, line)

class toggle_watcherCommand(sublime_plugin.WindowCommand):    
    original_layout = None
    def run(self):
        if get_view("Variables") or get_view("Expression"):
            close_view("Variables")
            close_view("Expression")
        else:
            groups = self.window.num_groups()
            act_gr = self.window.active_group()
            cells, rows, cols = map(self.window.get_layout().__getitem__, ['cells','rows','cols'])
            new_layout ={'cells': cells+[[len(cols)-1,0,len(cols),len(rows)],[len(cols)-1,len(rows),len(cols),len(rows)-1]],
                         'rows' : rows+[.8],
                         'cols' : [.8*col for col in cols]+[1.]}
            self.window.set_layout(new_layout)
            self.window.focus_group(groups)
            f = self.window.new_file()
            f.set_name("Variables")
            f.run_command("fill_view",{'text':''})
            f.run_command("toggle_setting",{"setting":"word_wrap"})
            self.window.focus_group(groups+1)
            f = self.window.new_file()
            f.set_name("Expression")
            f.run_command("fill_view",{'text':''})
            f.run_command("toggle_setting",{"setting":"word_wrap"})
            self.window.focus_group(act_gr)

class refresh_expressionsCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        global expressions
        if self.view.name() == "Expression":
            expressions = parse_expressions(get_view_content("Expression"))
            fill_view("Expression", expression_content())

class fill_viewCommand(sublime_plugin.TextCommand):
     def run(self, edit,**kwargs):
         self.view.replace(edit, sublime.Region(0,self.view.size()), kwargs['text'])

@contextmanager
def highlight(filename,line):
    v = sublime.active_window().find_open_file(filename)
    if v:
        v.add_regions("0",[get_line(v,line-1)],"comment","bookmark")
    yield
    if v:
        v.add_regions("0",[                 ],"comment","bookmark")

def get_line(v, n):
    return v.line(v.text_point(n,0))

def get_curline():
    V = sublime.active_window().active_view()
    return V.rowcol(V.sel()[0].begin())[0]

def get_view_content(name):
    view = get_view(name)
    return view.substr(sublime.Region(0,view.size())) if view else None

def fill_view(name,content):
    view = get_view(name)
    if view: view.run_command("fill_view",{'text': content})

def close_view(name):
    W = sublime.active_window()
    old_view = W.active_view()
    view = get_view(name)
    W.focus_view(view)
    if view:
        view.set_scratch(True)
        view.close()    
    if not W.views_in_group(W.active_group()):
        W.run_command("close_pane",{})
    W.focus_view(old_view)

def get_view(name):
    some = [v for v in sublime.active_window().views() if v.name()==name]
    return some[0] if len(some)>0 else None

def watcher_content(globals,locals):
    return 'Globals:'            +'\n\n'+\
              dict_table(globals)+'\n\n'+\
           'Locals:'             +'\n\n'+\
              dict_table(locals)

def tryeval(expr,globals,locals):
    try:
        return eval(expr,globals,locals)
    except Exception as e:
        return e

def expression_content():
    if expressions:
        res = [DB.tryeval(expr) for expr in expressions]
        maxlen = max(map(len, expressions))
        expr = [k+' '*(maxlen-len(k)) for k in expressions]
        return '\n'.join([e+' ┃ '+str(r) for r,e in zip(res,expr)])
    else:
        return ''

def parse_expressions(txt):
    return [l.split(' ┃ ')[0].strip() for l in txt.split('\n')] if txt else []

def dict_table(d):
    ks, vs = d.keys(), d.values()
    maxlen = max(map(len, ks))
    ks =[k+' '*(maxlen-len(k)) for k in ks]
    return '\n'.join([k+' ┃ '+str(v) for k,v in sorted(zip(ks,vs))])