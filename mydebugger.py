import sublime
import sublime_plugin
import threading
from .backends import dbPython2
from .backends import dbPython3
from .backends import dbPython3S
from contextlib import contextmanager
from time import sleep
from copy import deepcopy
from os.path import realpath

breakpoints = {}
curlang = "Python3S"
DB = dbPython3S.DBPython3S()


class languageCommand(sublime_plugin.WindowCommand):
    def run(self, lang):
        global DB, curlang
        if lang == curlang:
            return
        try:
            DB = eval("db{0}.DB{0}()".format(lang), globals(), locals())
            sublime.status_message("language: " + lang)
            print("language:", lang)
            curlang = lang
        except Exception as e:
            sublime.status_message(lang + " not installed")
            print(lang + " not installed")

    def is_checked(self, lang):
        return lang == curlang


class debugCommand(sublime_plugin.WindowCommand):
    input_panel = None
    cmd_status = None
    cmd = None

    def run(self):
        sublime.status_message("Started Debugging")
        print("Started Debugging")
        filename = realpath(self.window.active_view().file_name())
        DB.parent = self
        DB.breakpoints = deepcopy(breakpoints)
        # self.window.run_command("toggle_watcherCommand",{})
        threading.Timer(.2, lambda: DB.runscript(filename)).start()

    def show_empty_panel(self):
        self.window.show_input_panel("command (type h for help)", "",
                                     self.success,
                                     self.open,
                                     self.cancel)

    def success(self, s):
        self.cmd_status = "success"
        self.cmd = s

    def cancel(self):
        self.cmd_status = "cancel"
        self.show_empty_panel()

    def open(self, s):
        self.cmd_status = "open"

    def get_cmd(self, line, locals, globals, filename):
        fill_view("Variables", watcher_content(globals, locals))
        refresh_expressions()
        self.show_empty_panel()
        with highlight(filename, line):
            while not self.cmd_status == "success":
                sleep(.1)
        cmd = self.cmd
        self.cmd_status = None
        self.cmd = None
        return cmd

    def set_break(self, filename, line, bpinfo):
        print("set_break", filename, line, bpinfo)
        set_breakGUI(filename, line, bpinfo)

    def clear_break(self, filename, line):
        clear_breakGUI(filename, line)

    def toggle_break(self, filename, line):
        toggle_breakGUI(filename, line)

    def show_help(self, s):
        # s = '\n'.join([l for l in s.split('\n')])
        # import mdpopups
        # mdpopups.show_popup(self.window.active_view(), s, max_width=960)
        # while mdpopups.is_popup_visible(self.window.active_view()):
        #     pass

        # lines=s.split('\n')
        # html=''.join(["<p>"+line+"</p>" for line in lines])
        # view = self.window.active_view()
        # view.show_popup(html)
        # while view.is_popup_visible() : pass

        view = self.window.create_output_panel("help")
        view.run_command("fill_view", {'text': s})
        view.sel().clear()
        self.window.run_command("show_panel", {"panel": "output.help"})
        p = self.window.active_panel()
        while self.window.active_panel() == p: pass

    def show_exception(self, s):
        self.window.set_status_bar_visible(True)
        sublime.status_message("EXCEPTION: " + s)

    def finished(self):
        pass


class toggle_breakpointCommand(sublime_plugin.WindowCommand):
    def run(self):
        filename = self.window.active_view().file_name()
        line = get_curline() + 1
        toggle_breakGUI(filename, line)
        toggle_breakDB(filename, line)


@contextmanager
def bp_manager(filename):
    global breakpoints
    V = sublime.active_window().find_open_file(filename)
    if filename not in breakpoints:
        breakpoints.update({filename: {}})
    bps = breakpoints[filename]
    yield bps
    style = "string", "circle", sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
    V.add_regions("bp", [get_line(V, l - 1) for l in bps], *style)
    fill_view("Breakpoints", breakpoints_content())


def set_breakGUI(filename, line, bpinfo):
    filename = realpath(filename)
    with bp_manager(filename) as bps:
        if line not in bps:
            bps.update({line: {}})
        bps[line] = bpinfo


def clear_breakGUI(filename, line):
    filename = realpath(filename)
    with bp_manager(filename) as bps:
        if line in bps:
            bps.pop(line)


def toggle_breakGUI(filename, line):
    filename = realpath(filename)
    with bp_manager(filename) as bps:
        bps.pop(line) if line in bps else bps.update({line: {}})


def toggle_breakDB(filename, line):
    filename = realpath(filename)
    DB.toggle_break(filename, line)

# def update_breakDB(filename,line):
#     bps = breakpoints[filename]
#     (DB.set_break if line in bps else DB.clear_break)(filename, line)


class toggle_watcherCommand(sublime_plugin.WindowCommand):
    original_layout = None

    def run(self):
        names = ["Variables", "Expression", "Breakpoints"]
        if any(map(get_view, names)):
            for name in names:
                close_view(name)
        else:
            groups = self.window.num_groups()
            act_gr = self.window.active_group()
            layout = self.window.get_layout()
            cells, rows, cols = layout['cells'], layout['rows'], layout['cols']
            nrows, ncols = len(rows), len(cols)
            new_cells = [[ncols - 1, 0        , ncols, nrows    ],
                         [ncols - 1, nrows    , ncols, nrows + 1],
                         [ncols - 1, nrows + 1, ncols, 1.       ]]
            new_layout = {'cells': cells + new_cells,
                          'rows': rows + [.6, .8],
                          'cols': [.8 * col for col in cols] + [1.]}
            self.window.set_layout(new_layout)
            for i, name in enumerate(names):
                self.window.focus_group(groups + i)
                self.new_file(name)
            self.window.focus_group(act_gr)

    def new_file(self, name):
        f = self.window.new_file()
        f.set_name(name)
        f.run_command("fill_view", {'text': ''})
        f.run_command("toggle_setting", {"setting": "word_wrap"})
        f.run_command("toggle_setting", {"setting": "gutter"})


class refresh_expressionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.name() == "Expression":
            refresh_expressions()


class fill_viewCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        region = sublime.Region(0, self.view.size())
        self.view.replace(edit, region, kwargs['text'])
        self.view.show(0)
        self.view.sel().clear()


@contextmanager
def highlight(filename, line):
    w = sublime.active_window()
    v = w.find_open_file(filename)
    if not v:
        v = w.open_file(filename)
    w.focus_view(v)
    v.add_regions("0", [get_line(v, line - 1)], "comment", "bookmark")
    v.show(v.text_point(line, 0))  # focus line beginning
    yield
    v.add_regions("0", [                     ], "comment", "bookmark")


def get_line(v, n):
    return v.line(v.text_point(n, 0))


def get_curline():
    V = sublime.active_window().active_view()
    return V.rowcol(V.sel()[0].begin())[0]


def get_view_content(name):
    view = get_view(name)
    return view.substr(sublime.Region(0, view.size())) if view else None


def fill_view(name, content):
    view = get_view(name)
    if view:
        view.run_command("fill_view", {'text': content})


def close_view(name):
    W = sublime.active_window()
    old_view = W.active_view()
    view = get_view(name)
    W.focus_view(view)
    if view:
        view.set_scratch(True)
        view.close()
    if not W.views_in_group(W.active_group()):
        W.run_command("close_pane", {})
    W.focus_view(old_view)


def get_view(name):
    some = [v for v in sublime.active_window().views() if v.name() == name]
    return some[0] if len(some) > 0 else None


def tryeval(expr, globals, locals):
    try:
        return eval(expr, globals, locals)
    except Exception as e:
        return e


def breakpoints_content():
    def ran_to_str(r):
        try:
            s = ':'.join(['' if n is None else str(n) for n in r])
            return s
        except:
            return None

    def bp_type(v):
        return v.get("cond") or ran_to_str(v.get("range")) or ''

    def fbps_to_str(fbps):
        f, bps = fbps
        d = {str(k): bp_type(v) or '' for k, v in bps.items()}
        return f + '\n' + dict_table(d)
    return '\n'.join(map(fbps_to_str, breakpoints.items()))


def watcher_content(globals, locals):
    fields = ['Globals:', dict_table(globals), 'Locals:', dict_table(locals)]
    return "\n\n".join(fields)


def refresh_expressions():
    expressions = get_keys(get_view_content("Expression"))
    d = {expr: DB.tryeval(expr) for expr in expressions}
    fill_view("Expression", dict_table(d))


def get_keys(txt):
    keys = [l.split(' ┃ ')[0].strip() for l in txt.split('\n')] if txt else []
    return [k for k in keys if k]  # list(filter(bool, keys))


def dict_table(d):
    # d = {k: v for k, v in d.items() if not k.endswith("__")}
    ks, vs = d.keys(), d.values()
    maxlen = max(map(len, ks)) if ks else 0
    ks = [k.ljust(maxlen) for k in ks]
    vs = [str(v).replace("\n", "\n" + " " * maxlen + ' ┃ ') for v in vs]
    return '\n'.join(map(' ┃ '.join, sorted(zip(ks, vs))))
