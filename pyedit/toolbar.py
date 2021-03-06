import sys
import webbrowser
from contextlib import contextmanager
from io import StringIO
from re import match
from time import sleep
from tkinter import (
    BOTH,
    END,
    Button,
    Menu,
    filedialog,
    messagebox,
    simpledialog,
    Entry,
    LEFT,
    colorchooser
)
from traceback import format_exc

import requests

from pyedit.syntax_highlighting import Syntax


class Toolbar:
    def __init__(self, master, text) -> None:

        self.master = master
        self.text = text
        self.syntax = Syntax(master)
        self.toolbar = Menu(self.master)
        self.master.config(menu=self.toolbar)
        self.filemenu = Menu(self.toolbar)
        self.editmenu = Menu(self.toolbar)
        self.selectionmenu = Menu(self.toolbar)
        self.syntaxmenu = Menu(self.toolbar)
        self.helpmenu = Menu(self.toolbar)
        self.toolbar.add_cascade(label="File", menu=self.filemenu)
        self.toolbar.add_cascade(label="Edit", menu=self.editmenu)
        self.toolbar.add_cascade(label="Selection", menu=self.selectionmenu)
        self.toolbar.add_cascade(label="Syntax", menu=self.syntaxmenu)
        self.toolbar.add_cascade(label="Help", menu=self.helpmenu)
        self.current_file = None

    def open_file_button(self) -> None:
        def open_file():
            ftypes = [("Python files", "*.py"), ("All files", "*")]
            dlg = filedialog.Open(filetypes=ftypes)

            filename = dlg.show()
            self.current_file = filename
            lines = read_file(filename)
            self.text.insert(END, lines)
            self.syntax.highlight(self.text)

        def read_file(filename):
            with open(filename) as f:
                return f.read()

        self.filemenu.add_command(label="Open File", command=open_file)

    def save_file_button(self) -> None:
        def save_file():
            if self.current_file is None:
                self.save_file_as()

            else:
                with open(self.current_file, "w") as f:
                    text = str(self.text.get(1.0, END))
                    f.write(text)
                    f.close()
                    self.syntax.highlight(self.text)
                    self.master.title("File Saved.")
                    self.master.update()
                    sleep(2)
                    self.master.title("PyEdit")
                    self.master.update()

        self.filemenu.add_command(label="Save File", command=save_file)

    def save_file_as_button(self) -> None:
        self.filemenu.add_command(label="Save File as...", command=self.save_file_as)

    def save_file_as(self) -> None:
        f = filedialog.asksaveasfile(mode="w", defaultextension=".py")

        text = str(self.text.get(1.0, END))
        f.write(text)
        f.close()
        self.syntax.highlight(self.text)
        self.current_file = f.name
        self.master.title(f"File saved as {f.name}.")
        self.master.update()
        sleep(2)
        self.master.title("PyEdit")
        self.master.update()

    @contextmanager
    def stdoutIO(self, stdout=None):
        old = sys.stdout
        if stdout is None:
            stdout = StringIO()

        sys.stdout = stdout
        yield stdout
        sys.stdout = old

    def post_to_hastebin_button(self) -> None:
        def post_to_hastebin():
            text = self.text.get(1.0, END)
            resp = requests.post("https://hastebin.com/documents", data=text)
            data = resp.json()
            link = f"https://hastebin.com/{data['key']}"
            self.master.clipboard_append(link)
            self.master.update()
            webbrowser.open(link)

        self.filemenu.add_command(label="Post to hastebin", command=post_to_hastebin)

    def run_button(self) -> None:
        def run():
            if self.current_file is None:
                self.save_file_as()

            else:
                try:
                    code = compile(self.text.get(1.0, END), self.current_file, "exec")
                    with self.stdoutIO() as s:
                        exec(code)

                    code_res = s.getvalue()

                    messagebox.showinfo("Result", str(code_res))

                except:
                    code_res = format_exc()
                    messagebox.showerror("Error", str(code_res))

        self.filemenu.add_command(label="Run", command=run)

    def close_editor_button(self) -> None:
        def close_editor():
            self.master.destroy()

        self.filemenu.add_command(label="Close Editor", command=close_editor)

    def undo_button(self) -> None:
        def undo():
            self.text.event_generate("<<Undo>>")

        self.editmenu.add_command(label="Undo", command=undo)

    def redo_button(self) -> None:
        def redo():
            self.text.event_generate("<<Redo>>")

        self.editmenu.add_command(label="Redo", command=redo)

    def cut_button(self) -> None:
        def cut():
            self.text.event_generate("<<Cut>>")

        self.editmenu.add_command(label="Cut", command=cut)

    def copy_button(self) -> None:
        def copy():
            self.text.event_generate("<<Copy>>")

        self.editmenu.add_command(label="Copy", command=copy)

    def paste_button(self) -> None:
        def paste():
            self.text.event_generate("<<Paste>>")

        self.editmenu.add_command(label="Paste", command=paste)

    def find_and_replace_button(self) -> None:
        def find_and_replace():
            entry = Entry()
            entry.pack(side=LEFT, fill=BOTH, expand=1)

            self.regex = False

            def find():
                self.find_string = entry.get()
                self.text.tag_remove(self.find_string, 1.0, END)
                first = "1.0"
                indexes = []

                while True:
                    if self.regex:
                        first = self.text.search(
                            rf"{self.find_string}",
                            first,
                            nocase=False,
                            stopindex=END,
                            regexp=self.regex,
                        )

                    else:
                        first = self.text.search(
                            f"{self.find_string}",
                            first,
                            nocase=False,
                            stopindex=END,
                            regexp=self.regex,
                        )

                    first_splitted = first.split(".")

                    try:
                        last = f"{first_splitted[0]}.{int(first_splitted[1]) + len(self.find_string)}"

                    except IndexError:
                        break

                    indexes.append((first, last))

                    self.text.tag_add(self.find_string, first, last)
                    first = last

                self.text.tag_config(self.find_string, background="#e9f02b")

                return indexes

            find_button = Button(self.master, text="Find", command=find)
            find_button.pack(side=LEFT)

            entry2 = Entry()
            entry2.pack(side=LEFT, fill=BOTH, expand=1)

            def replace():
                self.text.tag_delete(self.find_string)
                replace_string = entry2.get()
                indexes = find()
                for index in indexes:
                    self.text.delete(index[0], index[1])
                    self.text.insert(index[0], replace_string)

            replace_button = Button(self.master, text="Replace", command=replace)

            replace_button.pack(side=LEFT)

            def toggle():
                if toggle_button.config("text")[-1] == "Regex Off":
                    toggle_button.config(text="Regex On")
                    self.regex = True

                else:
                    toggle_button.config(text="Regex Off")
                    self.regex = False

            toggle_button = Button(self.master, text="Regex Off", command=toggle)
            toggle_button.pack(pady=5, side=LEFT)

            def exit_all():
                entry.destroy()
                entry2.destroy()
                find_button.destroy()
                replace_button.destroy()
                toggle_button.destroy()
                exit_button.destroy()

            exit_button = Button(self.master, text="Exit", command=exit_all)

            exit_button.pack(pady=5, side=LEFT)

        self.editmenu.add_command(label="Find and Replace", command=find_and_replace)

    def select_all_button(self) -> None:
        def select_all():
            self.text.tag_add("sel", 1.0, END)

        self.selectionmenu.add_command(label="Select All", command=select_all)

    def deselect_all_button(self) -> None:
        def deselect_all():
            self.text.tag_remove("sel", 1.0, END)

        self.selectionmenu.add_command(label="Deselect All", command=deselect_all)

    def keyword_highlighting_button(self) -> None:
        def keyword_highlighting():
            color = colorchooser.askcolor()

            if color[0] is not None:
                self.syntax.colors["keyword"] = color[1]

        self.syntaxmenu.add_command(label="Keyword", command=keyword_highlighting)

    def builtin_highlighting_button(self) -> None:
        def builtin_highlighting():
            color = colorchooser.askcolor()

            if color[0] is not None:
                self.syntax.colors["builtin"] = color[1]

        self.syntaxmenu.add_command(label="Built-in", command=builtin_highlighting)

    def number_highlighting_button(self) -> None:
        def number_highlighting():
            color = colorchooser.askcolor()

            if color[0] is not None:
                self.syntax.colors["number"] = color[1]

        self.syntaxmenu.add_command(label="Number", command=number_highlighting)

    def comment_highlighting_button(self) -> None:
        def comment_highlighting():
            color = colorchooser.askcolor()

            if color[0] is not None:
                self.syntax.colors["comment"] = color[1]

        self.syntaxmenu.add_command(label="Comment", command=comment_highlighting)

    def string_highlighting_button(self) -> None:
        def string_highlighting():
            color = colorchooser.askcolor()

            if color[0] is not None:
                self.syntax.colors["string"] = color[1]

        self.syntaxmenu.add_command(label="String", command=string_highlighting)

    def definition_highlighting_button(self) -> None:
        def definition_highlighting():
            color = colorchooser.askcolor()

            if color[0] is not None:
                self.syntax.colors["definition"] = color[1]

        self.syntaxmenu.add_command(label="Definition", command=definition_highlighting)

    def stackoverflow_button(self) -> None:
        def stackoverflow():
            problem = simpledialog.askstring(
                title="Stackoverflow", prompt="What problem do you need help with?"
            )

            resp = requests.get(
                "https://api.stackexchange.com/search",
                params={
                    "site": "stackoverflow.com",
                    "intitle": problem,
                    "sort": "votes",
                },
                headers={"Accept": "application/json;charset=UTF-8"},
            )

            data = resp.json()

            try:
                webbrowser.open(data["items"][0]["link"])

            except IndexError:
                messagebox.showerror(
                    "Not Found", "I couldn't find any related posts to your problem."
                )

        self.helpmenu.add_command(label="Stackoverflow", command=stackoverflow)
