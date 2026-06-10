
import tkinter as tk
from tkinter import ttk

DarkThemeValue = 0
LightThemeValue= 0
UseDark = True
ThemeWidgets = []


def Dark(Value):
    Value = max(0, min(100, int(Value)))
    GrayValue = 25 + Value
    return f"#{GrayValue:02x}{GrayValue:02x}{GrayValue:02x}"

def Light(Value):
    Value = max(0, min(100, int(Value)))
    GrayValue = 155 + Value
    return f"#{GrayValue:02x}{GrayValue:02x}{GrayValue:02x}"

def BG(Extra = 0):
    if UseDark:
        return Dark(DarkThemeValue + Extra)
    return Light(LightThemeValue - Extra)

def FG(Extra = 0):
    if UseDark:
        return Light(LightThemeValue + Extra)
    return Dark(DarkThemeValue - Extra)

def ApplyThemeToWidget(Widget):
    if isinstance(Widget, Button):

        if getattr(Widget, "ThemeFG", True):
            Widget.config(fg=FG(0))

        if getattr(Widget, "ThemeBG", True):
            Widget.config(bg=BG(10),)
            
        Widget.config(    
            highlightbackground=BG(5),
            highlightcolor=BG(5),
            borderwidth=1
            )
        pass
    elif isinstance(Widget, Label):
        if getattr(Widget, "ThemeFG", True):
            Widget.config(fg=FG(0))

        if getattr(Widget, "ThemeBG", True):
            Widget.config(bg=BG(0))

    elif isinstance(Widget, Frame):
        Widget.config(
            bg=BG()
        )
    elif isinstance(Widget, LabelFrame):

        if getattr(Widget, "ThemeFG", True):
            Widget.config(fg=FG(0))

        if getattr(Widget, "ThemeBG", True):
            Widget.config(bg=BG(0))

    elif isinstance(Widget, Checkbutton):
        if getattr(Widget, "ThemeFG", True):
            Widget.config(fg=FG(0))

        if getattr(Widget, "ThemeBG", True):
            Widget.config(bg=BG(10),)

        Widget.config(
            activebackground=BG(15),
            activeforeground=FG(15),
            selectcolor=BG(15),
            highlightbackground=BG(0),
            borderwidth=0
        )
    elif isinstance(Widget, Scale):
        if getattr(Widget, "ThemeFG", True):
            Widget.config(fg=FG(0))

        if getattr(Widget, "ThemeBG", True):
            Widget.config(bg=BG(10),)
        
        Widget.config(
            troughcolor=BG(25),
            highlightbackground=BG(15),
            borderwidth=0
        )
    elif isinstance(Widget, Entry):
        if getattr(Widget, "ThemeFG", True):
            Widget.config(fg=FG(20))

        if getattr(Widget, "ThemeBG", True):
            Widget.config(bg=BG(20),)
        
        Widget.config(
            insertbackground=FG(),
            readonlybackground=BG(-20)
        )
    elif isinstance(Widget, Text):
        if getattr(Widget, "ThemeFG", True):
            Widget.config(fg=FG(0))

        if getattr(Widget, "ThemeBG", True):
            Widget.config(bg=BG(25),)

        Widget.config(
            insertbackground=FG()
        )
    elif isinstance(Widget, Canvas):
        Widget.config(
            bg=BG()
        )
    elif isinstance(Widget, Scrollbar):
        Widget.config(
            bg=BG(),
            activebackground=BG(15),
            troughcolor=FG(25),
        )
    elif isinstance(Widget, Toplevel):
        Widget.config(
            bg=BG()
        )
    elif isinstance(Widget, Notebook):
        Style = ttk.Style()

        Style.configure("Null.TNotebook",background=BG())

        Style.configure("Null.TNotebook.Tab",background=BG(15),foreground=FG())

        Style.map("Null.TNotebook.Tab",

            background=[
                ("selected", BG()),
                ("active", BG(15))],

            foreground=[
                ("selected", FG()),
                ("active", FG(15))])

        Widget.configure(style="Null.TNotebook")
    elif isinstance(Widget, Combobox):
        Style = ttk.Style()
        Style.configure(
        "Null.TCombobox",
            background=BG(15),
            foreground=FG(),
            fieldbackground=BG(),
            arrowcolor=FG(),
            bordercolor=BG(25),
            darkcolor=BG(25),
            lightcolor=BG(25),
        )

        Style.map("Null.TCombobox",

            fieldbackground=[
                ("readonly", BG()),
                ("disabled", BG(10)),
                ("focus", BG()),
                ("active", BG()),
            ],

            foreground=[
                ("readonly", FG()),
                ("disabled", FG(-30)),
                ("focus", FG()),
                ("active", FG()),
            ],

            background=[
                ("readonly", BG(15)),
                ("disabled", BG(20)),
                ("focus", BG(15)),
                ("active", BG(15)),
            ],

            arrowcolor=[
                ("readonly", FG()),
                ("disabled", FG(-30)),
                ("focus", FG()),
                ("active", FG()),
            ],

            bordercolor=[
                ("focus", BG(40)),
                ("!focus", BG(25)),
            ],

            lightcolor=[
                ("focus", BG(40)),
                ("!focus", BG(25)),
            ],

            darkcolor=[
                ("focus", BG(40)),
                ("!focus", BG(25)),
            ]
            )

        Widget.configure(style="Null.TCombobox")

    elif isinstance(Widget, Separator):
        pass
    elif isinstance(Widget, Tk):
        Widget.config(bg=BG())


def ApplyTheme(WhichTheme):
    global UseDark
    if WhichTheme == "Dark":
        UseDark = True
    else:
        UseDark = False

    for Widget in ThemeWidgets[:]:
        try:
            if Widget.winfo_exists():
                ApplyThemeToWidget(Widget)
                
            else:
                ThemeWidgets.remove(Widget)
        except:
            pass

def RegisterThemeWidget(widget):
    if widget not in ThemeWidgets:
        ThemeWidgets.append(widget)
        ApplyThemeToWidget(widget)

    return widget

class Frame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class LabelFrame(tk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Label(tk.Label):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Button(tk.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Checkbutton(tk.Checkbutton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Scale(tk.Scale):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Entry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Text(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Canvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Scrollbar(tk.Scrollbar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Toplevel(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Notebook(ttk.Notebook):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        RegisterThemeWidget(self)

class Combobox(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Separator(ttk.Separator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RegisterThemeWidget(self)

class Tk(tk.Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        RegisterThemeWidget(self)
