#region Imports and Safty Check

import json
import importlib.util
import shutil
import subprocess
import os
import sys

BaseDir = os.path.dirname(os.path.abspath(__file__))
RootDir = os.path.dirname(BaseDir)
InstallerPath = os.path.join(RootDir,"InstallNullSuite(Mint).sh")

with open(os.path.join(RootDir, "Dependencies.json"), "r") as f:
    Dependencies = json.load(f)

MissingModules = any(
    importlib.util.find_spec(Module) is None
    for Module in Dependencies["NullSuitePyCheckPips"]
)
 
MissingPackages = any(
    shutil.which(Command) is None
    for Command in Dependencies["NullSuitePyCheckPackages"]
)
if MissingModules or MissingPackages:

    subprocess.run(
        ["pkill", "-x", "NSLauncher.sh"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
        )
    
    subprocess.run(
        [
            "x-terminal-emulator",
            "-e",
            "bash",
            InstallerPath
        ],
        check=True
    )

    sys.exit()

import tkinter as tk
from tkinter import (ttk,filedialog,messagebox)
import threading
import setproctitle
import time
import webbrowser
import re
import getpass
import queue
from queue import Queue
import select
import mido # type: ignore
import uinput
import traceback
import shlex
from pynput import mouse, keyboard
import atexit
import tempfile
from PIL import Image, ImageTk, ImageDraw
import hashlib
from datetime import datetime, timedelta
import urllib.request
import nulltk # type: ignore

setproctitle.setproctitle("NullSuite")
os.environ["PULSE_PROP_application.name"] = "NullMidiSounds"
import pygame

#endregion

#region NullSuite 
SystemLoading = True
ProgramLoading = False
Root = nulltk.Tk(className="NullSuite")
Root.title("NullSuite")
Root.geometry("1600x900")
Main = nulltk.Frame(Root)
Main.pack(fill="both", expand=True, padx=10, pady=10)
style = ttk.Style()
style.map("TNotebook.Tab",foreground=[("disabled", "#666666"),("selected", "#000000"),("!disabled", "#000000")])
NullWireActive = tk.BooleanVar(value=False)
NullMidiActive = tk.BooleanVar(value=False)
NullProtonActive = tk.BooleanVar(value=False)
NullMonitorActive = tk.BooleanVar(value=False)
NullGitActive = tk.BooleanVar(value=False)
NullFocusActive = tk.BooleanVar(value=False)
NullMojiActive = tk.BooleanVar(value=False)
StartMinimizedActive= tk.BooleanVar(value=False)
StartInTrayActive= tk.BooleanVar(value=False)
DontLoadAppsOnStartUpActive= tk.BooleanVar(value=False)
MixerInitialized = False
LoadPopup = nulltk.Toplevel(Root)
LoadPopup.title("Loading NullSuite Data")
Width = 1000
Height = 100
Root.update_idletasks()
RootX = Root.winfo_x()
RootY = Root.winfo_y()
RootWidth = Root.winfo_width()
RootHeight = Root.winfo_height()
X = RootX + ((RootWidth // 2) - (Width // 2))
Y = RootY + ((RootHeight // 2) - (Height // 2))
LoadPopup.geometry(f"{Width}x{Height}+{X}+{Y}")
LoadPopup.resizable(False, False)
LoadPopup.transient(Root)
LoadPopup.grab_set()
LoadPopup.attributes("-topmost", True)
LoadFrame = nulltk.Frame(LoadPopup)
LoadFrame.pack(fill="both", expand=True)
Butts = tk.StringVar(value = "Loading")
nulltk.Label(LoadFrame,textvariable=Butts,font=("Arial", 12)).pack(expand=True)
LoadPopup.update()
BaseDir = os.path.dirname(os.path.abspath(__file__))
IconPath = os.path.join(BaseDir,"NullSuite.png")
ConfigPath = os.path.join(BaseDir,"NullSuite.json")
TrackerPath = os.path.join(BaseDir, "TrackerLogs")
ClipboardPath = os.path.join(TrackerPath, "Clipboard")
BaseEmojisPath = os.path.join(BaseDir, "BaseEmoji.json")
Python = os.path.join(BaseDir, "venv", "bin", "python3")
NWPath = os.path.join(BaseDir, "NW.sh") 
SpotifySongPath = os.path.join(BaseDir, "SpotifySong.txt")
IconImage = tk.PhotoImage(file=IconPath)
CircadianPath = os.path.join(BaseDir, "CircadianClock.png")
ClockOriginal = Image.open(CircadianPath)
ClockImage = ImageTk.PhotoImage(ClockOriginal)
Root.iconphoto(True, IconImage)
LoadTimes = {}
LoadCompleted = 0
LastLoadCompletedNumber = 0
ProgramCount = 0
ActualProgramLoadedCount =0 
ActualProgramOnCount = 0
HiddenToTray = False
SaveLock = threading.Lock()
DarkTheme = tk.BooleanVar(value=True)

def StartTray():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import Gtk, AppIndicator3
    indicator = AppIndicator3.Indicator.new(
        "nullsuite",
        IconPath,
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    menu = Gtk.Menu()
    def Show(_):
        global HiddenToTray
        HiddenToTray = False
        Root.deiconify()
        Root.lift()
        Root.focus_force()

    def OpenFileLocation(_):
        subprocess.Popen(["xdg-open", BaseDir])
    
    def Quit(_):
        if SystemLoading:
            return
        
        subprocess.run([NWPath, "ClearSinks"])
        subprocess.run(
                    ["pkill", "-x", "NSLauncher.sh"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        Root.after(0, Root.destroy)
        Gtk.main_quit()

    def Restart(_):
        if SystemLoading:
            return
        #subprocess.run([NWPath, "ClearSinks"])
        subprocess.Popen([sys.executable] + sys.argv)
        Root.after(0, Root.destroy)
        Gtk.main_quit()

    # ==============================
    # Menu Items
    # ==============================
    toggle = Gtk.MenuItem(label="Show")
    toggle.connect("activate", Show)
    menu.append(toggle)

    filelocation = Gtk.MenuItem(label="Open File Location")
    filelocation.connect("activate", OpenFileLocation)
    menu.append(filelocation)

    spacer = Gtk.MenuItem(label="———")
    spacer.set_sensitive(False)
    menu.append(spacer)

    restartbtn = Gtk.MenuItem(label="Restart")
    restartbtn.connect("activate", Restart)
    menu.append(restartbtn)

    quitbtn = Gtk.MenuItem(label="Quit")
    quitbtn.connect("activate", Quit)
    menu.append(quitbtn)

    menu.show_all()
    indicator.set_menu(menu)

    Gtk.main()
    
def GetSavableMidiRows():

    SaveRows = []

    for Row in MidiRows:

        SaveRow = {}

        for Key, Value in Row.items():

            if Key in [
                "VirtualPort",
                "Frame",
                "Button",
                "Widgets",
                "ControllerPageVar",
                "OutputPort"
            ]:
                continue

            elif Key == "DrumList":

                CleanDrums = []

                for Drum in Value:

                    CleanDrum = {}

                    for DrumKey, DrumValue in Drum.items():

                        if DrumKey == "Channels":
                            CleanDrum[DrumKey] = []
                            continue

                        CleanDrum[DrumKey] = DrumValue

                    CleanDrums.append(CleanDrum)

                SaveRow[Key] = CleanDrums

            else:
                SaveRow[Key] = Value

        SaveRows.append(SaveRow)

    return SaveRows

def LoadConfig():
    global ProgramCount, ActualProgramOnCount
    if not os.path.isfile(ConfigPath):
        SaveConfig("NullSuite", True)
        SaveConfig("NullProton", True)
        SaveConfig("NullWire", True)
        SaveConfig("NullMonitor", True)
        SaveConfig("NullMidi", True)
        SaveConfig("NullGit", True)
        SaveConfig("NullFocus", True)
        SaveConfig("NullMoji", True)

    try:
        with open(ConfigPath, "r") as f:
            data = json.load(f)

        nullsuite = data.get("NullSuite", {})

        Modules = {
        "NullWire": {
            "Config": "NullWireActive",
            "Toggle": NullWireActive,
            "Start": StartUpNullWire,
            "Tab": NullWire,
        },

        "NullMonitor": {
            "Config": "NullMonitorActive",
            "Toggle": NullMonitorActive,
            "Start": StartUpNullMonitor,
            "Tab": NullMonitor,
        },

        "NullMidi": {
            "Config": "NullMidiActive",
            "Toggle": NullMidiActive,
            "Start": StartUpNullMidi,
            "Tab": NullMidi,
        },

        "NullProton": {
            "Config": "NullProtonActive",
            "Toggle": NullProtonActive,
            "Start": StartUpNullProton,
            "Tab": NullProton,
        },

        "NullGit": {
            "Config": "NullGitActive",
            "Toggle": NullGitActive,
            "Start": StartUpNullGit,
            "Tab": NullGit,
        },

        "NullFocus": {
            "Config": "NullFocusActive",
            "Toggle": NullFocusActive,
            "Start": StartUpNullFocus,
            "Tab": NullFocus,
        },
    
        "NullMoji":{
            "Config": "NullMojiActive",
            "Toggle": NullMojiActive,
            "Start": StartUpNullMoji,
            "Tab": NullMoji,
        }
    }

        ProgramCount = len(Modules)
        LoadStagger = 0

        nullsuite = data.get("NullSuite", {})
        StartMinimizedActive.set(nullsuite.get("StartMinimized", False))
        DarkTheme.set(nullsuite.get("DarkTheme", True))
        BlackVar.set(nullsuite.get("DarkValue"))
        WhiteVar.set(nullsuite.get("LightValue"))
        nulltk.DarkThemeValue = BlackVar.get()
        nulltk.LightThemeValue = WhiteVar.get()

        if StartMinimizedActive.get():
            Root.after(0, Root.iconify)

        StartInTrayActive.set(nullsuite.get("StartInTray", False))

        if StartInTrayActive.get():
            Root.after(0, Root.withdraw)

        Log("NullSuite: Loading programs! (Some programs load so fast it wont show in the counter. You're Welcome 😎)")

        for Name, Module in Modules.items():
            Module["Toggle"].set(nullsuite.get(Module["Config"], False))

            if Module["Toggle"].get():
                LoadStagger += 250
                ActualProgramOnCount+=1


            Root.after(LoadStagger, Module["Start"])


        return True

    except Exception as e:
        Log(f"NullSuite: LoadConfig failed: {e}")
        return False

def SaveConfig(Which, FirstTimeSetup=False):
    global LastLoadCompletedNumber
    if FirstTimeSetup == False:
        if LoadCompleted < ProgramCount:
            if LastLoadCompletedNumber != LoadCompleted:
                LastLoadCompletedNumber = LoadCompleted
                Log(f"NullSuite: Not Done Loading {ActualProgramLoadedCount}/{ActualProgramOnCount}")
            return

        if SystemLoading:
            return
        
    with SaveLock:
    
        try:
            with open(ConfigPath, "r") as f:
                data = json.load(f)
        except:
            data = {}

        if Which == "NullSuite":
            data.update({
            "NullSuite": {
                "NullWireActive": NullWireActive.get(),
                "NullMonitorActive": NullMonitorActive.get(),
                "NullMidiActive": NullMidiActive.get(),
                "NullProtonActive": NullProtonActive.get(),
                "NullGitActive": NullGitActive.get(),
                "NullFocusActive": NullFocusActive.get(),
                "NullMojiActive": NullMojiActive.get(),
                "StartMinimized": StartMinimizedActive.get(),
                "StartInTray": StartInTrayActive.get(),
                "DarkTheme": DarkTheme.get(),
                "DarkValue": BlackVar.get(),
                "LightValue": WhiteVar.get()
            }
        })

        elif Which == "NullProton":
            data.update({
            "NullProton": {
                "Default": ProtonVars["Default"].get(),
                "A": ProtonVars["A"].get(),
                "B": ProtonVars["B"].get(),
                "Min": MinVar.get(),
                "Close": CloseVar.get(),
                "Games": ProtonGames
            }
        })
        elif Which == "NullWire":
            data.update({
            "NullWire": {
                "OutputWires": OutputWires,
                "InputWires":  InputWires,
            }
        })

        elif Which == "NullMonitor":
            data.update({
            "NullMonitor": {
            "Profiles": Profiles,
            "ActiveProfile": ActiveProfile,
            "ScanForMouse": ScanForMouse
            }
        })
        elif Which == "NullMidi":
            data.update({
            "NullMidi": {
            "MidiRows": GetSavableMidiRows()
            }
        })
        elif Which == "NullGit":
            data.update({
                "NullGit": {"Repos":Repos}
            })
        elif Which == "NullFocus":
            data.update({
            "NullFocus": {
            "AppClassification": AppClassification,
            "WriteToDiskSeconds": WriteToDiskSeconds,
            "MinimumWindowTime": MinimumWindowTime,
            "NewDayThreshold": NewDayThreshold,
            "Operators": NullFocusOperators
            }
            })
        elif Which == "NullMoji":
            data.update({
            "NullMoji": {
            "CustomEmoji": CustomEmojis,
            "RecentEmoji": RecentEmojis
            }
            })
        
        else:
            return

        try:
            with open(ConfigPath, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            Log(f"NullSuite: SaveConfig failed:{e}")

def BringToFront():
    Root.deiconify()
    Root.lift()
    Root.focus_force()

    Root.attributes("-topmost", True)
    Root.after(50, lambda: Root.attributes("-topmost", False))

def WatchShowSignal():
    global PreviousWindowID, CalledWithShortcut
    ShowPath = os.path.join(BaseDir, "NullSuite.show")

    while True:
        if os.path.exists(ShowPath):
            with open(ShowPath,"r") as f:
                Command = f.read().strip()
            os.remove(ShowPath)

            if Command == "SHOW":
                Root.after(0, BringToFront)

            elif Command == "NULLMOJI":
                CalledWithShortcut = True
                PreviousWindowID = GetActiveWindowID()
                Root.after(3, NullMojiFocus)
                continue

            Root.after(0, BringToFront)

        time.sleep(0.1)

def BindMouseWheel(self, widget):

    try:
        widget.bind("<Button-4>", self.OnMouseWheel)
        widget.bind("<Button-5>", self.OnMouseWheel)
    except:
        pass

    for child in widget.winfo_children():
        self.BindMouseWheel(child)

def ChangeTheme():
    nulltk.DarkThemeValue = BlackVar.get()
    nulltk.LightThemeValue = WhiteVar.get()
    if DarkTheme.get() == True:
        nulltk.ApplyTheme("Dark")
    else:
        nulltk.ApplyTheme("Light")
    SaveConfig("NullSuite")
    return

class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.Canvas = nulltk.Canvas(self, highlightthickness=0)
        scrollbar = nulltk.Scrollbar(self, orient="vertical", command=self.Canvas.yview)
        self.Inner = nulltk.Frame(self.Canvas)
        self.Window = self.Canvas.create_window((0, 0), window=self.Inner, anchor="nw")
        self.Inner.bind("<Configure>", lambda e: self.Canvas.configure(scrollregion=self.Canvas.bbox("all")))
        self.Canvas.bind("<Configure>", lambda e: self.Canvas.itemconfig(self.Window, width=e.width))
        self.Canvas.configure(width=0)
        self.Canvas.configure(yscrollcommand=scrollbar.set)
        self.Canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.BindMouseWheel(self.Inner)

    def BindMouseWheel(self, widget):

        widget.bind("<Button-4>", self.OnMouseWheel)
        widget.bind("<Button-5>", self.OnMouseWheel)

        for child in widget.winfo_children():
            self.BindMouseWheel(child)

    def OnMouseWheel(self, event):

        ContentHeight = self.Inner.winfo_reqheight()
        ViewHeight = self.Canvas.winfo_height()

        if ContentHeight <= ViewHeight:
            return

        if isinstance(event.widget, (nulltk.Scale, ttk.Scale)):
            return

        if event.num == 4:
            self.Canvas.yview_scroll(-1, "units")

        elif event.num == 5:
            self.Canvas.yview_scroll(1, "units")

class HoriScrollableFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.Canvas = nulltk.Canvas(self,highlightthickness=0)
        self.Scrollbar = nulltk.Scrollbar(self,orient="horizontal",command=self.Canvas.xview)
        self.Inner = nulltk.Frame(self.Canvas)
        self.Window = self.Canvas.create_window((0, 0),window=self.Inner,anchor="nw")
        self.Inner.bind("<Configure>",lambda e: self.Canvas.configure(scrollregion=self.Canvas.bbox("all")))
        self.Canvas.bind("<Configure>",lambda e: self.Canvas.itemconfig(self.Window,height=e.height))
        self.Canvas.configure(height=0)
        self.Canvas.configure(xscrollcommand=self.Scrollbar.set)
        self.Canvas.pack(side="top",fill="both",expand=True)
        self.Scrollbar.pack(side="bottom",fill="x")
        self.BindMouseWheel(self.Inner)

    def BindMouseWheel(self, widget):
        widget.bind("<Shift-Button-4>", self.OnMouseWheel)
        widget.bind("<Shift-Button-5>", self.OnMouseWheel)
        for child in widget.winfo_children():
            self.BindMouseWheel(child)

    def OnMouseWheel(self, event):
        ContentWidth = self.Inner.winfo_reqwidth()
        ViewWidth = self.Canvas.winfo_width()
        if ContentWidth <= ViewWidth:
            return
        if isinstance(event.widget, (nulltk.Scale, ttk.Scale)):
            return
        if event.num == 4:
            self.Canvas.xview_scroll(-1, "units")
        elif event.num == 5:
            self.Canvas.xview_scroll(1, "units")

class NullMessageBox(nulltk.Toplevel):
    def __init__(self, parent, title="", message="", buttons=("OK",)):
        super().__init__(parent)

        self.Result = None

        self.title(title)
        self.resizable(False, False)
        self.geometry("1000x500")

        self.transient(parent)
        self.grab_set()

        MainFrame = nulltk.Frame(self)
        MainFrame.pack(fill="both", expand=True, padx=10, pady=10)

        MessageLabel = nulltk.Label(
            MainFrame,
            text=message,
            justify="center",
            wraplength=800
        )
        MessageLabel.pack(fill="x", pady=(0,10))

        ButtonFrame = nulltk.Frame(MainFrame)
        ButtonFrame.pack(pady=5)

        DefaultButton = None

        for ButtonName in buttons:
            TheButton = nulltk.Button(
                ButtonFrame,
                text=ButtonName,
                command=lambda value=ButtonName: self.ButtonPressed(value)
            )
            TheButton.pack(side="left", padx=5)
            if DefaultButton is None:
                DefaultButton = TheButton

        self.protocol("WM_DELETE_WINDOW", self.Close)

        self.wait_visibility()
        self.focus_force()
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        DefaultButton.focus_set()

        self.bind("<Return>",lambda e: DefaultButton.invoke())
        self.bind("<Escape>", lambda e: self.Close())

    def ButtonPressed(self, value):
        self.Result = value
        self.destroy()

    def Close(self):
        self.Result = None
        self.destroy()

    def Show(self):
        self.wait_window()
        return self.Result

def SetupSlider(slider, variable, minimum, maximum, callback):
    def ScrollUp(event):
        slider.set(min(maximum, slider.get() + 5))
        callback()

    def ScrollDown(event):
        slider.set(max(minimum, slider.get() - 5))
        callback()

    slider.bind("<ButtonRelease-1>",lambda e: callback())
    slider.bind("<Button-4>", ScrollUp)
    slider.bind("<Button-5>", ScrollDown)
    
def BuildWindowSelectionList(Program):
    global WindowSelection
    WindowSelection.clear()

    try:
        Result = subprocess.run(
            ["wmctrl", "-lx"],
            capture_output=True,
            text=True
        )

        SeenClasses = set()
        IgnoredList = AppClassification.get("Ignored", [])

        for line in Result.stdout.splitlines():
            parts = line.split(None, 4)

            if len(parts) < 5:
                continue

            WindowClass = parts[2]
            WindowTitle = parts[4]

            if (
                WindowClass in SeenClasses
                or WindowClass.strip() == ""
                or WindowClass.lower() in [
                    "desktop.desktop",
                    "gnome-shell.gnome-shell",
                    "plasmashell.plasmashell"
                ]
            ) or Program =="NullFocus" and WindowClass in IgnoredList:
                continue

            SeenClasses.add(WindowClass)
            DisplayName = WindowTitle.strip()

            if DisplayName == "":
                DisplayName = WindowClass

            WindowSelection.append({
                "UIName": DisplayName,
                "ClassName": WindowClass
            })
    except Exception as e:
        Log(f"NullSuite: BuildWindowSelectionList Error: {e}" "Error")

def SearchForWindow(Dict, var, ClassName,DisplayName,Program, Page=None):
    BuildWindowSelectionList(Program)
    global TrackerPopup

    Popup = nulltk.Toplevel(Root)
    TrackerPopup = Popup
    Popup.title("Select Window")
    Popup.geometry("800x600")
    Popup.grab_set()

    ScrollFrame = ScrollableFrame(Popup)
    ScrollFrame.pack(fill="both", expand=True)

    for Window in WindowSelection:
        nulltk.Button(
            ScrollFrame.Inner,
            text=f"Window Title:{Window['UIName']}\n\nProcess Name: {Window['ClassName']}",
            justify="left",
            anchor="w",
            command=lambda w=Window: SelectWindow(w, Dict, var, ClassName,DisplayName, Popup, Program, Page)
        ).pack(fill="x", padx=2, pady=2)

def SelectWindow(Window, Dict, var, ClassName,DisplayName, Popup, Program, Page=None):
    global TrackerPopup, NullFocusOperator

    normalizeddisplayname = NormalizeDisplayName(Window["UIName"],Window["ClassName"])
    NormalizedClass = Window["ClassName"].split(".")[-1].lower()


    if Program == "NullMidi":
        if Page != None:
            Dict[ClassName][Page] = Window["ClassName"]
            var.set(normalizeddisplayname)
            Dict[DisplayName][Page] = normalizeddisplayname
        else:
            Dict[ClassName] = Window["ClassName"]
            var.set(normalizeddisplayname)
            Dict[DisplayName] = normalizeddisplayname
    elif Program == "NullFocus":
        Dict.setdefault(ClassName,[])
        if Window["ClassName"] not in Dict[ClassName]:
            NormalizedClass = Window["ClassName"].split(".")[0].lower()
            Dict[ClassName].append(NormalizedClass)
    elif Program == "Operator":
        Program = "NullFocus"
        Operator = {
            "DisplayName": normalizeddisplayname,
            "WindowClass": NormalizedClass,
            "DeleteConfirmation": False,
            "Focused": {
                "KeyOrAction": False,
                "WindowSpecific": False,
                "OnlyThisWindow": None,
                "FileOrCommand": False,
                "Keys": [],
                "FilePath": "",
                "Command": "",
            },
            "Unfocused": {
                "KeyOrAction": False,
                "WindowSpecific": False,
                "OnlyThisWindow": None,
                "FileOrCommand": False,
                "Keys": [],
                "FilePath": "",
                "Command": "",
            }
            
        }

        NullFocusOperators.append(Operator)

        CreateOperatorRow(Operator)
    elif Program == "NullFocusOperator":
        Program = "NullFocus"
        Dict[ClassName] = NormalizedClass
        var.set(NormalizedClass)

    
    Popup.destroy()
    TrackerPopup = None
    SaveConfig(Program)

def NormalizeDisplayName(WindowTitle, WindowClass):
    if " - " in WindowTitle:
        return WindowTitle.split(" - ")[-1].strip()

    return WindowClass.split(".")[0].capitalize()

def OpenImagePopUp(Path, ThumbnailSize=256):
    Popup = nulltk.Toplevel(Root)
    Popup.title("Select Image")
    Popup.geometry("1400x900")

    SelectedImage = [None]
    Thumbnails = []

    ScrollFrame = ScrollableFrame(Popup)
    ScrollFrame.pack(fill="both", expand=True)

    Images = []

    SupportedTypes = (
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".webp",
        ".gif"
    )

    for File in sorted(os.listdir(Path)):
        FullPath = os.path.join(Path, File)

        if (
            os.path.isfile(FullPath)
            and File.lower().endswith(SupportedTypes)
        ):
            Images.append(FullPath)

    def SelectImage(ImagePath):
        SelectedImage[0] = ImagePath
        Popup.destroy()

    for Index, ImagePath in enumerate(Images):
        Row = Index // 5
        Column = Index % 5

        Cell = nulltk.Frame(
            ScrollFrame.Inner,
            relief="groove",
            borderwidth=2
        )

        Cell.grid(
            row=Row,
            column=Column,
            padx=5,
            pady=5,
            sticky="n"
        )

        try:
            Thumb = Image.open(ImagePath)
            Thumb.thumbnail((ThumbnailSize, ThumbnailSize))

            Photo = ImageTk.PhotoImage(Thumb)
            Thumbnails.append(Photo)

            nulltk.Label(
                Cell,
                image=Photo
            ).pack()

        except Exception:
            nulltk.Label(
                Cell,
                text="Preview Failed",
                width=30,
                height=15
            ).pack()

        nulltk.Label(
            Cell,
            text=os.path.basename(ImagePath),
            wraplength=ThumbnailSize
        ).pack()

        nulltk.Button(
            Cell,
            text="Select",
            command=lambda P=ImagePath: SelectImage(P)
        ).pack(fill="x")

    ScrollFrame.BindMouseWheel(ScrollFrame.Inner)

    Popup.transient(Root)
    Popup.grab_set()

    Root.wait_window(Popup)

    return SelectedImage[0]

def UpdateStartUpToggles(Which):
    
    if Which == "Wire":
        StartUpNullWire()

    elif Which == "Cursor":
        StartUpNullMonitor()

    elif Which == "Midi":
        StartUpNullMidi()

    elif Which == "Proton":
        StartUpNullProton()

    elif Which == "Git":
        StartUpNullGit()

    elif Which == "Tracker":
        StartUpNullFocus()

    elif Which == "Moji":
        StartUpNullMoji()

    SaveConfig("NullSuite")
    return

def Log(Message, Type = "Basic"):
    TimeStamp = datetime.now().strftime("%H:%M:%S")

    Type = Type.lower()
    if Type == "warning":
        LogNote = nulltk.Label(NullSuiteLog, text=f"{TimeStamp} — {Message}", fg="#CCCC00", bg="#000000", ThemeBG= False, ThemeFG= False, anchor="w")
    elif Type == "error":
        LogNote = nulltk.Label(NullSuiteLog, text=f"{TimeStamp} — {Message}", fg="#FF0000", bg="#000000", ThemeBG= False, ThemeFG= False, anchor="w")
    else:
        LogNote = nulltk.Label(NullSuiteLog, text=f"{TimeStamp} — {Message}", fg="#009900", bg="#000000", ThemeBG= False, ThemeFG= False, anchor="w")

    LogNote.pack(fill="x", padx=10)

def MyExceptionLogger(exc_type, exc_value, exc_traceback):

    ErrorText = "".join(
        traceback.format_exception(
            exc_type,
            exc_value,
            exc_traceback
        )
    )

    print(f"ERROR: {ErrorText}", "Error")
    Log(f"ERROR: {ErrorText}", "Error")

sys.excepthook = MyExceptionLogger

Notebook = nulltk.Notebook(Main)
Notebook.pack(fill="both", expand=True)
NullSuite = nulltk.Frame(Notebook)
NullWire = nulltk.Frame(Notebook)
NullMonitor = nulltk.Frame(Notebook)
NullMidi = nulltk.Frame(Notebook)
NullProton = nulltk.Frame(Notebook)
NullGit = nulltk.Frame(Notebook)
NullFocus = nulltk.Frame(Notebook)
NullMoji = nulltk.Frame(Notebook)
Notebook.add(NullSuite, text="Main Menu")
Notebook.add(NullWire, text="NullWire")
Notebook.add(NullMonitor, text="NullMonitor")
Notebook.add(NullMidi, text = "NullMidi")
Notebook.add(NullProton, text = "NullProton")
Notebook.add(NullGit, text = "NullGit")
Notebook.add(NullFocus, text = "NullFocus")
Notebook.add(NullMoji, text = "NullMoji")
NullSuiteChangeLogPage = nulltk.Frame(NullSuite)
NullSuiteChangeLogPage.pack(fill="both", expand=True)
NullSuiteChangeLogPage.rowconfigure(2, weight=1)
NullSuiteChangeLogPage.columnconfigure(0, weight=1)
NullSuiteToggles = nulltk.Frame(NullSuiteChangeLogPage)
NullSuiteToggles.grid(row=0,column=0, pady=(5,2), sticky="ew")
NullSuiteTogglesOptions = nulltk.Frame(NullSuiteChangeLogPage)
NullSuiteTogglesOptions.grid(row=1,column=0, pady=(2,20), sticky="ew")
NullSuiteToggles.rowconfigure(0,weight=0)
NullSuiteToggles.columnconfigure(0,weight=0)
NullSuiteToggles.columnconfigure(1,weight=0)
NullSuiteToggles.columnconfigure(2,weight=0)
NullSuiteToggles.columnconfigure(3,weight=0)
NullSuiteToggles.columnconfigure(4,weight=0)
NullSuiteToggles.columnconfigure(5,weight=0)
NullSuiteToggles.columnconfigure(6,weight=0)
NullSuiteToggles.columnconfigure(7,weight=0)
NullSuiteToggles.columnconfigure(8,weight=0)
NullSuiteTogglesOptions.rowconfigure(0,weight=0)
NullSuiteTogglesOptions.columnconfigure(0,weight=0)
NullSuiteTogglesOptions.columnconfigure(1,weight=0)
NullSuiteTogglesOptions.columnconfigure(2,weight=0)
NullWireActivator = nulltk.Checkbutton(NullSuiteToggles, text="NullWire?", variable=NullWireActive, command=lambda: UpdateStartUpToggles("Wire"))
NullWireActivator.grid(row=0,column=0, padx=1,pady=1, sticky="w" )
NullMonitorActivator = nulltk.Checkbutton(NullSuiteToggles, text="NullMonitor?", variable=NullMonitorActive,command=lambda: UpdateStartUpToggles("Cursor"))
NullMonitorActivator.grid(row=0,column=1, padx=1,pady=1, sticky="w")
NullMidiActivator = nulltk.Checkbutton(NullSuiteToggles, text="NullMidi?", variable=NullMidiActive,command=lambda: UpdateStartUpToggles("Midi"))
NullMidiActivator.grid(row=0,column=2, padx=1,pady=1, sticky="w")
NullProtonActivator = nulltk.Checkbutton(NullSuiteToggles, text="NullProton?", variable=NullProtonActive,command=lambda: UpdateStartUpToggles("Proton"))
NullProtonActivator.grid(row=0,column=3, padx=1,pady=1, sticky="w")
NullGitActivator = nulltk.Checkbutton(NullSuiteToggles, text="NullGit?", variable=NullGitActive,command=lambda: UpdateStartUpToggles("Git"))
NullGitActivator.grid(row=0,column=4, padx=1,pady=1, sticky="w")
NullFocusActivator = nulltk.Checkbutton(NullSuiteToggles, text="NullFocus?", variable=NullFocusActive,command=lambda: UpdateStartUpToggles("Tracker"))
NullFocusActivator.grid(row=0,column=5, padx=1,pady=1, sticky="w")
NullMojiActivator = nulltk.Checkbutton(NullSuiteToggles, text="NullMoji?", variable=NullMojiActive,command=lambda: UpdateStartUpToggles("Moji"))
NullMojiActivator.grid(row=0,column=6, padx=1,pady=1, sticky="w")
StartMinimizedActivator = nulltk.Checkbutton(NullSuiteTogglesOptions, text="Start Minimized?", variable=StartMinimizedActive,command=lambda: UpdateStartUpToggles("Start"))
StartMinimizedActivator.grid(row=0,column=0, padx=1,pady=1, sticky="w")
StartInTrayActivator = nulltk.Checkbutton(NullSuiteTogglesOptions, text="Start In Tray?", variable=StartInTrayActive,command=lambda: UpdateStartUpToggles("Tray"))
StartInTrayActivator.grid(row=0,column=1, padx=1,pady=1, sticky="w")
NullSuiteDarkModeToggle = nulltk.Checkbutton(NullSuiteTogglesOptions, text="Dark Mode", variable= DarkTheme, command=lambda: ChangeTheme())
NullSuiteDarkModeToggle.grid(row=0,column=2, padx=1,pady=1, sticky="we")
ttk.Separator(NullSuiteTogglesOptions,orient="vertical").grid(row=0,column=3,sticky="ns",padx=5)
BlackVar = tk.IntVar(value=100)
BlackValueText = nulltk.Label(NullSuiteTogglesOptions, text="Blackness")
BlackValueText.grid(row=0, column=4, sticky="ew")
BlackLevel = nulltk.Scale(NullSuiteTogglesOptions,from_=0,to=100,orient="horizontal",showvalue=0,variable=BlackVar)
BlackLevel.grid(row=0, column=5, sticky="ew")
BlackLevel.bind("<ButtonRelease-1>", lambda e: ChangeTheme())
BlackLevel.set(BlackVar.get())
BlackLevelValue = nulltk.Label(NullSuiteTogglesOptions, textvariable=BlackVar, width=4)
BlackLevelValue.grid(row=0, column=6, padx=5, sticky="w")
ttk.Separator(NullSuiteTogglesOptions,orient="vertical").grid(row=0,column=7,sticky="ns",padx=5)
WhiteVar = tk.IntVar(value=100)
WhiteValueText = nulltk.Label(NullSuiteTogglesOptions, text="Whiteness")
WhiteValueText.grid(row=0, column=8, sticky="ew")
WhiteLevel = nulltk.Scale(NullSuiteTogglesOptions,from_=0,to=100,orient="horizontal",showvalue=0,variable=WhiteVar)
WhiteLevel.grid(row=0, column=9, sticky="ew")
WhiteLevel.bind("<ButtonRelease-1>", lambda e: ChangeTheme())
WhiteLevel.set(WhiteVar.get())
WhiteLevelValue = nulltk.Label(NullSuiteTogglesOptions, textvariable=WhiteVar, width=4)
WhiteLevelValue.grid(row=0, column=10, padx=5, sticky="w")
NullSuiteList = ScrollableFrame(NullSuiteChangeLogPage)
NullSuiteList.grid(row=2,column=0, sticky="ensw", columnspan=99)
NullSuiteList.rowconfigure(0,weight=1)
NullSuiteList.columnconfigure(0,weight=1)
NullSuiteListInner = NullSuiteList.Inner
NullSuiteListInner.rowconfigure(0,weight=1)
NullSuiteListInner.columnconfigure(0,weight=1)
NullSuiteLog = nulltk.LabelFrame(NullSuiteListInner, text="NullSuite Log", bg="#000000", ThemeBG= False)
NullSuiteLog.pack(fill="both", expand=True, padx=10, pady=10)

AboutNullWire = nulltk.Label(
    NullSuiteChangeLogPage,
    text="Welcome to NullSuite! A collective trashpile of applications from NullForgeStudios, for ease of use with LinuxMint!  Enjoy, This will ALWAYS be free, buuuuuuuut if you wanna donate to help it along... "
)
AboutNullWire.grid(row=3, column=0, sticky="ew", padx=5, pady=(5,0))
link = nulltk.Label(
    NullSuiteChangeLogPage,
    text="Our Ko-fi",
    fg="Blue",
    cursor="hand2",
    ThemeFG = False
)
link.grid(row=4, column=0, sticky="ew", padx=5, pady=(0,10))
link.bind("<Button-1>", lambda e: webbrowser.open_new("https://ko-fi.com/nullforgestudios"))



def HideToTray():
    global HiddenToTray
    if SystemLoading:
        return
    Root.withdraw()
    HiddenToTray = True

def Startup():
    global SystemLoading
    SystemLoading = True
    WaitForLoad()
    
def WaitForLoad():
    global ProgramCount, BaseEmoji, NullMojiAllEmojiButtons, CustomEmojis, RecentEmojis
    threading.Thread(target=StartTray, daemon=True).start()
    threading.Thread(target=WatchShowSignal, daemon=True).start()
    threading.Thread(target=NullMonitorLoop, daemon=True).start()
    threading.Thread(target=NullMidiLoop, daemon=True).start()
    threading.Thread(target=NullWireLoop, daemon=True).start()
    threading.Thread(target=SoundPlayer, daemon=True).start()
    threading.Thread(target=CymbalPlayer, daemon=True).start()
    threading.Thread(target=DrumPlayer, daemon=True).start()
    threading.Thread(target=NullGitLoop, daemon=True).start()
    threading.Thread(target=NullFocusLoop, daemon=True).start()
    threading.Thread(target=NullFocusFocusLoop, daemon=True).start()
    threading.Thread(target=NullFocusClockLoop, daemon=True).start()
    threading.Thread(target=NullFocusClipBoardLoop, daemon=True).start()
    
    LoadConfig()
    ChangeTheme()

    emojis = None
    if not os.path.isfile(BaseEmojisPath):
        Butts.set("Emoji File not found???")
        Root.update_idletasks()
        return
    try:
        with open(BaseEmojisPath, "r") as f:
            data = json.load(f)
            emojis = data.get("Emojis", [])
            ColumnCount = 3
            BaseEmoji = data.get("Emojis", [])
            for i, EmojiData in enumerate(emojis):
                Button = nulltk.Button(NullMojiAllEmojisInner,text=EmojiData["Emoji"],font=("Noto Color Emoji",15),command=lambda E=EmojiData: CopyEmoji(E), width = 4)
                Button.grid(row=i // ColumnCount,column=i % ColumnCount,padx=2,pady=2)
                NullMojiAllEmojiButtons.append(Button)
            NullMojiAllEmojisColumnList.BindMouseWheel(NullMojiMainPage)
    except Exception as e:
        Butts.set(f"ERROR LOADING EMOJIS FILE\n\n{e}")
        Root.update_idletasks()
        return False

    try:
        with open(ConfigPath, "r") as f:
            data = json.load(f)
            moji = data.get("NullMoji", {})
            CustomEmojis = moji['CustomEmoji']
            RecentEmojis = moji['RecentEmoji']
    except Exception as e:
        Butts.set(f"ERROR LOADING NULL Moji SAVE\n\n{e}")
        Root.update_idletasks()
        return False
    
    DoneLoadingCheck()

def DoneLoadingCheck():
    global SystemLoading

    if ProgramCount != LoadCompleted:
        Root.after(10, DoneLoadingCheck)
        return

    SystemLoading = False
    try:
        LoadPopup.grab_release()
    except:
        pass
    LoadPopup.destroy()
    Root.focus_force()
    

#endregion

#region NullProton
ProtonDrive = os.path.join(BaseDir, "ProtonDrive")
ProtonVars = {
    "Default": tk.StringVar(value="[ not set ]"),
    "A": tk.StringVar(value="[ not set ]"),
    "B": tk.StringVar(value="[ not set ]"),
    "Min": tk.BooleanVar(value=False),
    "Close": tk.BooleanVar(value=False)
}
ProtonGames = []
ProtonGameRows = []
LogQueue = queue.Queue()

def RefreshRowUI(RowIndex):
    State = ProtonGames[RowIndex]
    Frame = ProtonGameRows[RowIndex]
    Buttons = Frame.Buttons

    for key, btn in Buttons.items():
        if key == State.get("LastProton"):
            btn.configure(bg="#a1a1a1")
        else:
            btn.configure(bg=btn.DefaultBg)

def AddGameRow(State=None, Loading=False):
    RowIndex = len(ProtonGameRows)

    if State is None:
        State = {
            "Path": "",
            "LaunchArgs": "",
            "SteamLaunchOptions": "",
            "LastProton": "None"
        }

    GameName = os.path.splitext(os.path.basename(State["Path"]))[0] if State["Path"] else "New Game"

    Frame = nulltk.LabelFrame(ProtonGameContainer,text=GameName)
    Frame.grid(row=RowIndex,column=0,sticky="ew",pady=(5,5),padx=(0,10))

    for i in range(12):
        Frame.columnconfigure(i,weight=0)

    Frame.columnconfigure(2,weight=1)

    ProtonGameRows.append(Frame)

    if not Loading:
        ProtonGames.append(State)

    PathVar = tk.StringVar(value=State["Path"])
    LaunchArgsVar = tk.StringVar(value=State.get("LaunchArgs",""))
    SteamArgsVar = tk.StringVar(value=State.get("SteamLaunchOptions",""))

    def UpdateState(*args):
        State["LaunchArgs"] = LaunchArgsVar.get()
        State["SteamLaunchOptions"] = SteamArgsVar.get()
        if SaveTimer:
            Root.after_cancel(SaveTimer)

        SaveTimer = Root.after(3000,lambda: SaveConfig("NullProton"))

    LaunchArgsVar.trace_add("write",UpdateState)
    SteamArgsVar.trace_add("write",UpdateState)

    def UpdateTitle():
        Name = os.path.splitext(os.path.basename(State["Path"]))[0] if State["Path"] else "New Game"
        Frame.configure(text=Name)

    def RemoveSelf():
        Index = ProtonGameRows.index(Frame)

        Frame.destroy()
        ProtonGameRows.pop(Index)
        ProtonGames.pop(Index)

        SaveConfig("NullProton")

        for i, Row in enumerate(ProtonGameRows):
            Row.grid_configure(row=i)

    def Browse():
        Path = filedialog.askopenfilename(title="Select Game Executable")

        if Path:
            State["Path"] = Path
            PathVar.set(Path)
            UpdateTitle()
            SaveConfig("NullProton")

    nulltk.Button(Frame,text="Remove",width=8,command=RemoveSelf).grid(row=0,column=0,padx=3)

    ttk.Separator(Frame,orient="vertical").grid(row=0,column=1,sticky="ns",padx=5)

    nulltk.Entry(Frame,textvariable=PathVar,state="readonly").grid(row=0,column=2,padx=3,sticky="ew")

    nulltk.Button(Frame,text="Browse",width=8,command=Browse).grid(row=0,column=3,padx=3)

    ttk.Separator(Frame,orient="vertical").grid(row=0,column=4,sticky="ns",padx=5)

    Buttons = {}

    Buttons["Default"] = nulltk.Button(Frame,text="Default",width=12,command=lambda: LaunchGame(State,"Default",RowIndex))
    Buttons["Default"].grid(row=0,column=5,padx=2)
    Buttons["Default"].DefaultBg = Buttons["Default"].cget("bg")

    Buttons["A"] = nulltk.Button(Frame,text="Proton A",width=12,command=lambda: LaunchGame(State,"A",RowIndex))
    Buttons["A"].grid(row=0,column=6,padx=2)
    Buttons["A"].DefaultBg = Buttons["Default"].cget("bg")

    Buttons["B"] = nulltk.Button(Frame,text="Proton B",width=12,command=lambda: LaunchGame(State,"B",RowIndex))
    Buttons["B"].grid(row=0,column=7,padx=2)
    Buttons["B"].DefaultBg = Buttons["Default"].cget("bg")

    ttk.Separator(Frame,orient="vertical").grid(row=0,column=8,sticky="ns",padx=5)

    Buttons["Linux"] = nulltk.Button(Frame,text="Linux",width=12,command=lambda: LaunchGame(State,"Linux",RowIndex))
    Buttons["Linux"].grid(row=0,column=9,padx=2)
    Buttons["Linux"].DefaultBg = Buttons["Default"].cget("bg")

    Lowerframe = nulltk.Frame(Frame)
    Lowerframe.grid(row=1,column=0,columnspan=99,sticky="ew")
    Lowerframe.columnconfigure(0,weight=1)
    Lowerframe.columnconfigure(1,weight=1)

    LaunchArgs = nulltk.Entry(Lowerframe,textvariable=LaunchArgsVar)
    LaunchArgs.grid(row=0,column=0,padx=3,pady=(3,3),sticky="ew")

    SteamArgs = nulltk.Entry(Lowerframe,textvariable=SteamArgsVar)
    SteamArgs.grid(row=0,column=1,padx=3,pady=(3,3),sticky="ew")

    ToolTip(LaunchArgs, "You can set Launch arguments here. Such as \"-windowed\"")

    ToolTip(SteamArgs, "You can set Steam arguments here. Such as \"SteamOS=1 SteamDeck=1\"")


    Frame.Buttons = Buttons

    RefreshRowUI(RowIndex)

    if not Loading:
        SaveConfig("NullProton")

def UpdateOverlay():
    while not LogQueue.empty():
        Line = LogQueue.get()
        OverlayLabel.config(text=OverlayLabel.cget("text") + Line + "\n")
    Root.after(100, UpdateOverlay)

def ShowOverlay():
    OverlayLabel.config(text="")
    ProtonOverlay.lift()

def HideOverlay():
    ProtonOverlay.lower()

def LaunchGame(State, Mode, RowIndex):
    def Run():
        Path = State["Path"]

        if not os.path.isfile(Path):
            LogQueue.put("❌ Invalid path")
            return
        
        if Mode == "Linux":
            State["LastProton"] = Mode
            SaveConfig("NullProton")
            Root.after(0, lambda: RefreshRowUI(RowIndex))
            Root.after(0, ShowOverlay)
            LogQueue.put("🐧 Launching (Linux)...")
            Env = BuildEnv(State)
            Env.pop("SDL_VIDEO_X11_WMCLASS",None)
            Env.pop("SDL_VIDEO_X11_WMCLASS_NAME",None)
            LaunchArgs = shlex.split(State.get("LaunchArgs",""))
            try:
                subprocess.Popen([Path, *LaunchArgs],env=Env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL,start_new_session=True)
                LogQueue.put("✅ Game launched")
                time.sleep(1)
                Root.after(0, ProtonOverlay.lower)
            except Exception as e:
                LogQueue.put(f"❌ Failed: {e}")

            if ProtonVars['Min'].get():
                Root.after(0, Root.iconify)
                return

            if ProtonVars['Close'].get():
                Root.after(0, Root.destroy)
                return

            return

        ProtonPath = ProtonVars[Mode].get()
        LaunchArgs = shlex.split(State.get("LaunchArgs",""))

        if not os.path.isfile(ProtonPath):
            LogQueue.put(f"❌ Proton '{Mode}' not set")
            return

        BaseDir = os.path.dirname(os.path.abspath(__file__))
        Prefix = os.path.join(BaseDir, ProtonDrive, "Default")
        os.makedirs(Prefix, exist_ok=True)

        Env = BuildEnv(State)
        Env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = os.path.expanduser("~/.steam/steam/")
        Env["STEAM_COMPAT_DATA_PATH"] = Prefix

        Root.after(0, ShowOverlay)

        LogQueue.put("🚀 Launching...")
        LogQueue.put("Please wait...\n")

        Proc = subprocess.Popen(
            [ProtonPath, "run", Path, *LaunchArgs],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=Env
            
        )
        
        StartTime = time.time()
        LAUNCH_TIMEOUT = 10
        LastOutput = time.time()

        while True:
            if time.time() - LastOutput > 3:
                break

            if time.time() - StartTime > LAUNCH_TIMEOUT:
                break

            rlist, _, _ = select.select([Proc.stdout], [], [], 0.1)

            if rlist:
                line = Proc.stdout.readline()
                if line:
                    LogQueue.put(line.strip())
                    LastOutput = time.time()

        LogQueue.put("\n✅ Game launched")

        State["LastProton"] = Mode
        SaveConfig("NullProton")
        Root.after(0, lambda: RefreshRowUI(RowIndex))
        if ProtonVars['Min'].get():
                Root.after(0, Root.iconify)
                return

        if ProtonVars['Close'].get():
            Root.after(0, Root.destroy)
            return

        time.sleep(1)

        Root.after(0, ProtonOverlay.lower)

    threading.Thread(target=Run, daemon=True).start()

def BuildEnv(State):
    Env = os.environ.copy()

    SteamOpts = State.get("SteamLaunchOptions","")

    for Item in shlex.split(SteamOpts):
        if Item == "%command%":
            continue

        if "=" in Item:
            Key, Value = Item.split("=",1)
            Env[Key] = Value

    return Env

def MakeProtonRow(row, key, label):
    nulltk.Label(ProtonTop, text=label, anchor="w").grid(row=row, column=0, padx=3, pady=5, sticky="w")

    entry = nulltk.Entry(ProtonTop, textvariable=ProtonVars[key], state="readonly")
    entry.grid(row=row, column=1, padx=3, pady=5, sticky="ew")

    def Pick():
        Home = os.path.expanduser("~")

        Paths = [
            os.path.join(Home, ".steam/root/compatibilitytools.d"),
            os.path.join(Home, ".local/share/Steam/compatibilitytools.d")
        ]

        StartDir = next((p for p in Paths if os.path.isdir(p)), Home)

        path = filedialog.askopenfilename(
        title=f"Select Proton ({label})",
        initialdir=StartDir,
        filetypes=[("Proton Executable", "proton*"),("All Files", "*")])

        if path:
            ProtonVars[key].set(path)
            SaveConfig("NullProton")

    nulltk.Button(ProtonTop, text="Browse", command=Pick).grid(row=row, column=2, sticky="ew")

ProtonMain = nulltk.Frame(NullProton)
ProtonMain.pack(fill="both", expand=True, padx=10, pady=10)
ProtonTop = nulltk.Frame(ProtonMain)
ProtonTop.pack(fill="x")
ProtonTop.rowconfigure(0, weight=1)
ProtonTop.rowconfigure(1, weight=1)
ProtonTop.rowconfigure(2, weight=1)
ProtonTop.columnconfigure(0, weight=0)
ProtonTop.columnconfigure(1, weight=2)
ProtonTop.columnconfigure(2, weight=1)
MakeProtonRow(0, "Default", "Default Proton:")
MakeProtonRow(1, "A", "Proton A:")
MakeProtonRow(2, "B", "Proton B:")
ProtonScroll = ScrollableFrame(ProtonMain)
ProtonScroll.pack(fill="both", expand=True)
ProtonGameContainer = ProtonScroll.Inner
ProtonGameContainer.columnconfigure(0, weight=1)
nulltk.Frame(ProtonTop,height=2,bg="gray").grid(row=3,column=0,columnspan=3,sticky="ew",pady=6)
nulltk.Button(ProtonTop, text="Add Game", command=AddGameRow).grid(row=4, column=2, sticky="ew",)
checkboxframe = nulltk.Frame(ProtonTop)
checkboxframe.grid(row=4, column=1, sticky="ew")
checkboxframe.columnconfigure(0,weight=1)
checkboxframe.columnconfigure(1,weight=1)
CloseVar = tk.BooleanVar(value=ProtonVars["Close"].get())
MinVar = tk.BooleanVar(value=ProtonVars["Min"].get())
closenp = nulltk.Checkbutton(checkboxframe,text="Close To Tray",variable=ProtonVars["Close"])
closenp.grid(row=0, column=0, sticky="ew")
minimize = nulltk.Checkbutton(checkboxframe,text="Minimize On Launch",variable=ProtonVars["Min"])
minimize.grid(row=0, column=1, sticky="ew")
nulltk.Frame(ProtonTop,height=3,bg="gray").grid(row=5,column=0,columnspan=3,sticky="ew",pady=6)
ProtonVars["Close"].trace_add("write",lambda *args: SaveConfig("NullProton"))
ProtonVars["Min"].trace_add("write",lambda *args: SaveConfig("NullProton"))
ProtonOverlay = nulltk.Frame(ProtonScroll, bg="#000000", ThemeBG = False)
ProtonOverlay.place(relx=0, rely=0, relwidth=1, relheight=1)
ProtonOverlay.lower()
OverlayLabel = nulltk.Label(
    ProtonOverlay,
    text="",
    fg="white",
    bg="#000000",
    justify="left",
    anchor="nw"
)
OverlayLabel.pack(fill="both", expand=True, padx=10, pady=10)

def StartUpNullProton():
    global ProtonGames, LoadCompleted, ProtonGameRows,ActualProgramLoadedCount
   
    if NullProtonActive.get() == True:
        proton = None
        if not os.path.isfile(ConfigPath):
            Butts.set("Save File not found???")
            Root.update_idletasks()
            return False
        try:
            with open(ConfigPath, "r") as f:
                data = json.load(f)
                proton = data.get("NullProton", {})
        except Exception as e:
            Butts.set(f"ERROR LOADING NULL PROTON SAVE\n\n{e}")
            Root.update_idletasks()
            return False

        ProtonVars["Default"].set(proton.get("Default", "[ not set ]"))
        ProtonVars["A"].set(proton.get("A", "[ not set ]"))
        ProtonVars["B"].set(proton.get("B", "[ not set ]"))

        ProtonGames.clear()
        ProtonGames.extend(proton.get("Games", []))

        for row in ProtonGameRows[:]:
            row.destroy()

        ProtonGameRows.clear()


        for Game in ProtonGames.copy():
            AddGameRow(Game, True)

        Notebook.add(NullProton, text="NullProton"),
        ActualProgramLoadedCount+=1
    else:
        Notebook.forget(NullProton)


    LoadCompleted += 1
    return


#endregion

#region NullMidi
EscapeHeld = False
HeldKeys = set()
KeyBeingInput = False
KeySaving = False
MidiBeingInput = False
MidiRows = []
SaveRows = []
MidiRowObjects = []
MidiDeviceListeners = {}
UInputDevice = None
ActiveCapture = {
    "Type": None,
    "Cancel": False
}
SoundQueue = Queue()
DrumQueue = Queue()
CymbalQueue = Queue()
CymbalChannelStart = 0
CymbalChannelEnd = 149 
DrumChannelStart = 150
DrumChannelEnd = 199
KickChannelStart = 200
KickChannelEnd = 255  
LastPedalValue = 100
KickChannels = KickChannelStart
DrumChannels = DrumChannelStart
CymbalChannels = CymbalChannelStart
PreviousPedalValue = 0
HiHatPedalChoked = False
LastHiHatState = "Open"
NewHiHatState = "Open"
HiHatHitHafClosedTime = time.time()
WindowSelection = []
LoadedSounds = {}

def CancelActiveCapture():
    ActiveCapture["Cancel"] = True

def PlaySound(Data):

    global LoadedSounds

    SoundPath = Data.get("Path")
    ChannelID = Data.get("Channel")
    Volume = Data.get("Volume", 1.0)
    Loops = Data.get("Loops", 0)
    FadeIn = Data.get("FadeIn", 0)

    if SoundPath is None:
        return

    if ChannelID is None:
        return

    Sound = LoadedSounds.get(SoundPath)

    if not Sound:
        Sound = pygame.mixer.Sound(SoundPath)
        LoadedSounds[SoundPath] = Sound

    MixerChannel = pygame.mixer.Channel(ChannelID)

    MixerChannel.set_volume(Volume)

    MixerChannel.play(
        Sound,
        loops=Loops,
        fade_ms=FadeIn
    )

def SoundPlayer():

    global LoadedSounds

    while True:

        try:
            Data = SoundQueue.get()

            if not Data:
               continue

            PlaySound(Data)
        except Exception as E:
            Log(f"NullMidi: SoundPlayer Error:{E}", "Error")
            time.sleep(0.05)

def CymbalPlayer():

    global LoadedSounds

    while True:

        try:
            Data = CymbalQueue.get()

            if not Data:
               continue

            PlaySound(Data)
        except Exception as E:
            Log(f"NullMidi: SoundPlayer Error: {E}", "Error")
            time.sleep(0.05)

def DrumPlayer():

    global LoadedSounds

    while True:

        try:
            Data = DrumQueue.get()

            if not Data:
               continue

            PlaySound(Data)
        except Exception as E:
            Log(f"NullMidi: SoundPlayer Error: {E}", "Error")
            time.sleep(0.05)

def CleanupDrumChannels(Drum):

    if not Drum["Channels"]:
        return

    Alive = []

    for ChannelID in Drum["Channels"]:

        if pygame.mixer.Channel(ChannelID).get_busy():
            Alive.append(ChannelID)

    Drum["Channels"] = Alive

def BuildGlobalUInputDevice():
    global UInputDevice

    Keys = set()

    for Row in MidiRows:

        for Drum in Row.get("DrumList", []):

            for Field in [
                "CenterKeyOutput",
                "RimKeyOutput",
                "BowKeyOutput",
                "HiHatClosedKeyOutput",
                "HiHatHalfKeyOutput",
                "HiHatOpenKeyOutput",
                "HiHatBellOpenKeyOutput",
                "HiHatBellClosedKeyOutput"
            ]:

                for Key in Drum.get(Field) or []:

                    Candidate = f"KEY_{Key.upper()}"

                    if hasattr(uinput, Candidate):

                        Keys.add(
                            getattr(uinput, Candidate)
                        )

        for Controller in Row.get("ControllerList", []):
            for PageKeys in Controller.get("KeyOutputs", []):
                for Key in PageKeys:
                    Candidate = f"KEY_{Key.upper()}"
                    if hasattr(uinput, Candidate):
                        Keys.add(getattr(uinput, Candidate))

    if UInputDevice:
        UInputDevice.destroy()

    UInputDevice = uinput.Device(list(Keys))

def PressKeyCombo(Keys, Window=False, SentWindowClassName=None):
    if not Keys:
        return

    try:
        
        if not UInputDevice:
            BuildGlobalUInputDevice()

        Mapped = []

        for Key in Keys:
            Candidate = f"KEY_{Key.upper()}"

            if hasattr(uinput, Candidate):
                Mapped.append(getattr(uinput, Candidate))

        if not Mapped:
            return

        if Window and SentWindowClassName:

            SearchClass = SentWindowClassName.split(".")[-1]
            Result = subprocess.run(
                [
                    "xdotool",
                    "search",
                    "--class",
                    SearchClass
                ],
                capture_output=True,
                text=True
            )

            WindowIDs = Result.stdout.strip().splitlines()

            if not WindowIDs:
                return

            XDOMap = {
                "LEFTSHIFT": "Shift_L",
                "RIGHTSHIFT": "Shift_R",
                "LEFTCTRL": "Control_L",
                "RIGHTCTRL": "Control_R",
                "LEFTALT": "Alt_L",
                "RIGHTALT": "Alt_R"
                }

            KeyCombo = "+".join(XDOMap.get(Key, Key)for Key in Keys)

            for WindowID in WindowIDs:
                subprocess.Popen(
                    [
                        "xdotool",
                        "key",
                        "--window",
                        WindowID,
                        KeyCombo
                    ],
                    start_new_session=True
                )

            return

        for Key in Mapped[:-1]:
            UInputDevice.emit(Key, 1)

        UInputDevice.emit_click(Mapped[-1])

        for Key in Mapped[:-1]:
            UInputDevice.emit(Key, 0)

        UInputDevice.syn()

    except Exception as e:
        Log(f"NullMidi: PressKeyCombo Error: {e}", "Error")

def NormalizeKey(Key):
    Key = Key.upper()
    if "SHIFT" in Key: return "LEFTSHIFT"
    if "CONTROL" in Key: return "LEFTCTRL"
    if "ALT" in Key: return "LEFTALT"
    return Key

def SortKeys(Keys):
    Priority = {
        "LEFTSHIFT": 0,
        "RIGHTSHIFT": 0,
        "LEFTCTRL": 1,
        "RIGHTCTRL": 1,
        "LEFTALT": 2,
        "RIGHTALT": 2
    }
    return sorted(Keys, key=lambda K: (Priority.get(K, 99), K))

def FormatKeyName(Key):
    if "SHIFT" in Key: return "Shift"
    if "CTRL" in Key: return "Ctrl"
    if "ALT" in Key: return "Alt"
    return Key

def IsOnlyModifiers(Keys):
    for K in Keys:
        if not ("SHIFT" in K or "CTRL" in K or "ALT" in K):
            return False
    return True

def IsModifier(Key):
        return (
            "SHIFT" in Key
            or "CTRL" in Key
            or "ALT" in Key
            or "SUPER" in Key
        )

def SaveBinding(Target,Field,Button,Keys,Program, Page):
        global HeldKeys, KeyBeingInput, KeySaving
        if Page is None:
            Target[Field] = Keys
        else:
            Target[Field][Page] = Keys
        Button.config(text="+".join(FormatKeyName(K)for K in Keys) if Keys else "Set Key")
        BuildGlobalUInputDevice()
        SaveConfig(Program)
        FinishKeyInput()
 
def FinishKeyInput():
    global KeyBeingInput, HeldKeys, KeySaving

    KeyBeingInput = False
    KeySaving = False
    HeldKeys.clear()

    Root.unbind("<KeyPress>")
    Root.unbind("<KeyRelease>")

def DetectKey(Button, Target, Field, Program, Page=None, Timeout=4):
    global KeyBeingInput, EscapeHeld, HeldKeys
    if KeyBeingInput or KeySaving:
        return
    else:
        KeyBeingInput = True

    EndTime = time.time() + Timeout
    Button.config(text=f"Waiting... {Timeout}")

    def Tick():
        global KeyBeingInput, EscapeHeld, HeldKeys, KeySaving

        if KeyBeingInput == False:
            return

        Remaining = int(EndTime - time.time())
        if Remaining <= 0:
            if HeldKeys: #This is so it saves modifiers. 
                if EscapeHeld:
                    Button.config(text="Set Key")
                    SaveBinding(Target,Field,Button,[],Program, Page)
                else:
                    SaveBinding(Target,Field,Button,SortKeys(HeldKeys),Program,Page)
            else:
                SaveBinding(Target,Field,Button,[],Program,Page)
            return
        
        if not HeldKeys:
            Button.config(text=f"Waiting... {Remaining}")
        elif IsOnlyModifiers(HeldKeys):
            Button.config(text=f"Holding... {Remaining}")
        else:
            SaveBinding(Target,Field,Button,SortKeys(HeldKeys),Program,Page)

        Root.after(25, Tick)

    def OnPress(Event):
        global EscapeHeld,  HeldKeys
        Key = NormalizeKey(Event.keysym)
        if Key == "ESCAPE":
            EscapeHeld = True
            Root.after(1000,lambda: (SaveBinding(Target,Field,Button,[],Program,Page)) if EscapeHeld else None)
            return
        
        if IsModifier(Key):
            HeldKeys.add(Key)
        else:
            ModifierKeys = {K for K in HeldKeys if IsModifier(K)}
            HeldKeys.clear()
            HeldKeys.update(ModifierKeys)
            HeldKeys.add(Key)
            SaveBinding(Target,Field,Button,SortKeys(HeldKeys),Program,Page)
        
            

    def OnRelease(Event):
        global EscapeHeld
        Key = NormalizeKey(Event.keysym)
        if Key == "ESCAPE":
            EscapeHeld = False

    Root.bind("<KeyPress>", OnPress)
    Root.bind("<KeyRelease>", OnRelease)
    Tick()

def StartMidiListener(Device):

    if Device in MidiDeviceListeners:
        return

    Running = True

    def MidiListener():

        try:
            Port = mido.open_input(Device)

        except Exception as E:
            Log(f"NullMidi: ❌ Failed To Open MIDI Device: {Device}, \n {E}")
            return

        MidiDeviceListeners[Device]["Port"] = Port

        Log(f"NullMidi: Successfully Started MIDI Listener for {Device}")

        while True:
            ListenerData = MidiDeviceListeners.get(Device)

            if not ListenerData:
                break

            if not ListenerData["Running"]:
                break

            try:
                for Message in Port:

                    HandleMidiMessage(Device, Message)

            except Exception as E:
                Log(f"❌ MIDI Runtime Error ({Device})", "Error")
                Log(E)
                break

        try:
            Port.close()
        except:
            pass

        Log(f"NullMidi: Successfully Closed MIDI Listener for {Device}")

    Thread = threading.Thread(target=MidiListener, daemon=True)

    MidiDeviceListeners[Device] = {
        "Thread": Thread,
        "Port": None,
        "Running": Running
    }

    Thread.start()

def StopMidiListener(Device):

    if Device not in MidiDeviceListeners:
        return

    MidiDeviceListeners[Device]["Running"] = False

    Port = MidiDeviceListeners[Device].get("Port")

    if Port:
        try:
            Port.close()
        except:
            pass

    del MidiDeviceListeners[Device]

    Log(f"NullMidi: Successfully Closed MIDI Listener for {Device}")

def GetMidiController(Row, Note):
    if Note == Row['PageUpMidi']:
        return "PageUp"
    elif Note == Row['PageDownMidi']:
        return "PageDown"
    else:
        for Controller in Row['ControllerList']:
            if Controller['MidiInput'] == Note:
                return Controller
    return

def HandleMidiMessage(Device, msg):
    global LastPedalValue, PreviousPedalValue, HiHatPedalChoked, LastHiHatState, NewHiHatState, HiHatHitHafClosedTime
    for Row in MidiRows:
        if not Row.get("Active"):
            continue

        if Row.get("Device") != Device:
            continue

        DrumInput = None
        ControllerInput = None
        KeyboardInput = None

        try:
            if Row['Controller']:
                ControllerInput = GetMidiController(Row, msg.note)

                if ControllerInput == "PageUp":
                    if msg.type == "note_on":
                        ControllerPageHandler(Row,"Up")
                        continue
                elif ControllerInput == "PageDown":
                    if msg.type == "note_on":
                        ControllerPageHandler(Row,"Down")
                        continue
                else:
                    if not ControllerInput:
                        Log("NullMidi: It's set as a controller...but its not controller.")
                        continue
            elif Row['Keyboard']:
                continue




            if msg.type == "control_change":
                if Row['Drums']:
                    if msg.control == 4:
                        PreviousPedalValue = LastPedalValue
                        LastPedalValue = msg.value
                        for Drum in Row['DrumList']:
                            if not Drum['Hihat']:
                                continue
                            if not HiHatPedalChoked:
                                if (PreviousPedalValue < Drum['HiHatClosedThreshold']and LastPedalValue >= Drum['HiHatClosedThreshold']):
                                    HiHatPedalChoked = True
                                    for ChannelID in Drum['Channels']:
                                        pygame.mixer.Channel(ChannelID).fadeout(50)
                                    Drum['Channels'].clear()
                            else:
                                if (LastPedalValue <= Drum['HiHatClosedThreshold'] -10):
                                     HiHatPedalChoked = False

                            if PreviousPedalValue <= Drum['HiHatOpenThreshold']:
                                LastHiHatState = "Open"
                            elif PreviousPedalValue > Drum['HiHatOpenThreshold'] and LastPedalValue < Drum['HiHatClosedThreshold']:
                                LastHiHatState = "Half"
                            elif PreviousPedalValue >= Drum['HiHatClosedThreshold']:
                                LastHiHatState = "Closed"
                            
                            if LastPedalValue <= Drum['HiHatOpenThreshold']:
                                NewHiHatState = "Open"
                            elif LastPedalValue > Drum['HiHatOpenThreshold'] and LastPedalValue < Drum['HiHatClosedThreshold']:
                                NewHiHatState = "Half"
                            elif LastPedalValue >= Drum['HiHatClosedThreshold']:
                                NewHiHatState = "Closed"

                            
                            if LastHiHatState in ['Closed', 'Half'] and NewHiHatState == "Open":
                                if (time.time() - HiHatHitHafClosedTime) <= Drum['HiHatOpenTime'] /1000:
                                    for ChannelID in Drum['Channels']:
                                        pygame.mixer.Channel(ChannelID).fadeout(50)
                                    Drum['Channels'].clear()
                                    UseThisChannel = GetPlaybackChannel("Hihat")
                                    Drum['Channels'].append(UseThisChannel)

                                    CymbalQueue.put({
                                    "Owner": Drum,
                                    "Channel": UseThisChannel,
                                    "Path": Drum['HiHatOpenPath'],
                                    "Volume": Drum['HiHatOpenVolume'] / 100,
                                    "FadeIn": Drum['HiHatFadeIn']
                                    })
                                    LastHiHatState = NewHiHatState
                        continue
                elif Row['Keyboard']:
                    continue
                else:
                    continue

            if msg.type == "polytouch":
                if Row['Drums']:
                    Drum = ResolveDrumChoke(
                        Row,
                        msg.note
                    )
                    if not Drum:
                        continue
                    for ChannelID in Drum['Channels']:
                        pygame.mixer.Channel(ChannelID).fadeout(50)
                    Drum['Channels'].clear()
                    continue

                elif Row['Keyboard']:
                    continue

                elif Row['Controller']:
                    continue
                else:
                    continue

            if msg.type == "note_on" and msg.velocity >= 1:
                if Row['Drums']:
                    DrumInput = ResolveDrum(Row,msg.note)
                    if not DrumInput:
                        continue

                    if Row['SendKeys']:
                        PressKeyCombo(DrumInput["Keys"])

                    if not Row['Mute']:
                        if DrumInput['Type'] == "Hihat":
                            if msg.note in [DrumInput['HiHatClosedMidiInput'], DrumInput['HiHatHalfMidiInput'], DrumInput['HiHatBellClosedMidiInput']]:
                                HiHatHitHafClosedTime = time.time()
                            if msg.note == DrumInput['HiHatStompMidiInput']:
                                for ChannelID in DrumInput['Channels']:
                                    pygame.mixer.Channel(ChannelID).fadeout(50)
                                DrumInput['Channels'].clear()
                        
                        Velocity = msg.velocity
                        NormalizedVolume = 100
                        MinVolume = 0
                        MaxVolume = 100

                        if DrumInput['Kick']:
                            if Velocity < DrumInput['KickDrumVelocityMin']:
                                Velocity = DrumInput['KickDrumVelocityMin']

                        if Velocity <= DrumInput['GNThresh']:
                            if Row['DynamicVolume']:
                                MaxVolume = Row['GhostNoteVolume'] / 100
                                NormalizedVolume = (Velocity / 127) * MaxVolume
                            else:
                                NormalizedVolume = (Row['GhostNoteVolume'] / 100)

                        elif Velocity >= DrumInput['SlamThresh']:
                            if Row['DynamicVolume']:
                                MinVolume = (Row['SlamNoteVolume']/100)
                                NormalizedVolume = (
                                    MinVolume + ((Velocity /127)) * (1.0 - MinVolume))
                            else:
                                NormalizedVolume = (Row['SlamNoteVolume'] / 100)

                        else:
                            if Row['DynamicVolume']:
                                NormalizedVolume = Velocity / 127
                            else:
                                NormalizedVolume = 1.0

                        NormalizedVolume *= (DrumInput['Volume'] / 100)

                        CleanupDrumChannels(DrumInput['Drum'])

                        UseThisChannel = GetPlaybackChannel(DrumInput['Type'])

                        DrumInput["Channels"].append(
                            UseThisChannel
                        )

                        if DrumInput['Cymbal'] or DrumInput['Hihat']:

                            CymbalQueue.put({

                            "Owner": DrumInput['Drum'],
                            "Channel": UseThisChannel,
                            "Path": DrumInput['SoundPath'],
                            "Volume": NormalizedVolume,
                            "FadeIn": 0
                            })
                        else:
                            DrumQueue.put({

                            "Owner": DrumInput['Drum'],
                            "Channel": UseThisChannel,
                            "Path": DrumInput['SoundPath'],
                            "Volume": NormalizedVolume,
                            "FadeIn": 0
                            })

                    continue

                elif Row['Keyboard']:
                    continue

                elif Row['Controller']:


                    Page = Row['ControllerPage'] -1
                    if ControllerInput['KeyOrAction'][Page]  == False:
                        PressKeyCombo(ControllerInput["KeyOutputs"][Page], ControllerInput['WindowSpecific'][Page] , ControllerInput['WindowClassName'][Page] )
                    elif ControllerInput['KeyOrAction'][Page] == True: 
                        if ControllerInput['FileOrCustom'][Page]  == False:
                            threading.Thread(target=MidiFileOpen,args=(ControllerInput['StartFilePath'][Page],),daemon=True).start()
                        elif ControllerInput['FileOrCustom'][Page]  == True:
                            threading.Thread(target=MidiCustomRun,args=(ControllerInput['CustomCommand'][Page],),daemon=True).start()
                    continue

                else:
                    continue

        except Exception as E:

            Log(f"NullMidi: HandleMidiMessage Error: {E}", "Error")

def GetPorts(CurrentRow=None):
    try:
        RawPorts = mido.get_input_names()
    except Exception:
        RawPorts = []

    IgnoreKeywords = (
        "Virtual",
        "LoopMIDI",
        "Through",
        "Midi Through",
        "Monitor"
    )

    UsedPorts = set()

    for Row in MidiRows:

        if Row is CurrentRow:
            continue

        Device = Row.get("Device")

        if Device and Device != "None":
            UsedPorts.add(Device)

    ValidPorts = ["None"]

    for Port in RawPorts:

        if any(K in Port for K in IgnoreKeywords):
            continue

        if Port in UsedPorts:
            continue

        if Port not in ValidPorts:
            ValidPorts.append(Port)

    CurrentDevice = CurrentRow.get("Device")

    if (
        CurrentDevice
        and CurrentDevice not in ValidPorts
    ):
        ValidPorts.append(CurrentDevice)

    return ValidPorts

def DetectNote(Button, Device, Target, Field, AllowCC=False, Timeout=4):
    global MidiBeingInput

    if MidiBeingInput:
        return

    CancelActiveCapture()
    ActiveCapture["Cancel"] = False
    Button.config(text=f"Hold ESC to clear {Timeout-1}")
    EscapeHeld = [False]
    EndTime = time.time() + (Timeout - 1)

    try:
        Port = mido.open_input(Device)
    except:
        Button.config(text="Error")
        return

    def Cleanup():
        global MidiBeingInput
        try:
            Port.close()
        except:
            pass
        MidiBeingInput = False
        Root.unbind("<KeyPress>")
        Root.unbind("<KeyRelease>")

    def ClearBinding():
        if not EscapeHeld[0]:
            return
        Target[Field] = None
        Button.config(text="Set Midi")
        SaveConfig("NullMidi")
        Cleanup()

    def OnPress(Event):
        Key = NormalizeKey(Event.keysym)
        if Key == "ESCAPE":
            if not EscapeHeld[0]:
                EscapeHeld[0] = True
                Root.after(1000, ClearBinding)

    def OnRelease(Event):
        Key = NormalizeKey(Event.keysym)
        if Key == "ESCAPE":
            EscapeHeld[0] = False

    def Tick():
        if ActiveCapture["Cancel"]:
            Cleanup()
            return
        Remaining = int(EndTime - time.time())
        if Remaining <= 0:
            Button.config(text="Set Midi")
            Cleanup()
            return
        Button.config(text=f"Hold ESC to clear - {Remaining}")

        for Msg in Port.iter_pending():
            if Msg.type == "note_on":
                Target[Field] = Msg.note
                Button.config(text=f"{Msg.note}")
                SaveConfig("NullMidi")
                Cleanup()
                return
            elif Msg.type == "control_change" and AllowCC:
                Target[Field] = Msg.control
                Button.config(text=f"{Msg.control}")
                SaveConfig("NullMidi")
                Cleanup()
                return
            elif Msg.type == "polytouch":
                Target[Field] = Msg.note
                Button.config(text=f"{Msg.note}")
                SaveConfig("NullMidi")
                Cleanup()
                return
        Root.after(3, Tick)
    Root.bind("<KeyPress>", OnPress)
    Root.bind("<KeyRelease>", OnRelease)
    MidiBeingInput = True
    Tick()

def ResolveDrum(Row, Note):
    for Drum in Row['DrumList']:

        if Drum['Kick']:
            DrumType = "Kick"
        elif Drum['Cymbal']:
            DrumType = "Cymbal"
        elif Drum['Hihat']:
            DrumType = "Hihat"
        else:
            DrumType = "Drum"

        Match = {
            "Drum": Drum,
            "Channels": Drum['Channels'],
            "Keys": [],

            "Kick": Drum['Kick'],
            "DrumType": Drum['Drum'],
            "Cymbal": Drum['Cymbal'],
            "Hihat": Drum['Hihat'],

            "Type": DrumType,

            "SoundPath": None,
            "Volume": 100,

            "GNThresh": -1,
            "SlamThresh": 130,

            "KickDrumVelocityMin": Drum['KickDrumMinimumVelocity'],

            "HiHatClosedMidiInput": Drum['HiHatClosedMidiInput'],
            "HiHatHalfMidiInput": Drum['HiHatHalfMidiInput'],
            "HiHatOpenMidiInput": Drum['HiHatOpenMidiInput'],
            "HiHatStompMidiInput": Drum['HiHatStompMidiInput'],
            "HiHatBellOpenMidiInput": Drum['HiHatBellOpenMidiInput'],
            "HiHatBellClosedMidiInput": Drum['HiHatBellClosedMidiInput'],
        }

        # --------------------------------------------------
        # HIHAT
        # --------------------------------------------------

        if Drum['Hihat']:

            if LastPedalValue >= Drum['HiHatClosedThreshold']:
                HiHatState = "Closed"
            elif LastPedalValue <= Drum['HiHatOpenThreshold']:
                HiHatState = "Open"
            else:
                HiHatState = "Half"

            if HiHatState == "Closed":
                if Note == Drum['HiHatClosedMidiInput']:
                    Match["SoundPath"] = Drum['HiHatClosedPath']
                    Match["Volume"] = Drum['HiHatClosedVolume']
                    Match["Keys"] = Drum['HiHatClosedKeyOutput']
                    return Match

                elif Note == Drum['HiHatBellClosedMidiInput']:
                    Match["SoundPath"] = Drum['HiHatBellClosedPath']
                    Match["Volume"] = Drum['HiHatBellClosedVolume']
                    Match["Keys"] = Drum['HiHatBellClosedKeyOutput']
                    return Match

                elif Note == Drum['HiHatBellOpenMidiInput']:
                    Match["SoundPath"] = Drum['HiHatBellClosedPath']
                    Match["Volume"] = Drum['HiHatBellClosedVolume']
                    Match["Keys"] = Drum['HiHatBellClosedKeyOutput']
                    return Match

                elif Note == Drum['HiHatStompMidiInput']:
                    Match["SoundPath"] = Drum['HiHatStompPath']
                    Match["Volume"] = Drum['HiHatStompVolume']
                    Match["Keys"] = Drum['HiHatStompKeyOutput']
                    return Match

                elif Note == Drum['HiHatHalfMidiInput']:
                    Match["SoundPath"] = Drum['HiHatClosedPath']
                    Match["Volume"] = Drum['HiHatClosedVolume']
                    Match["Keys"] = Drum['HiHatClosedKeyOutput']
                    return Match


            elif HiHatState == "Half":

                if Note == Drum['HiHatHalfMidiInput']:
                    Match["SoundPath"] = Drum['HiHatHalfPath']
                    Match["Volume"] = Drum['HiHatHalfVolume']
                    Match["Keys"] = Drum['HiHatHalfKeyOutput']
                    return Match

                elif Note == Drum['HiHatBellOpenMidiInput']:
                    Match["SoundPath"] = Drum['HiHatHalfPath']
                    Match["Volume"] = Drum['HiHatHalfVolume']
                    Match["Keys"] = Drum['HiHatHalfKeyOutput']
                    return Match

            else:

                if Note == Drum['HiHatOpenMidiInput']:
                    Match["SoundPath"] = Drum['HiHatOpenPath']
                    Match["Volume"] = Drum['HiHatOpenVolume']
                    Match["Keys"] = Drum['HiHatOpenKeyOutput']
                    return Match

                elif Note == Drum['HiHatBellOpenMidiInput']:
                    Match["SoundPath"] = Drum['HiHatBellOpenPath']
                    Match["Volume"] = Drum['HiHatBellOpenVolume']
                    Match["Keys"] = Drum['HiHatBellOpenKeyOutput']
                    return Match

        # --------------------------------------------------
        # CENTER
        # --------------------------------------------------

        elif Note == Drum['CenterMidiInput']:
            Match["SoundPath"] = Drum['CenterSoundFilePath']
            Match["Volume"] = Drum['CenterVolume']
            Match["GNThresh"] = Drum['CenterGhostNoteThreshold']
            Match["SlamThresh"] = Drum['CenterSlamNoteThreshold']
            Match["Keys"] = Drum['CenterKeyOutput']
            return Match

        # --------------------------------------------------
        # RIM
        # --------------------------------------------------

        elif Note == Drum['RimMidiInput']:
            Match["SoundPath"] = Drum['RimSoundFilePath']
            Match["Volume"] = Drum['RimVolume']
            Match["GNThresh"] = Drum['RimGhostNoteThreshold']
            Match["SlamThresh"] = Drum['RimSlamNoteThreshold']
            Match["Keys"] = Drum['RimKeyOutput']
            return Match

        # --------------------------------------------------
        # BOW
        # --------------------------------------------------

        elif Note == Drum['BowMidiInput']:
            Match["SoundPath"] = Drum['BowSoundFilePath']
            Match["Volume"] = Drum['BowVolume']
            Match["GNThresh"] = Drum['BowGhostNoteThreshold']
            Match["SlamThresh"] = Drum['BowSlamNoteThreshold']
            Match["Keys"] = Drum['BowKeyOutput']
            return Match

    return None

def GetPlaybackChannel(DrumType):

    global CymbalChannels
    global DrumChannels
    global KickChannels

    # ==============================
    # Cymbal / HiHat Pool
    # ==============================
    if DrumType in ["Hihat", "Cymbal"]:

        StartChannel = CymbalChannels

        while True:

            Channel = pygame.mixer.Channel(CymbalChannels)
            if not Channel.get_busy():

                UseChannel = CymbalChannels

                CymbalChannels += 1

                if CymbalChannels > CymbalChannelEnd:
                    CymbalChannels = CymbalChannelStart

                return UseChannel

            CymbalChannels += 1

            if CymbalChannels > CymbalChannelEnd:
                CymbalChannels = CymbalChannelStart

            if CymbalChannels == StartChannel:
                break

    elif DrumType == "Kick":
        StartChannel = KickChannels

        while True:
            Channel = pygame.mixer.Channel(KickChannels)
            if not Channel.get_busy():

                UseChannel = KickChannels

                KickChannels += 1

                if KickChannels > KickChannelEnd:
                    KickChannels = KickChannelStart

                return UseChannel

            KickChannels += 1

            if KickChannels > KickChannelEnd:
                KickChannels = KickChannelStart

            if KickChannels == StartChannel:
                break

    # ==============================
    # Drum Pool
    # ==============================
    else:

        StartChannel = DrumChannels
        while True:
            Channel = pygame.mixer.Channel(DrumChannels)

            if not Channel.get_busy():

                UseChannel = DrumChannels

                DrumChannels += 1

                if DrumChannels > DrumChannelEnd:
                    DrumChannels = DrumChannelStart

                return UseChannel

            DrumChannels += 1

            if DrumChannels > DrumChannelEnd:
                DrumChannels = DrumChannelStart

            if DrumChannels == StartChannel:
                break

    return UseChannel

def CreateVirtualPort(Row):
    Name = f"NullMidiVirtualPort{len(MidiRows)+1:02d}"
    try:
        Port = mido.open_output(Name, virtual=True)
        Row["VirtualPortName"] = Name
        Row["VirtualPort"] = Port
    except Exception as E:
        Log(f"NullMidi: Failed To Create Virtual Port {E} — Midi device wont work")
        Row["VirtualPortName"] = None
        Row["VirtualPort"] = None

def DestroyVirtualPort(Row):
    try:
        if Row.get("VirtualPort"):
            Row["VirtualPort"].close()
    except Exception as e:
        Log(f"NullMidi: Couldn't Destroy Virtual Port: {e}")
    Row["VirtualPort"] = None
    Row["VirtualPortName"] = None

def ResolveDrumChoke(Row, Note):

    for Drum in Row['DrumList']:
        if Drum['Hihat']:

            if Drum['HiHatBellOpenMidiInput'] == Note:
                return Drum
            elif Drum['HiHatBellClosedMidiInput'] == Note:
                return Drum

            elif Drum['HiHatOpenMidiInput'] == Note:
                return Drum

            elif Drum['HiHatHalfMidiInput'] == Note:
                return Drum

            elif Drum['HiHatClosedMidiInput'] == Note:
                return Drum
            
        if Drum['Cymbal']:
            if Drum['BowMidiInput'] == Note:
                return Drum
            elif Drum['CenterMidiInput'] == Note:
                return Drum
            elif Drum['RimMidiInput'] == Note:
                return Drum

    return None

def MidiCustomRun(Command):
    subprocess.Popen(shlex.split(Command),start_new_session=True)
    return

def MidiFileOpen(Path):
    try:
        subprocess.Popen(
            ["xdg-open", Path],
            start_new_session=True
        )
    except Exception as e:
        Log(f"NullMidi: Couldn't Open File Because: {e}")
    return

def ControllerPageHandler(Row, Which):
        if Which=="Up":
            if Row['ControllerPage'] == 99:
                return
            else:
                Row['ControllerPage'] += 1

        elif Which == "Down":
            if Row['ControllerPage'] == 1:
                return
            else:
                Row['ControllerPage'] -= 1

        Row['ControllerPageVar'].set(Row['ControllerPage'])
        SaveConfig("NullMidi")

        try:
            if Row['OutputPort'] == None:
                Row['OutputPort'] = mido.open_output(Row['Device'])
            Row['OutputPort'].send(mido.Message("program_change",program=Row['ControllerPage']))
        except Exception as E:
            Log(f"Uhhhh Controller didn't change page?:{E}")

def SearchForSoundFile(Drum, var, Field):
        path = filedialog.askopenfilename(
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if not path:
            return
        
        Drum[Field] = path
        var.set(path)

        SaveConfig("NullMidi")

def SearchForAnyFile(Controller, var, Field, Page=None):
        path = filedialog.askopenfilename(
            filetypes=[("All files", "*.*")]
        )
        if not path:
            return
        
        if Page != None:
            Controller[Field][Page] = path
        else:
            Controller[Field] = path
        
        var.set(path)

        SaveConfig("NullMidi")

def AddMidiRow(Row=None, Loading=False):
    global MidiRows, DeleteDeviceConfirmation, DeleteDeviceRowConfirmation, MidiRowObjects
    Frame = nulltk.Frame(MidiContainer)
    Frame.pack(fill="x", expand=False, padx=5, pady=5)
    Frame.columnconfigure(0, weight=1)
    Frame.rowconfigure(0, weight=1)
    
   
    if Row is None:
        Row = {}
        Row['Index'] = len(MidiRows) -1
        Row['Device'] = None
        Row['SendKeys'] = True
        Row['Controller'] = False
        Row['ControllerPage'] = 1
        Row['PageUpMidi'] = None
        Row['PageDownMidi'] = None
        Row['Drums'] = False
        Row['Keyboard'] = False
        Row['Active'] = True
        Row['Mute'] = True
        Row['RowCollapsed'] = False
        Row['RowName'] = ""
        Row['DrumList'] = []
        Row['KeyboardList'] = []
        Row['ControllerList'] = []
        Row['GhostNoteVolume'] = 10
        Row['SlamNoteVolume'] = 100
        Row['DynamicVolume'] = True
        Row['DeleteConfirmation'] = False
        Row['OutputPort'] = None

    ControllerRowPage = tk.IntVar(value=Row.get("ControllerPage",False))
    Row['ControllerPageVar'] = ControllerRowPage
    
    if 'OutputPort' not in Row:
        Row['OutputPort'] = None

    if 'ControllerPageVar' not in Row:
        Row['ControllerPageVar'] = tk.IntVar(value=Row['ControllerPage'])

    


    CreateVirtualPort(Row)

    # --- Togglerow before any selection
    TogglesRow = nulltk.Frame(Frame)
    TogglesRow.pack(fill="x", padx=5, pady=5)
    TogglesRow.columnconfigure(0, weight=1)
    TogglesRow.columnconfigure(1, weight=1)
    TogglesRow.columnconfigure(2, weight=1)
    TogglesRow.columnconfigure(3, weight=1)
    TogglesRow.columnconfigure(4, weight=1)
    

    TogglesRowAlwaysFalseControllerVar = tk.BooleanVar(value=False)
    TogglesRowAlwaysFalseDrumVar = tk.BooleanVar(value=False)
    TogglesRowAlwaysFalseKeyboardVar = tk.BooleanVar(value=False)

    ControllerToggle = nulltk.Checkbutton(TogglesRow, text="Controller", variable=TogglesRowAlwaysFalseControllerVar, command=lambda: HideToggleRowShowOtherRow("Controller"),)
    ControllerToggle.grid(row=0, column=0, sticky="ew", padx=2)
    DrumsToggle = nulltk.Checkbutton(TogglesRow, text="Drums", variable=TogglesRowAlwaysFalseDrumVar, command=lambda: HideToggleRowShowOtherRow("Drums"))
    DrumsToggle.grid(row=0, column=1, sticky="ew", padx=2)
    KeyboardToggle = nulltk.Checkbutton(TogglesRow, text="Keyboard", variable=TogglesRowAlwaysFalseKeyboardVar, command=lambda: HideToggleRowShowOtherRow("Keyboard"))
    KeyboardToggle.grid(row=0, column=2, sticky="ew", padx=2)
    ToggleRowDelete = nulltk.Button(TogglesRow, text="Delete Device", command=lambda:RemoveMidiRow(Frame, Row,ToggleRowDelete))
    ToggleRowDelete.grid(row=0, column=4, sticky="ew", padx=2)
    #----------------------
    
    BasicTopRow = nulltk.Frame(Frame)
    BasicTopRow.pack(fill="x", padx=5, pady=5)
    BasicTopRow.columnconfigure(0, weight=0)
    BasicTopRow.columnconfigure(1, weight=0)
    BasicTopRow.columnconfigure(2, weight=0)
    BasicTopRow.columnconfigure(3, weight=0)
    BasicTopRow.columnconfigure(4, weight=0)
    BasicTopRow.columnconfigure(5, weight=0)
    BasicTopRow.columnconfigure(6, weight=0)
    BasicTopRow.columnconfigure(7, weight=0)
    BasicTopRow.columnconfigure(8, weight=0)
    BasicTopRow.columnconfigure(9, weight=0)
    BasicTopRow.columnconfigure(10, weight=1)
    BasicTopRow.columnconfigure(11, weight=0)
    BasicTopRow.rowconfigure(0, weight=0)
    
    ControllerRow = nulltk.Frame(Frame)
    ControllerRow.pack(fill="both", expand=True, padx=5, pady=5)
    ControllerRow.rowconfigure(0, weight=0)
    ControllerRow.rowconfigure(1, weight=0)
    ControllerRow.columnconfigure(0, weight=0)
    ControllerRow.columnconfigure(1, weight=0)
    ControllerRow.columnconfigure(2, weight=0)
    ControllerRow.columnconfigure(3, weight=0)
    ControllerRow.columnconfigure(4, weight=0)
    ControllerRow.columnconfigure(5, weight=0)
    ControllerRow.columnconfigure(6, weight=0)
    ControllerRow.columnconfigure(7, weight=0)
    ControllerRow.columnconfigure(8, weight=0)
    ControllerRow.columnconfigure(9, weight=0)
    ControllerRow.columnconfigure(10, weight=0)
    ControllerRow.columnconfigure(11, weight=1)
    ControllerRow.pack_forget()

    DrumRow = nulltk.Frame(Frame)
    DrumRow.pack(fill="x", expand=False, padx=5, pady=5)
    DrumRow.columnconfigure(0, weight=0)
    DrumRow.columnconfigure(1, weight=1)
    DrumRow.columnconfigure(2, weight=0)
    DrumRow.columnconfigure(3, weight=0)
    DrumRow.columnconfigure(4, weight=0)
    DrumRow.columnconfigure(5, weight=1)
    DrumRow.columnconfigure(6, weight=0)
    DrumRow.columnconfigure(7, weight=0)
    DrumRow.columnconfigure(8, weight=0)
    DrumRow.rowconfigure(0,weight=1)
    DrumRow.rowconfigure(1,weight=0)
    DrumRow.rowconfigure(2,weight=0,)
    DrumRow.pack_forget()

    KeyboardRow = nulltk.Frame(Frame)
    KeyboardRow.pack(fill="x", padx=5, pady=5)
    nulltk.Label(KeyboardRow, text="Keyboard has been redacted, Just go here lol: ").pack(fill="x", padx=5, pady=5)
    pianist = nulltk.Label(KeyboardRow,text="https://www.onlinepianist.com/virtual-piano",fg="blue",cursor="hand2")
    pianist.pack(fill="x", padx=5, pady=5)
    pianist.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.onlinepianist.com/virtual-piano"))
    
    KeyboardRow.pack_forget()


    TopRowAlwaysTrueControllerRowVar = tk.BooleanVar(value=True)
    TopRowAlwaysTrueDrumRowVar = tk.BooleanVar(value=True)
    TopRowAlwaysTrueKeyboardRowVar = tk.BooleanVar(value=True)

    ActiveMidiDevice = tk.BooleanVar(value=Row.get("Active", True))
    MuteMidiDevice = tk.BooleanVar(value=Row.get("Mute", True))
    RowName = tk.StringVar(value=Row.get("RowName", ""))
    DynamicVolumeCheck = tk.BooleanVar(value=Row.get("DynamicVolume", True))
    SendKeysVar = tk.BooleanVar(value=Row.get("SendKeys", True))

    SoundWidgets = {}

    def CollapseRow(Row, Loading=False):
        if Loading:
            DrumRow.pack_forget()
            ControllerRow.pack_forget()
            KeyboardRow.pack_forget()
            if Row["RowCollapsed"]:
                BasicTopRowCollapseButton.config(text="▶")
            else:
                BasicTopRowCollapseButton.config(text="▼")
                if Row["Drums"]:
                    DrumRow.pack(fill="x", expand=False, padx=5, pady=5)
                elif Row["Controller"]:
                    ControllerRow.pack(fill="x", padx=5, pady=5)
                elif Row["Keyboard"]:
                    KeyboardRow.pack(fill="x", padx=5, pady=5)
            return

        if Row["RowCollapsed"]:
            BasicTopRowCollapseButton.config(text="▼")
            if Row["Drums"]:
                DrumRow.pack(fill="both", expand=True, padx=5, pady=5)
            elif Row["Controller"]:
                ControllerRow.pack(fill="x", padx=5, pady=5)
            elif Row["Keyboard"]:
                KeyboardRow.pack(fill="x", padx=5, pady=5)
            Row["RowCollapsed"] = False
        else:
            DrumRow.pack_forget()
            ControllerRow.pack_forget()
            KeyboardRow.pack_forget()
            BasicTopRowCollapseButton.config(text="▶")
            Row["RowCollapsed"] = True
        SaveConfig("NullMidi")
            
    def HideBasictopRow():
        TogglesRowAlwaysFalseControllerVar.set(False)
        TogglesRowAlwaysFalseDrumVar.set(False)
        TogglesRowAlwaysFalseKeyboardVar.set(False)
        TopRowAlwaysTrueControllerRowVar.set(True)
        TopRowAlwaysTrueDrumRowVar.set(True)
        TopRowAlwaysTrueKeyboardRowVar.set(True)
        Row['Controller'] = False
        Row['Drums'] = False
        Row['Keyboard'] = False
        BasicTopRow.pack_forget()
        ControllerRow.pack_forget()
        DrumRow.pack_forget()
        KeyboardRow.pack_forget()
        BasicTopRowControllerToggle.grid_remove()
        BasicTopRowDrumToggle.grid_remove()
        BasicTopRowKeyboardToggle.grid_remove()
        TogglesRow.pack(fill="x", padx=5, pady=5)

    def UpdateActiveState():
        Row["Active"] = ActiveMidiDevice.get()
        SaveConfig("NullMidi")

    def UpdateMuted():
        Row["Mute"] = MuteMidiDevice.get()

        if Row['Mute']:
            for widget in SoundWidgets.keys():
                widget.grid_forget()
        else:
            for widget, data in SoundWidgets.items():
                widget.grid(row=data['row'],column=data['column'],sticky=data['sticky'],padx=data['padx'],pady=data['pady'])

        SaveConfig("NullMidi")

    def UpdateDynamics():
        Row["DynamicVolume"] = DynamicVolumeCheck.get()
        SaveConfig("NullMidi")

    def UpdateKeyInputs():
        Row["SendKeys"] = SendKeysVar.get()
        SaveConfig("NullMidi")

    BasicTopRowCollapseButton = nulltk.Button(BasicTopRow, text="▼", command=lambda:CollapseRow(Row, False), width = 2)
    BasicTopRowCollapseButton.grid(row=0, column=0, sticky="ew", padx=2)


    BasicTopRowControllerToggle = nulltk.Checkbutton(BasicTopRow,variable=TopRowAlwaysTrueControllerRowVar,text="Controller", command=lambda:HideBasictopRow(), width = 12)
    BasicTopRowControllerToggle.grid(row=0, column=1, sticky="ew", padx=2)
    BasicTopRowControllerToggle.grid_remove()

    BasicTopRowDrumToggle = nulltk.Checkbutton(BasicTopRow,variable=TopRowAlwaysTrueDrumRowVar,text="Drums", command=lambda:HideBasictopRow(), width = 12)
    BasicTopRowDrumToggle.grid(row=0, column=1, sticky="ew", padx=2)
    BasicTopRowDrumToggle.grid_remove()

    BasicTopRowKeyboardToggle = nulltk.Checkbutton(BasicTopRow,variable=TopRowAlwaysTrueKeyboardRowVar,text="Keyboard", command=lambda:HideBasictopRow(), width = 12)
    BasicTopRowKeyboardToggle.grid(row=0, column=1, sticky="ew", padx=2)
    BasicTopRowKeyboardToggle.grid_remove()
    #---

    Divider = nulltk.Frame(BasicTopRow,width=2,bg="#555")
    Divider.grid(row=0,column=2,sticky="news",padx=5)

    BasicTopRowActiveMidi = nulltk.Checkbutton(BasicTopRow,variable=ActiveMidiDevice, text="Active?", command=lambda: UpdateActiveState())
    BasicTopRowActiveMidi.grid(row=0, column=3, sticky="ew", padx=2)

    BasicTopRowSendKeys= nulltk.Checkbutton(BasicTopRow,variable=SendKeysVar, text="Send Keys?", command=lambda: UpdateKeyInputs())
    BasicTopRowSendKeys.grid(row=0, column=4, sticky="ew", padx=2)

    BasicTopRowMuteMidi = nulltk.Checkbutton(BasicTopRow,variable=MuteMidiDevice, text="Mute", command=lambda: UpdateMuted())
    BasicTopRowMuteMidi.grid(row=0, column=5, sticky="ew", padx=2)

    def UpdateRowName(Row):
        Row['RowName'] = RowName.get()
        SaveConfig("NullMidi")

    BasicTopRowNameLabel = nulltk.Label(BasicTopRow, text="Name:")
    BasicTopRowNameLabel.grid(row=0, column=6, sticky="e", padx=2)

    BasicTopRowRowName = nulltk.Entry(BasicTopRow, textvariable=RowName, width=20)
    BasicTopRowRowName.grid(row=0, column=7, sticky="ew", padx=2)
    RowName.trace_add("write", lambda *args: UpdateRowName(Row))

    def UpdateMidiDevice(Event=None):
        Row["Device"] = MidiDeviceVar.get()
        SaveConfig("NullMidi")

    PortName = tk.StringVar(value=Row["VirtualPortName"])

    BasicTopRowVPText = nulltk.Label(BasicTopRow, text="Virtual\nPort Name:")
    BasicTopRowVPText.grid(row=0, column=8, sticky="ew", padx=2)

    BasicTopRowVPName = nulltk.Entry(BasicTopRow, textvariable=PortName, width=22, state="readonly")
    BasicTopRowVPName.grid(row=0, column=9, sticky="ew", padx=2)

    MidiDeviceVar = tk.StringVar(value=Row.get("Device", ""))
    BasicTopRowMidiDeviceDropDown = nulltk.Combobox(BasicTopRow, textvariable=MidiDeviceVar, state="readonly",values=GetPorts(Row))
    BasicTopRowMidiDeviceDropDown.grid(row=0, column=10, sticky="ew", padx=2)
    BasicTopRowMidiDeviceDropDown.bind("<<ComboboxSelected>>",UpdateMidiDevice)
    BasicTopRowMidiDeviceDropDown.bind("<Button-1>",lambda e: BasicTopRowMidiDeviceDropDown.configure(values=GetPorts(Row)))

    BasicTopRowDelete = nulltk.Button(BasicTopRow, text="Delete Device", command=lambda:RemoveMidiRow(Frame, Row,BasicTopRowDelete), width = 14)
    BasicTopRowDelete.grid(row=0, column=11, sticky="ew", padx=2)

    BasicTopRow.pack_forget()

    def HideToggleRowShowOtherRow(Which):
        Row["RowCollapsed"] = False
        CollapseRow(Row,False)
        TogglesRow.pack_forget()
        ControllerRow.pack_forget()
        DrumRow.pack_forget()
        KeyboardRow.pack_forget()
        BasicTopRow.pack(fill="x", padx=5, pady=5)
        Row['Controller'] = False
        Row['Drums'] = False
        Row['Keyboard'] = False
        TogglesRowAlwaysFalseControllerVar.set(False)
        TogglesRowAlwaysFalseDrumVar.set(False)
        TogglesRowAlwaysFalseKeyboardVar.set(False)
        TopRowAlwaysTrueControllerRowVar.set(True)
        TopRowAlwaysTrueDrumRowVar.set(True)
        TopRowAlwaysTrueKeyboardRowVar.set(True)

        if Which == "Controller":
            Row['Controller'] = True
            BasicTopRowControllerToggle.grid()
        elif Which == "Drums":
            Row['Drums'] = True
            BasicTopRowDrumToggle.grid()
        elif Which == "Keyboard":
            Row['Keyboard'] = True
            BasicTopRowKeyboardToggle.grid()
        SaveConfig("NullMidi")
    
    


    # --------------- Controller

    Controllerlist = nulltk.Frame(ControllerRow)
    Controllerlist.pack(fill="both", expand="True", padx=5, pady=5)
    Controllerlist.grid(row=1, column=0, sticky="ewns", padx=2,columnspan=20)
    Controllerlist.columnconfigure(0,weight=1)
    Controllerlist.rowconfigure(0,weight=0)
    nulltk.Label(ControllerRow, text="Page:").grid(row=0, column=1, sticky="ew", padx=(5,1))
    ControllerShowPage = nulltk.Entry(ControllerRow, textvariable=ControllerRowPage, state="readonly", width=3)
    ControllerShowPage.grid(row=0, column=2, sticky="ew", padx=(5,1))

    

    ControllerPageDown = nulltk.Button(ControllerRow, command=lambda: ControllerPageHandler(Row, "Down"), text="Page Down", width=8)
    ControllerPageDown.grid(row=0, column=3)

    ControllerPageUp = nulltk.Button(ControllerRow, command=lambda: ControllerPageHandler(Row, "Up"), text="Page Up", width=8)
    ControllerPageUp.grid(row=0, column=4)

    Divider = nulltk.Frame(ControllerRow,width=2,bg="#555")
    Divider.grid(row=0,column=5,sticky="news",padx=5)

    nulltk.Label(ControllerRow, text="Page Down Midi").grid(row=0, column=6, sticky="e", padx=(5,0))

    ControllerMidiPageDown = nulltk.Button(ControllerRow,text=("Set Midi"if Row.get("PageDownMidi") is None else str(Row.get("PageDownMidi"))),command=lambda: DetectNote(ControllerMidiPageDown,Row["Device"],Row, "PageDownMidi"), width =15)
    ControllerMidiPageDown.grid(row=0, column=7)

    ControllerMidiPageUp = nulltk.Button(ControllerRow,text=("Set Midi"if Row.get("PageUpMidi") is None else str(Row.get("PageUpMidi"))),command=lambda: DetectNote(ControllerMidiPageUp,Row["Device"],Row, "PageUpMidi"), width =15)
    ControllerMidiPageUp.grid(row=0, column=8)

    nulltk.Label(ControllerRow, text="Page Up Midi").grid(row=0, column=9, sticky="w", padx=(0,5))

    Divider = nulltk.Frame(ControllerRow,width=2,bg="#555")
    Divider.grid(row=0,column=10,sticky="news",padx=5)

    AddControllerObjectToList = nulltk.Button(ControllerRow, text="Add Controller", command=lambda:AddControllerToList(None,False))
    AddControllerObjectToList.grid(row=0, column=11, sticky="ew", padx=2)

    

    def AddControllerToList(Controller=None, Loading=False):
        ControllerFrame = nulltk.Frame(Controllerlist)
        ControllerFrame.pack(fill="x", padx=5, pady=5)
        ControllerFrame.columnconfigure(0, weight=0)
        ControllerFrame.columnconfigure(1, weight=0)
        ControllerFrame.columnconfigure(2, weight=0)
        ControllerFrame.columnconfigure(3, weight=0)
        ControllerFrame.columnconfigure(4, weight=0)
        ControllerFrame.columnconfigure(5, weight=0)
        ControllerFrame.columnconfigure(6, weight=2)
        ControllerFrame.columnconfigure(7, weight=0)
        ControllerFrame.columnconfigure(8, weight=0)
        ControllerFrame.rowconfigure(0, weight=0)
        

        InternalControllerPage = tk.StringVar(value="1")
        def GetInternalPage():
            return int(InternalControllerPage.get())-1

        if Controller is None:
            Controller = {}
            Controller['DeleteConfirmation'] = False
            Controller['MidiInput'] = None
            Controller['KeyOutputs'] = [[] for i in range(1,101)]
            Controller['KeyOrAction'] = [False for i in range(1,101)]
            Controller['WindowSpecific'] = [False for i in range(1,101)]
            Controller['WindowClassName'] = ["" for i in range(1,101)]
            Controller['WindowDisplayName'] = ["" for i in range(1,101)]
            Controller['StartFilePath'] = ["" for i in range(1,101)]
            Controller['CustomCommand'] = ["" for i in range(1,101)]
            Controller['FileOrCustom'] = [False for i in range(1,101)]
            Row['ControllerList'].append(Controller)
            SaveConfig("NullMidi")

        
        pages = []
        for i in range(1,100):
            pages.append(i)
        KeyOrAction = tk.BooleanVar(value=Controller["KeyOrAction"][GetInternalPage()])
        WindowSpecific = tk.BooleanVar(value=Controller["WindowSpecific"][GetInternalPage()])
        WindowDisplayName = tk.StringVar(value=Controller["WindowDisplayName"][GetInternalPage()])
        StartFilePath = tk.StringVar(value=Controller["StartFilePath"][GetInternalPage()])
        CustomCommand = tk.StringVar(value=Controller["CustomCommand"][GetInternalPage()])
        FileOrCustom = tk.BooleanVar(value=Controller["FileOrCustom"][GetInternalPage()])

        def ControllerUIUpdater():
            Controller['KeyOrAction'][GetInternalPage()] = KeyOrAction.get()
            Controller['WindowSpecific'][GetInternalPage()]= WindowSpecific.get()
            Controller['FileOrCustom'][GetInternalPage()]= FileOrCustom.get()
            Controller['WindowDisplayName'][GetInternalPage()]= WindowDisplayName.get()
            Controller['StartFilePath'][GetInternalPage()]= StartFilePath.get()
            Controller['CustomCommand'][GetInternalPage()]= CustomCommand.get()

            ControllerKeyOutputButton.grid_forget()
            ControllerWindowSpecificSwitcher.grid_forget()
            ControllerWindowSpecifiWindowShow.grid_forget()
            ControllerWindowSpecificChooseWindowButton.grid_forget()
            ControllerFileSwitcher.grid_forget()
            ControllerFileSwitcher.grid_forget()
            ControllerCustomEntryShow.grid_forget()
            ControllerCustomRunButton.grid_forget()
            ControllerActionEntryShow.grid_forget()
            ControllerChooseFile.grid_forget()
            ControllerWindowSpecifiWindowShow.grid_forget()
            ControllerWindowSpecificChooseWindowButton.grid_forget()
            ControllerActionEntryShow.grid_forget()
            ControllerChooseFile.grid_forget()
            ControllerCustomEntryShow.grid_forget()
            ControllerCustomRunButton.grid_forget()


            if KeyOrAction.get():
                ControllerFileSwitcher.grid(row=0, column=4, sticky="ew", padx=2)

                if FileOrCustom.get():
                    ControllerCustomEntryShow.grid(row=0, column=6, sticky="ew")
                    ControllerCustomRunButton.grid(row=0, column=5)
                else:
                    ControllerActionEntryShow.grid(row=0, column=6, sticky="ew")
                    ControllerChooseFile.grid(row=0, column=5)
            else:
                ControllerKeyOutputButton.grid(row=0, column=4, sticky="ew")
                ControllerWindowSpecificSwitcher.grid(row=0, column=5, sticky="ew", padx=2)

                if WindowSpecific.get():
                    ControllerWindowSpecifiWindowShow.grid(row=0, column=6, sticky="ew")
                    ControllerWindowSpecificChooseWindowButton.grid(row=0, column=7)
                                    
            SaveConfig("NullMidi")
            
        def RemoveController(Controller, Button, Timeout=4):
            EndTime = time.time() + (Timeout)

            def Tick(Row):
                if Controller['DeleteConfirmation'] == False:
                    return
                else:
                    Remaining = int(EndTime - time.time())
                    if Remaining <= 0:
                        if not Button.winfo_exists():
                            return
                        Button.config(text="Delete Controller")
                        Controller['DeleteConfirmation'] = False
                        return
                    if not Button.winfo_exists():
                        return
                    else:
                        Button.config(text=f"R U Sure? {Remaining}")
                        Root.after(1000, Tick, Row)

            if Controller['DeleteConfirmation'] == False:
                Controller['DeleteConfirmation'] = True
                Tick(Row)
                return

            Row["ControllerList"].remove(Controller)
            ControllerFrame.destroy()
            SaveConfig("NullMidi")

        def UpdateCustomCommand(*args):
            Controller['CustomCommand'][GetInternalPage()] = CustomCommand.get()
            SaveConfig("NullMidi")

        def OnControllerPageChange():
            ControllerKeyOutputButton.config(text="+".join(Controller['KeyOutputs'][GetInternalPage()]) if Controller['KeyOutputs'][GetInternalPage()]else "Set Key")
            KeyOrAction.set(Controller['KeyOrAction'][GetInternalPage()])
            WindowSpecific.set(Controller['WindowSpecific'][GetInternalPage()])
            WindowDisplayName.set(Controller['WindowDisplayName'][GetInternalPage()])
            StartFilePath.set(Controller['StartFilePath'][GetInternalPage()])
            CustomCommand.set(Controller['CustomCommand'][GetInternalPage()])
            FileOrCustom.set(Controller['FileOrCustom'][GetInternalPage()])
            ControllerUIUpdater()
            return

        #--- absolutes
        ControllerPageDropDown = nulltk.Combobox(ControllerFrame, values=pages, textvariable=InternalControllerPage, state="readonly", width=3)
        ControllerPageDropDown.grid(row=0, column=0, sticky="ew", padx=(5,1))
        ControllerPageDropDown.bind("<<ComboboxSelected>>",lambda e: OnControllerPageChange())

        ControllerKeyActionSwitcher = nulltk.Checkbutton(ControllerFrame, text="Keys|Action", variable=KeyOrAction, command=lambda:ControllerUIUpdater())
        ControllerKeyActionSwitcher.grid(row=0, column=1, sticky="ew", padx=2)

        ControllerMidiInputButton = nulltk.Button(ControllerFrame,text=("Set Midi"if Controller["MidiInput"] is None else str(Controller["MidiInput"])),command=lambda: DetectNote(ControllerMidiInputButton,Row["Device"],Controller,"MidiInput"),width=5)
        ControllerMidiInputButton.grid(row=0, column=2)

        SwitcherDivider = nulltk.Frame(ControllerFrame,width=2,bg="#555")
        SwitcherDivider.grid(row=0,column=3,sticky="news",padx=5)

        #--- Key

        ControllerKeyOutputButton = nulltk.Button(ControllerFrame,text=("+".join(FormatKeyName(K)for K in Controller["KeyOutputs"][GetInternalPage()]) or "Set Key"),command=lambda: DetectKey(ControllerKeyOutputButton,Controller,'KeyOutputs',"NullMidi",GetInternalPage()),width=25)

        ControllerWindowSpecificSwitcher = nulltk.Checkbutton(ControllerFrame, text="All|Window", variable=WindowSpecific, command=lambda:ControllerUIUpdater())

        ControllerWindowSpecifiWindowShow = nulltk.Entry(ControllerFrame, textvariable=WindowDisplayName, state="readonly")

        ControllerWindowSpecificChooseWindowButton = nulltk.Button(ControllerFrame, command=lambda: SearchForWindow(Controller, WindowDisplayName, "WindowClassName", "WindowDisplayName", "NullMidi", GetInternalPage() ), text="Choose Window", width=14)

        # ------ Opener 
        ControllerFileSwitcher = nulltk.Checkbutton(ControllerFrame, text="File|Custom", variable=FileOrCustom, command=lambda:ControllerUIUpdater())

        # ---- File

        ControllerChooseFile = nulltk.Button(ControllerFrame, command=lambda: SearchForAnyFile(Controller,StartFilePath,"StartFilePath",GetInternalPage()), text="Browse", width=8)

        ControllerActionEntryShow = nulltk.Entry(ControllerFrame, textvariable=StartFilePath, state="readonly")

        # ---- Custom

        ControllerCustomRunButton= nulltk.Button(ControllerFrame, command=lambda: MidiCustomRun(Controller['CustomCommand'][GetInternalPage()]), text="Run", width=8)

        ControllerCustomEntryShow = nulltk.Entry(ControllerFrame, textvariable=CustomCommand,)
        CustomCommand.trace_add("write", UpdateCustomCommand)

        #--- Always

        ControllerRemoveButton = nulltk.Button(ControllerFrame, command=lambda: RemoveController(Controller,ControllerRemoveButton), text="Remove Controller", width=18)
        ControllerRemoveButton.grid(row=0, column=8)

        MidiScrollBox.BindMouseWheel(Frame)


        if Loading:
            OnControllerPageChange()
            return

    # --------------- Drums

    DrumList = nulltk.Frame(DrumRow)#ScrollableFrame(DrumRow)
    DrumList.pack(fill="both", expand="True", padx=5, pady=5)

    DrumList.grid(row=2, column=0, sticky="ewns", padx=2,columnspan=10)
    DrumList.columnconfigure(0,weight=1)
    DrumList.rowconfigure(0,weight=0)


    def AddDrumToList(Drum=None, Loading=False):
        MainDrumFrame = nulltk.Frame(DrumList)
        MainDrumFrame.pack(fill="x", padx=5, pady=5)

        MainDrumFrame.columnconfigure(0, weight=1)
        MainDrumFrame.rowconfigure(0, weight=1)
        
        if Drum is None:
            Drum = {}
            Drum['DeleteConfirmation'] = False
            Drum['SpecificWindow'] = False
            Drum['WindowClassName'] = ""
            Drum['WindowDisplayName'] = ""
            Drum['Channels'] = []
            Drum['Collapsed'] = False
            Drum['DrumName'] = ""
            Drum['Drum'] = False
            Drum['Cymbal'] = False
            Drum['Kick'] = False
            Drum['Hihat'] = False

            Drum['CenterGhostNoteThreshold'] = 50
            Drum['CenterSlamNoteThreshold'] = 100

            Drum['RimGhostNoteThreshold'] = 50
            Drum['RimSlamNoteThreshold'] = 110

            Drum['BowGhostNoteThreshold'] = 50
            Drum['BowSlamNoteThreshold'] = 100

            Drum['CenterVolume'] = 75
            Drum['RimVolume'] = 75
            Drum['BowVolume'] = 75

            Drum['CenterMidiInput'] = None
            Drum['RimMidiInput'] = None
            Drum['BowMidiInput'] = None

            Drum['CenterKeyOutput'] = []
            Drum['RimKeyOutput'] = []
            Drum['BowKeyOutput'] = []
            
            Drum['CenterSoundFilePath'] = None
            Drum['RimSoundFilePath'] = None
            Drum['BowSoundFilePath'] = None

            Drum['KickDrumMinimumVelocity'] = 85

            Drum['HiHatClosedThreshold'] = 100
            Drum['HiHatClosedPath'] = None
            Drum['HiHatClosedVolume'] = 75
            Drum['HiHatClosedKeyOutput'] = []
            Drum['HiHatClosedMidiInput'] = None
            
            Drum['HiHatHalfPath'] = None
            Drum['HiHatHalfVolume'] = 75
            Drum['HiHatHalfKeyOutput'] = []
            Drum['HiHatHalfMidiInput'] = None

            Drum['HiHatOpenThreshold'] = 0
            Drum['HiHatOpenPath'] = None
            Drum['HiHatOpenVolume'] = 75
            Drum['HiHatOpenKeyOutput'] = []
            Drum['HiHatOpenMidiInput'] = None
            
            Drum['HiHatStompPath'] = None
            Drum['HiHatStompVolume'] = 100
            Drum['HiHatStompKeyOutput'] = []
            Drum['HiHatStompMidiInput'] = None
            Drum['HiHatFadeIn'] = 60
            Drum['HiHatOpenTime'] = 0.075
        
            Drum['HiHatBellOpenPath'] = None
            Drum['HiHatBellOpenVolume'] = 75
            Drum['HiHatBellOpenKeyOutput'] = []
            Drum['HiHatBellOpenMidiInput'] = None

            Drum['HiHatBellClosedPath'] = None
            Drum['HiHatBellClosedVolume'] = 75
            Drum['HiHatBellClosedKeyOutput'] = []
            Drum['HiHatBellClosedMidiInput'] = None

            Row['DrumList'].append(Drum)

        DrumWindowDisplayName = tk.StringVar(value= Drum.get("WindowDisplayName", ""))
        DrumWindowSpecific = tk.BooleanVar(value=Drum.get("WindowSpecific",False))

        def DrumWindowSpecificUpdater(Loading=False):
            Drum['WindowSpecific'] = DrumWindowSpecific.get()

            if Drum['WindowSpecific']:
                DrumWindowSpecifiWindowShow.grid(row=1, column=5, sticky="ew")
                DrumWindowSpecificChooseWindowButton.grid(row=1, column=8)
            else:
                DrumWindowSpecifiWindowShow.grid_forget()
                DrumWindowSpecificChooseWindowButton.grid_forget()
            SaveConfig("NullMidi")
            return
            

        DrumWindowSpecificSwitcher = nulltk.Checkbutton(DrumRow, text="All|Window", variable=DrumWindowSpecific, command=lambda:DrumWindowSpecificUpdater())
        DrumWindowSpecificSwitcher.grid(row=1, column=4, sticky="ew", padx=2)

        DrumWindowSpecificChooseWindowButton = nulltk.Button(DrumRow, command=lambda: SearchForWindow(Drum, DrumWindowDisplayName, "WindowClassName", "WindowDisplayName" ), text="Choose Window", width=14)
        DrumWindowSpecificChooseWindowButton.grid(row=1, column=8)
        DrumWindowSpecificChooseWindowButton.grid_forget()

        DrumWindowSpecifiWindowShow = nulltk.Entry(DrumRow, textvariable=DrumWindowDisplayName, state="readonly", width = 1)
        DrumWindowSpecifiWindowShow.grid(row=1, column=5, sticky="ew")
        DrumWindowSpecifiWindowShow.grid_forget()

        Divider = nulltk.Frame(DrumRow,width=2,bg="#555")
        Divider.grid(row=1,column=7,sticky="news",padx=5)

        Divider = nulltk.Frame(DrumRow,width=2,bg="#555")
        Divider.grid(row=1,column=3,sticky="news",padx=5)

        DrumRowAlwaysFalsePad = tk.BooleanVar(value=False)
        DrumRowAlwaysFalseCymbal = tk.BooleanVar(value=False)
        DrumRowAlwaysFalseKick = tk.BooleanVar(value=False)
        DrumRowAlwaysFalseHihat = tk.BooleanVar(value=False)

        MainDrumRowToggles = nulltk.Frame(MainDrumFrame)
        MainDrumRowToggles.grid(row=0, column=0, sticky="ew", padx=2)
        MainDrumRowToggles.columnconfigure(0, weight=1)
        MainDrumRowToggles.columnconfigure(1, weight=1)
        MainDrumRowToggles.columnconfigure(2, weight=1)
        MainDrumRowToggles.columnconfigure(3, weight=1)
        MainDrumRowToggles.columnconfigure(4, weight=1)
        MainDrumRowToggles.rowconfigure(0, weight=1)

        DrumRowDrumRow = nulltk.Frame(MainDrumFrame)
        DrumRowDrumRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowDrumRow.columnconfigure(0, weight=1)
        DrumRowDrumRow.rowconfigure(0, weight=0)
        DrumRowDrumRow.rowconfigure(1, weight=1)

        MainDrumRowToggles.rowconfigure(1, weight=1)
        DrumRowDrumRow.grid_forget()

        DrumRowCymbalRow = nulltk.Frame(MainDrumFrame)
        DrumRowCymbalRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowCymbalRow.columnconfigure(0, weight=1)
        DrumRowCymbalRow.rowconfigure(0, weight=0)
        DrumRowCymbalRow.rowconfigure(1, weight=1)
        DrumRowCymbalRow.grid_forget()

        DrumRowKickRow = nulltk.Frame(MainDrumFrame)
        DrumRowKickRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowKickRow.columnconfigure(0, weight=1)
        DrumRowKickRow.rowconfigure(0, weight=0)
        DrumRowKickRow.rowconfigure(1, weight=1)
        DrumRowKickRow.grid_forget()

        DrumRowHihatRow = nulltk.Frame(MainDrumFrame)
        DrumRowHihatRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowHihatRow.columnconfigure(0, weight=1)
        DrumRowHihatRow.rowconfigure(0, weight=0)
        DrumRowHihatRow.rowconfigure(1, weight=1)
        DrumRowHihatRow.rowconfigure(2, weight=1)
        DrumRowHihatRow.grid_forget()

        DrumRowAlwaysTrueCymbal = tk.BooleanVar(value=True)
        DrumRowAlwaysTrueKick = tk.BooleanVar(value=True)
        DrumRowAlwaysTrueHiHat = tk.BooleanVar(value=True)
        DrumRowAlwaysTruePad = tk.BooleanVar(value=True)
        
        def RemoveDrum(Drum, Button, Timeout=4):
            EndTime = time.time() + (Timeout)

            def Tick(Row):
                if Drum['DeleteConfirmation'] == False:
                    return
                else:
                    Remaining = int(EndTime - time.time())
                    if Remaining <= 0:
                        if not Button.winfo_exists():
                            return
                        Button.config(text="Delete Drum")
                        Drum['DeleteConfirmation'] = False
                        return
                    if not Button.winfo_exists():
                        return
                    else:
                        Button.config(text=f"R U Sure? {Remaining}")
                        Root.after(1000, Tick, Row)

            if Drum['DeleteConfirmation'] == False:
                Drum['DeleteConfirmation'] = True
                Tick(Row)
                return
            Row["DrumList"].remove(Drum)
            MainDrumFrame.destroy()
            SaveConfig("NullMidi")

        def SwitchDrumType(Which, Loading=False):
            MainDrumRowToggles.grid_forget()
            DrumRowDrumRow.grid_forget()
            DrumRowCymbalRow.grid_forget()
            DrumRowKickRow.grid_forget()
            DrumRowHihatRow.grid_forget()
            Drum['Drum'] = False
            Drum['Cymbal'] = False
            Drum['Kick'] = False
            Drum['Hihat'] = False
            DrumRowAlwaysFalsePad.set(False)
            DrumRowAlwaysFalseCymbal.set(False)
            DrumRowAlwaysFalseKick.set(False)
            DrumRowAlwaysFalseHihat.set(False)
            DrumRowAlwaysTruePad.set(True)
            DrumRowAlwaysTrueCymbal.set(True)
            DrumRowAlwaysTrueKick.set(True)
            DrumRowAlwaysTrueHiHat.set(True)

            def SetupPadRow(Loading=False):
                SoundWidgets.clear()
                DrumRowTopRow = nulltk.Frame(DrumRowDrumRow)
                DrumRowTopRow.grid(row=0, column=0, sticky="ew", padx=2)

                DrumRowTopRow.columnconfigure(0, weight=0 )
                DrumRowTopRow.columnconfigure(1, weight=0 )
                DrumRowTopRow.columnconfigure(2, weight=0 )
                DrumRowTopRow.columnconfigure(3, weight=0 )
                DrumRowTopRow.columnconfigure(4, weight=2 )
                DrumRowTopRow.columnconfigure(5, weight=1 )
                DrumRowTopRow.rowconfigure(0, weight=0 )

                DrumCollapseButton = nulltk.Button(DrumRowTopRow, text="▼", command=lambda:CollapseDrum(Drum, PadsContainer), width = 2)
                DrumCollapseButton.grid(row=0, column=0, sticky="ew", padx=2)

                def CollapseDrum(Drum, PadsContainer, Loading=False):
                    if Loading:
                        if Drum['Collapsed']:
                            PadsContainer.grid_forget()
                            DrumCollapseButton.config(text="▶")
                        else:
                            PadsContainer.grid(row=1, column=0, sticky="ew", padx=2)
                            DrumCollapseButton.config(text="▼")
                        return

                    if Drum['Collapsed']:
                        PadsContainer.grid(row=1, column=0, sticky="ew", padx=2)
                        DrumCollapseButton.config(text="▼")
                        Drum['Collapsed'] =  False
                    else:
                        PadsContainer.grid_forget()
                        DrumCollapseButton.config(text="▶")
                        Drum['Collapsed'] =  True

                        
                        

                    SaveConfig("NullMidi")

                DrumRowDrumToMainToggle = nulltk.Checkbutton(DrumRowTopRow, text="Pad", variable=DrumRowAlwaysTruePad, command=lambda:SwitchDrumType("Main"))
                DrumRowDrumToMainToggle.grid(row=0, column=1, sticky="ew", padx=2)
                Divider = nulltk.Frame(DrumRowTopRow,width=2,bg="#555")
                Divider.grid(row=0,column=2,sticky="ns",padx=5)
                DrumRowWhichDrum = nulltk.Label(DrumRowTopRow, text="Pad Name:")
                DrumRowWhichDrum.grid(row=0,column=3,sticky="w",padx=5)
                DrumName = tk.StringVar(value=Drum.get("DrumName", ""))

                def UpdateDrumName(Row):
                    Drum['DrumName'] = DrumName.get()
                    SaveConfig("NullMidi")

                DrumRowDrumName = nulltk.Entry(DrumRowTopRow, textvariable=DrumName, width=30)
                DrumRowDrumName.grid(row=0, column=4, sticky="ew", padx=2)
                DrumName.trace_add("write", lambda *args: UpdateDrumName(Drum))

                RemoveDrumObjectFromList= nulltk.Button(DrumRowTopRow, text="Delete Drum?", command=lambda:RemoveDrum(Drum, RemoveDrumObjectFromList))
                RemoveDrumObjectFromList.grid(row=0, column=5, sticky="ew", padx=2)

                PadsContainer = nulltk.Frame(DrumRowDrumRow)
                PadsContainer.grid(row=1, column=0, sticky="ew", padx=2)
                PadsContainer.columnconfigure(0,weight=4)
                PadsContainer.columnconfigure(1,weight=2)
                PadsContainer.columnconfigure(2,weight=4)


                #------------ CenterRow
                DrumRowCenterPad = nulltk.Frame(PadsContainer)
                DrumRowCenterPad.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
                DrumRowCenterPad.rowconfigure(0, weight=1)
                DrumRowCenterPad.rowconfigure(1, weight=1)
                DrumRowCenterPad.rowconfigure(2, weight=0)
                DrumRowCenterPad.columnconfigure(0, weight=1)

                DrumRowCenterLabel = nulltk.Label(DrumRowCenterPad, text= "Center Of Pad", width= 8, font=("TkDefaultFont", 12, "bold"))
                DrumRowCenterLabel.grid(row=0, column=0, sticky="ew")



                DrumRowInputsFrame = nulltk.Frame(DrumRowCenterPad)
                DrumRowInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                DrumRowCenterInputsLabel = nulltk.Label(DrumRowInputsFrame, text= "Inputs:", width =8 )
                DrumRowCenterInputsLabel.grid(row=0, column=0)

                DrumRowCenterMidiInputButton = nulltk.Button(DrumRowInputsFrame,text=("Set Midi"if Drum.get("CenterMidiInput") is None else str(Drum.get("CenterMidiInput"))),command=lambda: DetectNote(DrumRowCenterMidiInputButton,Row["Device"],Drum, "CenterMidiInput"), width =22)
                DrumRowCenterMidiInputButton.grid(row=0, column=1)

                DrumRowCenterKeyOutputButton = nulltk.Button(DrumRowInputsFrame,text=("+".join(FormatKeyName(K)for K in Drum.get("CenterKeyOutput")) or "Set Key"),command=lambda: DetectKey(DrumRowCenterKeyOutputButton,Drum,"CenterKeyOutput","NullMidi"),width=22)                
                DrumRowCenterKeyOutputButton.grid(row=0, column=2, sticky="ew")


                DrumCenterSounds = nulltk.LabelFrame(DrumRowCenterPad, text = "Sounds")
                DrumCenterSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))
                SoundWidgets[DrumCenterSounds] = {"row": 2,"column": 0,"sticky": "ew","padx": 5,"pady": (2,10)}

                DrumCenterSounds.columnconfigure(0,weight=0)
                DrumCenterSounds.columnconfigure(1,weight=0)
                DrumCenterSounds.columnconfigure(2,weight=0)
                DrumCenterSounds.columnconfigure(3,weight=0)
                DrumCenterSounds.rowconfigure(0,weight=0)
                DrumCenterSounds.rowconfigure(1,weight=0)
                DrumCenterSounds.rowconfigure(2,weight=0)
                DrumCenterSounds.rowconfigure(3,weight=0)

                DrumRowCenterSoundLocationVar = tk.StringVar(value= Drum.get("CenterSoundFilePath", ""))
                CenterVolumeVar = tk.IntVar(value=Drum.get("CenterVolume", 100))
                CenterGhostNote = tk.IntVar(value=Drum.get("CenterGhostNoteThreshold", 100))
                CenterSlam= tk.IntVar(value=Drum.get("CenterSlamNoteThreshold", 100))

                DrumRowCenterVolumeSliderLabel = nulltk.Label(DrumCenterSounds, text= "Volume", width = 12, height=2)
                DrumRowCenterVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                DrumRowCenterVolumeSlider = nulltk.Scale(DrumCenterSounds,from_=0,to=100,orient="horizontal",variable=CenterVolumeVar,showvalue=False, length=44,)
                DrumRowCenterVolumeSlider.grid(row=0, column=1, sticky="ew")
                DrumRowCenterVolumeShowLabel = nulltk.Label(DrumCenterSounds,textvariable=CenterVolumeVar)
                DrumRowCenterVolumeShowLabel.grid(row=0, column=2, sticky="w")


                DrumRowCenterSoundPathLabel = nulltk.Label(DrumCenterSounds, text= "Sound\nPath:", width = 12, height=2)
                DrumRowCenterSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))
                DrumRowCenterSoundLocationIF = nulltk.Entry(DrumCenterSounds, textvariable=DrumRowCenterSoundLocationVar, state="readonly", width=44)
                DrumRowCenterSoundLocationIF.grid(row=1, column=1, sticky="ew")
                DrumRowCenterBrowseButton = nulltk.Button(DrumCenterSounds, command=lambda: SearchForSoundFile(Drum ,DrumRowCenterSoundLocationVar, "CenterSoundFilePath" ), text="Browse", width=8)
                DrumRowCenterBrowseButton.grid(row=1, column=2)

                def UpdateCenterVolume(*args):
                    Drum["CenterVolume"] = CenterVolumeVar.get()
                    SaveConfig("NullMidi")

                def UpdateCenterGhost(*args):
                    Drum["CenterGhostNoteThreshold"] = CenterGhostNote.get()
                    SaveConfig("NullMidi")

                def UpdateCenterSlam(*args):
                    Drum["CenterSlamNoteThreshold"] = CenterSlam.get()
                    SaveConfig("NullMidi")

                DrumRowCenterGhostLabel = nulltk.Label(DrumCenterSounds, text= "Ghost Note\n Velocity Cap", width = 12, height=2)
                DrumRowCenterGhostLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                DrumRowCenterGhostSlider = nulltk.Scale(DrumCenterSounds,from_=1,to=127,orient="horizontal",variable=CenterGhostNote,showvalue=False, length=44,)
                DrumRowCenterGhostSlider.grid(row=2, column=1, sticky="ew")

                DrumRowCenterGhostShowLabel = nulltk.Label(DrumCenterSounds,textvariable=CenterGhostNote)
                DrumRowCenterGhostShowLabel.grid(row=2, column=2, sticky="w")


                DrumRowCenterSlamLabel = nulltk.Label(DrumCenterSounds, text= "Slam Note\n Velocity Min", width = 12, height=2)
                DrumRowCenterSlamLabel.grid(row=3, column=0, sticky="e", pady=(0,8))
                DrumRowCenterSlamSlider = nulltk.Scale(DrumCenterSounds,from_=1,to=127,orient="horizontal",variable=CenterSlam,showvalue=False, length=44,)
                DrumRowCenterSlamSlider.grid(row=3, column=1, sticky="ew")
                DrumRowCenterSlamShowLabel = nulltk.Label(DrumCenterSounds,textvariable=CenterSlam)
                DrumRowCenterSlamShowLabel.grid(row=3, column=2, sticky="w")

        
                Divider = nulltk.Frame(PadsContainer,width=2,bg="#555")
                Divider.grid(row=1,column=1,sticky="ns",padx=5)


                #------------ RimRow
                DrumRowRimPad = nulltk.Frame(PadsContainer)
                DrumRowRimPad.grid(row=1, column=2, sticky="ew", padx=2, pady=2)
                DrumRowRimPad.rowconfigure(0, weight=1)
                DrumRowRimPad.rowconfigure(1, weight=1)
                DrumRowRimPad.rowconfigure(2, weight=0)
                DrumRowRimPad.columnconfigure(0, weight=1)

                DrumRowRimLabel = nulltk.Label(DrumRowRimPad, text= "Rim Of Pad", width= 8, font=("TkDefaultFont", 12, "bold"))
                DrumRowRimLabel.grid(row=0, column=0, sticky="ew")



                DrumRowInputsFrame = nulltk.Frame(DrumRowRimPad)
                DrumRowInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                DrumRowRimInputsLabel = nulltk.Label(DrumRowInputsFrame, text= "Inputs:", width =8 )
                DrumRowRimInputsLabel.grid(row=0, column=0)

                DrumRowRimMidiInputButton = nulltk.Button(DrumRowInputsFrame,text=("Set Midi"if Drum.get("RimMidiInput") is None else str(Drum.get("RimMidiInput"))),command=lambda: DetectNote(DrumRowRimMidiInputButton,Row["Device"],Drum, "RimMidiInput"), width =22)
                DrumRowRimMidiInputButton.grid(row=0, column=1)

                DrumRowRimKeyOutputButton = nulltk.Button(DrumRowInputsFrame,text="+".join(FormatKeyName(K)for K in Drum.get("RimKeyOutput")) or "Set Key",command=lambda: DetectKey(DrumRowRimKeyOutputButton,Drum, "RimKeyOutput","NullMidi"), width=22)
                DrumRowRimKeyOutputButton.grid(row=0, column=2, sticky="ew")


                DrumRimSounds = nulltk.LabelFrame(DrumRowRimPad, text = "Sounds")
                DrumRimSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))
                SoundWidgets[DrumRimSounds] = {"row": 2,"column": 0,"sticky": "ew","padx": 5,"pady": (2,10)}
                DrumRimSounds.columnconfigure(0,weight=0)
                DrumRimSounds.columnconfigure(1,weight=0)
                DrumRimSounds.columnconfigure(2,weight=0)
                DrumRimSounds.columnconfigure(3,weight=0)
                DrumRimSounds.rowconfigure(0,weight=0)
                DrumRimSounds.rowconfigure(1,weight=0)
                DrumRimSounds.rowconfigure(2,weight=0)
                DrumRimSounds.rowconfigure(3,weight=0)

                DrumRowRimSoundLocationVar = tk.StringVar(value= Drum.get("RimSoundFilePath", ""))
                RimVolumeVar = tk.IntVar(value=Drum.get("RimVolume", 100))
                RimGhostNote = tk.IntVar(value=Drum.get("RimGhostNoteThreshold", 100))
                RimSlam= tk.IntVar(value=Drum.get("RimSlamNoteThreshold", 100))

                DrumRowRimVolumeSliderLabel = nulltk.Label(DrumRimSounds, text= "Volume", width = 12, height=2)
                DrumRowRimVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                DrumRowRimVolumeSlider = nulltk.Scale(DrumRimSounds,from_=0,to=100,orient="horizontal",variable=RimVolumeVar,showvalue=False, length=44,)
                DrumRowRimVolumeSlider.grid(row=0, column=1, sticky="ew")
                DrumRowRimVolumeShowLabel = nulltk.Label(DrumRimSounds,textvariable=RimVolumeVar)
                DrumRowRimVolumeShowLabel.grid(row=0, column=2, sticky="w")


                DrumRowRimSoundPathLabel = nulltk.Label(DrumRimSounds, text= "Sound\nPath:", width = 12, height=2)
                DrumRowRimSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))
                DrumRowRimSoundLocationIF = nulltk.Entry(DrumRimSounds, textvariable=DrumRowRimSoundLocationVar, state="readonly", width=44)
                DrumRowRimSoundLocationIF.grid(row=1, column=1, sticky="ew")
                DrumRowRimBrowseButton = nulltk.Button(DrumRimSounds, command=lambda: SearchForSoundFile(Drum ,DrumRowRimSoundLocationVar, "RimSoundFilePath" ), text="Browse", width=8)
                DrumRowRimBrowseButton.grid(row=1, column=2)
                

                def UpdateRimVolume(*args):
                    Drum["RimVolume"] = RimVolumeVar.get()
                    SaveConfig("NullMidi")

                def UpdateRimGhost(*args):
                    Drum["RimGhostNoteThreshold"] = RimGhostNote.get()
                    SaveConfig("NullMidi")

                def UpdateRimSlam(*args):
                    Drum["RimSlamNoteThreshold"] = RimSlam.get()
                    SaveConfig("NullMidi")

                DrumRowRimGhostLabel = nulltk.Label(DrumRimSounds, text= "Ghost Note\n Velocity Cap", width = 12, height=2)
                DrumRowRimGhostLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                DrumRowRimGhostSlider = nulltk.Scale(DrumRimSounds,from_=1,to=127,orient="horizontal",variable=RimGhostNote,showvalue=False, length=44,)
                DrumRowRimGhostSlider.grid(row=2, column=1, sticky="ew")

                DrumRowRimGhostShowLabel = nulltk.Label(DrumRimSounds,textvariable=RimGhostNote)
                DrumRowRimGhostShowLabel.grid(row=2, column=2, sticky="w")


                DrumRowRimSlamLabel = nulltk.Label(DrumRimSounds, text= "Slam Note\n Velocity Min", width = 12, height=2)
                DrumRowRimSlamLabel.grid(row=3, column=0, sticky="e", pady=(0,8))
                DrumRowRimSlamSlider = nulltk.Scale(DrumRimSounds,from_=1,to=127,orient="horizontal",variable=RimSlam,showvalue=False, length=44,)
                DrumRowRimSlamSlider.grid(row=3, column=1, sticky="ew")
                DrumRowRimSlamShowLabel = nulltk.Label(DrumRimSounds,textvariable=RimSlam)
                DrumRowRimSlamShowLabel.grid(row=3, column=2, sticky="w")

                MidiScrollBox.BindMouseWheel(Frame)

                SetupSlider(DrumRowCenterVolumeSlider,CenterVolumeVar,0,100,UpdateCenterVolume)

                SetupSlider(DrumRowCenterGhostSlider,CenterGhostNote,0,127,UpdateCenterGhost)

                SetupSlider(DrumRowCenterSlamSlider,CenterSlam,0,127,UpdateCenterSlam)

                SetupSlider(DrumRowRimVolumeSlider,RimVolumeVar,0,100,UpdateRimVolume)

                SetupSlider(DrumRowRimGhostSlider,RimGhostNote,0,127,UpdateRimGhost)

                SetupSlider(DrumRowRimSlamSlider,RimSlam,0,127,UpdateRimSlam)

                CollapseDrum(Drum, PadsContainer, Loading)
                UpdateMuted()

            def SetupCymbalRow(Loading=False):
                SoundWidgets.clear()
                CymbalRowTopRow = nulltk.Frame(DrumRowCymbalRow)
                CymbalRowTopRow.grid(row=0, column=0, sticky="ew", padx=2)

                CymbalRowTopRow.columnconfigure(0, weight=0 )
                CymbalRowTopRow.columnconfigure(1, weight=0 )
                CymbalRowTopRow.columnconfigure(2, weight=0 )
                CymbalRowTopRow.columnconfigure(3, weight=0 )
                CymbalRowTopRow.columnconfigure(4, weight=2 )
                CymbalRowTopRow.columnconfigure(5, weight=1 )
                CymbalRowTopRow.rowconfigure(0, weight=0 )

                CymbalCollapseButton = nulltk.Button(CymbalRowTopRow, text="▼", command=lambda:CollapseCymbal(Drum, CymbalsContainer), width = 2)
                CymbalCollapseButton.grid(row=0, column=0, sticky="ew", padx=2)

                def CollapseCymbal(Drum, CymbalsContainer, Loading=False):
                    if Loading:
                        if Drum['Collapsed']:
                            CymbalsContainer.grid_forget()
                            CymbalCollapseButton.config(text="▶")
                        else:
                            CymbalsContainer.grid(row=1, column=0, sticky="ew", padx=2)
                            CymbalCollapseButton.config(text="▼")
                        return

                    if Drum['Collapsed']:
                        CymbalsContainer.grid(row=1, column=0, sticky="ew", padx=2)
                        CymbalCollapseButton.config(text="▼")
                        Drum['Collapsed'] =  False
                    else:
                        CymbalsContainer.grid_forget()
                        CymbalCollapseButton.config(text="▶")
                        Drum['Collapsed'] =  True

                        
                        
                    SaveConfig("NullMidi")

                CymbalRowCymbalToMainToggle = nulltk.Checkbutton(CymbalRowTopRow, text="Cymbals", variable=DrumRowAlwaysTrueCymbal, command=lambda:SwitchDrumType("Main"))
                CymbalRowCymbalToMainToggle.grid(row=0, column=1, sticky="ew", padx=2)
                Divider = nulltk.Frame(CymbalRowTopRow,width=2,bg="#555")
                Divider.grid(row=0,column=2,sticky="ns",padx=5)
                CymbalRowWhichCymbal = nulltk.Label(CymbalRowTopRow, text="Cymbal Name:")
                CymbalRowWhichCymbal.grid(row=0,column=3,sticky="w",padx=5)
                CymbalName = tk.StringVar(value=Drum.get("DrumName", ""))

                def UpdateDrumName(Row):
                    Drum['DrumName'] = CymbalName.get()
                    SaveConfig("NullMidi")

                CymbalRowCymbalName = nulltk.Entry(CymbalRowTopRow, textvariable=CymbalName, width=30)
                CymbalRowCymbalName.grid(row=0, column=4, sticky="ew", padx=2)
                CymbalName.trace_add("write", lambda *args: UpdateDrumName(Drum))

                RemoveCymbalObjectFromList= nulltk.Button(CymbalRowTopRow, text="Delete Drum", command=lambda:RemoveDrum(Drum, RemoveCymbalObjectFromList))
                RemoveCymbalObjectFromList.grid(row=0, column=5, sticky="ew", padx=2)

                CymbalsContainer = nulltk.Frame(DrumRowCymbalRow)
                CymbalsContainer.grid(row=1, column=0, sticky="ew", padx=2)
                CymbalsContainer.rowconfigure(0,weight=1)
                CymbalsContainer.columnconfigure(0,weight=3)
                CymbalsContainer.columnconfigure(1,weight=1)
                CymbalsContainer.columnconfigure(2,weight=3)
                CymbalsContainer.columnconfigure(3,weight=1)
                CymbalsContainer.columnconfigure(4,weight=3)

                #------------ BellRow
                CymbalRowBellRow = nulltk.Frame(CymbalsContainer)
                CymbalRowBellRow.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
                CymbalRowBellRow.rowconfigure(0, weight=1)
                CymbalRowBellRow.rowconfigure(1, weight=1)
                CymbalRowBellRow.rowconfigure(2, weight=0)
                CymbalRowBellRow.columnconfigure(0, weight=1)

                CymbalRowBellLabel = nulltk.Label(CymbalRowBellRow, text="Bell Of Cymbal", width=8, font=("TkDefaultFont", 12, "bold"))
                CymbalRowBellLabel.grid(row=0, column=0, sticky="ew")

                CymbalRowBellInputsFrame = nulltk.Frame(CymbalRowBellRow)
                CymbalRowBellInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                CymbalRowBellInputsLabel = nulltk.Label(CymbalRowBellInputsFrame, text="Inputs:", width=8)
                CymbalRowBellInputsLabel.grid(row=0, column=0)

                CymbalRowBellMidiInputButton = nulltk.Button(CymbalRowBellInputsFrame, text=("Set Midi" if Drum.get("CenterMidiInput") is None else str(Drum.get("CenterMidiInput"))), command=lambda: DetectNote(CymbalRowBellMidiInputButton, Row["Device"], Drum, "CenterMidiInput"), width=22)
                CymbalRowBellMidiInputButton.grid(row=0, column=1)

                CymbalRowBellKeyOutputButton = nulltk.Button(CymbalRowBellInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("CenterKeyOutput")) or "Set Key", command=lambda: DetectKey(CymbalRowBellKeyOutputButton, Drum, "CenterKeyOutput","NullMidi"), width=22)
                CymbalRowBellKeyOutputButton.grid(row=0, column=2, sticky="ew")

                CymbalRowBellSounds = nulltk.LabelFrame(CymbalRowBellRow, text="Sounds")
                CymbalRowBellSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))
                SoundWidgets[CymbalRowBellSounds] = {"row": 2,"column": 0,"sticky": "ew","padx": 5,"pady": (2,10)}
                CymbalRowBellSounds.columnconfigure(0, weight=0)
                CymbalRowBellSounds.columnconfigure(1, weight=0)
                CymbalRowBellSounds.columnconfigure(2, weight=0)
                CymbalRowBellSounds.columnconfigure(3, weight=0)
                CymbalRowBellSounds.rowconfigure(0, weight=0)
                CymbalRowBellSounds.rowconfigure(1, weight=0)
                CymbalRowBellSounds.rowconfigure(2, weight=0)
                CymbalRowBellSounds.rowconfigure(3, weight=0)

                CymbalRowBellSoundLocationVar = tk.StringVar(value=Drum.get("CenterSoundFilePath", ""))
                BellVolumeVar = tk.IntVar(value=Drum.get("CenterVolume", 100))
                BellGhostNote = tk.IntVar(value=Drum.get("CenterGhostNoteThreshold", 100))
                BellSlam = tk.IntVar(value=Drum.get("CenterSlamNoteThreshold", 100))

                CymbalRowBellVolumeSliderLabel = nulltk.Label(CymbalRowBellSounds, text="Volume", width=12, height=2)
                CymbalRowBellVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                CymbalRowBellVolumeSlider = nulltk.Scale(CymbalRowBellSounds, from_=0, to=100, orient="horizontal", variable=BellVolumeVar, showvalue=False, length=35)
                CymbalRowBellVolumeSlider.grid(row=0, column=1, sticky="ew")

                CymbalRowBellVolumeShowLabel = nulltk.Label(CymbalRowBellSounds, textvariable=BellVolumeVar)
                CymbalRowBellVolumeShowLabel.grid(row=0, column=2, sticky="w")

                CymbalRowBellSoundPathLabel = nulltk.Label(CymbalRowBellSounds, text="Sound\nPath:",height=2, width=12, )
                CymbalRowBellSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                CymbalRowBellSoundLocationIF = nulltk.Entry(CymbalRowBellSounds, textvariable=CymbalRowBellSoundLocationVar, state="readonly", width=35)
                CymbalRowBellSoundLocationIF.grid(row=1, column=1, sticky="ew")

                CymbalRowBellBrowseButton = nulltk.Button(CymbalRowBellSounds, command=lambda: SearchForSoundFile(Drum, CymbalRowBellSoundLocationVar, "CenterSoundFilePath"), text="Browse", width=8)
                CymbalRowBellBrowseButton.grid(row=1, column=2)

                def UpdateBellVolume(*args):
                    Drum["CenterVolume"] = BellVolumeVar.get()
                    SaveConfig("NullMidi")

                def UpdateBellGhost(*args):
                    Drum["CenterGhostNoteThreshold"] = BellGhostNote.get()
                    SaveConfig("NullMidi")

                def UpdateBellSlam(*args):
                    Drum["CenterSlamNoteThreshold"] = BellSlam.get()
                    SaveConfig("NullMidi")

                CymbalRowBellGhostLabel = nulltk.Label(CymbalRowBellSounds, text="Ghost Note\n Velocity Cap", width=12, height=2)
                CymbalRowBellGhostLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                CymbalRowBellGhostSlider = nulltk.Scale(CymbalRowBellSounds, from_=1, to=127, orient="horizontal", variable=BellGhostNote, showvalue=False, length=35)
                CymbalRowBellGhostSlider.grid(row=2, column=1, sticky="ew")

                CymbalRowBellGhostShowLabel = nulltk.Label(CymbalRowBellSounds, textvariable=BellGhostNote)
                CymbalRowBellGhostShowLabel.grid(row=2, column=2, sticky="w")

                CymbalRowBellSlamLabel = nulltk.Label(CymbalRowBellSounds, text="Slam Note\n Velocity Min", width=12, height=2)
                CymbalRowBellSlamLabel.grid(row=3, column=0, sticky="e", pady=(0,8))

                CymbalRowBellSlamSlider = nulltk.Scale(CymbalRowBellSounds, from_=1, to=127, orient="horizontal", variable=BellSlam, showvalue=False, length=35)
                CymbalRowBellSlamSlider.grid(row=3, column=1, sticky="ew")

                CymbalRowBellSlamShowLabel = nulltk.Label(CymbalRowBellSounds, textvariable=BellSlam)
                CymbalRowBellSlamShowLabel.grid(row=3, column=2, sticky="w")

                Divider = nulltk.Frame(CymbalsContainer, width=2, bg="#555")
                Divider.grid(row=1, column=1, sticky="ns", padx=5)

                


                #------------ EdgeRow
                CymbalRowEdgeRow = nulltk.Frame(CymbalsContainer)
                CymbalRowEdgeRow.grid(row=1, column=2, sticky="ew", padx=2, pady=2)
                CymbalRowEdgeRow.rowconfigure(0, weight=1)
                CymbalRowEdgeRow.rowconfigure(1, weight=1)
                CymbalRowEdgeRow.rowconfigure(2, weight=0)
                CymbalRowEdgeRow.columnconfigure(0, weight=1)

                CymbalRowEdgeLabel = nulltk.Label(CymbalRowEdgeRow, text="Edge Of Cymbal", width=8, font=("TkDefaultFont", 12, "bold"))
                CymbalRowEdgeLabel.grid(row=0, column=0, sticky="ew")

                CymbalRowEdgeInputsFrame = nulltk.Frame(CymbalRowEdgeRow)
                CymbalRowEdgeInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                CymbalRowEdgeInputsLabel = nulltk.Label(CymbalRowEdgeInputsFrame, text="Inputs:", width=8)
                CymbalRowEdgeInputsLabel.grid(row=0, column=0)

                CymbalRowEdgeMidiInputButton = nulltk.Button(CymbalRowEdgeInputsFrame, text=("Set Midi" if Drum.get("RimMidiInput") is None else str(Drum.get("RimMidiInput"))), command=lambda: DetectNote(CymbalRowEdgeMidiInputButton, Row["Device"], Drum, "RimMidiInput"), width=22)
                CymbalRowEdgeMidiInputButton.grid(row=0, column=1)

                CymbalRowEdgeKeyOutputButton = nulltk.Button(CymbalRowEdgeInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("RimKeyOutput")) or "Set Key", command=lambda: DetectKey(CymbalRowEdgeKeyOutputButton, Drum, "RimKeyOutput","NullMidi"), width=22)
                CymbalRowEdgeKeyOutputButton.grid(row=0, column=2, sticky="ew")

                CymbalRowEdgeSounds = nulltk.LabelFrame(CymbalRowEdgeRow, text="Sounds")
                CymbalRowEdgeSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))
                SoundWidgets[CymbalRowEdgeSounds] = {"row": 2,"column": 0,"sticky": "ew","padx": 5,"pady": (2,10)}
                CymbalRowEdgeSounds.columnconfigure(0, weight=0)
                CymbalRowEdgeSounds.columnconfigure(1, weight=0)
                CymbalRowEdgeSounds.columnconfigure(2, weight=0)
                CymbalRowEdgeSounds.columnconfigure(3, weight=0)
                CymbalRowEdgeSounds.rowconfigure(0, weight=0)
                CymbalRowEdgeSounds.rowconfigure(1, weight=0)
                CymbalRowEdgeSounds.rowconfigure(2, weight=0)
                CymbalRowEdgeSounds.rowconfigure(3, weight=0)

                CymbalRowEdgeSoundLocationVar = tk.StringVar(value=Drum.get("RimSoundFilePath", ""))
                EdgeVolumeVar = tk.IntVar(value=Drum.get("RimVolume", 100))
                EdgeGhostNote = tk.IntVar(value=Drum.get("RimGhostNoteThreshold", 100))
                EdgeSlam = tk.IntVar(value=Drum.get("RimSlamNoteThreshold", 100))

                CymbalRowEdgeVolumeSliderLabel = nulltk.Label(CymbalRowEdgeSounds, text="Volume", width=12, height=2)
                CymbalRowEdgeVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                CymbalRowEdgeVolumeSlider = nulltk.Scale(CymbalRowEdgeSounds, from_=0, to=100, orient="horizontal", variable=EdgeVolumeVar, showvalue=False, length=22)
                CymbalRowEdgeVolumeSlider.grid(row=0, column=1, sticky="ew")

                CymbalRowEdgeVolumeShowLabel = nulltk.Label(CymbalRowEdgeSounds, textvariable=EdgeVolumeVar)
                CymbalRowEdgeVolumeShowLabel.grid(row=0, column=2, sticky="w")

                CymbalRowEdgeSoundPathLabel = nulltk.Label(CymbalRowEdgeSounds, text="Sound\nPath:", width=12, height=2)
                CymbalRowEdgeSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                CymbalRowEdgeSoundLocationIF = nulltk.Entry(CymbalRowEdgeSounds, textvariable=CymbalRowEdgeSoundLocationVar, state="readonly", width=22)
                CymbalRowEdgeSoundLocationIF.grid(row=1, column=1, sticky="ew")

                CymbalRowEdgeBrowseButton = nulltk.Button(CymbalRowEdgeSounds, command=lambda: SearchForSoundFile(Drum, CymbalRowEdgeSoundLocationVar, "RimSoundFilePath"), text="Browse", width=8)
                CymbalRowEdgeBrowseButton.grid(row=1, column=2)

                def UpdateEdgeVolume(*args):
                    Drum["RimVolume"] = EdgeVolumeVar.get()
                    SaveConfig("NullMidi")

                def UpdateEdgeGhost(*args):
                    Drum["RimGhostNoteThreshold"] = EdgeGhostNote.get()
                    SaveConfig("NullMidi")

                def UpdateEdgeSlam(*args):
                    Drum["RimSlamNoteThreshold"] = EdgeSlam.get()
                    SaveConfig("NullMidi")

                CymbalRowEdgeGhostLabel = nulltk.Label(CymbalRowEdgeSounds, text="Ghost Note\n Velocity Cap", width=12, height=2)
                CymbalRowEdgeGhostLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                CymbalRowEdgeGhostSlider = nulltk.Scale(CymbalRowEdgeSounds, from_=1, to=127, orient="horizontal", variable=EdgeGhostNote, showvalue=False, length=22)
                CymbalRowEdgeGhostSlider.grid(row=2, column=1, sticky="ew")

                CymbalRowEdgeGhostShowLabel = nulltk.Label(CymbalRowEdgeSounds, textvariable=EdgeGhostNote)
                CymbalRowEdgeGhostShowLabel.grid(row=2, column=2, sticky="w")

                CymbalRowEdgeSlamLabel = nulltk.Label(CymbalRowEdgeSounds, text="Slam Note\n Velocity Min", width=12, height=2)
                CymbalRowEdgeSlamLabel.grid(row=3, column=0, sticky="e", pady=(0,8))

                CymbalRowEdgeSlamSlider = nulltk.Scale(CymbalRowEdgeSounds, from_=1, to=127, orient="horizontal", variable=EdgeSlam, showvalue=False, length=22)
                CymbalRowEdgeSlamSlider.grid(row=3, column=1, sticky="ew")

                CymbalRowEdgeSlamShowLabel = nulltk.Label(CymbalRowEdgeSounds, textvariable=EdgeSlam)
                CymbalRowEdgeSlamShowLabel.grid(row=3, column=2, sticky="w")


                Divider = nulltk.Frame(CymbalsContainer, width=2, bg="#555")
                Divider.grid(row=1, column=3, sticky="ns", padx=5)

                #------------ BowRow
                CymbalRowBowRow = nulltk.Frame(CymbalsContainer)
                CymbalRowBowRow.grid(row=1, column=4, sticky="ew", padx=2, pady=2)
                CymbalRowBowRow.rowconfigure(0, weight=1)
                CymbalRowBowRow.rowconfigure(1, weight=1)
                CymbalRowBowRow.rowconfigure(2, weight=0)
                CymbalRowBowRow.columnconfigure(0, weight=1)

                CymbalRowBowLabel = nulltk.Label(CymbalRowBowRow, text="Bow Of Cymbal", width=8, font=("TkDefaultFont", 12, "bold"))
                CymbalRowBowLabel.grid(row=0, column=0, sticky="ew")

                CymbalRowBowInputsFrame = nulltk.Frame(CymbalRowBowRow)
                CymbalRowBowInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                CymbalRowBowInputsLabel = nulltk.Label(CymbalRowBowInputsFrame, text="Inputs:", width=8)
                CymbalRowBowInputsLabel.grid(row=0, column=0)

                CymbalRowBowMidiInputButton = nulltk.Button(CymbalRowBowInputsFrame, text=("Set Midi" if Drum.get("BowMidiInput") is None else str(Drum.get("BowMidiInput"))), command=lambda: DetectNote(CymbalRowBowMidiInputButton, Row["Device"], Drum, "BowMidiInput"), width=22)
                CymbalRowBowMidiInputButton.grid(row=0, column=1)

                CymbalRowBowKeyOutputButton = nulltk.Button(CymbalRowBowInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("BowKeyOutput")) or "Set Key", command=lambda: DetectKey(CymbalRowBowKeyOutputButton, Drum, "BowKeyOutput","NullMidi"), width=22)
                CymbalRowBowKeyOutputButton.grid(row=0, column=2, sticky="ew")

                CymbalRowBowSounds = nulltk.LabelFrame(CymbalRowBowRow, text="Sounds")
                CymbalRowBowSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))
                SoundWidgets[CymbalRowBowSounds] = {"row": 2,"column": 0,"sticky": "ew","padx": 5,"pady": (2,10)}
                CymbalRowBowSounds.columnconfigure(0, weight=0)
                CymbalRowBowSounds.columnconfigure(1, weight=0)
                CymbalRowBowSounds.columnconfigure(2, weight=0)
                CymbalRowBowSounds.columnconfigure(3, weight=0)
                CymbalRowBowSounds.rowconfigure(0, weight=0)
                CymbalRowBowSounds.rowconfigure(1, weight=0)
                CymbalRowBowSounds.rowconfigure(2, weight=0)
                CymbalRowBowSounds.rowconfigure(3, weight=0)

                CymbalRowBowSoundLocationVar = tk.StringVar(value=Drum.get("BowSoundFilePath", ""))
                BowVolumeVar = tk.IntVar(value=Drum.get("BowVolume", 100))
                BowGhostNote = tk.IntVar(value=Drum.get("BowGhostNoteThreshold", 100))
                BowSlam = tk.IntVar(value=Drum.get("BowSlamNoteThreshold", 100))

                CymbalRowBowVolumeSliderLabel = nulltk.Label(CymbalRowBowSounds, text="Volume", width=12, height=2)
                CymbalRowBowVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                CymbalRowBowVolumeSlider = nulltk.Scale(CymbalRowBowSounds, from_=0, to=100, orient="horizontal", variable=BowVolumeVar, showvalue=False, length=22)
                CymbalRowBowVolumeSlider.grid(row=0, column=1, sticky="ew")

                CymbalRowBowVolumeShowLabel = nulltk.Label(CymbalRowBowSounds, textvariable=BowVolumeVar)
                CymbalRowBowVolumeShowLabel.grid(row=0, column=2, sticky="w")

                CymbalRowBowSoundPathLabel = nulltk.Label(CymbalRowBowSounds, text="Sound\nPath:", width=12, height=2)
                CymbalRowBowSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                CymbalRowBowSoundLocationIF = nulltk.Entry(CymbalRowBowSounds, textvariable=CymbalRowBowSoundLocationVar, state="readonly", width=22)
                CymbalRowBowSoundLocationIF.grid(row=1, column=1, sticky="ew")

                CymbalRowBowBrowseButton = nulltk.Button(CymbalRowBowSounds, command=lambda: SearchForSoundFile(Drum, CymbalRowBowSoundLocationVar, "BowSoundFilePath"), text="Browse", width=8)
                CymbalRowBowBrowseButton.grid(row=1, column=2)

                def UpdateBowVolume(*args):
                    Drum["BowVolume"] = BowVolumeVar.get()
                    SaveConfig("NullMidi")

                def UpdateBowGhost(*args):
                    Drum["BowGhostNoteThreshold"] = BowGhostNote.get()
                    SaveConfig("NullMidi")

                def UpdateBowSlam(*args):
                    Drum["BowSlamNoteThreshold"] = BowSlam.get()
                    SaveConfig("NullMidi")

                CymbalRowBowGhostLabel = nulltk.Label(CymbalRowBowSounds, text="Ghost Note\n Velocity Cap", width=12, height=2)
                CymbalRowBowGhostLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                CymbalRowBowGhostSlider = nulltk.Scale(CymbalRowBowSounds, from_=1, to=127, orient="horizontal", variable=BowGhostNote, showvalue=False, length=22)
                CymbalRowBowGhostSlider.grid(row=2, column=1, sticky="ew")

                CymbalRowBowGhostShowLabel = nulltk.Label(CymbalRowBowSounds, textvariable=BowGhostNote)
                CymbalRowBowGhostShowLabel.grid(row=2, column=2, sticky="w")

                CymbalRowBowSlamLabel = nulltk.Label(CymbalRowBowSounds, text="Slam Note\n Velocity Min", width=12, height=2)
                CymbalRowBowSlamLabel.grid(row=3, column=0, sticky="e", pady=(0,8))

                CymbalRowBowSlamSlider = nulltk.Scale(CymbalRowBowSounds, from_=1, to=127, orient="horizontal", variable=BowSlam, showvalue=False, length=22)
                CymbalRowBowSlamSlider.grid(row=3, column=1, sticky="ew")

                CymbalRowBowSlamShowLabel = nulltk.Label(CymbalRowBowSounds, textvariable=BowSlam)
                CymbalRowBowSlamShowLabel.grid(row=3, column=2, sticky="w")

                MidiScrollBox.BindMouseWheel(Frame)

                SetupSlider(CymbalRowBellVolumeSlider, BellVolumeVar, 0, 100, UpdateBellVolume)

                SetupSlider(CymbalRowBellGhostSlider, BellGhostNote, 0, 127, UpdateBellGhost)

                SetupSlider(CymbalRowBellSlamSlider, BellSlam, 0, 127, UpdateBellSlam)

                SetupSlider(CymbalRowEdgeVolumeSlider, EdgeVolumeVar, 0, 100, UpdateEdgeVolume)

                SetupSlider(CymbalRowEdgeGhostSlider, EdgeGhostNote, 0, 127, UpdateEdgeGhost)

                SetupSlider(CymbalRowEdgeSlamSlider, EdgeSlam, 0, 127, UpdateEdgeSlam)

                SetupSlider(CymbalRowBowVolumeSlider, BowVolumeVar, 0, 100, UpdateBowVolume)

                SetupSlider(CymbalRowBowGhostSlider, BowGhostNote, 0, 127, UpdateBowGhost)

                SetupSlider(CymbalRowBowSlamSlider, BowSlam, 0, 127, UpdateBowSlam)

                CollapseCymbal(Drum, CymbalsContainer, Loading)
                UpdateMuted()

            def SetupKickRow(Loading=False):
                SoundWidgets.clear()
                KickRowTopRow = nulltk.Frame(DrumRowKickRow)
                KickRowTopRow.grid(row=0, column=0, sticky="ew", padx=2)

                KickRowTopRow.columnconfigure(0, weight=0 )
                KickRowTopRow.columnconfigure(1, weight=0 )
                KickRowTopRow.columnconfigure(2, weight=0 )
                KickRowTopRow.columnconfigure(3, weight=0 )
                KickRowTopRow.rowconfigure(0, weight=0 )

                KickCollapseButton = nulltk.Button(KickRowTopRow, text="▼", command=lambda:CollapseKick(Drum, KickContainer), width = 2)
                KickCollapseButton.grid(row=0, column=0, sticky="ew", padx=2)

                def CollapseKick(Drum, KickContainer, Loading=False):
                    if Loading:
                        if Drum['Collapsed']:
                            KickContainer.grid_forget()
                            KickCollapseButton.config(text="▶")
                        else:
                            KickContainer.grid(row=1, column=0, sticky="ew", padx=2)
                            KickCollapseButton.config(text="▼")
                        return

                    if Drum['Collapsed']:
                        KickContainer.grid(row=1, column=0, sticky="ew", padx=2)
                        KickCollapseButton.config(text="▼")
                        Drum['Collapsed'] =  False
                    else:
                        KickContainer.grid_forget()
                        KickCollapseButton.config(text="▶")
                        Drum['Collapsed'] =  True

                        
                        
                    SaveConfig("NullMidi")

                DrumRowDrumToMainToggle = nulltk.Checkbutton(KickRowTopRow, text="Bass", variable=DrumRowAlwaysTruePad, command=lambda:SwitchDrumType("Main"))
                DrumRowDrumToMainToggle.grid(row=0, column=1, sticky="ew", padx=2)
                Divider = nulltk.Frame(KickRowTopRow,width=2,bg="#555")
                Divider.grid(row=0,column=2,sticky="ns",padx=5)

                RemoveDrumObjectFromList= nulltk.Button(KickRowTopRow, text="Remove Drum", command=lambda:RemoveDrum(Drum, RemoveDrumObjectFromList))
                RemoveDrumObjectFromList.grid(row=0, column=3, sticky="ew", padx=2)

                KickContainer = nulltk.Frame(DrumRowKickRow)
                KickContainer.grid(row=1, column=0, sticky="ew", padx=2)
                KickContainer.columnconfigure(0,weight=1)



                #---kicks
                DrumRowKickPad = nulltk.Frame(KickContainer)
                DrumRowKickPad.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                DrumRowKickPad.rowconfigure(0, weight=1)
                DrumRowKickPad.rowconfigure(1, weight=1)
                DrumRowKickPad.rowconfigure(2, weight=0)
                DrumRowKickPad.columnconfigure(0, weight=1)

                DrumRowKickLabel = nulltk.Label(DrumRowKickPad,text="Kick Drum",width=8,font=("TkDefaultFont", 12, "bold"))
                DrumRowKickLabel.grid(row=0, column=0, sticky="ew")

                DrumRowKickInputsFrame = nulltk.Frame(DrumRowKickPad)
                DrumRowKickInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                DrumRowKickInputsLabel = nulltk.Label(DrumRowKickInputsFrame,text="Inputs:",width=8)
                DrumRowKickInputsLabel.grid(row=0, column=0)

                DrumRowKickMidiInputButton = nulltk.Button(DrumRowKickInputsFrame,text=("Set Midi" if Drum.get("CenterMidiInput") is None else str(Drum.get("CenterMidiInput"))),command=lambda: DetectNote(DrumRowKickMidiInputButton,Row["Device"],Drum,"CenterMidiInput"),width=22)
                DrumRowKickMidiInputButton.grid(row=0, column=1)

                DrumRowKickKeyOutputButton = nulltk.Button(DrumRowKickInputsFrame,text="+".join(FormatKeyName(K)for K in Drum.get("CenterKeyOutput")) or "Set Key",command=lambda: DetectKey(DrumRowKickKeyOutputButton,Drum,"CenterKeyOutput","NullMidi"),width=22)
                DrumRowKickKeyOutputButton.grid(row=0, column=2, sticky="ew")


                DrumRowKickSounds = nulltk.LabelFrame(DrumRowKickPad,text="Sounds")
                DrumRowKickSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))
                SoundWidgets[DrumRowKickSounds] = {"row": 2,"column": 0,"sticky": "ew","padx": 5,"pady": (2,10)}

                DrumRowKickSounds.columnconfigure(0,weight=0)
                DrumRowKickSounds.columnconfigure(1,weight=0)
                DrumRowKickSounds.columnconfigure(2,weight=0)

                CenterVolumeVar = tk.IntVar(value=Drum.get("CenterVolume", 75))
                KickDrumMinimumVelocityVar = tk.IntVar(value=Drum.get("KickDrumMinimumVelocity", 85))
                DrumRowKickSoundLocationVar = tk.StringVar(value=Drum.get("CenterSoundFilePath", ""))


                DrumRowKickVolumeSliderLabel = nulltk.Label(DrumRowKickSounds,text="Volume",width=12,height=2)
                DrumRowKickVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                DrumRowKickVolumeSlider = nulltk.Scale(DrumRowKickSounds,from_=0,to=100,orient="horizontal",variable=CenterVolumeVar,showvalue=False,length=44)
                DrumRowKickVolumeSlider.grid(row=0, column=1, sticky="ew")

                DrumRowKickVolumeShowLabel = nulltk.Label(DrumRowKickSounds,textvariable=CenterVolumeVar)
                DrumRowKickVolumeShowLabel.grid(row=0, column=2, sticky="w")


                DrumRowKickSoundPathLabel = nulltk.Label(DrumRowKickSounds,text="Sound\nPath:",width=12,height=2)
                DrumRowKickSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                DrumRowKickSoundLocationIF = nulltk.Entry(DrumRowKickSounds,textvariable=DrumRowKickSoundLocationVar,state="readonly",width=44)
                DrumRowKickSoundLocationIF.grid(row=1, column=1, sticky="ew")

                DrumRowKickBrowseButton = nulltk.Button(DrumRowKickSounds,command=lambda: SearchForSoundFile(Drum,DrumRowKickSoundLocationVar, "CenterSoundFilePath"),text="Browse",width=8)
                DrumRowKickBrowseButton.grid(row=1, column=2)


                def UpdateKickVolume(*args):
                    Drum["CenterVolume"] = CenterVolumeVar.get()
                    SaveConfig("NullMidi")


                def UpdateKickMinimumVelocity(*args):
                    Drum["KickDrumMinimumVelocity"] = KickDrumMinimumVelocityVar.get()
                    SaveConfig("NullMidi")


                DrumRowKickMinimumVelocityLabel = nulltk.Label(DrumRowKickSounds,text="Minimum Kick\nVelocity",width=12,height=2)
                DrumRowKickMinimumVelocityLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                DrumRowKickMinimumVelocitySlider = nulltk.Scale(DrumRowKickSounds,from_=1,to=127,orient="horizontal",variable=KickDrumMinimumVelocityVar,showvalue=False,length=44)
                DrumRowKickMinimumVelocitySlider.grid(row=2, column=1, sticky="ew")

                DrumRowKickMinimumVelocityShowLabel = nulltk.Label(DrumRowKickSounds,textvariable=KickDrumMinimumVelocityVar)
                DrumRowKickMinimumVelocityShowLabel.grid(row=2, column=2, sticky="w")

                MidiScrollBox.BindMouseWheel(Frame)

                SetupSlider(DrumRowKickVolumeSlider, CenterVolumeVar, 0, 100, UpdateKickVolume)

                SetupSlider(DrumRowKickMinimumVelocitySlider, KickDrumMinimumVelocityVar, 0, 127, UpdateKickMinimumVelocity)

                CollapseKick(Drum, KickContainer, Loading)
                UpdateMuted()

            def SetupHihatRow(Loading=False):
                SoundWidgets.clear()

                HihatRowTopRow = nulltk.Frame(DrumRowHihatRow)
                HihatRowTopRow.grid(row=0, column=0, sticky="ew", padx=2)

                HihatRowTopRow.columnconfigure(0, weight=0)
                HihatRowTopRow.columnconfigure(1, weight=0)
                HihatRowTopRow.columnconfigure(2, weight=0)
                HihatRowTopRow.columnconfigure(3, weight=0)
                HihatRowTopRow.rowconfigure(0, weight=0)

                HihatContainer = nulltk.Frame(DrumRowHihatRow)
                HihatContainer.grid(row=1, column=0, sticky="ew", padx=2)

                HihatContainer.columnconfigure(0, weight=1)
                HihatContainer.columnconfigure(1, weight=1)
                HihatContainer.columnconfigure(2, weight=1)
                HihatContainer.columnconfigure(3, weight=1)
                HihatContainer.columnconfigure(4, weight=1)

                HihatContainer.rowconfigure(0, weight=1)
                HihatContainer.rowconfigure(1, weight=1)

                def CollapseHiHat(Drum, HihatContainer, Loading=False):
                    
                    if Loading:
                        if Drum['Collapsed']:
                            HihatContainer.grid_forget()
                            HihatCollapseButton.config(text="▶")
                        else:
                            HihatContainer.grid(row=1, column=0, sticky="ew", padx=2)
                            HihatCollapseButton.config(text="▼")
                        return
                    
                    
                    if Drum['Collapsed']:
                        HihatContainer.grid(row=1, column=0, sticky="ew", padx=2)
                        HihatCollapseButton.config(text="▼")
                        if not Loading:
                            Drum['Collapsed'] = False
                        
                    else:
                        HihatContainer.grid_forget()
                        HihatCollapseButton.config(text="▶")
                        if not Loading:
                            Drum['Collapsed'] = True
                    SaveConfig("NullMidi")

                HihatCollapseButton = nulltk.Button(HihatRowTopRow, text="▼", command=lambda:CollapseHiHat(Drum, HihatContainer), width=2)
                HihatCollapseButton.grid(row=0, column=0, sticky="ew", padx=2)

                HihatRowToMainToggle = nulltk.Checkbutton(HihatRowTopRow, text="HiHat", variable=DrumRowAlwaysTrueHiHat, command=lambda:SwitchDrumType("Main"))
                HihatRowToMainToggle.grid(row=0, column=1, sticky="ew", padx=2)

                Divider = nulltk.Frame(HihatRowTopRow, width=2, bg="#555")
                Divider.grid(row=0, column=2, sticky="ns", padx=5)

                RemoveHiHatObjectFromList = nulltk.Button(HihatRowTopRow, text="Delete Drum", command=lambda:RemoveDrum(Drum, RemoveHiHatObjectFromList))
                RemoveHiHatObjectFromList.grid(row=0, column=3, sticky="ew", padx=2)



                #------------ ClosedRow
                HihatRowClosedRow = nulltk.Frame(HihatContainer)
                HihatRowClosedRow.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

                HihatRowClosedRow.rowconfigure(0, weight=1)
                HihatRowClosedRow.rowconfigure(1, weight=1)
                HihatRowClosedRow.rowconfigure(2, weight=0)
                HihatRowClosedRow.columnconfigure(0, weight=1)

                HihatRowClosedLabel = nulltk.Label(HihatRowClosedRow, text="Closed HiHat", width=8, font=("TkDefaultFont", 12, "bold"))
                HihatRowClosedLabel.grid(row=0, column=0, sticky="ew")

                HihatRowClosedInputsFrame = nulltk.Frame(HihatRowClosedRow)
                HihatRowClosedInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                HihatRowClosedInputsLabel = nulltk.Label(HihatRowClosedInputsFrame, text="Inputs:", width=8)
                HihatRowClosedInputsLabel.grid(row=0, column=0)

                HihatRowClosedMidiInputButton = nulltk.Button(HihatRowClosedInputsFrame, text=("Set Midi" if Drum.get("HiHatClosedMidiInput") is None else str(Drum.get("HiHatClosedMidiInput"))), command=lambda: DetectNote(HihatRowClosedMidiInputButton, Row["Device"], Drum, "HiHatClosedMidiInput"), width=22)
                HihatRowClosedMidiInputButton.grid(row=0, column=1)

                HihatRowClosedKeyOutputButton = nulltk.Button(HihatRowClosedInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("HiHatClosedKeyOutput")) or "Set Key", command=lambda: DetectKey(HihatRowClosedKeyOutputButton, Drum, "HiHatClosedKeyOutput","NullMidi"), width=22)
                HihatRowClosedKeyOutputButton.grid(row=0, column=2, sticky="ew")

                HihatRowClosedSounds = nulltk.LabelFrame(HihatRowClosedRow, text="Sounds")
                HihatRowClosedSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))

                SoundWidgets[HihatRowClosedSounds] = {"row": 2, "column": 0, "sticky": "ew", "padx": 5, "pady": (2,10)}

                HihatRowClosedSounds.columnconfigure(0, weight=0)
                HihatRowClosedSounds.columnconfigure(1, weight=0)
                HihatRowClosedSounds.columnconfigure(2, weight=0)

                HihatRowClosedSoundLocationVar = tk.StringVar(value=Drum.get("HiHatClosedPath", ""))
                ClosedVolumeVar = tk.IntVar(value=Drum.get("HiHatClosedVolume", 75))
                ClosedThresholdVar = tk.IntVar(value=Drum.get("HiHatClosedThreshold", 100))

                HihatRowClosedVolumeSliderLabel = nulltk.Label(HihatRowClosedSounds, text="Volume", width=12, height=2)
                HihatRowClosedVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                HihatRowClosedVolumeSlider = nulltk.Scale(HihatRowClosedSounds, from_=0, to=100, orient="horizontal", variable=ClosedVolumeVar, showvalue=False, length=22)
                HihatRowClosedVolumeSlider.grid(row=0, column=1, sticky="ew")

                HihatRowClosedVolumeShowLabel = nulltk.Label(HihatRowClosedSounds, textvariable=ClosedVolumeVar)
                HihatRowClosedVolumeShowLabel.grid(row=0, column=2, sticky="w")

                HihatRowClosedSoundPathLabel = nulltk.Label(HihatRowClosedSounds, text="Sound\nPath:", width=12, height=2)
                HihatRowClosedSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                HihatRowClosedSoundLocationIF = nulltk.Entry(HihatRowClosedSounds, textvariable=HihatRowClosedSoundLocationVar, state="readonly", width=22)
                HihatRowClosedSoundLocationIF.grid(row=1, column=1, sticky="ew")

                HihatRowClosedBrowseButton = nulltk.Button(HihatRowClosedSounds, command=lambda: SearchForSoundFile(Drum, HihatRowClosedSoundLocationVar, "HiHatClosedPath"), text="Browse", width=8)
                HihatRowClosedBrowseButton.grid(row=1, column=2)

                def UpdateClosedVolume(*args):
                    Drum["HiHatClosedVolume"] = ClosedVolumeVar.get()
                    SaveConfig("NullMidi")

                def UpdateClosedThreshold(*args):
                    Drum["HiHatClosedThreshold"] = ClosedThresholdVar.get()
                    SaveConfig("NullMidi")

                HihatRowClosedThresholdLabel = nulltk.Label(HihatRowClosedSounds, text="Closed\nThreshold", width=12, height=2)
                HihatRowClosedThresholdLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                HihatRowClosedThresholdSlider = nulltk.Scale(HihatRowClosedSounds, from_=0, to=127, orient="horizontal", variable=ClosedThresholdVar, showvalue=False, length=22)
                HihatRowClosedThresholdSlider.grid(row=2, column=1, sticky="ew")

                HihatRowClosedThresholdShowLabel = nulltk.Label(HihatRowClosedSounds, textvariable=ClosedThresholdVar)
                HihatRowClosedThresholdShowLabel.grid(row=2, column=2, sticky="w")

                

                Divider = nulltk.Frame(HihatContainer, width=2, bg="#555")
                Divider.grid(row=0, column=1, sticky="ns", padx=5)

                                #------------ HalfRow
                HihatRowHalfRow = nulltk.Frame(HihatContainer)
                HihatRowHalfRow.grid(row=0, column=2, sticky="ew", padx=2, pady=2)

                HihatRowHalfRow.rowconfigure(0, weight=1)
                HihatRowHalfRow.rowconfigure(1, weight=1)
                HihatRowHalfRow.rowconfigure(2, weight=0)
                HihatRowHalfRow.columnconfigure(0, weight=1)

                HihatRowHalfLabel = nulltk.Label(HihatRowHalfRow, text="Half HiHat", width=8, font=("TkDefaultFont", 12, "bold"))
                HihatRowHalfLabel.grid(row=0, column=0, sticky="ew")

                HihatRowHalfInputsFrame = nulltk.Frame(HihatRowHalfRow)
                HihatRowHalfInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                HihatRowHalfInputsLabel = nulltk.Label(HihatRowHalfInputsFrame, text="Inputs:", width=8)
                HihatRowHalfInputsLabel.grid(row=0, column=0)

                HihatRowHalfMidiInputButton = nulltk.Button(HihatRowHalfInputsFrame, text=("Set Midi" if Drum.get("HiHatHalfMidiInput") is None else str(Drum.get("HiHatHalfMidiInput"))), command=lambda: DetectNote(HihatRowHalfMidiInputButton, Row["Device"], Drum, "HiHatHalfMidiInput"), width=22)
                HihatRowHalfMidiInputButton.grid(row=0, column=1)

                HihatRowHalfKeyOutputButton = nulltk.Button(HihatRowHalfInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("HiHatHalfKeyOutput")) or "Set Key", command=lambda: DetectKey(HihatRowHalfKeyOutputButton, Drum, "HiHatHalfKeyOutput","NullMidi"), width=22)
                HihatRowHalfKeyOutputButton.grid(row=0, column=2, sticky="ew")

                

                HihatRowHalfSounds = nulltk.LabelFrame(HihatRowHalfRow, text="Sounds")
                HihatRowHalfSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))

                SoundWidgets[HihatRowHalfSounds] = {"row": 2, "column": 0, "sticky": "ew", "padx": 5, "pady": (2,10)}

                HihatRowHalfSounds.columnconfigure(0, weight=0)
                HihatRowHalfSounds.columnconfigure(1, weight=0)
                HihatRowHalfSounds.columnconfigure(2, weight=0)

                HihatRowHalfSoundLocationVar = tk.StringVar(value=Drum.get("HiHatHalfPath", ""))
                HalfVolumeVar = tk.IntVar(value=Drum.get("HiHatHalfVolume", 75))
                

                HihatRowHalfVolumeSliderLabel = nulltk.Label(HihatRowHalfSounds, text="Volume", width=12, height=2)
                HihatRowHalfVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                HihatRowHalfVolumeSlider = nulltk.Scale(HihatRowHalfSounds, from_=0, to=100, orient="horizontal", variable=HalfVolumeVar, showvalue=False, length=22)
                HihatRowHalfVolumeSlider.grid(row=0, column=1, sticky="ew")

                HihatRowHalfVolumeShowLabel = nulltk.Label(HihatRowHalfSounds, textvariable=HalfVolumeVar)
                HihatRowHalfVolumeShowLabel.grid(row=0, column=2, sticky="w")

                HihatRowHalfSoundPathLabel = nulltk.Label(HihatRowHalfSounds, text="Sound\nPath:", width=12, height=2)
                HihatRowHalfSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                HihatRowHalfSoundLocationIF = nulltk.Entry(HihatRowHalfSounds, textvariable=HihatRowHalfSoundLocationVar, state="readonly", width=22)
                HihatRowHalfSoundLocationIF.grid(row=1, column=1, sticky="ew")

                HihatRowHalfBrowseButton = nulltk.Button(HihatRowHalfSounds, command=lambda: SearchForSoundFile(Drum, HihatRowHalfSoundLocationVar, "HiHatHalfPath"), text="Browse", width=8)
                HihatRowHalfBrowseButton.grid(row=1, column=2)

                def UpdateHalfVolume(*args):
                    Drum["HiHatHalfVolume"] = HalfVolumeVar.get()
                    SaveConfig("NullMidi")

                
                Divider = nulltk.Frame(HihatContainer, width=2, bg="#555")
                Divider.grid(row=0, column=3, sticky="ns", padx=5)



                #------------ OpenRow
                HihatRowOpenRow = nulltk.Frame(HihatContainer)
                HihatRowOpenRow.grid(row=0, column=4, sticky="ew", padx=2, pady=2)

                HihatRowOpenRow.rowconfigure(0, weight=1)
                HihatRowOpenRow.rowconfigure(1, weight=1)
                HihatRowOpenRow.rowconfigure(2, weight=0)
                HihatRowOpenRow.columnconfigure(0, weight=1)

                HihatRowOpenLabel = nulltk.Label(HihatRowOpenRow, text="Open HiHat", width=8, font=("TkDefaultFont", 12, "bold"))
                HihatRowOpenLabel.grid(row=0, column=0, sticky="ew")

                HihatRowOpenInputsFrame = nulltk.Frame(HihatRowOpenRow)
                HihatRowOpenInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                HihatRowOpenInputsLabel = nulltk.Label(HihatRowOpenInputsFrame, text="Inputs:", width=8)
                HihatRowOpenInputsLabel.grid(row=0, column=0)

                HihatRowOpenMidiInputButton = nulltk.Button(HihatRowOpenInputsFrame, text=("Set Midi" if Drum.get("HiHatOpenMidiInput") is None else str(Drum.get("HiHatOpenMidiInput"))), command=lambda: DetectNote(HihatRowOpenMidiInputButton, Row["Device"], Drum, "HiHatOpenMidiInput"), width=22)
                HihatRowOpenMidiInputButton.grid(row=0, column=1)

                HihatRowOpenKeyOutputButton = nulltk.Button(HihatRowOpenInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("HiHatOpenKeyOutput")) or "Set Key", command=lambda: DetectKey(HihatRowOpenKeyOutputButton, Drum, "HiHatOpenKeyOutput","NullMidi"), width=22)
                HihatRowOpenKeyOutputButton.grid(row=0, column=2, sticky="ew")

                HihatRowOpenSounds = nulltk.LabelFrame(HihatRowOpenRow, text="Sounds")
                HihatRowOpenSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))

                SoundWidgets[HihatRowOpenSounds] = {"row": 2, "column": 0, "sticky": "ew", "padx": 5, "pady": (2,10)}

                HihatRowOpenSounds.columnconfigure(0, weight=0)
                HihatRowOpenSounds.columnconfigure(1, weight=0)
                HihatRowOpenSounds.columnconfigure(2, weight=0)

                HihatRowOpenSoundLocationVar = tk.StringVar(value=Drum.get("HiHatOpenPath", ""))
                OpenVolumeVar = tk.IntVar(value=Drum.get("HiHatOpenVolume", 75))
                OpenThresholdVar = tk.IntVar(value=Drum.get("HiHatOpenThreshold", 0))

                HihatRowOpenVolumeSliderLabel = nulltk.Label(HihatRowOpenSounds, text="Volume", width=12, height=2)
                HihatRowOpenVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                HihatRowOpenVolumeSlider = nulltk.Scale(HihatRowOpenSounds, from_=0, to=100, orient="horizontal", variable=OpenVolumeVar, showvalue=False, length=22)
                HihatRowOpenVolumeSlider.grid(row=0, column=1, sticky="ew")

                HihatRowOpenVolumeShowLabel = nulltk.Label(HihatRowOpenSounds, textvariable=OpenVolumeVar)
                HihatRowOpenVolumeShowLabel.grid(row=0, column=2, sticky="w")

                HihatRowOpenSoundPathLabel = nulltk.Label(HihatRowOpenSounds, text="Sound\nPath:", width=12, height=2)
                HihatRowOpenSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                HihatRowOpenSoundLocationIF = nulltk.Entry(HihatRowOpenSounds, textvariable=HihatRowOpenSoundLocationVar, state="readonly", width=22)
                HihatRowOpenSoundLocationIF.grid(row=1, column=1, sticky="ew")

                HihatRowOpenBrowseButton = nulltk.Button(HihatRowOpenSounds, command=lambda: SearchForSoundFile(Drum, HihatRowOpenSoundLocationVar, "HiHatOpenPath"), text="Browse", width=8)
                HihatRowOpenBrowseButton.grid(row=1, column=2)

                def UpdateOpenVolume(*args):
                    Drum["HiHatOpenVolume"] = OpenVolumeVar.get()
                    SaveConfig("NullMidi")

                def UpdateOpenThreshold(*args):
                    Drum["HiHatOpenThreshold"] = OpenThresholdVar.get()
                    SaveConfig("NullMidi")

                HihatRowOpenThresholdLabel = nulltk.Label(HihatRowOpenSounds, text="Open\nThreshold", width=12, height=2)
                HihatRowOpenThresholdLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                HihatRowOpenThresholdSlider = nulltk.Scale(HihatRowOpenSounds, from_=0, to=127, orient="horizontal", variable=OpenThresholdVar, showvalue=False, length=22)
                HihatRowOpenThresholdSlider.grid(row=2, column=1, sticky="ew")

                HihatRowOpenThresholdShowLabel = nulltk.Label(HihatRowOpenSounds, textvariable=OpenThresholdVar)
                HihatRowOpenThresholdShowLabel.grid(row=2, column=2, sticky="w")

                


                #------------ StompRow
                HihatRowStompRow = nulltk.Frame(HihatContainer)
                HihatRowStompRow.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                HihatRowStompRow.rowconfigure(0, weight=1)
                HihatRowStompRow.rowconfigure(1, weight=1)
                HihatRowStompRow.rowconfigure(2, weight=0)
                HihatRowStompRow.columnconfigure(0, weight=1)

                HihatRowStompLabel = nulltk.Label(HihatRowStompRow, text="HiHat Stomp", width=8, font=("TkDefaultFont", 12, "bold"))
                HihatRowStompLabel.grid(row=0, column=0, sticky="ew")

                HihatRowStompInputsFrame = nulltk.Frame(HihatRowStompRow)
                HihatRowStompInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                HihatRowStompInputsLabel = nulltk.Label(HihatRowStompInputsFrame, text="Inputs:", width=8)
                HihatRowStompInputsLabel.grid(row=0, column=0)

                HihatRowStompMidiInputButton = nulltk.Button(HihatRowStompInputsFrame, text=("Set Midi" if Drum.get("HiHatStompMidiInput") is None else str(Drum.get("HiHatStompMidiInput"))), command=lambda: DetectNote(HihatRowStompMidiInputButton, Row["Device"], Drum, "HiHatStompMidiInput"), width=22)
                HihatRowStompMidiInputButton.grid(row=0, column=1)

                HihatRowStompKeyOutputButton = nulltk.Button(HihatRowStompInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("HiHatStompKeyOutput")) or "Set Key", command=lambda: DetectKey(HihatRowStompKeyOutputButton, Drum, "HiHatStompKeyOutput","NullMidi"), width=22)
                HihatRowStompKeyOutputButton.grid(row=0, column=2, sticky="ew")

                HihatRowStompSounds = nulltk.LabelFrame(HihatRowStompRow, text="Sounds")
                HihatRowStompSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))

                SoundWidgets[HihatRowStompSounds] = {"row": 2, "column": 0, "sticky": "ew", "padx": 5, "pady": (2,10)}

                HihatRowStompSounds.columnconfigure(0, weight=0)
                HihatRowStompSounds.columnconfigure(1, weight=0)
                HihatRowStompSounds.columnconfigure(2, weight=0)

                HihatRowStompSoundLocationVar = tk.StringVar(value=Drum.get("HiHatStompPath", ""))
                StompVolumeVar = tk.IntVar(value=Drum.get("HiHatStompVolume", 100))

                HihatRowStompVolumeSliderLabel = nulltk.Label(HihatRowStompSounds, text="Volume", width=12, height=2)
                HihatRowStompVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                HihatRowStompVolumeSlider = nulltk.Scale(HihatRowStompSounds, from_=0, to=100, orient="horizontal", variable=StompVolumeVar, showvalue=False, length=22)
                HihatRowStompVolumeSlider.grid(row=0, column=1, sticky="ew")

                HihatRowStompVolumeShowLabel = nulltk.Label(HihatRowStompSounds, textvariable=StompVolumeVar)
                HihatRowStompVolumeShowLabel.grid(row=0, column=2, sticky="w")

                HihatRowStompSoundPathLabel = nulltk.Label(HihatRowStompSounds, text="Sound\nPath:", width=12, height=2)
                HihatRowStompSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                HihatRowStompSoundLocationIF = nulltk.Entry(HihatRowStompSounds, textvariable=HihatRowStompSoundLocationVar, state="readonly", width=22)
                HihatRowStompSoundLocationIF.grid(row=1, column=1, sticky="ew")

                HihatRowStompBrowseButton = nulltk.Button(HihatRowStompSounds, command=lambda: SearchForSoundFile(Drum, HihatRowStompSoundLocationVar, "HiHatStompPath"), text="Browse", width=8)
                HihatRowStompBrowseButton.grid(row=1, column=2)

                HihatRowStompSoundLocationVar = tk.StringVar(value=Drum.get("HiHatStompPath", ""))

                def UpdateStompVolume(*args):
                    Drum["HiHatStompVolume"] = StompVolumeVar.get()
                    SaveConfig("NullMidi")

                

                HihatOpenFadeInVar = tk.IntVar(value=Drum.get("HiHatFadeIn", 60))

                HihatRowOpenFadeInSliderLabel = nulltk.Label(HihatRowStompSounds, text="Open Fade In", width=12, height=2)
                HihatRowOpenFadeInSliderLabel.grid(row=2, column=0, sticky="e", pady=(0,8))

                HihatRowOpenFadeInSlider = nulltk.Scale(HihatRowStompSounds, from_=0, to=500, orient="horizontal", variable=HihatOpenFadeInVar, showvalue=False, length=22)
                HihatRowOpenFadeInSlider.grid(row=2, column=1, sticky="ew")

                HihatRowFadeInShowLabel = nulltk.Label(HihatRowStompSounds, textvariable=HihatOpenFadeInVar)
                HihatRowFadeInShowLabel.grid(row=2, column=2, sticky="w")

                def UpdateFadeIn(*args):
                    Drum["HiHatFadeIn"] = HihatOpenFadeInVar.get()
                    SaveConfig("NullMidi")

                

                HihatOpenTimeVar = tk.IntVar(value=Drum.get("HiHatOpenTime", 75))

                HihatRowOpenTimeSliderLabel = nulltk.Label(HihatRowStompSounds, text="Time To\n Open HiHats", width=12, height=2)
                HihatRowOpenTimeSliderLabel.grid(row=3, column=0, sticky="e", pady=(0,8))

                HihatRowOpenTimeSlider = nulltk.Scale(HihatRowStompSounds, from_=0, to=500, orient="horizontal", variable=HihatOpenTimeVar, showvalue=False, length=22)
                HihatRowOpenTimeSlider.grid(row=3, column=1, sticky="ew")

                HihatRowTimeShowLabel = nulltk.Label(HihatRowStompSounds, textvariable=HihatOpenTimeVar)
                HihatRowTimeShowLabel.grid(row=3, column=2, sticky="w")

                def UpdateHiHatOpenTime(*args):
                    Drum["HiHatOpenTime"] = HihatOpenTimeVar.get()
                    SaveConfig("NullMidi")


                Divider = nulltk.Frame(HihatContainer, width=2, bg="#555")
                Divider.grid(row=1, column=1, sticky="ns", padx=5)



                #------------ BellOpenRow
                HihatRowBellOpenRow = nulltk.Frame(HihatContainer)
                HihatRowBellOpenRow.grid(row=1, column=2, sticky="ew", padx=2, pady=2)

                HihatRowBellOpenRow.rowconfigure(0, weight=1)
                HihatRowBellOpenRow.rowconfigure(1, weight=1)
                HihatRowBellOpenRow.rowconfigure(2, weight=0)
                HihatRowBellOpenRow.columnconfigure(0, weight=1)

                HihatRowBellOpenLabel = nulltk.Label(HihatRowBellOpenRow, text="Bell Open HiHat", width=8, font=("TkDefaultFont", 12, "bold"))
                HihatRowBellOpenLabel.grid(row=0, column=0, sticky="ew")

                HihatRowBellOpenInputsFrame = nulltk.Frame(HihatRowBellOpenRow)
                HihatRowBellOpenInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                HihatRowBellOpenInputsLabel = nulltk.Label(HihatRowBellOpenInputsFrame, text="Inputs:", width=8)
                HihatRowBellOpenInputsLabel.grid(row=0, column=0)

                HihatRowBellOpenMidiInputButton = nulltk.Button(HihatRowBellOpenInputsFrame, text=("Set Midi" if Drum.get("HiHatBellOpenMidiInput") is None else str(Drum.get("HiHatBellOpenMidiInput"))), command=lambda: DetectNote(HihatRowBellOpenMidiInputButton, Row["Device"], Drum, "HiHatBellOpenMidiInput"), width=22)
                HihatRowBellOpenMidiInputButton.grid(row=0, column=1)

                HihatRowBellOpenKeyOutputButton = nulltk.Button(HihatRowBellOpenInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("HiHatBellOpenKeyOutput")) or "Set Key", command=lambda: DetectKey(HihatRowBellOpenKeyOutputButton, Drum, "HiHatBellOpenKeyOutput","NullMidi"), width=22)
                HihatRowBellOpenKeyOutputButton.grid(row=0, column=2, sticky="ew")

                HihatRowBellOpenSounds = nulltk.LabelFrame(HihatRowBellOpenRow, text="Sounds")
                HihatRowBellOpenSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))

                SoundWidgets[HihatRowBellOpenSounds] = {"row": 2, "column": 0, "sticky": "ew", "padx": 5, "pady": (2,10)}

                HihatRowBellOpenSounds.columnconfigure(0, weight=0)
                HihatRowBellOpenSounds.columnconfigure(1, weight=0)
                HihatRowBellOpenSounds.columnconfigure(2, weight=0)

                HihatRowBellOpenSoundLocationVar = tk.StringVar(value=Drum.get("HiHatBellOpenPath", ""))
                BellOpenVolumeVar = tk.IntVar(value=Drum.get("HiHatBellOpenVolume", 75))

                HihatRowBellOpenVolumeSliderLabel = nulltk.Label(HihatRowBellOpenSounds, text="Volume", width=12, height=2)
                HihatRowBellOpenVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                HihatRowBellOpenVolumeSlider = nulltk.Scale(HihatRowBellOpenSounds, from_=0, to=100, orient="horizontal", variable=BellOpenVolumeVar, showvalue=False, length=22)
                HihatRowBellOpenVolumeSlider.grid(row=0, column=1, sticky="ew")

                HihatRowBellOpenVolumeShowLabel = nulltk.Label(HihatRowBellOpenSounds, textvariable=BellOpenVolumeVar)
                HihatRowBellOpenVolumeShowLabel.grid(row=0, column=2, sticky="w")

                HihatRowBellOpenSoundPathLabel = nulltk.Label(HihatRowBellOpenSounds, text="Sound\nPath:", width=12, height=2)
                HihatRowBellOpenSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                HihatRowBellOpenSoundLocationIF = nulltk.Entry(HihatRowBellOpenSounds, textvariable=HihatRowBellOpenSoundLocationVar, state="readonly", width=22)
                HihatRowBellOpenSoundLocationIF.grid(row=1, column=1, sticky="ew")

                HihatRowBellOpenBrowseButton = nulltk.Button(HihatRowBellOpenSounds, command=lambda: SearchForSoundFile(Drum, HihatRowBellOpenSoundLocationVar, "HiHatBellOpenPath"), text="Browse", width=8)
                HihatRowBellOpenBrowseButton.grid(row=1, column=2)

                def UpdateBellOpenVolume(*args):
                    Drum["HiHatBellOpenVolume"] = BellOpenVolumeVar.get()
                    SaveConfig("NullMidi")

                

                Divider = nulltk.Frame(HihatContainer, width=2, bg="#555")
                Divider.grid(row=1, column=3, sticky="ns", padx=5)



                #------------ BellClosedRow
                HihatRowBellClosedRow = nulltk.Frame(HihatContainer)
                HihatRowBellClosedRow.grid(row=1, column=4, sticky="ew", padx=2, pady=2)

                HihatRowBellClosedRow.rowconfigure(0, weight=1)
                HihatRowBellClosedRow.rowconfigure(1, weight=1)
                HihatRowBellClosedRow.rowconfigure(2, weight=0)
                HihatRowBellClosedRow.columnconfigure(0, weight=1)

                HihatRowBellClosedLabel = nulltk.Label(HihatRowBellClosedRow, text="Bell Closed HiHat", width=8, font=("TkDefaultFont", 12, "bold"))
                HihatRowBellClosedLabel.grid(row=0, column=0, sticky="ew")

                HihatRowBellClosedInputsFrame = nulltk.Frame(HihatRowBellClosedRow)
                HihatRowBellClosedInputsFrame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

                HihatRowBellClosedInputsLabel = nulltk.Label(HihatRowBellClosedInputsFrame, text="Inputs:", width=8)
                HihatRowBellClosedInputsLabel.grid(row=0, column=0)

                HihatRowBellClosedMidiInputButton = nulltk.Button(HihatRowBellClosedInputsFrame, text=("Set Midi" if Drum.get("HiHatBellClosedMidiInput") is None else str(Drum.get("HiHatBellClosedMidiInput"))), command=lambda: DetectNote(HihatRowBellClosedMidiInputButton, Row["Device"], Drum, "HiHatBellClosedMidiInput"), width=22)
                HihatRowBellClosedMidiInputButton.grid(row=0, column=1)

                HihatRowBellClosedKeyOutputButton = nulltk.Button(HihatRowBellClosedInputsFrame, text="+".join(FormatKeyName(K)for K in Drum.get("HiHatBellClosedKeyOutput")) or "Set Key", command=lambda: DetectKey(HihatRowBellClosedKeyOutputButton, Drum, "HiHatBellClosedKeyOutput","NullMidi"), width=22)
                HihatRowBellClosedKeyOutputButton.grid(row=0, column=2, sticky="ew")

                HihatRowBellClosedSounds = nulltk.LabelFrame(HihatRowBellClosedRow, text="Sounds")
                HihatRowBellClosedSounds.grid(row=2, column=0, sticky="ew", padx=5, pady=(2,10))

                SoundWidgets[HihatRowBellClosedSounds] = {"row": 2, "column": 0, "sticky": "ew", "padx": 5, "pady": (2,10)}

                HihatRowBellClosedSounds.columnconfigure(0, weight=0)
                HihatRowBellClosedSounds.columnconfigure(1, weight=0)
                HihatRowBellClosedSounds.columnconfigure(2, weight=0)

                HihatRowBellClosedSoundLocationVar = tk.StringVar(value=Drum.get("HiHatBellClosedPath", ""))
                BellClosedVolumeVar = tk.IntVar(value=Drum.get("HiHatBellClosedVolume", 75))

                HihatRowBellClosedVolumeSliderLabel = nulltk.Label(HihatRowBellClosedSounds, text="Volume", width=12, height=2)
                HihatRowBellClosedVolumeSliderLabel.grid(row=0, column=0, sticky="e", pady=(0,8))

                HihatRowBellClosedVolumeSlider = nulltk.Scale(HihatRowBellClosedSounds, from_=0, to=100, orient="horizontal", variable=BellClosedVolumeVar, showvalue=False, length=22)
                HihatRowBellClosedVolumeSlider.grid(row=0, column=1, sticky="ew")

                HihatRowBellClosedVolumeShowLabel = nulltk.Label(HihatRowBellClosedSounds, textvariable=BellClosedVolumeVar)
                HihatRowBellClosedVolumeShowLabel.grid(row=0, column=2, sticky="w")

                HihatRowBellClosedSoundPathLabel = nulltk.Label(HihatRowBellClosedSounds, text="Sound\nPath:", width=12, height=2)
                HihatRowBellClosedSoundPathLabel.grid(row=1, column=0, sticky="e", pady=(0,8))

                HihatRowBellClosedSoundLocationIF = nulltk.Entry(HihatRowBellClosedSounds, textvariable=HihatRowBellClosedSoundLocationVar, state="readonly", width=22)
                HihatRowBellClosedSoundLocationIF.grid(row=1, column=1, sticky="ew")

                HihatRowBellClosedBrowseButton = nulltk.Button(HihatRowBellClosedSounds, command=lambda: SearchForSoundFile(Drum, HihatRowBellClosedSoundLocationVar,"HiHatBellClosedPath"), text="Browse", width=8)
                HihatRowBellClosedBrowseButton.grid(row=1, column=2)

                def UpdateBellClosedVolume(*args):
                    Drum["HiHatBellClosedVolume"] = BellClosedVolumeVar.get()
                    SaveConfig("NullMidi")

                MidiScrollBox.BindMouseWheel(Frame)

                SetupSlider(HihatRowBellClosedVolumeSlider, BellClosedVolumeVar, 0, 100, UpdateBellClosedVolume)

                SetupSlider(HihatRowBellOpenVolumeSlider, BellOpenVolumeVar, 0, 100, UpdateBellOpenVolume)
                
                SetupSlider(HihatRowOpenTimeSlider, HihatOpenTimeVar, 0, 500, UpdateHiHatOpenTime)

                SetupSlider(HihatRowOpenFadeInSlider, HihatOpenFadeInVar, 0, 500, UpdateFadeIn)

                SetupSlider(HihatRowStompVolumeSlider, StompVolumeVar, 0, 100, UpdateStompVolume)

                SetupSlider(HihatRowOpenVolumeSlider, OpenVolumeVar, 0, 100, UpdateOpenVolume)
                SetupSlider(HihatRowOpenThresholdSlider, OpenThresholdVar, 0, 127, UpdateOpenThreshold)

                SetupSlider(HihatRowHalfVolumeSlider, HalfVolumeVar, 0, 100, UpdateHalfVolume)

                SetupSlider(HihatRowClosedVolumeSlider, ClosedVolumeVar, 0, 100, UpdateClosedVolume)
                SetupSlider(HihatRowClosedThresholdSlider, ClosedThresholdVar, 0, 127, UpdateClosedThreshold)

                CollapseHiHat(Drum, HihatContainer, Loading)
                UpdateMuted()

            if Which == "Pad":
                DrumRowDrumRow.grid(row=0, column=0, sticky="ew", padx=2)
                Drum['Drum'] = True
                SetupPadRow(Loading)
            elif Which == "Cymbal":
                DrumRowCymbalRow.grid(row=0, column=0, sticky="ew", padx=2)
                Drum['Cymbal'] = True
                SetupCymbalRow(Loading)
            elif Which == "Kick":
                DrumRowKickRow.grid(row=0, column=0, sticky="ew", padx=2)
                Drum['Kick'] = True
                SetupKickRow(Loading)
            elif Which == "Hihat":
                DrumRowHihatRow.grid(row=0, column=0, sticky="ew", padx=2)
                Drum['Hihat'] = True
                SetupHihatRow(Loading)
            elif Which == "Main":
                MainDrumRowToggles.grid(row=0, column=0, sticky="ew", padx=2)


            SaveConfig("NullMidi")

        DrumRowDrumToggle = nulltk.Checkbutton(MainDrumRowToggles, text="Pad?", variable=DrumRowAlwaysFalsePad, command=lambda:SwitchDrumType("Pad"))
        DrumRowDrumToggle.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowCymbalToggle = nulltk.Checkbutton(MainDrumRowToggles, text="Cymbal?", variable=DrumRowAlwaysFalseCymbal, command=lambda: SwitchDrumType("Cymbal"))
        DrumRowCymbalToggle.grid(row=0, column=1, sticky="ew", padx=2)
        DrumRowKickToggle = nulltk.Checkbutton(MainDrumRowToggles, text="Kick?", variable=DrumRowAlwaysFalseKick, command=lambda: SwitchDrumType("Kick"))
        DrumRowKickToggle.grid(row=0, column=2, sticky="ew", padx=2)
        DrumRowHihatToggle = nulltk.Checkbutton(MainDrumRowToggles, text="Hihat?", variable=DrumRowAlwaysFalseHihat, command=lambda: SwitchDrumType("Hihat"))
        DrumRowHihatToggle.grid(row=0, column=3, sticky="ew", padx=2)
        RemoveDrumObjectFromListMainDrum = nulltk.Button(MainDrumRowToggles, text="Delete Drum", command=lambda:RemoveDrum(Drum, RemoveDrumObjectFromListMainDrum))
        RemoveDrumObjectFromListMainDrum.grid(row=0, column=4, sticky="ew", padx=2)

        MidiScrollBox.BindMouseWheel(Frame)

        if Loading:
            DrumWindowSpecificUpdater(True)
            if Drum['Drum']:
                SwitchDrumType("Pad", Loading)
            elif Drum['Cymbal']:
                SwitchDrumType("Cymbal", Loading)
            elif Drum['Kick']:
                SwitchDrumType("Kick", Loading)
            elif Drum['Hihat']:
                SwitchDrumType("Hihat", Loading)

        SaveConfig("NullMidi")
    
    DrumGhostNoteVolume = tk.IntVar(value=Row.get("GhostNoteVolume", 10))
    DrumSlamNoteVolume = tk.IntVar(value=Row.get("SlamNoteVolume", 100))

    def UpdateGhostVolume(*args):
        Row["GhostNoteVolume"] = DrumGhostNoteVolume.get()
        SaveConfig("NullMidi")
    
    def UpdateSlamVolume(*args):
        Row["SlamNoteVolume"] = DrumSlamNoteVolume.get()
        SaveConfig("NullMidi")
    

    DrumGhostVolumeLabel = nulltk.Label(DrumRow, text= "Ghost Note\n Volume", width = 12, height=2)
    DrumGhostVolumeLabel.grid(row=0, column=0, sticky="e")
    DrumGhostVolumeSlider = nulltk.Scale(DrumRow,from_=1,to=25,orient="horizontal",variable=DrumGhostNoteVolume,showvalue=False, length=44,)
    DrumGhostVolumeSlider.grid(row=0, column=1, sticky="ew")
    DrumGhostVolumeShowLabel = nulltk.Label(DrumRow,textvariable=DrumGhostNoteVolume)
    DrumGhostVolumeShowLabel.grid(row=0, column=2, sticky="w")

    Divider = nulltk.Frame(DrumRow,width=2,bg="#555")
    Divider.grid(row=0,column=3,sticky="news",padx=5)

    DrumSlamVolumeLabel = nulltk.Label(DrumRow, text= "Slam Note\n Volume", width = 12, height=2)
    DrumSlamVolumeLabel.grid(row=0, column=4, sticky="e")
    DrumSlamVolumeSlider = nulltk.Scale(DrumRow,from_=76,to=100,orient="horizontal",variable=DrumSlamNoteVolume,showvalue=False, length=44,)
    DrumSlamVolumeSlider.grid(row=0, column=5, sticky="ew")
    DrumSlamVolumeShowLabel = nulltk.Label(DrumRow,textvariable=DrumSlamNoteVolume)
    DrumSlamVolumeShowLabel.grid(row=0, column=6, sticky="w")

    Divider = nulltk.Frame(DrumRow,width=2,bg="#555")
    Divider.grid(row=0,column=7,sticky="news",padx=5)

    DynamicVolume = nulltk.Checkbutton(DrumRow,variable=DynamicVolumeCheck, text="Dynamic Volume", command=lambda: UpdateDynamics(), width=15)
    DynamicVolume.grid(row=0, column=8, sticky="ew", padx=2)

    AddDrumObjectToList = nulltk.Button(DrumRow, text="Add Drum", command=lambda:AddDrumToList())
    AddDrumObjectToList.grid(row=1, column=0, sticky="ew", padx=2, columnspan=2)

    MidiScrollBox.BindMouseWheel(Frame)

    SetupSlider(DrumGhostVolumeSlider,DrumGhostNoteVolume,1,25,UpdateGhostVolume)
    SetupSlider(DrumSlamVolumeSlider,DrumSlamNoteVolume,76,100,UpdateSlamVolume)
    

    
    MidiRows.append(Row)
    MidiRowObjects.append(Frame)

    if not Loading:
        SaveConfig("NullMidi")
    else:
        if Row['Drums']:
            HideToggleRowShowOtherRow("Drums")
            for drum in Row['DrumList']:
                AddDrumToList(drum, True)
        elif Row['Keyboard']:
            HideToggleRowShowOtherRow("Keyboard")
        elif Row['Controller']:
            HideToggleRowShowOtherRow("Controller")
            for controller in Row['ControllerList']:
                AddControllerToList(controller, True)

        CollapseRow(Row, True)

def RemoveMidiRow(Frame, Row, Button, Timeout=4):
    EndTime = time.time() + (Timeout)

    def Tick(Row):
        if Row['DeleteConfirmation'] == False:
            return
        else:
            Remaining = int(EndTime - time.time())

            if Remaining <= 0:
                if not Button.winfo_exists():
                    return
                Button.config(text="Delete Device")
                Row['DeleteConfirmation'] = False
                return
            if not Button.winfo_exists():
                return
            else:
                Button.config(text=f"R U Sure? {Remaining}")
                Root.after(1000, Tick, Row)
        
    if Row['DeleteConfirmation'] == False:
        Row['DeleteConfirmation'] = True
        Tick(Row)
        return 
    
        
    DestroyVirtualPort(Row)
    Frame.destroy()
    MidiRows.remove(Row)
    SaveConfig("NullMidi")
    return


TopBar = nulltk.Frame(NullMidi)
TopBar.pack(fill="x", padx=5, pady=5)
MidiScrollBox = ScrollableFrame(NullMidi)
MidiScrollBox.pack(fill="both", expand=True)
MidiContainer = MidiScrollBox.Inner
nulltk.Button(TopBar, text="Add New Input", command=lambda: AddMidiRow(None)).pack(fill="x")
ttk.Separator(NullMidi, orient="horizontal").pack(fill="both", pady=5)

def NullMidiLoop():
    global LoadTimes

    while True:
        if NullMidiActive.get() == True:
            Ports = mido.get_input_names()
            NeededDevices = set()
            for Row in MidiRows:
                if not Row.get("Active"):
                    continue
                Device = Row.get("Device")
                if not Device:
                    continue
                if Device not in Ports:
                    continue
                NeededDevices.add(Device)
            for Device in NeededDevices:
                if Device not in MidiDeviceListeners:
                    StartMidiListener(Device)
            for Device in list(MidiDeviceListeners.keys()):
                if Device not in NeededDevices:
                    StopMidiListener(Device)

        time.sleep(1)

def StartUpNullMidi():
    global MixerInitialized, MidiRows, LoadCompleted, MidiRowObjects,ActualProgramLoadedCount
    if NullMidiActive.get() == True:

        midi = None
        if not os.path.isfile(ConfigPath):
            Butts.set("Save File not found???")
            Root.update_idletasks()
            return False

        try:
            with open(ConfigPath, "r") as f:
                data = json.load(f)
                midi = data.get("NullMidi", {})

            for row in MidiRowObjects[:]:
                row.destroy()

            MidiRows.clear()
            MidiRowObjects.clear()

            for row in midi.get("MidiRows", []):
                AddMidiRow(row, True)

        except Exception as e:
            Butts.set(f"ERROR LOADING NULL MIDI SAVE\n\n{e}")
            Root.update_idletasks()
            return False

        if MixerInitialized == False:
            pygame.mixer.init(buffer=512)
            pygame.mixer.set_num_channels(256)
            MixerInitialized = True
        
        BuildGlobalUInputDevice()

        Notebook.add(NullMidi, text="NullMidi")
        ActualProgramLoadedCount+=1
    else:
        Notebook.forget(NullMidi)

    LoadCompleted += 1
    return

#endregion

#region NullMonitor
Overlays = None
OverlayWindows = []
NullMonitorSetActiveCheckBoxes = []
HideJob = None
ScanForMouse = False
XdotoolPath = shutil.which("xdotool") or "xdotool"
XrandrPath = shutil.which("xrandr") or "xrandr"
StartDetection = 0.01
EdgeBuffer = 3
ScanTime = 0.10
BaseDir = os.path.dirname(os.path.abspath(__file__))
RootDir = os.path.dirname(BaseDir)
Profiles = {}
ProfileWidgets = {}
ActiveProfile = None
LastMousePos = None
LastMoveTime = 0
LastWarpTime = 0
WarpCooldown = 0.01
Offset = 10
if not XdotoolPath or not XrandrPath:
    raise RuntimeError("xdotool or xrandr not found")
MonitorLayoutObjects = []
MonitorWallPaperRows = []
MonitorBoxes = []

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None

        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20

        self.tip = nulltk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")

        label = nulltk.Label(
            self.tip,
            text=self.text,
            bg="black",
            fg="white",
            padx=5,
            pady=3
        )
        label.pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

def CaptureLayout():
    try:
        Out = subprocess.check_output([XrandrPath]).decode()
    except:
        return []

    Layout = []

    for Line in Out.splitlines():
        if " connected" in Line:
            Parts = Line.split()
            ID = Parts[0]

            Resolution = None
            Pos = None
            Primary = "primary" in Parts

            for P in Parts:
                if "+" in P and "x" in P:
                    Resolution, X, Y = re.split(r"[+]", P)
                    Pos = f"{X}x{Y}"
                    break

            if not Resolution:
                continue

            Layout.append({
                "ID": ID,
                "Resolution": Resolution,
                "Pos": Pos,
                "Primary": Primary
            })

    return Layout

def GetMonitors():
    try:
        Out = subprocess.check_output([XrandrPath]).decode()
    except:
        return []

    Monitors = []

    for Line in Out.splitlines():
        if " connected" in Line:
            Parts = Line.split()
            ID = Parts[0]

            IsPrimary = " primary " in Line

            Resolution = None
            for P in Parts:
                if "+" in P and "x" in P:
                    Resolution = P.split("+")[0]
                    break

            if not Resolution:
                continue

            if IsPrimary:
                Label = f"Primary ({ID} {Resolution})"
            else:
                Label = f"{ID} ({Resolution})"

            Monitors.append({
                "ID": ID,
                "Label": Label,
                "Primary": IsPrimary
            })

    return Monitors

def GetProfiles():
    return list(Profiles.keys()) if Profiles else ["NO PROFILES. GO CREATE ONE"]

def ShowDetectionOverlay(which):
    global OverlayWindows
    if OverlayWindows:
        return


    OverlayWindows = []

    Bounds = GetMonitorBounds()

    for ID, B in Bounds.items():
        W = B["x2"] - B["x1"]
        H = B["y2"] - B["y1"]

        if which == "detection":
            Px = int(W * StartDetection)
            Py = int(H * StartDetection)
        else:
            Px = EdgeBuffer
            Py = EdgeBuffer

        # Left
        OverlayWindows.append(CreateOverlay(
            B["x1"], B["y1"], Px, H
        ))

        # Right
        OverlayWindows.append(CreateOverlay(
            B["x2"] - Px, B["y1"], Px, H
        ))

        # Top
        OverlayWindows.append(CreateOverlay(
            B["x1"], B["y1"], W, Py
        ))

        # Bottom
        OverlayWindows.append(CreateOverlay(
            B["x1"], B["y2"] - Py, W, Py
        ))
    return OverlayWindows

def CreateOverlay(x, y, w, h):
    Popup = nulltk.Toplevel(Root)
    Popup.overrideredirect(True)
    Popup.attributes("-topmost", True)
    Popup.attributes("-alpha", 0.25)

    Popup.geometry(f"{w}x{h}+{x}+{y}")
    Popup.configure(bg="red")

    return Popup

def HideDetectionOverlay():
    global OverlayWindows

    for W in OverlayWindows:
        try:
            W.destroy()
        except:
            pass

    OverlayWindows = []

def UpdateStartDetection(v):
    global StartDetection
    StartDetection = int(v) / 1000
    NullMonitorStartValueLabel.config(text=f"{int(v)}   |") 
    SaveConfig("NullMonitor")

def OnHoverEnter(e, which):
    global Overlays, HideJob
    if HideJob:
        Root.after_cancel(HideJob)
        HideJob = None
    HideDetectionOverlay()
    Overlays = ShowDetectionOverlay(which)

def OnHoverLeave(e):
    global HideJob
    HideJob = Root.after(50, HideDetectionOverlay)

def DelayedHide():
    Root.after(50, lambda: HideDetectionOverlay())

def UpdateEdgeBuffer(*args):
    global EdgeBuffer
    try:
        EdgeBuffer = int(NullMonitorEdgeBufferVar.get())
        SaveConfig("NullMonitor")
    except:
        pass

def UpdateScanTime(v):
    global ScanTime
    ScanTime = float(v)
    NullMonitorScanValueLabel.config(text=f"{ScanTime:.3f}")
    SaveConfig("NullMonitor")

def CenterOnRoot(Popup, width, height):
    Root.update_idletasks()

    rx = Root.winfo_rootx()
    ry = Root.winfo_rooty()
    rw = Root.winfo_width()
    rh = Root.winfo_height()

    x = rx + (rw // 2) - (width // 2)
    y = ry + (rh // 2) - (height // 2)

    Popup.geometry(f"{width}x{height}+{x}+{y}")

def SetActiveProfile(Name, Apply=True):
    global ActiveProfile

    ActiveProfile = Name

    for P, W in ProfileWidgets.items():
        W["ActiveVar"].set(P == Name)

    if Apply:
        if ActiveProfile not in Profiles:
            return
        ApplyProfileLayout(Name)

    SaveConfig("NullMonitor")

def ApplyProfileLayout(Name):
    global NullMonitorSetActiveCheckBoxes

    if Name not in Profiles:
        return
    Layout = Profiles[Name]["Layout"]
    Current = GetMonitors()
    Commands = ["xrandr"]
    ActiveIDs = set()
    for Monitor in Layout:
        ID = Monitor["ID"]
        ActiveIDs.add(ID)
        Commands.extend([
            "--output", ID,
            "--mode", Monitor["Resolution"]
        ])
        X, Y = Monitor["Pos"].split("x")
        Commands.extend([
            "--pos", f"{X}x{Y}"
        ])
        if Monitor.get("Primary"):
            Commands.append("--primary")
    for Monitor in Current:
        if Monitor["ID"] not in ActiveIDs:
            Commands.extend([
                "--output",
                Monitor["ID"],
                "--off"
            ])

    try:
        def DisableProfileSwitches():
            for item in NullMonitorSetActiveCheckBoxes:
                item.config(state="disabled")
            return

        DisableProfileSwitches()

        subprocess.run(
            Commands,
            check=True
        )
        

        def EnableProfileSwitches():
            for item in NullMonitorSetActiveCheckBoxes:
                item.config(state="normal")
            return

        if Profiles[Name].get("EnabledWallPapers"):
            Root.after(10000, lambda:UpdateLockScreenWallPapers(Name))
            Root.after(5000, lambda: EnableProfileSwitches())
        else:
            Root.after(15000, lambda: EnableProfileSwitches())

    except Exception as E:
        Log(f"NullMonitor: Couldn't apply profile because {E}")

def DeleteProfile(Name,Button, Frame, Timeout=4):
    global ActiveProfile

    EndTime = time.time() + (Timeout)

    def Tick(Name):
        if Name not in Profiles:
            return
        else:
            Remaining = int(EndTime - time.time())
            if Remaining <= 0:
                if not Button.winfo_exists():
                    return
                Button.config(text="Delete Profile?")
                Profiles[Name]['DeleteConfirmation'] = False
                return
            if not Button.winfo_exists():
                return
            else:
                Button.config(text=f"R U Sure? {Remaining}")
                Root.after(1000, Tick, Name)

    if Profiles[Name]['DeleteConfirmation'] == False:
        Profiles[Name]['DeleteConfirmation'] = True
        Tick(Name)
        return


    if len(Profiles) <= 1:
        return
    Frame.destroy()
    Profiles.pop(Name, None)
    ProfileWidgets.pop(Name, None)
    if ActiveProfile == Name or len(Profiles) == 1:
        New = list(Profiles.keys())[0]
        SetActiveProfile(New)

    SaveConfig("NullMonitor")

def OpenRemoveWarp(Name):
    Popup = nulltk.Toplevel(Root)
    Popup.title("Remove Warp")
    CenterOnRoot(Popup, 500, 300)

    Frame = nulltk.Frame(Popup, padx=10, pady=10)
    Frame.pack(fill="both", expand=True)

    Warps = Profiles.get(Name, {}).get("Warps", {})

    HasWarps = False

    for SourceID, WarpList in list(Warps.items()):
        for Warp in list(WarpList):
            HasWarps = True

            Text = (
                f'{SourceID}: {Warp["Edge"]} → '
                f'{Warp["Target"]}: {Warp["TargetEdge"]}'
            )

            nulltk.Button(
                Frame,
                text=Text,
                anchor="w",
                command=lambda S=SourceID, W=Warp: RemoveWarp(
                    Name,
                    S,
                    W,
                    Popup
                )
            ).pack(fill="x", pady=2)

    if not HasWarps:
        nulltk.Label(
            Frame,
            text="No warps configured."
        ).pack(pady=10)

def RemoveWarp(ProfileName, SourceID, Warp, Popup):
    WarpList = Profiles[ProfileName]["Warps"].get(SourceID, [])

    if Warp in WarpList:
        WarpList.remove(Warp)

    if not WarpList:
        Profiles[ProfileName]["Warps"].pop(SourceID, None)

    RefreshWarpDisplay(ProfileName)
    SaveConfig("NullMonitor")

    Popup.destroy()

    OpenRemoveWarp(ProfileName)

def RefreshWarpDisplay(Name):
    Warps = Profiles.get(Name, {}).get("Warps", {})

    Parts = []

    for SourceID, WarpList in Warps.items():
        for W in WarpList:
            Parts.append(
                f'{SourceID}: {W["Edge"]} → {W["Target"]}: {W["TargetEdge"]}'
            )

    Text = " , ".join(Parts) if Parts else "No warps"

    ProfileWidgets[Name]["WarpVar"].set(Text)

def SpawnMonitorPopups(OnSelect):
    Popups = {}

    Bounds = GetMonitorBounds()

    for ID, B in Bounds.items():
        Popup = nulltk.Toplevel(Root)
        Popup.overrideredirect(True)
        Popup.attributes("-topmost", True)

        width = 200
        height = 60

        x = B["x1"] + 20
        y = B["y1"] + 20

        Popup.geometry(f"{width}x{height}+{x}+{y}")
        Popup.config(cursor="hand2")

        Label = nulltk.Label(
            Popup,
            text=f"Click Here\n{ID}",
            bg="black",
            fg="white",
            font=("Arial", 12, "bold")
        )
        Label.pack(fill="both", expand=True)
        Label.bind("<Enter>", lambda e, L=Label: L.config(bg="#333"))
        Label.bind("<Leave>", lambda e, L=Label: L.config(bg="black"))

        Label.bind("<Button-1>", lambda e, mid=ID: OnSelect(mid))

        Popups[ID] = Popup

    return Popups

def CreateCenterPopup():
    Popup = nulltk.Toplevel(Root)
    CenterOnRoot(Popup, 400, 100)
    Popup.attributes("-topmost", True)
    

    Frame = nulltk.Frame(Popup)
    Frame.pack(fill="both", expand=True)

    Label = nulltk.Label(Frame, text="", font=("Arial", 12))
    Label.pack(expand=True)

    

    return Popup, Label

def OpenWarpConfigPopup(ProfileName, SourceID, TargetID):
    Popup = nulltk.Toplevel(Root)
    CenterOnRoot(Popup, 300, 200)
    Popup.title("Configure Warp")
    Popup.attributes("-topmost", True)

    Frame = nulltk.Frame(Popup, padx=10, pady=10)
    Frame.pack()

    nulltk.Label(Frame, text=f"{SourceID} → {TargetID}").pack(pady=5)

    Edges = ["TopLeft", "Top", "TopRight",
             "Right",
             "BottomRight", "Bottom", "BottomLeft",
             "Left"]

    SourceEdgeVar = tk.StringVar(value=Edges[0])
    TargetEdgeVar = tk.StringVar(value=Edges[0])

    nulltk.Label(Frame, text="Source Edge").pack()
    nulltk.Combobox(Frame, values=Edges, textvariable=SourceEdgeVar, state="readonly").pack()

    nulltk.Label(Frame, text="Target Edge").pack()
    nulltk.Combobox(Frame, values=Edges, textvariable=TargetEdgeVar, state="readonly").pack()

    def Confirm():
        Warp = {
            "Edge": SourceEdgeVar.get(),
            "Target": TargetID,
            "TargetEdge": TargetEdgeVar.get()
        }

        if SourceID not in Profiles[ProfileName]["Warps"]:
            Profiles[ProfileName]["Warps"][SourceID] = []

        if Warp not in Profiles[ProfileName]["Warps"][SourceID]:
            Profiles[ProfileName]["Warps"][SourceID].append(Warp)

        RefreshWarpDisplay(ProfileName)
        Popup.destroy()
        SaveConfig("NullMonitor")

    nulltk.Button(Frame, text="Confirm", command=Confirm).pack(pady=5)

def StartWarpSelection(ProfileName):
    State = {"source": None}

    def Cleanup():
        for p in list(Popups.values()):
            try:
                p.destroy()
            except:
                pass
        try:
            CenterPopup.destroy()
        except:
            pass

    CenterPopup, CenterLabel = CreateCenterPopup()

    CenterPopup.protocol("WM_DELETE_WINDOW", Cleanup)
    CenterPopup.bind("<Escape>", lambda e: Cleanup())



    def UpdateText(t):
        CenterLabel.config(text=t)

    def SelectSource(ID):
        State["source"] = ID

        # and with the commenting out of this...i allow single monitor warping ability \o/
        #Popups[ID].destroy()
        #del Popups[ID]

        UpdateText("Click to set warping TO monitor")
        for mid, popup in Popups.items():
            for w in popup.winfo_children():
                w.bind("<Button-1>", lambda e, m=mid: SelectTarget(m))

    def SelectTarget(ID):
        Source = State["source"]
        for p in Popups.values():
            p.destroy()

        CenterPopup.destroy()

        OpenWarpConfigPopup(ProfileName, Source, ID)

    Popups = SpawnMonitorPopups(SelectSource)

    UpdateText("Click to set warping FROM monitor")

def OpenAddWarp(Name):
    StartWarpSelection(Name)

def BuildUIFromProfiles():
    global NullMonitorSetActiveCheckBoxes

    NullMonitorSetActiveCheckBoxes.clear()
    
    for w in NullMonitorProfileContainer.winfo_children():
        w.destroy()

    ProfileWidgets.clear()

    for Name in Profiles:
        CreateProfileBox(Name)

    if ActiveProfile in ProfileWidgets:
        SetActiveProfile(ActiveProfile, Apply= False)

def GetMouseDirection(x, y):
    global LastMousePos

    if LastMousePos is None:
        LastMousePos = (x, y)
        return 0, 0

    lx, ly = LastMousePos
    dx = x - lx
    dy = y - ly

    LastMousePos = (x, y)

    return dx, dy

def IsEdgeBuffer(corner, x, y, B):
    left   = x <= B["x1"] + EdgeBuffer
    right  = x >= B["x2"] - EdgeBuffer
    top    = y <= B["y1"] + EdgeBuffer
    bottom = y >= B["y2"] - EdgeBuffer

    if corner == "Left":
        return left
    if corner == "Right": 
        return right
    if corner == "Top": 
        return top
    if corner == "Bottom": 
        return bottom

    if corner == "TopLeft":
        return left and top
    if corner == "TopRight":
        return right and top
    if corner == "BottomLeft":
        return left and bottom
    if corner == "BottomRight":
        return right and bottom

    return False

def ExecuteWarp(TargetID, TargetEdge, Bounds, ratio=None):
    TB = Bounds[TargetID]
    ratio = max(0, min(1, ratio))
    width  = TB["x2"] - TB["x1"]
    height = TB["y2"] - TB["y1"]

    if TargetEdge == "TopLeft":
        nx, ny = TB["x1"] + Offset, TB["y1"] + Offset

    elif TargetEdge == "TopRight":
        nx, ny = TB["x2"] - Offset, TB["y1"] + Offset

    elif TargetEdge == "BottomLeft":
        nx, ny = TB["x1"] + Offset, TB["y2"] - Offset

    elif TargetEdge == "BottomRight":
        nx, ny = TB["x2"] - Offset, TB["y2"] - Offset

    elif TargetEdge == "Left":
        nx = TB["x1"] + Offset
        ny = TB["y1"] + int(ratio * height)

    elif TargetEdge == "Right":
        nx = TB["x2"] - Offset
        ny = TB["y1"] + int(ratio * height)

    elif TargetEdge == "Top":
        nx = TB["x1"] + int(ratio * width)
        ny = TB["y1"] + Offset

    elif TargetEdge == "Bottom":
        nx = TB["x1"] + int(ratio * width)
        ny = TB["y2"] - Offset

    else:
        return


    subprocess.run([XdotoolPath, "mousemove", str(nx), str(ny)])

def GetCursorPos():
    try:
        Out = subprocess.check_output([XdotoolPath, "getmouselocation"]).decode()
        Parts = dict(p.split(":") for p in Out.strip().split())
        return int(Parts["x"]), int(Parts["y"])
    except:
        return None, None

def GetMonitorBounds():
    Bounds = {}

    Layout = Profiles[ActiveProfile]["Layout"]

    for M in Layout:
        ID = M["ID"]

        W, H = map(int, M["Resolution"].split("x"))
        X, Y = map(int, M["Pos"].split("x"))

        Bounds[ID] = {
            "x1": X,
            "y1": Y,
            "x2": X + W,
            "y2": Y + H
        }

    return Bounds

def GetCurrentMonitor(x, y, Bounds):
    for ID, B in Bounds.items():
        if B["x1"] <= x <= B["x2"] and B["y1"] <= y <= B["y2"]:
            return ID
    return None

def DetectEdge(x, y, B):
    W = B["x2"] - B["x1"]
    H = B["y2"] - B["y1"]

    mx = (x - B["x1"]) / W
    my = (y - B["y1"]) / H

    left   = mx <= StartDetection
    right  = mx >= 1 - StartDetection
    top    = my <= StartDetection
    bottom = my >= 1 - StartDetection

    if top and left:
        return "TopLeft"
    if top and right:
        return "TopRight"
    if bottom and left:
        return "BottomLeft"
    if bottom and right:
        return "BottomRight"

    if top:
        return "Top"
    if bottom:
        return "Bottom"
    if left:
        return "Left"
    if right:
        return "Right"

    return None

def ToggleNullMonitor():
    global ScanForMouse
    ScanForMouse = NullMonitorEnabledVar.get()
    if ScanForMouse:
        NullMonitorDisabledOverlay.place_forget()
    else:
        NullMonitorDisabledOverlay.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )
    SaveConfig("NullMonitor")

def UpdateDesktopWallPapers(ProfileName):

    Profile = Profiles[ProfileName]
    Layout = Profile["Layout"]
    Wallpapers = Profile["Wallpapers"]

    if not Layout:
        return

    MinX = min(int(M["Pos"].split("x")[0]) for M in Layout)
    MinY = min(int(M["Pos"].split("x")[1]) for M in Layout)

    MaxX = max(int(M["Pos"].split("x")[0]) +int(M["Resolution"].split("x")[0])for M in Layout)

    MaxY = max(int(M["Pos"].split("x")[1]) +int(M["Resolution"].split("x")[1])for M in Layout)

    CanvasWidth = MaxX - MinX
    CanvasHeight = MaxY - MinY

    Canvas = Image.new("RGB",(CanvasWidth, CanvasHeight),"black")

    for Monitor in Layout:
        ID = Monitor["ID"]
        MonitorX, MonitorY = map(int,Monitor["Pos"].split("x"))
        MonitorWidth, MonitorHeight = map(int,Monitor["Resolution"].split("x"))
        WallpaperData = Wallpapers.get(ID, {})
        Path = WallpaperData.get("DTPath", "")
        WallpaperMode = WallpaperData.get("DTMode", "Fill")
        if not Path or not os.path.exists(Path):
            continue
        Wallpaper = Image.open(Path).convert("RGB")
        PasteX = MonitorX - MinX
        PasteY = MonitorY - MinY

        if WallpaperMode == "Stretch":
            Wallpaper = Wallpaper.resize((MonitorWidth, MonitorHeight))

            Canvas.paste(Wallpaper,(PasteX, PasteY))

        # CENTER
        elif WallpaperMode == "Center":
            X = PasteX + (MonitorWidth - Wallpaper.width) // 2
            Y = PasteY + (MonitorHeight - Wallpaper.height) // 2
            Canvas.paste(Wallpaper,(X, Y))

        # TILE
        elif WallpaperMode == "Tile":

            for TileX in range(0,MonitorWidth,Wallpaper.width):
                for TileY in range(0,MonitorHeight,Wallpaper.height):
                    Canvas.paste(Wallpaper,(PasteX + TileX,PasteY + TileY))

        # MAX
        elif WallpaperMode == "Max":
            Scale = min(MonitorWidth / Wallpaper.width,MonitorHeight / Wallpaper.height)
            NewWidth = int(Wallpaper.width * Scale)
            NewHeight = int(Wallpaper.height * Scale)
            Wallpaper = Wallpaper.resize((NewWidth, NewHeight))
            X = PasteX + (MonitorWidth - NewWidth) // 2
            Y = PasteY + (MonitorHeight - NewHeight) // 2
            Canvas.paste(Wallpaper,(X, Y))
        # FILL
        else:
            Scale = max(MonitorWidth / Wallpaper.width,MonitorHeight / Wallpaper.height)
            NewWidth = int(Wallpaper.width * Scale)
            NewHeight = int(Wallpaper.height * Scale)
            Wallpaper = Wallpaper.resize((NewWidth, NewHeight))
            CropX = max(0,(NewWidth - MonitorWidth) // 2)
            CropY = max(0,(NewHeight - MonitorHeight) // 2)
            Wallpaper = Wallpaper.crop(
                (
                    CropX,
                    CropY,
                    CropX + MonitorWidth,
                    CropY + MonitorHeight
                )
            )

            Canvas.paste(Wallpaper,(PasteX, PasteY))

    TempPath = os.path.join(
        tempfile.gettempdir(),
        "nullmonitor_wallpaper.png"
    )

    Canvas.save(TempPath)

    subprocess.Popen(
        [
            "feh",
            "--no-xinerama",
            "--bg-scale",
            TempPath
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def UpdateLockScreenWallPapers(ProfileName):

    Profile = Profiles[ProfileName]
    Layout = Profile["Layout"]
    Wallpapers = Profile["Wallpapers"]

    if not Layout:
        return

    MinX = min(int(M["Pos"].split("x")[0]) for M in Layout)
    MinY = min(int(M["Pos"].split("x")[1]) for M in Layout)

    MaxX = max(int(M["Pos"].split("x")[0]) +int(M["Resolution"].split("x")[0])for M in Layout)

    MaxY = max(int(M["Pos"].split("x")[1]) +int(M["Resolution"].split("x")[1])for M in Layout)

    CanvasWidth = MaxX - MinX
    CanvasHeight = MaxY - MinY


    Canvas = Image.new("RGB",(CanvasWidth, CanvasHeight),"black")

    for Monitor in Layout:
        ID = Monitor["ID"]
        MonitorX, MonitorY = map(int,Monitor["Pos"].split("x"))
        MonitorWidth, MonitorHeight = map(int,Monitor["Resolution"].split("x"))
        WallpaperData = Wallpapers.get(ID, {})
        Path = WallpaperData.get("LSPath", "")
        WallpaperMode = WallpaperData.get("LSMode", "Fill")
        if not Path or not os.path.exists(Path):
            continue
        Wallpaper = Image.open(Path).convert("RGB")
        PasteX = MonitorX - MinX
        PasteY = MonitorY - MinY

        if WallpaperMode == "Stretch":
            Wallpaper = Wallpaper.resize((MonitorWidth, MonitorHeight))

            Canvas.paste(Wallpaper,(PasteX, PasteY))

        # CENTER
        elif WallpaperMode == "Center":
            X = PasteX + (MonitorWidth - Wallpaper.width) // 2
            Y = PasteY + (MonitorHeight - Wallpaper.height) // 2
            Canvas.paste(Wallpaper,(X, Y))

        # TILE
        elif WallpaperMode == "Tile":

            for TileX in range(0,MonitorWidth,Wallpaper.width):
                for TileY in range(0,MonitorHeight,Wallpaper.height):
                    Canvas.paste(Wallpaper,(PasteX + TileX,PasteY + TileY))

        # MAX
        elif WallpaperMode == "Max":
            Scale = min(MonitorWidth / Wallpaper.width,MonitorHeight / Wallpaper.height)
            NewWidth = int(Wallpaper.width * Scale)
            NewHeight = int(Wallpaper.height * Scale)
            Wallpaper = Wallpaper.resize((NewWidth, NewHeight))
            X = PasteX + (MonitorWidth - NewWidth) // 2
            Y = PasteY + (MonitorHeight - NewHeight) // 2
            Canvas.paste(Wallpaper,(X, Y))
        # FILL
        else:
            Scale = max(MonitorWidth / Wallpaper.width,MonitorHeight / Wallpaper.height)
            NewWidth = int(Wallpaper.width * Scale)
            NewHeight = int(Wallpaper.height * Scale)
            Wallpaper = Wallpaper.resize((NewWidth, NewHeight))
            CropX = max(0,(NewWidth - MonitorWidth) // 2)
            CropY = max(0,(NewHeight - MonitorHeight) // 2)
            Wallpaper = Wallpaper.crop(
                (
                    CropX,
                    CropY,
                    CropX + MonitorWidth,
                    CropY + MonitorHeight
                )
            )

            Canvas.paste(Wallpaper,(PasteX, PasteY))

    TempPath = os.path.join(
    tempfile.gettempdir(),
    "nullmonitor_lockscreen_building.png"
    )

    FinalPath = os.path.join(
        tempfile.gettempdir(),
        "nullmonitor_lockscreen_wallpaper.png"
    )

    Canvas.save(TempPath)

    os.replace(TempPath, FinalPath)

    try:

        subprocess.run([
            "gsettings",
            "set",
            "org.cinnamon.desktop.background",
            "picture-options",
            "spanned"
        ], check=True)

        subprocess.run([
            "gsettings",
            "set",
            "org.cinnamon.desktop.background",
            "picture-uri",
            f"file://{FinalPath}"
        ], check=True)        
    except Exception:
        try:

            subprocess.run([
                "gsettings",
                "set",
                "org.cinnamon.desktop.background",
                "picture-options",
                "spanned"
            ], check=True)

            subprocess.run([
                "gsettings",
                "set",
                "org.cinnamon.desktop.background",
                "picture-uri-dark",
                f"file://{FinalPath}"
            ], check=True)

            

        except Exception as e:
            Log(f"NullMonitor, Error updating lock screen wallpapers {e}", "Error")
    
    Root.after(1, lambda: UpdateDesktopWallPapers(ProfileName))
    return

def ManageWallPapers(Name):

    global MonitorLayoutObjects, MonitorWallPaperRows, MonitorBoxes

    for Widget in MonitorLayoutObjects: Widget.destroy()
    for Widget in MonitorWallPaperRows: Widget.destroy()

    MonitorLayoutObjects.clear()
    MonitorWallPaperRows.clear()

    Layout = Profiles[Name]["Layout"]
    Positions = [tuple(map(int,Monitor["Pos"].split("x"))) for Monitor in Layout]

    MinX = min(X for X,Y in Positions)
    MinY = min(Y for X,Y in Positions)

    WallpaperModes = ["Fill","Stretch","Center","Max","Tile"]

    Boxes = {}

    for Monitor in Layout:
        X,Y = map(int,Monitor["Pos"].split("x"))
        Box = nulltk.LabelFrame(WallpaperLayoutContainer,text=Monitor["ID"],width=150,height=100)
        Box.grid(row=(Y-MinY)//1000,column=(X-MinX)//1000,padx=3,pady=3)
        Box.grid_propagate(False)
        MonitorLayoutObjects.append(Box)

    for Row, Monitor in enumerate(Layout):
        ID = Monitor["ID"]
        Data = Profiles[Name]["Wallpapers"].setdefault(ID,{
            "DTPath": "",
            "DTMode": "Fill",
            "LSPath": "",
            "LSMode": "Fill"
        })
        MonitorFrame = nulltk.LabelFrame(WallpaperScrollFrame.Inner,text=ID)
        MonitorFrame.grid(row=Row+1,column=0,padx=5,pady=5,sticky="ew")
        MonitorFrame.columnconfigure(0,weight=1)
        MonitorFrame.columnconfigure(1,weight=0)
        MonitorFrame.columnconfigure(2,weight=1)
        MonitorWallPaperRows.append(MonitorFrame)

        DTContainer = nulltk.Frame(MonitorFrame)
        DTContainer.grid(row=0,column=0,padx=5,pady=5,sticky="ew")
        DTContainer.columnconfigure(1,weight=1)
        ttk.Separator(MonitorFrame,orient="vertical").grid(row=0,column=1,sticky="ns",padx=5)
        LSContainer = nulltk.Frame(MonitorFrame)
        LSContainer.grid(row=0,column=2,padx=5,pady=5,sticky="ew")
        LSContainer.columnconfigure(1,weight=1)



        DTPathVar = tk.StringVar(value=Data["DTPath"])
        DTModeVar = tk.StringVar(value=Data.get("DTMode","Fill"))
        LSPathVar = tk.StringVar(value=Data["LSPath"])
        LSModeVar = tk.StringVar(value=Data.get("LSMode","Fill"))

        def DTBrowseForPic(Data=Data, PathVar=DTPathVar, ProfileName=Name):
            CurrentPath = DTPathVar.get()
            InitialDir = (os.path.dirname(CurrentPath)if CurrentPath and os.path.exists(CurrentPath)else os.path.expanduser("~"))
            Path = filedialog.askdirectory(initialdir=InitialDir,title="Choose Desktop Wallpaper Folder")
            if Path:
                SelectedImage = OpenImagePopUp(Path)
                if SelectedImage:
                    Data["DTPath"] = SelectedImage
                    PathVar.set(os.path.basename(SelectedImage))
                    SaveConfig("NullMonitor")
                    UpdateDesktopWallPapers(ProfileName)

        DTBrowseButton = nulltk.Button(DTContainer,text="Browse",width=8,command=lambda Data=Data, PathVar=DTPathVar, ProfileName=Name: DTBrowseForPic(Data, PathVar, ProfileName))
        DTBrowseButton.grid(row=0,column=0,padx=5,pady=5)
        nulltk.Entry(DTContainer,textvariable=DTPathVar,state="readonly").grid(row=0,column=1,padx=5,pady=5,sticky="ew")
        DTModebox = nulltk.Combobox(DTContainer,textvariable=DTModeVar,values=WallpaperModes,state="readonly",width=18)
        DTModebox.grid(row=0,column=2,padx=5,pady=5)

        def DTUpdateWallPaperStyle(ID, Data, ModeVar,ProfileName):
            Data["DTMode"] = ModeVar.get()
            UpdateDesktopWallPapers(ProfileName)
            SaveConfig("NullMonitor")

        DTModebox.bind("<<ComboboxSelected>>",lambda event, ID=ID, Data=Data, ModeVar=DTModeVar,ProfileName=Name:DTUpdateWallPaperStyle(ID, Data, ModeVar,ProfileName))

        #-------

        def LSBrowseForPic(Data=Data, PathVar=LSPathVar, ProfileName=Name):
            CurrentPath = LSPathVar.get()
            InitialDir = (os.path.dirname(CurrentPath)if CurrentPath and os.path.exists(CurrentPath)else os.path.expanduser("~"))
            Path = filedialog.askdirectory(initialdir=InitialDir,title="Choose Lock Screen Wallpaper Folder")
            if Path:
                SelectedImage = OpenImagePopUp(Path)
                if SelectedImage:
                    Data["LSPath"] = SelectedImage
                    PathVar.set(os.path.basename(SelectedImage))
                    SaveConfig("NullMonitor")
                    UpdateLockScreenWallPapers(ProfileName)

        LSBrowseButton = nulltk.Button(LSContainer,text="Browse",width=8,command=lambda Data=Data, PathVar=LSPathVar, ProfileName=Name: LSBrowseForPic(Data, PathVar, ProfileName))
        LSBrowseButton.grid(row=0,column=0,padx=5,pady=5)
        nulltk.Entry(LSContainer,textvariable=LSPathVar,state="readonly").grid(row=0,column=1,padx=5,pady=5,sticky="ew")
        LSModebox = nulltk.Combobox(LSContainer,textvariable=LSModeVar,values=WallpaperModes,state="readonly",width=18)
        LSModebox.grid(row=0,column=2,padx=5,pady=5)

        def LSUpdateWallPaperStyle(ID, Data, ModeVar,ProfileName):
            Data["LSMode"] = ModeVar.get()
            UpdateLockScreenWallPapers(ProfileName)
            SaveConfig("NullMonitor")

        LSModebox.bind("<<ComboboxSelected>>",lambda event, ID=ID, Data=Data, ModeVar=LSModeVar,ProfileName=Name:LSUpdateWallPaperStyle(ID, Data, ModeVar,ProfileName))


        Boxes[ID] = {
            "DTBox": DTModebox,
            "DTVar": DTModeVar,
            "DTPathVar": DTPathVar,
            "LSBox": LSModebox,
            "LSVar": LSModeVar,
            "LSPathVar": LSPathVar
            }

    MonitorBoxes = Boxes
    NullMonitorNotebook.tab(NullMonitorWallPapersPage,state="normal")
    NullMonitorNotebook.select(NullMonitorWallPapersPage)

def NullMonitorNoteBookChange(event):
    CurrentTab = NullMonitorNotebook.select()
    if str(CurrentTab) == str(NullMonitorPage):
        NullMonitorNotebook.tab(
            NullMonitorWallPapersPage,
            state="disabled"
        )
    return

def CreateProfileBox(Name):
    global NullMonitorSetActiveCheckBoxes
    Frame = nulltk.LabelFrame(NullMonitorProfileContainer,text=Name,padx=5,pady=5)
    Frame.pack(fill="x",pady=5)

    TopRow = nulltk.Frame(Frame)
    TopRow.pack(fill="x")
    TopRow.columnconfigure(2,weight=1)

    ActiveVar = tk.BooleanVar()

    ActiveCheck = nulltk.Checkbutton(TopRow,text="Active",variable=ActiveVar,command=lambda: SetActiveProfile(Name,Apply=True))
    ActiveCheck.grid(row=0,column=0,padx=2,pady=2,sticky="ew")

    NullMonitorSetActiveCheckBoxes.append(ActiveCheck)

    DeleteBtn = nulltk.Button(TopRow,text="Delete Profile",command=lambda: DeleteProfile(Name,DeleteBtn,Frame),width=16)
    DeleteBtn.grid(row=0,column=3,padx=2,pady=2,sticky="ew")

    

    EnableWallPaperVar = tk.BooleanVar(value=Profiles[Name].get("EnabledWallPapers",False))

    def UpdateWallPaperEnabled(thisbutton):
        Profiles[Name]["EnabledWallPapers"] = EnableWallPaperVar.get()
        if Profiles[Name]["EnabledWallPapers"] == False:
            thisbutton.grid_remove()
        else:
            thisbutton.grid(row=1,column=1,padx=2,pady=2)
        SaveConfig("NullMonitor")

    

    ManageWallPaper = nulltk.Button(TopRow,text="Manage Wallpapers",command=lambda: ManageWallPapers(Name))
    ManageWallPaper.grid(row=1,column=1,padx=2,pady=2,sticky="ew")

    WallPapersEnabled = nulltk.Checkbutton(TopRow,text="Wallpapers",variable=EnableWallPaperVar,command= lambda: UpdateWallPaperEnabled(ManageWallPaper), width=16)
    WallPapersEnabled.grid(row=0,column=1,padx=2,pady=2,sticky="ew")

    UpdateWallPaperEnabled(ManageWallPaper)

    Spacer3 = nulltk.Frame(Frame,bg="black",height=2)
    Spacer3.pack(fill="x",pady=5)

    BtnRow = nulltk.Frame(Frame)
    BtnRow.pack(fill="x")

    nulltk.Button(BtnRow,text="Create Warp",command=lambda: OpenAddWarp(Name)).pack(side="left",padx=2)
    nulltk.Button(BtnRow,text="Delete Warp",command=lambda: OpenRemoveWarp(Name)).pack(side="left",padx=2)

    WarpBox = nulltk.Frame(Frame,padx=1,pady=1)
    WarpBox.pack(fill="x",pady=5)

    InnerWarp = nulltk.Frame(WarpBox)
    InnerWarp.pack(fill="x")

    WarpVar = tk.StringVar()

    WarpLabel = nulltk.Label(InnerWarp,textvariable=WarpVar,anchor="w",justify="left")
    WarpLabel.pack(fill="x",padx=5,pady=3)

    ProfileWidgets[Name] = {
        "Frame": Frame,
        "ActiveVar": ActiveVar,
        "EnableWallPaperVar": EnableWallPaperVar,
        "WarpVar": WarpVar
    }

    RefreshWarpDisplay(Name)

def CreateProfile():
    Name = NullMonitorProfileNameVar.get().strip()

    if not Name:
        return

    if Name in Profiles:
        return

    Layout = CaptureLayout()
    Wallpapers = {}

    for monitor in Layout:
        Wallpapers[monitor['ID']] = {
            "DTPath": "",
            "DTMode": "Fill",
            "LSPath": "",
            "LSMode": "Fill"
            }

    Profiles[Name] = {
        "Layout": Layout,
        "EnabledWallPapers": False,
        "Wallpapers": Wallpapers,
        "Warps": {},
        "DeleteConfirmation": False,
    }

    CreateProfileBox(Name)
    NullMonitorProfileNameVar.set("")
    SetActiveProfile(Name)
    SaveConfig("NullMonitor")


NullMonitorNotebook = nulltk.Notebook(NullMonitor)
NullMonitorNotebook.pack(fill="both", expand=True)
NullMonitorPage = nulltk.Frame(NullMonitorNotebook)
NullMonitorWallPapersPage = nulltk.Frame(NullMonitorNotebook)
NullMonitorNotebook.add(NullMonitorPage, text="Main")
NullMonitorNotebook.add(NullMonitorWallPapersPage, text="WallPapers",state="disabled")
NullMonitorNotebook.bind("<<NotebookTabChanged>>",NullMonitorNoteBookChange)
    #region NullMonitor Main Page
NullMonitorCheck = nulltk.Frame(NullMonitorPage)
NullMonitorCheck.pack(fill="x", padx=5, pady=5)
NullMonitorTopBar = nulltk.Frame(NullMonitorPage)
NullMonitorTopBar.pack(fill="x", padx=5, pady=5)
NullMonitorTopBar.columnconfigure(0, weight=2)
NullMonitorTopBar.columnconfigure(1, weight=1)
NullMonitorTopBar.rowconfigure(0, weight=0)
NullMonitorTopBar.rowconfigure(1, weight=0)
NullMonitorProfileBox = nulltk.Frame(NullMonitorPage)
NullMonitorProfileBox.pack(fill="x", padx=5, pady=5)
NullMonitorProfileBox.columnconfigure(0, weight=2)
NullMonitorProfileBox.columnconfigure(1, weight=1)
NullMonitorProfileBox.rowconfigure(0, weight=0)
NullMonitorProfileNameVar = tk.StringVar()
NullMonitorProfileEntry = nulltk.Entry(NullMonitorProfileBox, textvariable=NullMonitorProfileNameVar)
NullMonitorProfileEntry.grid(row=0, column=0, sticky="ew", padx=(0,5))
NullMonitorCreateBtn = nulltk.Button(NullMonitorProfileBox, text="Create Profile", command=CreateProfile)
NullMonitorCreateBtn.grid(row=0, column=1, sticky="ew")
NullMonitorEditables = nulltk.Frame(NullMonitorTopBar)
NullMonitorEditables.grid(row=1, column=0, sticky="ew", padx=(0,5))
NullMonitorStartDetectionVar = tk.IntVar(value=int(StartDetection * 1000))
NullMonitorRow = nulltk.Frame(NullMonitorEditables)
NullMonitorRow.pack(fill="x", pady=2)
NullMonitordetectionlabel = nulltk.Label(NullMonitorRow, text="Detection:", width=11)
NullMonitordetectionlabel.grid(row=0, column=0, padx=(0,0), sticky="w")
NullMonitorStartValueLabel = nulltk.Label(NullMonitorRow, text=f"{int(StartDetection * 1000)}   |", width=6)
NullMonitorStartValueLabel.grid(row=0, column=2, padx=(0,0))
NullMonitorScanValueLabel = nulltk.Label(NullMonitorRow, text=f"{ScanTime:.2f}", width=4)
NullMonitorScanValueLabel.grid(row=0, column=7, padx=(0,0))
NullMonitorSlider1 = nulltk.Scale(
    NullMonitorRow,
    from_=1,
    to=50,
    resolution=1,
    orient="horizontal",
    variable=NullMonitorStartDetectionVar,
    command=lambda v: UpdateStartDetection(v),
    showvalue=0
)
NullMonitorSlider1.grid(row=0, column=1, sticky="ew", padx=(0,0))
ToolTip(NullMonitordetectionlabel, "When your mouse enters this area, edge detection begins, Lower values may help performance, but detection might suffer. Recommended is 15")
NullMonitorSlider1.bind("<Button-4>", lambda e: (NullMonitorSlider1.set(min(50, NullMonitorSlider1.get()+5)), UpdateStartDetection(NullMonitorSlider1.get())))
NullMonitorSlider1.bind("<Button-5>", lambda e: (NullMonitorSlider1.set(max(0, NullMonitorSlider1.get()-5)), UpdateStartDetection(NullMonitorSlider1.get())))
NullMonitorSlider1.bind("<Enter>", lambda e: OnHoverEnter(e, "detection"))
NullMonitorSlider1.bind("<Leave>", lambda e: DelayedHide())
NullMonitoredge = nulltk.Label(NullMonitorRow, text="Buffer:", width= 7)
NullMonitoredge.grid(row=0, column=3, padx=(0,0), sticky="w")
NullMonitorEdgeBufferVar = tk.IntVar(value=EdgeBuffer)
NullMonitorEntry = nulltk.Entry(NullMonitorRow, textvariable=NullMonitorEdgeBufferVar, width=5)
NullMonitorEntry.grid(row=0, column=4, padx=(0,0))
NullMonitorEntry.bind("<Enter>", lambda e: OnHoverEnter(e, "edge"))
NullMonitorEntry.bind("<Leave>", lambda e: DelayedHide())
NullMonitorEdgeBufferVar.trace_add("write", UpdateEdgeBuffer)
ToolTip(NullMonitoredge, "How many pixels past the edge triggers a warp")
NullMonitorScan = nulltk.Label(NullMonitorRow, text="|   ScanTime", width=12)
NullMonitorScan.grid(row=0, column=5, padx=(0,0), sticky="w")
NullMonitorScanTimeVar = tk.DoubleVar(value=ScanTime)
NullMonitorSlider2 = nulltk.Scale(
    NullMonitorRow,
    from_=0.010,
    to=0.20,
    resolution=0.005,
    orient="horizontal",
    variable=NullMonitorScanTimeVar,
    command=lambda v: UpdateScanTime(v),
    showvalue=0
)
NullMonitorSlider2.grid(row=0, column=6, sticky="ew")
NullMonitorSlider2.bind("<Button-4>", lambda e: (NullMonitorSlider2.set(min(150, NullMonitorSlider2.get()+0.005)), UpdateScanTime()))
NullMonitorSlider2.bind("<Button-5>", lambda e: (NullMonitorSlider2.set(max(0, NullMonitorSlider2.get()-0.005)), UpdateScanTime()))
ToolTip(NullMonitorScan, "How often the cursor is scanned (higher = less CPU, more delay). Recommended is 0.05 or lower.")
NullMonitorScroll = ScrollableFrame(NullMonitorPage)
NullMonitorScroll.pack(fill="both", expand=True, padx=5, pady=5)
NullMonitorProfileContainer = NullMonitorScroll.Inner
NullMonitorProfileContainer.pack(padx=(0,10),fill="x")
NullMonitorEnabledVar = tk.BooleanVar(value=ScanForMouse)
NullMonitorDisabledOverlay = nulltk.Frame(NullMonitorTopBar,bg="#000000", ThemeBG = False)
NullMonitorDisabledOverlay.place(relx=0,rely=0,relwidth=1,relheight=1)
NullMonitorOverlayText = nulltk.Label(NullMonitorDisabledOverlay,text="NullMonitor is currently disabled. When disabled, no cursor scanning occurs, and no background resources are used. Enable 'Scan For Mouse' to activate NullMonitor.",bg="#000000",fg="white", ThemeBG = False)
NullMonitorOverlayText.pack(anchor="center")
NullMonitorToggle = nulltk.Checkbutton(NullMonitorCheck,text="Scan For Mouse",variable=NullMonitorEnabledVar,command=ToggleNullMonitor)
NullMonitorToggle.grid(row=0,column=1,columnspan=2,pady=(5,0))
    #endregion

    #region NullMonitor Wallpaper Page

NullMonitorWallPapersPage.columnconfigure(0,weight=1)
NullMonitorWallPapersPage.rowconfigure(2,weight=1)
WallpaperPreviewFrame = nulltk.LabelFrame(NullMonitorWallPapersPage,text="Monitor Layout")
WallpaperPreviewFrame.grid(row=0,column=0,padx=5,pady=5,sticky="ew")
WallpaperPreviewFrame.columnconfigure(0,weight=1)

WallpaperLayoutContainer = nulltk.Frame(WallpaperPreviewFrame)
WallpaperLayoutContainer.grid(row=0,column=0,pady=5)

WallpaperInfoFrame = nulltk.Frame(NullMonitorWallPapersPage)
WallpaperInfoFrame.grid(row=1,column=0,padx=5,pady=5,sticky="ew")
WallpaperInfoFrame.columnconfigure(0,weight=1)
WallpaperInfoFrame.columnconfigure(1,weight=0)
WallpaperInfoFrame.columnconfigure(2,weight=1)

desktoplabel = nulltk.Label(WallpaperInfoFrame, text="Desktop Wallpapers")
desktoplabel.grid(row=0,column=0,padx=5,pady=5,sticky="ew")
ttk.Separator(WallpaperInfoFrame,orient="vertical").grid(row=0,column=1,sticky="ns",padx=5)
lockscreenlabel = nulltk.Label(WallpaperInfoFrame, text="LockScreen Wallpapers")
lockscreenlabel.grid(row=0,column=2,padx=5,pady=5,sticky="ew")


WallpaperScrollFrame = ScrollableFrame(NullMonitorWallPapersPage)
WallpaperScrollFrame.grid(row=2,column=0,padx=5,pady=5,sticky="nsew")
WallpaperScrollFrame.Inner.columnconfigure(0,weight=1)
    #endregion

def NullMonitorLoop():
    global LastWarpTime, LastOutputs, LastInputs, LastSources, LoadTimes
    
    while True:

        if NullMonitorActive.get() == False:
            time.sleep(1)
            continue


        if ScanForMouse:
            x, y = GetCursorPos()
            if x is None:
                time.sleep(0.1)
                continue

            Bounds = GetMonitorBounds()
            CurrentID = GetCurrentMonitor(x, y, Bounds)

            if not CurrentID:
                continue

            B = Bounds[CurrentID]
            Corner = DetectEdge(x, y, B)

            if Corner not in ["TopLeft", "TopRight", "BottomLeft", "BottomRight", "Left", "Right", "Top", "Bottom"]:
                continue

            if not IsEdgeBuffer(Corner, x, y, B):
                continue

            if ActiveProfile not in Profiles:
                time.sleep(0.05)
                continue

            Warps = Profiles[ActiveProfile]["Warps"]

            if CurrentID not in Warps:
                continue

            for W in Warps[CurrentID]:
                if W["Edge"] != Corner:
                    continue

                TargetID = W["Target"]
                TargetEdge = W["TargetEdge"]

                if TargetID not in Bounds:
                    Log("NullMonitor: target not in bounds (I have no idea how the fuck you did that but here it is)")
                    continue

                SourceB = B

                ratio = 0.5

                if Corner in ["Left", "Right"]:
                    ratio = (y - SourceB["y1"]) / (SourceB["y2"] - SourceB["y1"])
                elif Corner in ["Top", "Bottom"]:
                    ratio = (x - SourceB["x1"]) / (SourceB["x2"] - SourceB["x1"])

                now = time.time()
                if now - LastWarpTime < WarpCooldown:
                    continue

                LastWarpTime = now
                ExecuteWarp(TargetID, TargetEdge, Bounds, ratio)
                break

        time.sleep(max(ScanTime, WarpCooldown))

def StartUpNullMonitor():
    global Profiles, ActiveProfile, ScanForMouse, LoadCompleted, SystemLoading,ActualProgramLoadedCount
    
    if NullMonitorActive.get() == True:
        SystemLoading = True
        cursor = None
        if not os.path.isfile(ConfigPath):
            Butts.set("Save File not found???")
            Root.update_idletasks()
            return False
        try:
            with open(ConfigPath, "r") as f:
                data = json.load(f)
                cursor = data.get("NullMonitor", {})

        except Exception as e:
            Butts.set(f"ERROR LOADING Null MonitorSAVE\n\n{e}")
            Root.update_idletasks()
            return False


        Profiles.clear()
        Profiles.update(cursor.get("Profiles", {}))
        ActiveProfile = cursor.get("ActiveProfile")
        ScanForMouse = cursor.get("ScanForMouse", False)
        

        if len(Profiles) == 0:
            Layout = CaptureLayout()
            Wallpapers = {}

            for monitor in Layout:
                Wallpapers[monitor['ID']] = {
                    "DTPath": "",
                    "DTMode": "Fill",
                    "LSPath": "",
                    "LSMode": "Fill"
                    }

            Profiles["Default"] = {
            "Layout": Layout,
            "EnabledWallPapers": False,
            "Wallpapers": Wallpapers,
            "Warps": {},
            "DeleteConfirmation": False,
            }
            ActiveProfile = "Default"
            SaveConfig("NullMonitor")
        
        BuildUIFromProfiles()
        NullMonitorEnabledVar.set(ScanForMouse)
        ToggleNullMonitor()

        if ActiveProfile and Profiles[ActiveProfile].get("EnabledWallPapers"):
            Root.after(1000,lambda:  UpdateLockScreenWallPapers(ActiveProfile))

        Notebook.add(NullMonitor, text="NullMonitor")
        ActualProgramLoadedCount+=1
    else:
        Notebook.forget(NullMonitor)

    SystemLoading = False
    LoadCompleted += 1
    return

#endregion

#region NullGit
Repos = {}
RepoBoxes = []
CurrentManagedRepo = None
CurrentDownloadProcess = None
NullGitDividers = []

def InstallGitLoginThings():
    Result = NullMessageBox(Root,
    "Install GitHub Support?",
    "This will install software required for GitHub integration.\n\n"
    "This includes:\n"
    "• Git\n"
    "• GitHub CLI (gh)\n\n"
    "Approximate Disk Usage: ~20 MB\n\n"
    "Continue?",
    ("SureWhyNot", "No Thanks")
    ).Show()

    if Result != "SureWhyNot":
        return

    try:
        subprocess.run(
            [
                "pkexec",
                "apt",
                "install",
                "-y",
                "git",
                "gh"
            ],
            check=True
        )

        #After V
        NullMessageBox(Root,"It's Installed~","Git and GitHub CLI have been installed.\n\n"
            "Use 'Login To GitHub' to authenticate.", ("Coolbeans 👍",)).Show()
        


        InstallGithubButton.grid_forget()
        NullGitCheckUpdates.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=5,
            pady=(3,5),
            columnspan=99
        )

    except Exception as e:
        NullMessageBox(Root,"It Broke",f"Failed to install for... Some reason. Probably This:\n\n{e}"
            ,("Well damn. OH WELL",)).Show()

def LoginToGitHub():
    try:
        subprocess.run(
            ["gh", "auth", "login"],
            check=True
        )

        NullMessageBox(Root,"You're Logged in!","Successfully logged in~", ("Yay 🎊",)).Show()


        BuildRepoList()

    except Exception as e:
        NullMessageBox(Root,"Well that failed.",f"Somethin messedup. This:\n\n{str(e)}", ("Ok...",)).Show()

def BrowseForRepo():
    Path = filedialog.askdirectory()
    if not Path:
        return
    GitPath = os.path.join(Path, ".git")
    if os.path.isdir(GitPath):
        NullGitInputPath.set(Path)
    else:
        NullMessageBox(Root,"Invalid Repo","There is no .git there...", ("Ok...",)).Show()

def CreateRepo():

    Path = NullGitCreateRepoPath.get().strip()

    if not Path:
        return

    try:

        # ------------------------------
        # Initialize Repo
        # ------------------------------

        subprocess.run(
            ["git", "init"],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        # ------------------------------
        # Check Existing Files
        # ------------------------------

        Files = [
            File
            for File in os.listdir(Path)
            if File != ".git"
        ]

        # ------------------------------
        # Empty Repo Fix
        # ------------------------------

        if not Files:

            ReadMePath = os.path.join(
                Path,
                "README.md"
            )

            with open(ReadMePath, "w") as File:

                File.write(
                    "Required file for Repo"
                )

        # ------------------------------
        # Initial Commit
        # ------------------------------

        subprocess.run(
            ["git", "add", "."],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "first"
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        # ------------------------------
        # Remote Setup
        # ------------------------------

        Remote = NullGitCreateRepoLink.get().strip()

        if Remote.startswith("git remote add origin"):
            Remote = Remote.replace("git remote add origin","").strip()

        if Remote:

            subprocess.run(
                [
                    "git",
                    "remote",
                    "add",
                    "origin",
                    Remote
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

            subprocess.run(
                [
                    "git",
                    "push",
                    "-u",
                    "origin",
                    "main"
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        # ------------------------------
        # Add To NullGit
        # ------------------------------

        AddRepo(Path)


    except subprocess.CalledProcessError as e:
        NullMessageBox(Root,"Create Repo failed!?",f"Ya Broke It:\n{e}\n\n{e.stderr}", ("Ok...",)).Show()


    except Exception as e:
        NullMessageBox(Root,"Create Repo failed!?",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def SetCloneLocation():
    Path = filedialog.askdirectory()
    if not Path:
        return
    NullGitClonePath.set(Path)

def CloneRepo():
    Path = NullGitClonePath.get().strip()
    Link = NullGitCloneLink.get().strip()
    if not Path or not Link:
        return
    try:
        subprocess.run(
            [
                "git",
                "clone",
                Link
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        RepoName = os.path.basename(Link)
        if RepoName.endswith(".git"):
            RepoName = RepoName[:-4]
        RepoPath = os.path.join(
            Path,
            RepoName
        )
        AddRepo(RepoPath)
    except subprocess.CalledProcessError as e:
        NullMessageBox(Root,"Clone Repo failed!?",f"Ya Broke It:\n{e.stderr}", ("Ok...",)).Show()
    except Exception as e:
        NullMessageBox(Root,"Clone Repo failed!?",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def SetRepoCreationLocation():
    Path = filedialog.askdirectory()
    if not Path:
        return
    NullGitCreateRepoPath.set(Path)

def GetBranches(Path):  
    try: 
        Result = subprocess.run(
            ["git", "branch", "-a", "--format=%(refname:short)"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        Branches = []

        for Branch in Result.stdout.strip().split("\n"):
            Branch = Branch.replace("remotes/origin/", "")
            Branch = Branch.replace("origin/", "")

            if Branch.strip() == "origin":
                continue

            if "HEAD" in Branch or Branch.strip() == "":
                continue

            if Branch not in Branches:
                Branches.append(Branch)

        return sorted(Branches)
    except:
        return []
    
def GetCurrentBranch(Path):
    try:
        Result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        return Result.stdout.strip()

    except:
        return ""

def ChangeBranch(Repo, Branch, StatusVar):
    StatusVar.set("🔄 Checking...")
    try:
        subprocess.run(
            ["git", "checkout", Branch],
            cwd=Repo['Path'],
            check=True,
            capture_output=True,
            text=True
        )

        StatusVar.set(GetRepoStatus(Repo))
    except Exception as e:
        NullMessageBox(Root,"Branch Change Failed",f"{str(e)}", ("Ok...",)).Show()

def GetLatestReleaseData(RepoName):
    try:
        URL = f"https://api.github.com/repos/{RepoName}/releases/latest"

        Request = urllib.request.Request(
            URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "NullSuite"
            }
        )

        with urllib.request.urlopen(Request) as Response:
            Data = json.loads(Response.read().decode())

        Assets = Data.get("assets", [])

        if (
            Data.get("tag_name")
            and isinstance(Assets, list)
            and len(Assets) > 0
        ):
            return Data
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        Log(f"NullGit: Error getting latest release data {e}", "Error")
    except Exception as e:
        Log(f"NullGit: Error getting latest release data {e}", "Error")

    return None

def GetRepoStatus(Repo):
    Path = Repo["Path"]
    Selected = Repo.get(
        "CurrentBranch",
        ""
    )

    if "[Release]" in Selected:
        try:
            RepoName = GetGitHubRepo(Path)
            if not RepoName:
                return "❔ No GitHub Repo"
            Data = GetLatestReleaseData(RepoName)
            if not Data:
                return "❔ Release Unknown"
            LatestTag = Data.get(
                "tag_name",
                ""
            )
            InstalledTag = Repo.get(
                "InstalledReleaseTag",
                ""
            )
            if not InstalledTag:
                return "❔ No Release Installed"
            if InstalledTag == LatestTag:
                return "💚 Up To Date"
            return "📛 Needs Updated"
        except Exception as e:
            Log(f"NullGit: Error getting latest release status - {e}", "Error")
            return "❔ Release Unknown"

    try:

        subprocess.run(
            ["git", "fetch"],
            cwd=Path,
            capture_output=True,
            text=True
        )

        Result = subprocess.run(
            ["git", "status", "-sb"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        Status = Result.stdout.lower()

        if "behind" in Status:
            return "📛 Needs Updated"

        if "ahead" in Status:
            return "⏩ Ahead"

        return "💚 Up To Date"

    except Exception as e:

        Log(f"NullGit: Error getting branch status {e}", "Error")

        return "❔ Unknown"

def ShowDownloadOverlay():
    DownloadOverlay.place(
        relx=0,
        rely=0,
        relwidth=1,
        relheight=1
    )

    DownloadOverlay.lift()

def HideDownloadOverlay():
    DownloadOverlay.place_forget()

def UpdateDownloadOverlay(percent=0, eta="--", file=""):
    DownloadOverlayLabel.config(
        text=(
            f"Downloading Release...\n\n"
            f"{file}\n\n"
            f"Progress: {percent:.1f}%\n"
            f"ETA: {eta}\n\n"
            "Please wait..."
        )
    )

def CancelDownload():
    global CurrentDownloadProcess
    if CurrentDownloadProcess:
        try:
            CurrentDownloadProcess.terminate()
        except:
            pass
    HideDownloadOverlay()

def PushGit(Repo, CommitMessage, Status, updatethisvar):
    Path = Repo["Path"]
    Message = CommitMessage.get().strip()
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        if Message:
            subprocess.run(
                ["git", "commit", "-m", Message],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        else:
            subprocess.run(
                ["git", "commit", "-m", "Quick Commit"],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        PushCommand = ["git", "push"]

        subprocess.run(
            PushCommand,
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        Status.set(GetRepoStatus(Repo))
        updatethisvar.set(CommitMessage.get())
        CommitMessage.set("")


    except subprocess.CalledProcessError as e:
        NullMessageBox(Root,"Push Failed",f"Sorry about that \n {e}", ("Ok...",)).Show()

    except Exception as e:
        NullMessageBox(Root,"Push Failed",f"Sorry about that \n {str(e)}", ("Ok...",)).Show()

def PullRepo(Repo, StatusVar):
    Selected = Repo.get(
        "CurrentBranch",
        ""
    )

    if "[Branch]" in Selected:
        Branch = Selected.replace(
            " [Branch]",
            ""
        )
        Path = Repo["Path"]
        StatusVar.set("🔄 Pulling...")
        try:
            subprocess.run(
                [
                    "git",
                    "pull",
                    "origin",
                    Branch
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
            StatusVar.set(
                GetRepoStatus(Repo)
            )
        except subprocess.CalledProcessError as e:
            StatusVar.set(
                "🔴 Pull Failed"
            )
            NullMessageBox(Root,"Pull Failed",f"{e.stderr}", ("Ok...",)).Show()
        except Exception as e:
            StatusVar.set(
                "🔴 Pull Failed"
            )
            NullMessageBox(Root,"Pull Failed",f"{str(e)}", ("Ok...",)).Show()
        return

    if "[Release]" in Selected:
        PullRelease(
            Repo,
            StatusVar
        )
        return
    StatusVar.set(
        "⚪ Unknown"
    )

def PushOnlyCommited():

    if not CurrentManagedRepo:
        return

    Path = CurrentManagedRepo["Path"]

    Message = OnlyCommitMessage.get().strip()

    try:
        if Message:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    Message
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        else:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "Quick Commit"
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        subprocess.run(
            [
                "git",
                "push"
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        CommittedVar.set(
            Result.stdout.strip()
        )

        OnlyCommitMessage.set("")
    except subprocess.CalledProcessError as e:
        NullMessageBox(Root,"Push Failed",f"{e.stderr}", ("Ok...",)).Show()
    except Exception as e:
        NullMessageBox(Root,"Push Failed",f"{str(e)}", ("Ok...",)).Show()

def ForcePushCommit():
    if not CurrentManagedRepo:
        return
    Path = CurrentManagedRepo["Path"]
    Message = OnlyCommitMessage.get().strip()
    Confirm = NullMessageBox(Root,"Force It???",f"Are you Sure you want to FORCE it? Might mess things up", ("Sure Do"," Nope, Accident",)).Show()

    if not Confirm:
        return

    try:
        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        StagedFiles = Result.stdout.strip()
        if not StagedFiles:

            subprocess.run(
                [
                    "git",
                    "add",
                    "."
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        if Message:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    Message
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        else:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "I wasn't asking. I said COMMIT"
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        subprocess.run(
            [
                "git",
                "push",
                "--force"
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set(
            Result.stdout.strip()
        )
        OnlyCommitMessage.set("")

    except subprocess.CalledProcessError as e:
        NullMessageBox(Root,"That Somehow Failed",f"{e.stderr}", ("Ok...",)).Show()
    except Exception as e:
        NullMessageBox(Root,"That Somehow Failed",f"{str(e)}", ("Ok...",)).Show()

def OnNotebookChanged(event):
    CurrentTab = NullGitNotebook.select()
    if str(CurrentTab) == str(NullGitMainPage):
        NullGitNotebook.forget(NullGitManagePage)
        global CurrentManagedRepo
        CurrentManagedRepo = None

def MergeBranch():
    
    global CurrentManagedRepo
    Path = CurrentManagedRepo["Path"]
    Branch = CurrentMergeBranch.get()
    if not Branch:
        return

    try:
        subprocess.run(
            ["git", "merge", Branch],
            cwd=Path,
            check=True
        )
    except Exception as e:
        Log(f"NullGit: Failed to merge {e}")

def ManageRepo(Repo):
    global CurrentManagedRepo
    Path = Repo["Path"]

    CurrentManagedRepo = Repo

    ManageRepoPath.set(Path)
    try:
        Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        ManageRemoteURL.set(
            Result.stdout.strip()
        )
    except:
        ManageRemoteURL.set("")

    ManageBranchName.set(
        Repo.get("CurrentBranch", "")
    )
    GitIgnorePath = os.path.join(
        Path,
        ".gitignore"
    )
    if os.path.exists(GitIgnorePath):
        CreateGitIgnoreButton.grid_remove()
        EditGitIgnoreButton.grid()
        with open(GitIgnorePath, "r") as File:

            GitIgnoredVar.set(
                File.read()
            )

        GitList.grid()

    else:
        EditGitIgnoreButton.grid_remove()
        CreateGitIgnoreButton.grid()
        GitIgnoredVar.set("")
        GitList.grid_remove()

    try:
        Result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        Files = Result.stdout.strip()
        CommittedVar.set(Files)

    except:
        CommittedVar.set("")

    try:
        Result = subprocess.run(
            ["git", "branch"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        Branches = []

        for B in Result.stdout.splitlines():

            Clean = B.replace ("*", "").strip()
            if Clean != CurrentManagedRepo["CurrentBranch"].replace(" [Branch]", ""):
                Branches.append(Clean)

        MergeBranchBox["values"] = Branches

    except Exception as e:
        Log(f"NullGit: Error with Manage - {e}", "Error")

    NullGitNotebook.add(NullGitManagePage, text="Manage")
    NullGitNotebook.select(NullGitManagePage)
    return

def DownloadReleaseThread(Repo, StatusVar, SelectedAssets, Tag, Path, OpenOnFinish):

    global CurrentDownloadProcess

    try:

        TotalAssets = len(SelectedAssets)

        CurrentAsset = 0

        for Asset in SelectedAssets:

            CurrentAsset += 1

            DownloadURL = Asset.get("browser_download_url", "")
            FileName = Asset.get("name", "UnknownFile")

            NameLower = FileName.lower()

            if "linux" in NameLower:
                Platform = "Linux"

            elif "windows" in NameLower:
                Platform = "Windows"

            elif "mac" in NameLower:
                Platform = "Mac"

            else:
                Platform = "Unknown"

            ReleasePath = os.path.join(Path, "Releases", Platform)

            os.makedirs(ReleasePath, exist_ok=True)

            DownloadPath = os.path.join(ReleasePath, FileName)

            Root.after(
                0,
                UpdateDownloadOverlay,
                0,
                "--",
                f"{FileName}\n({CurrentAsset}/{TotalAssets})"
            )

            StatusVar.set(f"🟣 Downloading...")

            CurrentDownloadProcess = subprocess.Popen(
                [
                    "wget",
                    "--progress=bar:force",
                    "-O",
                    DownloadPath,
                    DownloadURL
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )

            Percent = 0
            ETA = "--"

            for Line in CurrentDownloadProcess.stdout:

                Line = Line.strip()


                PercentMatch = re.search(r"(\d+)\%", Line)

                ETAMatch = re.search(
                    r"ETA\s+([0-9hms:]+)",
                    Line,
                    re.IGNORECASE
                )

                if PercentMatch:
                    Percent = float(PercentMatch.group(1))

                if ETAMatch:
                    ETA = ETAMatch.group(1)

                Root.after(
                    0,
                    UpdateDownloadOverlay,
                    Percent,
                    ETA,
                    f"{FileName}\n({CurrentAsset}/{TotalAssets})"
                )

            CurrentDownloadProcess.wait()

            if CurrentDownloadProcess.returncode != 0:

                Root.after(
                    0,
                    HideDownloadOverlay
                )

                Root.after(
                    0,
                    lambda: NullMessageBox(Root,"Download... Failed?",f"{FileName} failed to download o.O", ("Ok...",)).Show()
                )

                return

            if FileName.endswith(".zip"):

                subprocess.run(
                    ["unzip", "-o", DownloadPath, "-d", ReleasePath],
                    check=True
                )

                os.remove(DownloadPath)

            elif FileName.endswith(".7z"):

                subprocess.run(
                    ["7z", "x", "-y", DownloadPath, f"-o{ReleasePath}"],
                    check=True
                )

                os.remove(DownloadPath)

        Repo["InstalledReleaseTag"] = Tag

        SaveConfig("NullGit")

        Root.after(
            0,
            HideDownloadOverlay
        )

        Root.after(
            0,
            lambda: StatusVar.set(
                "💚 Up To Date"
            )
        )
        if OpenOnFinish:

            subprocess.Popen(
                ["xdg-open", ReleasePath]
            )


    except Exception as e:

        Root.after(
            0,
            HideDownloadOverlay
        )

        Root.after(
            0,
            lambda: StatusVar.set(
                "❌ Failed"
            )
        )

        Root.after(
            0,
            lambda: NullMessageBox(Root,"Download... Failed?",f"For this reason:\n{str(e)}", ("Ok...",)).Show()
            )
    finally:
        CurrentDownloadProcess = None

def PullRelease(Repo, StatusVar):

    Path = Repo["Path"]

    RepoName = GetGitHubRepo(Path)

    if not RepoName:
        StatusVar.set("🔴 No Repo")
        return

    StatusVar.set("🟣 Checking...")

    try:

        Data = GetLatestReleaseData(RepoName)

        if not Data:

            StatusVar.set("🔴 No Release")

            NullMessageBox(Root,"No Release Found?",f"Can't pull something that don't exist.", ("Ok...",)).Show()

            return

        Assets = Data.get("assets", [])

        if not Assets:

            StatusVar.set("🔴 No Assets")

            NullMessageBox(Root,"Nothing to download?",f"release has no downloadable files?", ("Ok...",)).Show()

            return

        # ==================================================
        # Asset Selection Popup
        # ==================================================

        Popup = nulltk.Toplevel(Root)

        Popup.title("Select Release Assets")

        Popup.geometry("500x450")

        Popup.transient(Root)

        Popup.grab_set()

        nulltk.Label(
            Popup,
            text="Select Release Assets"
        ).pack(pady=5)

        Scroll = ScrollableFrame(Popup)

        Scroll.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        AssetVars = []

        for Asset in Assets:

            Name = Asset.get("name", "Unknown")

            Size = round(
                Asset.get("size", 0) / 1024 / 1024,
                2
            )

            Var = tk.BooleanVar()

            nulltk.Checkbutton(
                Scroll.Inner,
                text=f"{Name} ({Size} MB)",
                variable=Var
            ).pack(
                anchor="w",
                padx=5,
                pady=2
            )

            AssetVars.append({
                "Var": Var,
                "Asset": Asset
            })

        OpenOnFinish = tk.BooleanVar(value=False)

        nulltk.Checkbutton(
            Popup,
            text="Open Folder After Download",
            variable=OpenOnFinish
        ).pack(pady=5)

        SelectedAssets = []

        def DownloadSelected():

            for Item in AssetVars:

                if Item["Var"].get():

                    SelectedAssets.append(
                        Item["Asset"]
                    )

            Popup.destroy()

        nulltk.Button(
            Popup,
            text="Download Selected",
            command=DownloadSelected
        ).pack(pady=5)

        Popup.wait_window()

        # ==================================================
        # Cancelled
        # ==================================================

        if not SelectedAssets:

            StatusVar.set("⚪ Cancelled")

            return

        Tag = Data.get(
            "tag_name",
            "UnknownRelease"
        )

        # ==================================================
        # Start Download Thread
        # ==================================================

        ShowDownloadOverlay()

        UpdateDownloadOverlay(
            0,
            "--",
            "Preparing Download..."
        )

        threading.Thread(
            target=DownloadReleaseThread,
            args=(
                Repo,
                StatusVar,
                SelectedAssets,
                Tag,
                Path,
                OpenOnFinish.get()
            ),
            daemon=True
        ).start()

    except Exception as e:

        StatusVar.set("🔴 Failed")

        NullMessageBox(Root,"Pull Failed",f"{str(e)}", ("Ok...",)).Show()

def GetGitHubRepo(Path):
    try:
        Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        URL = Result.stdout.strip()
        URL = URL.replace("git@github.com:", "")
        URL = URL.replace("https://github.com/", "")
        URL = URL.replace(".git", "")
        return URL

    except:
        return None

def UpdateRepoStatus(Repo, StatusVar):
    Result = GetRepoStatus(Repo)
    Root.after(
        0,
        lambda: StatusVar.set(Result)
    )

def UpdateReleaseOption(
    Repo,
    RepoOptions,
    BranchBox
):

    try:

        RepoName = GetGitHubRepo(
            Repo["Path"]
        )

        if not RepoName:
            return

        Data = GetLatestReleaseData(
            RepoName
        )

        if (
            Data
            and Data.get("tag_name")
            and isinstance(Data.get("assets"), list)
            and len(Data.get("assets")) > 0
        ):

            RepoOptions.append({
                "Label":"Latest [Release]",
                "Type":"Release",
                "Value":"latest"
            })

            DisplayValues = [
                x["Label"]
                for x in RepoOptions
            ]

            Root.after(
                0,
                lambda: BranchBox.config(
                    values=DisplayValues
                )
            )

    except Exception as e:

       Log(f"NullGit: Release Detection Error - {e}", "Error")

def GetCurrentCommit(Path):
    try:
        return subprocess.check_output(
            ["git","log","-1","--pretty=%s"],
            cwd=Path,
            text=True
        ).strip()
    except:
        return "Unknown Commit"

def GetReleaseDisplay(Repo):
    RepoName = GetGitHubRepo(Repo["Path"])

    if not RepoName:
        return "Unknown Release"

    Data = GetLatestReleaseData(RepoName)

    if not Data:
        return "Unknown Release"

    return Data.get("tag_name", "Unknown Release")

def AddRepoObject(Repo):
    global RepoBoxes,NullGitDividers
    Frame = nulltk.LabelFrame(NullGitcontainer, text=Repo["Name"])
    Frame.pack(fill="x", padx=5, pady=5)
    Frame.columnconfigure(0, weight=0)
    Frame.columnconfigure(1, weight=2)
    Frame.columnconfigure(2, weight=0)
    for i in range(9):
        Frame.rowconfigure(i, weight=0)

    StatusVar = tk.StringVar()
    StatusVar.set("⚪ Checking...")
    Branches = GetBranches(Repo["Path"])
    RepoOptions = []
    CommitVar = tk.StringVar()

    for Branch in Branches:
        RepoOptions.append({"Label": f"{Branch} [Branch]", "Type": "Branch", "Value": Branch})

    
    DisplayValues = [x["Label"] for x in RepoOptions]
    SavedBranch = Repo.get("CurrentBranch", f"{GetCurrentBranch(Repo['Path'])} [Branch]")
    CurrentBranch = tk.StringVar(value=SavedBranch)
    Repo["CurrentBranch"] = SavedBranch
    def OnRepoOptionChanged():
        Selected = CurrentBranch.get()
        Match = next((x for x in RepoOptions if x["Label"] == Selected), None)
        if not Match:
            return
        Repo["CurrentBranch"] = Match["Label"]
        if Match["Type"] == "Branch":
            ChangeBranch(Repo, Match["Value"], StatusVar)
            CommitVar.set(GetCurrentCommit(Repo["Path"]))
        elif Match["Type"] == "Release":
            CommitVar.set(GetReleaseDisplay(Repo))
        StatusVar.set(GetRepoStatus(Repo))
        SaveConfig("NullGit")
        Frame.focus_set()


    StatusLabel = nulltk.Label(Frame, textvariable=StatusVar, width=15, padx=5)
    StatusLabel.grid(row=0, column=0, sticky="ew")

    BranchBox = nulltk.Combobox(Frame, values=DisplayValues, textvariable=CurrentBranch, state="readonly")
    BranchBox.grid(row=0, column=1, sticky="ew",padx=10)
    BranchBox.bind("<<ComboboxSelected>>", lambda e: OnRepoOptionChanged())
    BranchBox.unbind_class("TCombobox", "<Button-4>")
    BranchBox.unbind_class("TCombobox", "<Button-5>")

    try:
        threading.Thread(target=UpdateReleaseOption,args=(Repo,RepoOptions,BranchBox),daemon=True).start()
    except Exception as e:
        Log(f"NullGit: Release Detection Error {e}", "Error")

    

    nulltk.Button(Frame, text="Pull Repo", width=10, command=lambda: PullRepo(Repo, StatusVar)).grid(row=1, column=0, sticky="ew",pady=5, padx=5)
    
    CommitLabel = nulltk.Entry(Frame,textvariable=CommitVar, state="readonly")
    CommitLabel.grid(row=1,column=1,columnspan=3,sticky="ew",padx=10,pady=5)

    ttk.Separator(Frame, orient="horizontal").grid(row=2, column=0, sticky="ew", columnspan=99, pady=6)
    
    InnerFrame = nulltk.Frame(Frame)
    InnerFrame.grid(row=6, column=0, sticky="ew", padx=5, pady=2,columnspan=3)
    InnerFrame.columnconfigure(0, weight=1)
    InnerFrame.columnconfigure(1, weight=1)
    nulltk.Button(InnerFrame, text="Open Repo In Browser", command=lambda: OpenRepo(Repo, False)).grid(row=0, column=0, sticky="ew", padx=5, pady=2)
    nulltk.Button(InnerFrame, text="Open Repo Location", command=lambda: OpenRepo(Repo, True)).grid(row=0, column=1, sticky="ew", padx=5, pady=2)

    ttk.Separator(Frame, orient="horizontal").grid(row=7, column=0, sticky="ew", columnspan=99, pady=6)
    if IsOwner(Repo['Path']):
        CommitMessage = tk.StringVar()
        CommitMessageShow = nulltk.Label(Frame, text="Commit Message:", width=15, padx=5)
        CommitMessageShow.grid(row=3, column=0, sticky="ew")
        CommitEntry = nulltk.Entry(Frame, width=30, textvariable=CommitMessage)
        CommitEntry.grid(row=3, column=1, sticky="ew", padx=5)
        nulltk.Button(Frame, text="Push Repo", width=10, command=lambda: PushGit(Repo, CommitMessage, StatusVar, CommitVar)).grid(row=4, column=0, padx=5)
        ttk.Separator(Frame, orient="horizontal").grid(row=5, column=0, sticky="ew", columnspan=99, pady=6)
        nulltk.Button(Frame, text="Manage Repo", command=lambda: ManageRepo(Repo)).grid(row=8, column=0, columnspan=99, sticky="ew", padx=5, pady=5)
        
    else:
        DeleteButton = nulltk.Button(Frame, text="Delete Repo From NullGit", command=lambda: DeleteRepoInNull(Repo, DeleteButton))
        DeleteButton.grid(row=8, column=0, sticky="ew", padx=5, pady=5, columnspan=3)

    threading.Thread(target=UpdateRepoStatus,args=(Repo, StatusVar),daemon=True).start()
    Root.after(1, OnRepoOptionChanged)
    RepoBoxes.append(Frame)
    NullGitReposList.BindMouseWheel(NullGitMainPage)

    RepoNullGitSep = nulltk.Frame(NullGitcontainer,height=6,Reversed = True)
    RepoNullGitSep.pack(fill="x", padx=1, pady=(10,5))

    NullGitDividers.append(RepoNullGitSep)
    
def BuildRepoList():
    global RepoBoxes, NullGitDividers

    for div in range(len(NullGitDividers)):
        NullGitDividers[div].destroy()

    NullGitDividers.clear()

    for Box in RepoBoxes:
        Box.destroy()

    RepoBoxes.clear()

    for repo in Repos.values():
        AddRepoObject(repo)
        
    return

def GetLoggedInGitHubUser():
    if shutil.which("gh") is None:
        InstallGithubButton.grid(row=0, column=1, sticky="ew", padx=5, pady=(3,5))
        NullGitCheckUpdates.grid(row=0, column=0, sticky="ew", padx=5, pady=(3,5))
        return None

    try:
        Result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=True
        )
        return Result.stdout.strip().lower()
    except:
        return None

def GetRepoOwner(Path):
    try:
        Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        URL = Result.stdout.strip().lower()
        URL = URL.replace("git@github.com:", "")
        URL = URL.replace("https://github.com/", "")
        URL = URL.replace(".git", "")
        Owner = URL.split("/")[0]
        return Owner
    except:
        return None

def IsOwner(Path):
    if shutil.which("gh") is None:
        InstallGithubButton.grid(row=0, column=1, sticky="ew", padx=5, pady=(3,5))
        NullGitCheckUpdates.grid(row=0, column=0, sticky="ew", padx=5, pady=(3,5))
        return False

    User = GetLoggedInGitHubUser()
    if not User:
        return False
    Owner = GetRepoOwner(Path)
    if not Owner:
        return False
    return User == Owner

def AddRepo(Path):

    Name = os.path.basename(Path)

    if Path in Repos:
        return
    
    Repos[Path] = {
        "Name": Name,
        "Path": Path,
        "DeleteConfirmation": False
    }

    SaveConfig("NullGit")
    BuildRepoList()

def OpenRepo(Repo, LocalOrNet=True):
    try:
        if LocalOrNet:
            subprocess.Popen(
                ["xdg-open", Repo["Path"]]
            )
        else:
            Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Repo["Path"],
            capture_output=True,
            text=True,
            check=True
        )
            URL = Result.stdout.strip()

            if URL.startswith("git@github.com:"):
                URL = URL.replace(
                    "git@github.com:",
                    "https://github.com/"
                )
            if URL.endswith(".git"):
                URL = URL[:-4]
            subprocess.Popen(
                ["xdg-open", URL]
            )
    except Exception as e:
        NullMessageBox(Root,"Idk how... But Open failed?",f"{str(e)}", ("Ok...",)).Show()

def DeleteRepoInNull(Repo, Button, Timeout=4):
    EndTime = time.time() + (Timeout)

    def Tick(Repo):
        if Repo == None:
            return
        else:
            Remaining = int(EndTime - time.time())
            if Remaining <= 0:
                if not Button.winfo_exists():
                    return
                Button.config(text="Delete Repo From NullGit")
                Repo['DeleteConfirmation'] = False
                return
            if not Button.winfo_exists():
                return
            else:
                Button.config(text=f"R U Sure? {Remaining}")
                Root.after(1000, Tick, Repo)

    if Repo['DeleteConfirmation'] == False:
        Repo['DeleteConfirmation'] = True
        Tick(Repo)
        return
    Path = Repo["Path"]
    Repos.pop(Path, None)
    SaveConfig("NullGit")
    BuildRepoList()
    NullGitNotebook.select(NullGitMainPage)

def CreateBranchOnGit():
    if not CurrentManagedRepo:
        return
    Path = CurrentManagedRepo["Path"]
    Branch = ManageBranchName.get().strip()
    if not Branch:
        return
    try:
        subprocess.run(
            ["git", "checkout", "-b", Branch],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        
        subprocess.run(
        ["git", "push", "--set-upstream", "origin", Branch],
        cwd=Path,
        check=True,
        capture_output=True,
        text=True
        )
        SaveConfig("NullGit")
        BuildRepoList()
    except Exception as e:
        NullMessageBox(Root,"Branch Creation Failed?",f"{str(e)}", ("Ok...",)).Show()

def RenameBranchOnGit():
    if not CurrentManagedRepo:
        return
    Path = CurrentManagedRepo["Path"]
    OldBranch = CurrentManagedRepo["CurrentBranch"].replace(" [Branch]","")
    NewBranch = ManageBranchName.get().strip()
    if not NewBranch:
        return
    try:
        subprocess.run(
            [
                "git",
                "branch",
                "-m",
                OldBranch,
                NewBranch
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        CurrentManagedRepo["CurrentBranch"] = f"{NewBranch} [Branch]"
        SaveConfig("NullGit")
        BuildRepoList()
    except Exception as e:
        NullMessageBox(Root,"Renaming Branch Failed",f"{str(e)}", ("Ok...",)).Show()

def DeleteBranchOnGit():

    if not CurrentManagedRepo:
        return

    Path = CurrentManagedRepo["Path"]

    Branch = CurrentManagedRepo["CurrentBranch"].replace(" [Branch]","")

    Branches = GetBranches(Path)

    if len(Branches) <= 1:

        NullMessageBox(Root,"Can't let you do that starfox",f"Gotta have at least one branch.", ("Ok...",)).Show()

        return

    Confirm = NullMessageBox(Root,
    "Delete The Branch?",
    ("He's Dead Jim(Yes)", "Nuh Uh")
    ).Show()

    if not Confirm:
        return

    try:
        OtherBranch = next(
            B for B in Branches
            if B != Branch
        )
        subprocess.run(
            [
                "git",
                "checkout",
                OtherBranch
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            [
                "git",
                "branch",
                "-D",
                Branch
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        DeleteRemote = NullMessageBox(Root,
        "Delete On Github Too?",
        "It's Been deleted...Wanna delete it on Github too?",
        ("SureWhyNot", "No Thanks")
        ).Show()

        
        if DeleteRemote:
            subprocess.run(
            [
                "git",
                "push",
                "origin",
                "--delete",
                Branch
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
            )
        SaveConfig("NullGit")
        BuildRepoList()
        NullGitNotebook.select(
            NullGitMainPage
        )
        NullMessageBox(Root,
        "Branch Killed",
        f"The branch was deleted → {Branch}",
        ("OK!",)
        ).Show()

    except subprocess.CalledProcessError as e:
        NullMessageBox(Root,"Deleting The Branch Failed!?",f"Ya Broke It:\n{e}\n\n{e.stderr}", ("Ok...",)).Show()

    except Exception as e:
        NullMessageBox(Root,"Deleting The Branch Failed!?",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def CreateGitIgnoreFile():
    if not CurrentManagedRepo:
        NullMessageBox(Root,"creating the .ignore failed o_O",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()
        return
    Path = CurrentManagedRepo["Path"]
    GitIgnorePath = os.path.join(
        Path,
        ".gitignore"
    )
    try:
        open(GitIgnorePath, "w").close()
        CreateGitIgnoreButton.grid_remove()
        EditGitIgnoreButton.grid()
        GitList.grid()
        GitIgnoredVar.set("")

    except Exception as e:
        NullMessageBox(Root,"creating the .ignore failed o_O",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def EditGitIgnoreFile():

    Popup = nulltk.Toplevel(Root)
    Popup.title("Edit .gitignore")
    Popup.resizable(False, False)

    Popup.transient(Root)
    Popup.grab_set()

    Frame = nulltk.Frame(Popup)
    Frame.pack(padx=10, pady=10)

    nulltk.Label(
        Frame,
        text="What do you want to ignore?"
    ).pack(fill="x", pady=(0, 10))

    nulltk.Button(
        Frame,
        text="Select File",
        command=lambda: SelectGitIgnore(
            "file",
            Popup
        )
    ).pack(fill="x", pady=3)

    nulltk.Button(
        Frame,
        text="Select Folder",
        command=lambda: SelectGitIgnore(
            "folder",
            Popup
        )
    ).pack(fill="x", pady=3)

def SelectGitIgnore(Type, Popup):

    Popup.destroy()

    if not CurrentManagedRepo:
        return

    RepoPath = CurrentManagedRepo["Path"]

    if Type == "file":

        SelectedPath = filedialog.askopenfilename(
            initialdir=RepoPath
        )

    else:

        SelectedPath = filedialog.askdirectory(
            initialdir=RepoPath
        )

    if not SelectedPath:
        return

    try:

        GitIgnorePath = os.path.join(
            RepoPath,
            ".gitignore"
        )

        RelativePath = os.path.relpath(
            SelectedPath,
            RepoPath
        )

        RelativePath = "/" + RelativePath.replace("\\", "/")

        if os.path.isdir(SelectedPath):
            RelativePath += "/"

        Lines = []

        if os.path.exists(GitIgnorePath):

            with open(GitIgnorePath, "r") as File:

                Lines = [
                    Line.strip()
                    for Line in File.readlines()
                    if Line.strip()
                ]

        if RelativePath in Lines:

            # ------------------------------
            # Remove ignore
            # ------------------------------
            Lines.remove(RelativePath)

            subprocess.run(
                [
                    "git",
                    "add",
                    RelativePath.strip("/")
                ],
                cwd=RepoPath,
                capture_output=True,
                text=True
            )

        else:

            # ------------------------------
            # Add ignore
            # ------------------------------
            Lines.append(RelativePath)

            subprocess.run(
                [
                    "git",
                    "rm",
                    "--cached",
                    "-r",
                    RelativePath.strip("/")
                ],
                cwd=RepoPath,
                capture_output=True,
                text=True
            )

        Lines = sorted(set(Lines))

        with open(GitIgnorePath, "w") as File:

            File.write(
                "\n".join(Lines)
            )

        GitIgnoredVar.set(
            "\n".join(Lines)
        )

        if Lines:
            GitList.grid()
        else:
            GitList.grid_remove()

    except Exception as e:
        NullMessageBox(Root,"Editing Failed?",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def AddFileToCommit():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]
    SelectedPath = filedialog.askopenfilename(
        initialdir=RepoPath
    )
    if not SelectedPath:
        return
    try:
        RelativePath = os.path.relpath(
            SelectedPath,
            RepoPath
        )
        RelativePath = RelativePath.replace(
            "\\",
            "/"
        )
        subprocess.run(
            [
                "git",
                "add",
                RelativePath
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )

        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set(
            Result.stdout.strip()
        )

    except Exception as e:
        NullMessageBox(Root,"Adding File Failed?",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def RemoveFileFromCommit():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]
    SelectedPath = filedialog.askopenfilename(
        initialdir=RepoPath
    )
    if not SelectedPath:
        return

    try:
        RelativePath = os.path.relpath(
            SelectedPath,
            RepoPath
        )
        RelativePath = RelativePath.replace(
            "\\",
            "/"
        )
        subprocess.run(
            [
                "git",
                "reset",
                "HEAD",
                RelativePath
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )

        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set(
            Result.stdout.strip()
        )
    except Exception as e:
        NullMessageBox(Root,"Remove Failed?",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def ClearCurrentCommit():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]

    Confirm = NullMessageBox(Root,
    "Clear The Commit?",
    "You sure you want to remove everything from the current commit?",
    ("SureWhyNot", "No Thanks")
    ).Show()

    if not Confirm:
        return
    try:
        subprocess.run(
            [
                "git",
                "reset",
                "HEAD"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set("")

        NullMessageBox(Root,
        "Commit Cleared",
        "All staged files removed~",
        ("OK!",)
        ).Show()
    except Exception as e:
        NullMessageBox(Root,"Well That failed!?",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

def StashAndPull():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]
    
    Confirm = NullMessageBox(Root,
    "Stash That Shit?",
    "Yup abandon all and pull the current. \n Sure you want to do this?",
    ("SureWhyNot", "No Thanks")
    ).Show()

    if not Confirm:
        return

    try:
        subprocess.run(
            [
                "git",
                "stash"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        subprocess.run(
            [
                "git",
                "pull"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        
        NullMessageBox(Root,
        "Repo Updated~",
        "Local changes stashed.\nLatest repo pulled.",
        ("OK!",)
        ).Show()


        BuildRepoList()
        SaveConfig("NullGit")

    except Exception as e:
        NullMessageBox(Root,"Well That Failed",f"Ya Broke It:\n{str(e)}", ("Ok...",)).Show()

NullGitNotebook = nulltk.Notebook(NullGit)
NullGitNotebook.pack(fill="both", expand=True)
NullGitMainPage = nulltk.Frame(NullGitNotebook)
NullGitManagePage = nulltk.Frame(NullGitNotebook)
NullGitNotebook.add(NullGitMainPage, text="Repos")
NullGitNotebook.add(NullGitManagePage, text="Manage")
NullGitNotebook.bind("<<NotebookTabChanged>>",OnNotebookChanged)
    #region MainPage
NullGitMainPage.rowconfigure(0, weight=1)
NullGitMainPage.columnconfigure(0, weight=1)
NullGitInputPath = tk.StringVar()
NullGitCreateRepoPath = tk.StringVar()
NullGitCreateRepoLink = tk.StringVar()
NullGitClonePath = tk.StringVar()
NullGitCloneLink =tk.StringVar()
NullGitReposList = ScrollableFrame(NullGitMainPage)
NullGitReposList.grid(row=0, column=0, sticky="nsew", padx=5, columnspan=3)
NullGitcontainer = NullGitReposList.Inner
DownloadOverlay = nulltk.Frame(NullGit,bg="#000000", ThemeBG = False)
DownloadOverlayLabel = nulltk.Label(DownloadOverlay,text="Downloading...",font=("Arial", 12),justify="center")
DownloadOverlayLabel.pack(expand=True)
nulltk.Button(DownloadOverlay,text="Cancel",command=CancelDownload).pack(pady=10)
NullGitOptionsArea = nulltk.LabelFrame(NullGitcontainer, text= "NullGit Options")
NullGitOptionsArea.pack(fill="x", padx=5, pady=5)
NullGitOptionsArea.columnconfigure(0, weight=1)
NullGitOptionsArea.columnconfigure(1, weight=1)
NullGitCheckUpdates = nulltk.Button(NullGitOptionsArea, text="Check For Updates",command=lambda:BuildRepoList())
NullGitCheckUpdates.grid(row=0, column=0, columnspan=99, sticky="ew", padx=5, pady=(3,5))
InstallGithubButton = nulltk.Button(NullGitOptionsArea, text="Install Github Login",command=lambda: InstallGitLoginThings())
InstallGithubButton.grid(row=0, column=1, sticky="e", padx=5)
InstallGithubButton.grid_forget()
NullGitAddRepo = nulltk.LabelFrame(NullGitcontainer, text= "Add A Repo")
NullGitAddRepo.pack(fill="x", padx=5, pady=5)
NullGitAddRepo.columnconfigure(1, weight=1)
nulltk.Button(NullGitAddRepo, text="Browse For Repo", width =16,command=lambda: BrowseForRepo()).grid(row=0, column=0, sticky="e", padx=5, pady=5)
nulltk.Entry(NullGitAddRepo,width=30,textvariable=NullGitInputPath,state="readonly",readonlybackground="#e7e7e7").grid(row=0, column=1, sticky="ew")
nulltk.Button(NullGitAddRepo, text="Add Repo", width =16,command=lambda: AddRepo(NullGitInputPath.get())).grid(row=0, column=2, sticky="e", padx=5)
NullGitCreateRepo = nulltk.LabelFrame(NullGitcontainer, text= "Create Repo")
NullGitCreateRepo.pack(fill="x", padx=5, pady=5)
NullGitCreateRepo.columnconfigure(1, weight=1)
NullGitCreateRepo.columnconfigure(2, weight=1)
nulltk.Button(NullGitCreateRepo, text="Creation Location", width =16,command=lambda: SetRepoCreationLocation()).grid(row=0, column=0, sticky="w", padx=5, pady=5)
nulltk.Entry(NullGitCreateRepo,width=30,textvariable=NullGitCreateRepoPath,state="readonly",).grid(row=0, column=1, sticky="ew")
nulltk.Entry(NullGitCreateRepo,width=30,textvariable=NullGitCreateRepoLink,).grid(row=0, column=2, sticky="ew")
nulltk.Button(NullGitCreateRepo, text="Create Repo", width =16,command=lambda:CreateRepo()).grid(row=0, column=3, sticky="ew", padx=5)
NullGitCloneRepo = nulltk.LabelFrame(NullGitcontainer, text= "Clone Repo")
NullGitCloneRepo.pack(fill="x", padx=5, pady=5)
NullGitCloneRepo.columnconfigure(1, weight=1)
NullGitCloneRepo.columnconfigure(2, weight=1)
nulltk.Button(NullGitCloneRepo, text="Set Clone Location", width =16,command=lambda:SetCloneLocation()).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
nulltk.Entry(NullGitCloneRepo,width=30,textvariable=NullGitClonePath,state="readonly",readonlybackground="#e7e7e7").grid(row=0, column=1, sticky="ew")
GitCloneRepoEntry = nulltk.Entry(NullGitCloneRepo,width=30,textvariable=NullGitCloneLink,readonlybackground="#e7e7e7")
GitCloneRepoEntry.grid(row=0, column=2, sticky="ew")
ToolTip(GitCloneRepoEntry, "Paste the github link here. you do not need to add \"git\", just the link to the webpage will suffice.")
nulltk.Button(NullGitCloneRepo, text="Clone Repo", width =16,command=lambda:CloneRepo()).grid(row=0, column=3, sticky="w", padx=5)
NullGitSep = nulltk.Frame(NullGitcontainer,height=12, Reversed = True)
NullGitSep.pack(fill="x", padx=1, pady=(10,5))
    #endregion
    #region ManagePage
ManageRemoteURL = tk.StringVar()
ManageRepoPath = tk.StringVar()
ManageBranchName = tk.StringVar()
GitIgnoredVar = tk.StringVar()
CommittedVar = tk.StringVar()
NullGitManagePage.columnconfigure(0, weight=1)
NullGitManagePage.rowconfigure(0, weight=0)
NullGitManagePage.rowconfigure(1, weight=0)
NullGitManagePage.rowconfigure(2, weight=1)
NullGitManagePage.rowconfigure(3, weight=1)
NullGitManagePage.rowconfigure(4, weight=0)
RepoFrame = nulltk.LabelFrame(NullGitManagePage,text="Repo Management",bd=3,relief="solid")
RepoFrame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
RepoFrame.columnconfigure(0, weight=0)
RepoFrame.columnconfigure(1, weight=1)
RepoFrame.columnconfigure(2, weight=0)
RepoFrame.rowconfigure(0, weight=1)
BranchFrame = nulltk.LabelFrame(NullGitManagePage,text="Branch Management",bd=3,relief="solid")
BranchFrame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
BranchFrame.columnconfigure(0, weight=0)
BranchFrame.columnconfigure(1, weight=1)
BranchFrame.columnconfigure(2, weight=0)
BranchFrame.rowconfigure(0, weight=1)
IgnoreFrame = nulltk.LabelFrame(NullGitManagePage,text="GitIgnore Management",bd=3,relief="solid")
IgnoreFrame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
IgnoreFrame.columnconfigure(0, weight=1)
IgnoreFrame.rowconfigure(0, weight=0)
IgnoreFrame.rowconfigure(1, weight=1)
CommitFrame = nulltk.LabelFrame(NullGitManagePage,text="Commit Management",bd=3,relief="solid")
CommitFrame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
CommitFrame.columnconfigure(0, weight=1)
CommitFrame.columnconfigure(1, weight=1)
CommitFrame.rowconfigure(0, weight=0)
CommitFrame.rowconfigure(1, weight=0)
CommitFrame.rowconfigure(2, weight=0)
CommitFrame.rowconfigure(3, weight=1)
NuclearFrame = nulltk.LabelFrame(NullGitManagePage,text="Nuclear Commands",bd=3,relief="solid")
NuclearFrame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
NuclearFrame.columnconfigure(0, weight=1)
NuclearFrame.columnconfigure(1, weight=1)
NuclearFrame.rowconfigure(0, weight=0)
NuclearFrame.rowconfigure(1, weight=0)
NuclearFrame.rowconfigure(2, weight=1)
DeleteNullGitRepoButton = nulltk.Button(RepoFrame, text="Delete Repo From NullGit", command=lambda:DeleteRepoInNull(CurrentManagedRepo, DeleteNullGitRepoButton))
DeleteNullGitRepoButton.grid(row=0, column=0, sticky="ew", padx=5, pady=2, columnspan=3)
nulltk.Button(BranchFrame, text="Create Branch", width= 11, command=lambda:CreateBranchOnGit()).grid(row=0, column=0, sticky="ew", padx=5, pady=2)
nulltk.Entry(BranchFrame, textvariable=ManageBranchName).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
nulltk.Button(BranchFrame, text="Rename Branch", width= 11, command=lambda:RenameBranchOnGit()).grid(row=0, column=2, sticky="ew", padx=5, pady=2)
nulltk.Button(BranchFrame, text="Delete Branch", command=lambda:DeleteBranchOnGit()).grid(row=1, column=0, sticky="ew", padx=5, pady=2, columnspan=3)
CurrentMergeBranch = tk.StringVar()
MergeBranches = nulltk.Label(BranchFrame,text="Merge this branch into current:",font=("Arial", 12),justify="center")
MergeBranches.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
MergeBranchBox = nulltk.Combobox(BranchFrame, values=[], textvariable=CurrentMergeBranch, state="readonly")
MergeBranchBox.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
MergeButton = nulltk.Button(BranchFrame,text="Merge", command=lambda:MergeBranch())
MergeButton.grid(row=2,column=2,sticky="ew",padx=5,pady=2)
CreateGitIgnoreButton = nulltk.Button(IgnoreFrame,text="Create .gitignore", command=lambda:CreateGitIgnoreFile())
CreateGitIgnoreButton.grid(row=0,column=0,sticky="ew",padx=5,pady=2)
EditGitIgnoreButton = nulltk.Button(IgnoreFrame,text="Edit .gitignore", command=lambda:EditGitIgnoreFile())
EditGitIgnoreButton.grid(row=0,column=0,sticky="ew",padx=5,pady=2)
ToolTip(EditGitIgnoreButton, "Adding a file to the .gitignore also removes it from the repo, to remove something from the .gitignore, add a file/folder already in the .gitignore")
GitList = ScrollableFrame(IgnoreFrame)
GitList.grid(row=1, column=0, sticky="nsew", padx=5, columnspan=3)
GitListContainer = GitList.Inner
GitListContainer.configure(bg="white")
CreateGitIgnoreButton.grid_remove()
EditGitIgnoreButton.grid_remove()
GitList.grid_remove()
GitIgnoredLabel = nulltk.Label(GitListContainer,textvariable=GitIgnoredVar, justify="left",anchor="nw",bg="white",fg="black")
GitIgnoredLabel.pack(fill="both",expand=True,padx=5,pady=5)
nulltk.Button(CommitFrame, text="Add File To Commit", command=lambda:AddFileToCommit()).grid(row=0, column=0, sticky="ew", padx=5, pady=2)
nulltk.Button(CommitFrame, text="Remove File From Commit", command=lambda:RemoveFileFromCommit()).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
nulltk.Button(CommitFrame, text="Clear Current Commit", command=lambda:ClearCurrentCommit()).grid(row=1, column=0, sticky="ew", padx=5, pady=2, columnspan=2)
OnlyCommitMessage = tk.StringVar()
nulltk.Entry(CommitFrame,width=30,textvariable=OnlyCommitMessage).grid(row=2, column=0, sticky="ew", padx=5)
nulltk.Button(CommitFrame, text="Push Commit List", command=lambda:PushOnlyCommited()).grid(row=2, column=1, sticky="ew", padx=5, pady=2, columnspan=2)
CommitList = ScrollableFrame(CommitFrame)
CommitList.grid(row=3, column=0, sticky="nsew", padx=5, columnspan=2)
CommitListContainer = CommitList.Inner
CommitListContainer.configure(bg="white")
CommittedLabel = nulltk.Label(CommitListContainer,textvariable=CommittedVar,justify="left",anchor="nw",bg="white",fg="black")
CommittedLabel.pack(fill="both",expand=True,padx=5,pady=5) 
Stash = nulltk.Button(NuclearFrame,text="Stash & Pull", command=lambda:StashAndPull())
Stash.grid(row=0,column=0,sticky="ew",padx=5,pady=2,)
ForcePush = nulltk.Button(NuclearFrame,text="Force Push", command=lambda:ForcePushCommit())
ForcePush.grid(row=0,column=1,sticky="ew",padx=5,pady=2, columnspan=2)
    #endregion

def NullGitLoop():
    while True:
        if NullGitActive.get() == False:
            time.sleep(1)
            continue

        for _ in range(1800):
            if NullGitActive.get() == False:
                break
            time.sleep(1)

        try:
            if NullGitActive.get() == True:
                Root.after(1, BuildRepoList)
        except Exception as e:
            Log(f"NullGit: The loop errored somehow - {e}")

def StartUpNullGit():
    global Repos, LoadCompleted, SystemLoading,ActualProgramLoadedCount
    
    if NullGitActive.get() == True:
        SystemLoading = True
        repos = None
        if not os.path.isfile(ConfigPath):
            Butts.set("Save File not found???")
            Root.update_idletasks()
            return False

        try:
            with open(ConfigPath, "r") as f:
                data = json.load(f)
                repos = data.get("NullGit", {})
        except Exception as e:
            Butts.set(f"ERROR LOADING NULL GIT SAVE\n\n{e}")
            Root.update_idletasks()
            return False
        
        Repos = repos.get("Repos", {})
        BuildRepoList()


        Notebook.add(NullGit, text="NullGit")
        ActualProgramLoadedCount+=1
    
    else:
        Notebook.forget(NullGit)
    LoadCompleted += 1
    SystemLoading = False
    return

#endregion

#region NullFocus
WriteToDiskSeconds = 60
MinimumWindowTime = 1
NewDayThreshold = 3
CompletedCycles = []
CurrentFocus = None
OldFocus = None
FocusStartTime = time.time()
PreviousFocusStartTime = 0
PreviousInputTime = 0
CurrentInputTIme = time.time()
LastWriteToDisk = time.time()
CurrentCycle = {
    "StartTime": datetime.now().strftime("%m/%d/%y - %I:%M%p"),
    "TimeSpent": {}}
AppClassification = {}
MouseListener = None
KeyboardListener = None
TrackerSaveTimer = None
YearButtons = []
MonthButtons = []
CycleButtons = []
ClassificationRows = []
IgnoreAppDeleteConfirmation = {}
TrackerReminders = {}
OnCurrentCycle = False
CurrentViewedYear = None
CurrentViewedMonth = None
CurrentViewedCycle = None
TrackerPopup = None
WindowDeleteConfirmation = {}
ResetClock = True
LastClockUpdate = None
ClockRotation = 0
ClockUpdatedViaCycle = True
WaitForNullFocusLoad = False
ClipBoardHistory = []
ClipBoardRows = []
LastClipBoard = None
DontCopyToClipBoardData = False
NullFocusOperators= []
NullFocusOperatorRows = []
LastProcessedFocus = None
CurrentSpotifySong = ""
SpotifyID = None
DeletionCheckBoxes = []
ClipLock = threading.Lock()

def RegisterAnyActivity():
    global CurrentInputTIme, PreviousInputTime
    PreviousInputTime = CurrentInputTIme
    CurrentInputTIme = time.time()

    if CurrentFocus != None:
        ActivityTimeout = 15
        ActiveDuration = min(CurrentInputTIme - PreviousInputTime, ActivityTimeout)
        DisplayName = (CurrentFocus.replace("-", " ").title())
        Classification = None

        for Category, Windows in AppClassification.items():
            if CurrentFocus in Windows:
                Classification = Category
                break

        CurrentCycle["TimeSpent"].setdefault(CurrentFocus,
            {
            "Name": DisplayName,
                    "FocusedTime": 0,
                "ActiveTime": 0,
                "Classification": Classification
                }
            )
        CurrentCycle["TimeSpent"][CurrentFocus]["Classification"] = Classification
        CurrentCycle["TimeSpent"][CurrentFocus]["ActiveTime"] += ActiveDuration

    return

def OnMouseClick(x,y,Button,Pressed):
    if Pressed:
        RegisterAnyActivity()

def OnMouseScroll(x, y, dx, dy):
    RegisterAnyActivity()

def OnKeyPress(Key):
    RegisterAnyActivity()

def ChangedWindowFocus(NewFocus):
    global CurrentFocus, FocusStartTime, CurrentCycle, PreviousFocusStartTime, OldFocus, CurrentViewedCycle, CurrentViewedMonth, CurrentViewedYear, OnCurrentCycle, ResetClock

    OldFocus = CurrentFocus
    CurrentFocus = NewFocus
    PreviousFocusStartTime = FocusStartTime
    FocusStartTime = time.time()
    FocusedDuration = (FocusStartTime - PreviousFocusStartTime)
    
    if OldFocus is not None and OldFocus != CurrentFocus:
        DisplayName = (OldFocus.replace("-", " ").title())
        Classification = None
        for Category, Windows in AppClassification.items():
            if OldFocus in Windows:
                Classification = Category
                break

        CurrentCycle["TimeSpent"].setdefault(OldFocus,
                    {
                        "Name": DisplayName,
                        "FocusedTime": 0,
                        "ActiveTime": 0,
                        "Classification": Classification
                    }
                )
        CurrentCycle["TimeSpent"][OldFocus]["Classification"] = Classification

        if FocusedDuration > (NewDayThreshold * 3600):
            CurrentCycle = {
                "StartTime": datetime.now().strftime("%m/%d/%y - %I:%M%p"),
                "LastUpdated": time.time(),
                "TimeSpent": {
                            "Sleep": {
                                "Name": "Sleep",
                                "FocusedTime": int(
                                    FocusedDuration
                                ),
                                "ActiveTime": 0,
                                "Classification": "Sleep"
                            }
                        }
                    }
            SaveTrackerLog()
            CurrentViewedCycle = CurrentCycle["StartTime"]
            ClickYearButton(CurrentViewedYear)
            ClickMonthButton(CurrentViewedYear, CurrentViewedMonth)
            ClickCycleButton(CurrentViewedYear,CurrentViewedMonth,CurrentCycle["StartTime"])
            OnCurrentCycle = True
            ResetClock = True
        elif FocusedDuration >= MinimumWindowTime:
            CurrentCycle['TimeSpent'][OldFocus]['FocusedTime'] += int(FocusedDuration)

    if OnCurrentCycle and HiddenToTray == False:
        ClickCycleButton(CurrentViewedYear, CurrentViewedMonth, CurrentViewedCycle)
            
    NullFocusRunOperators()

    return

def WatchFocus():
    if NullFocusActive.get() == True:
        proc = subprocess.Popen(
            ["xprop", "-root", "-spy", "_NET_ACTIVE_WINDOW"],
            stdout=subprocess.PIPE,
            text=True
        )

        for line in proc.stdout:
            try:
                if NullFocusActive.get() == True:
                    WindowID= line.strip().split()[-1]
                    yield WindowID
                else:
                    proc.terminate()
                    break
            except Exception:
                continue
    time.sleep(1)
    
def GetWindowClass(WindowID):
    try:
        WindowClass = subprocess.check_output(
            ["xprop", "-id", str(WindowID), "WM_CLASS"],
            stderr=subprocess.DEVNULL
        ).decode()

        return WindowClass.strip().split('"')[-2].lower()

    except Exception:
        return None

def AddNewTracker(Name=None, Loading=False):
    global AppClassification
    Frame = nulltk.Frame(ClassiciationListContainer, pady=5)
    Frame.pack(fill="x", expand=True)
    TrackerFrame = nulltk.Frame(Frame, pady=2)

    TrackerFrame.pack(fill="x", expand=True)
    TrackerFrame.columnconfigure(0, weight=0)
    TrackerFrame.columnconfigure(1, weight=1)
    TrackerFrame.columnconfigure(2, weight=0)
    TrackerFrame.rowconfigure(0, weight=0)
    TrackerFrame.rowconfigure(1, weight=1)


    if Name == None:
        Count = 1
        while f"NewClassification{Count}" in AppClassification:
            Count += 1

        Name = f"NewClassification{Count}"
        AppClassification[Name] = []

    elif Name not in AppClassification:
        AppClassification[Name] = []

    OriginalName = Name
    ClassificationNameVar = tk.StringVar(value=Name)
    TrackerDeleteConfirmation = tk.BooleanVar(value=False)

    def RenameClassification(_=None):
        nonlocal OriginalName
        NewName = ClassificationNameVar.get().strip()

        if not NewName:
            ClassificationNameVar.set(OriginalName)
            return
        
        if NewName == OriginalName:
            return
        
        if NewName in AppClassification:
            ClassificationNameVar.set(OriginalName)
            return

        AppClassification[NewName] = AppClassification.pop(OriginalName)
        OriginalName = NewName
        RefreshCategoryWindows()
        UpdateTrackerQuality()
        return

    def RemoveTracker(Button, DeleteThis, Timeout=4):
        EndTime = time.time() + Timeout
        def Tick():
            Remaining = int(EndTime - time.time())
            if Remaining <= 0:
                if not Button.winfo_exists():
                    return
                Button.config(text="Delete Category")
                TrackerDeleteConfirmation.set(False)
                return

            if not Button.winfo_exists():
                return

            Button.config(text=f"R U Sure? {Remaining}")
            Root.after(1000, Tick)
            return

        if TrackerDeleteConfirmation.get() == False:
            TrackerDeleteConfirmation.set(True)
            Remaining = int(EndTime - time.time())
            Button.config(text=f"R U Sure? {Remaining}")
            Tick()
            return

        if OriginalName in AppClassification:
            del AppClassification[OriginalName]

        DeleteThis.destroy()
        RefreshCategoryWindows()
        UpdateTrackerQuality()
        return

    DeleteButton = nulltk.Button(TrackerFrame,text = "Delete Category",command=lambda: RemoveTracker(DeleteButton,TrackerFrame), width = 15)
    DeleteButton.grid(row=0,column=0,padx=3,pady=3,sticky="ew")
    ClassificationEntry = nulltk.Entry(TrackerFrame,textvariable=ClassificationNameVar)
    ClassificationEntry.grid(row=0,column=1,padx=3,pady=3,sticky="ew")

    ClassificationEntry.bind("<FocusOut>",RenameClassification)
    ClassificationEntry.bind("<Return>",RenameClassification)

    def WaitForTrackerPopUp():
            if TrackerPopup is None:
                SaveConfig("NullFocus")
                RefreshCategoryWindows()
                return
            Root.after(100, WaitForTrackerPopUp)

    def AddWindowTrackerSpecialty(AppClassification,OriginalName):

        SearchForWindow(AppClassification,None,OriginalName,None,"NullFocus")
        
        WaitForTrackerPopUp()
        return
    
    def DeleteCategory(OriginalName):
        DeleteCategoryWindow(OriginalName)
        WaitForTrackerPopUp()
        return
    

    AddWindowButton = nulltk.Button(TrackerFrame,text="Add Window",command=lambda: AddWindowTrackerSpecialty(AppClassification,OriginalName), width = 11)
    AddWindowButton.grid(row=0,column=2,padx=3,pady=3,sticky="ew")

    RemoveWindowButton = nulltk.Button(TrackerFrame,text="Del Window",command=lambda:DeleteCategory(OriginalName), width = 11)
    RemoveWindowButton.grid(row=0,column=3,padx=3,pady=3,sticky="ew")

    CategoryWindowsVar = tk.StringVar()

    def RefreshCategoryWindows():
        CategoryWindowsVar.set(
            ", ".join(
            [
            FormatWindowName(Window)
            for Window in AppClassification.get(
                OriginalName,
                []
            )
            ]   
            )
            )
        return

    AllCategoryWindows = nulltk.Label(TrackerFrame,textvariable=CategoryWindowsVar ,anchor="nw",justify="left")
    AllCategoryWindows.grid(row=1, column=0, sticky="nsew", rowspan=3, columnspan=3)

    if Loading:
        RefreshCategoryWindows()

    return

def FormatWindowName(WindowName):
            Parts = WindowName.split(".")
            if len(Parts) > 1:
                WindowName = Parts[-1]
            WindowName = WindowName.replace("-", " ")
            WindowName = WindowName.title()
            return WindowName

def DeleteCategoryWindow(Category):
    global TrackerPopup

    Popup = nulltk.Toplevel(Root)
    TrackerPopup = Popup
    Popup.title(f"Remove {Category} Window")
    Popup.geometry("300x400")
    Popup.grab_set()

    ScrollFrame = ScrollableFrame(Popup)
    ScrollFrame.pack(fill="both", expand=True)

    for WindowName in AppClassification.get(Category,[]):
        Button = nulltk.Button(ScrollFrame.Inner,text=f"Remove {FormatWindowName(WindowName)}")
        Button.config(command=lambda W=WindowName, B=Button: RemoveCategoryWindow(Category,W,B,Popup))
        Button.pack(fill="x")
    return

def RemoveCategoryWindow(Category, WindowName, Button, Popup, Timeout=4):

    global WindowDeleteConfirmation, TrackerPopup

    EndTime = time.time() + Timeout

    def Tick():

        Remaining = int(EndTime - time.time())

        if Remaining <= 0:

            if not Button.winfo_exists():
                return

            Button.config(text=f"Remove {WindowName}")

            WindowDeleteConfirmation[WindowName] = False

            return


        if not Button.winfo_exists():
            return

        Button.config(text=f"R U Sure? {Remaining}")

        Root.after(1000, Tick)

        return

    if WindowDeleteConfirmation.get(WindowName,False) == False:

        WindowDeleteConfirmation[WindowName] = True

        Tick()

        return

    if WindowName in AppClassification.get(Category,[]):
        AppClassification[Category].remove(WindowName)

    UpdateTrackerQuality()

    SaveConfig("NullFocus")

    Button.destroy()

    Popup.destroy()
    TrackerPopup = None

    return

def AddIgnoredTracker():
    global TrackerPopup
    SearchForWindow(
        AppClassification,
        IgnoredAppListVar,
        "Ignored",
        "IgnoredDisplay",
        "NullFocus"
    )

    def WaitForTrackerPopUp():
            if TrackerPopup is None:
                SaveConfig("NullFocus")
                UpdateTrackerQuality()
                Root.update_idletasks()
                return
            Root.after(100, WaitForTrackerPopUp)

    WaitForTrackerPopUp()
    

    return

def DeleteIgnoredTracker():
    Popup = nulltk.Toplevel(Root)
    Popup.title("Remove Ignored Tracker")
    Popup.geometry("300x400")
    Popup.grab_set()

    ScrollFrame = ScrollableFrame(Popup)
    ScrollFrame.pack(fill="both", expand=True)

    for App in AppClassification.get("Ignored", []):
        Button = nulltk.Button(ScrollFrame.Inner,text=f"Remove {App}")
        Button.config(command=lambda A=App, B=Button:RemoveIgnoredTracker(A, B))
        Button.pack(fill="x")

    return

def RemoveIgnoredTracker(App, Button, Timeout=4):
    global IgnoreAppDeleteConfirmation
    EndTime = time.time() + Timeout
    def Tick():
        global IgnoreAppDeleteConfirmation
        Remaining = int(EndTime - time.time())
        if Remaining <= 0:
            if not Button.winfo_exists():
                return
            Button.config(text=f"Remove {App}")
            IgnoreAppDeleteConfirmation[App] = False
            return
        if not Button.winfo_exists():
            return

        Button.config(text=f"R U Sure? {Remaining}")
        Root.after(1000, Tick)

    if IgnoreAppDeleteConfirmation.get(App, False) == False:
        IgnoreAppDeleteConfirmation[App] = True
        Tick()
        return

    if App in AppClassification.get("Ignored",[]):
        AppClassification["Ignored"].remove(App)
    UpdateTrackerQuality()
    SaveConfig("NullFocus")
    Button.destroy()
    return

def UpdateTrackerQuality():
    global WriteToDiskSeconds, MinimumWindowTime, NewDayThreshold

    WriteToDiskSeconds = TrackerWriteInterval.get()
    MinimumWindowTime = TrackerMinimumWindowTime.get()
    NewDayThreshold = TrackerNewDay.get()
    ignoredlist = AppClassification.get("Ignored", [])
    WriteIntervalText.config(text=f"Save To Disk Every: {WriteToDiskSeconds} Minutes")
    RequiredFocusText.config(text=f"Window Focus Time Req: {MinimumWindowTime} Seconds")
    NewDayText.config(text=f"New Cycle After {NewDayThreshold} Hours of inactivity")
    IgnoredAppListVar.set(value="\n".join(ignoredlist))
    QueueTrackerSave()

    return

def QueueTrackerSave():
    global TrackerSaveTimer
    if TrackerSaveTimer:
        Root.after_cancel(TrackerSaveTimer)
    TrackerSaveTimer = Root.after(
        1000,
        lambda: SaveConfig("NullFocus")
    )

def ClickYearButton(Year):

    global MonthButtons, CycleButtons, CurrentViewedYear
    CurrentViewedYear = Year


    YearPath = os.path.join(
        TrackerPath,
        f"{Year}.json"
    )

    with open(YearPath, "r") as f:
        Data = json.load(f)

    for Button in MonthButtons:
        Button.destroy()

    MonthButtons.clear()

    for Button in CycleButtons:
        Button.destroy()

    CycleButtons.clear()

    CurrentLogView.set("")
    Root.update_idletasks()
    for Month in sorted(Data.keys()):

        Button = nulltk.Button(
            MonthChoicesButtons,
            text=Month,
            command=lambda M=Month, Y=Year: ClickMonthButton(Y, M),
            width=14
        )

        Button.pack(fill="x")

        MonthButtons.append(Button)

    return

def ClickMonthButton(Year, Month):

    global CycleButtons, CurrentViewedMonth
    CurrentViewedMonth = Month

    YearPath = os.path.join(
        TrackerPath,
        f"{Year}.json"
    )

    with open(YearPath, "r") as f:
        Data = json.load(f)

    MonthData = Data.get(Month, {})

    for Button in CycleButtons:
        Button.destroy()

    CycleButtons.clear()

    CurrentLogView.set("")
    Root.update_idletasks()
    for Cycle in sorted(MonthData.keys(),key=lambda x: datetime.strptime(x,"%m/%d/%y - %I:%M%p"),reverse=True):
        CycleDate = datetime.strptime(Cycle,"%m/%d/%y - %I:%M%p")
        Day = CycleDate.day
        Suffix = GetDaySuffix(Day)
        DisplayText = (f"{Day}{Suffix} - " f"{CycleDate.strftime('%I:%M%p')}")

        Button = nulltk.Button(
            CycleChoicesButtons,
            text=DisplayText,
            command=lambda C=Cycle, Y=Year, M=Month: ClickCycleButton(Y, M, C),
            width=15
        )

        Button.pack(fill="x")

        CycleButtons.append(Button)

    return

def ClickCycleButton(Year, Month, Cycle):
    global OnCurrentCycle, CurrentViewedCycle
    CurrentViewedCycle = Cycle

    YearPath = os.path.join(TrackerPath,f"{Year}.json")

    with open(YearPath, "r") as f:
        Data = json.load(f)
    if Cycle == CurrentCycle["StartTime"]:
        CycleData = CurrentCycle
        OnCurrentCycle = True
    else:
        CycleData = Data.get(Month, {}).get(Cycle, {})
        OnCurrentCycle = False

    Output = ""
    CycleDate = datetime.strptime(Cycle,"%m/%d/%y - %I:%M%p")
    StartDisplay = CycleDate.strftime("%I:%M:%S%p")
    if OnCurrentCycle:
        TotalSeconds = int(time.time() - CycleDate.timestamp())
    else:
        TotalSeconds = sum(
            AppData.get("FocusedTime",0)
            for AppData in CycleData.get("TimeSpent",{}).values()
            if AppData.get("Classification") != "Sleep"
        )
    TotalHours = int(TotalSeconds // 3600)
    TotalMinutes = int((TotalSeconds % 3600) // 60)
    TotalSecs = int(TotalSeconds % 60)

    
    Day = CycleDate.day
    Suffix = GetDaySuffix(Day)
    Output += f"{Year} {Month} The {Day}{Suffix}"

    if OnCurrentCycle:
        Output += " [LIVE]"
    Output += "\n"
    Output += (
    f"[STARTED: {StartDisplay}]\n"
    f"[TOTAL: "
    f"{TotalHours:02}:"
    f"{TotalMinutes:02}:"
    f"{TotalSecs:02}]\n\n"
    )
    TimeSpent = CycleData.get("TimeSpent",{})
    Grouped = {}

    for AppID, AppData in TimeSpent.items():
        Classification = AppData.get("Classification",None)
        if not Classification:
            Classification = "No Category"
        Grouped.setdefault(Classification,[])
        Grouped[Classification].append((AppID, AppData))

    CategoryOrder = {
    "Sleep": 0,
    "No Category": 999
}

    for Category, Apps in sorted(Grouped.items(),key=lambda x: CategoryOrder.get(x[0],100)):
        if Category == "Sleep":
                for AppID, AppData in Apps:
                    FocusedSeconds = AppData.get("FocusedTime",0)
                    ActiveSeconds = AppData.get("ActiveTime",0)
                    FocusedHours = int(FocusedSeconds // 3600)
                    FocusedMinutes = int((FocusedSeconds % 3600) // 60)
                    FocusedSecs = int(FocusedSeconds % 60)
                    SleepTime = CycleDate - timedelta(seconds=FocusedSeconds)

                    Output += (
                        f"Went To Sleep At: "
                        f"{SleepTime.strftime('%I:%M:%S %p')}\n"
                        f"Slept Yesterday, For : "
                        f"{FocusedHours:02}:"
                        f"{FocusedMinutes:02}:"
                        f"{FocusedSecs:02}\n\n"
                    )
                continue
        elif Category == "Ignored":
            continue


        Output += (
            f"====================================================== "
            f"{Category} "
            f"====================================================\n"
        )
        CategoryFocused = sum(AppData.get("FocusedTime",0)for _, AppData in Apps)

        CategoryActive = sum(AppData.get("ActiveTime",0)for _, AppData in Apps)

        CategoryFocusedHours = int(CategoryFocused // 3600)
        CategoryFocusedMinutes = int((CategoryFocused % 3600) // 60)
        CategoryFocusedSecs = int(CategoryFocused % 60)

        CategoryActiveHours = int(CategoryActive // 3600)
        CategoryActiveMinutes = int((CategoryActive % 3600) // 60)
        CategoryActiveSecs = int(CategoryActive % 60)

        if Category not in ["Injection", "Sleep", "Ignored"]:
            for AppID, AppData in sorted(Apps,key=lambda x: x[1].get("FocusedTime",0),reverse=True):
                FocusedSeconds = AppData.get("FocusedTime",0)
                ActiveSeconds = AppData.get("ActiveTime",0)
                FocusedHours = int(FocusedSeconds // 3600)
                FocusedMinutes = int((FocusedSeconds % 3600) // 60)
                FocusedSecs = int(FocusedSeconds % 60)
                ActiveHours = int(ActiveSeconds // 3600)
                ActiveMinutes = int((ActiveSeconds % 3600) // 60)
                ActiveSecs = int(ActiveSeconds % 60)
                DisplayName = AppData.get("Name",AppID)
                Output += (
                    f"{DisplayName}: "
                    f"{FocusedHours:02}:"
                    f"{FocusedMinutes:02}:"
                    f"{FocusedSecs:02} "
                    f"("
                    f"{ActiveHours:02}:"
                    f"{ActiveMinutes:02}:"
                    f"{ActiveSecs:02}"
                        f")\n"
                )
            Output += (
            f"\n"
            f"Total: "
            f"{CategoryFocusedHours:02}:"
            f"{CategoryFocusedMinutes:02}:"
            f"{CategoryFocusedSecs:02} "
            f"("
            f"{CategoryActiveHours:02}:"
            f"{CategoryActiveMinutes:02}:"
            f"{CategoryActiveSecs:02}"
            f")\n\n"
            )
        else:
            if Category == "Sleep":
                continue
            else:
                for AppID, AppData in Apps:
                    DisplayName = AppData.get("Name",AppID)
                    Output += f"{DisplayName}\n"
            
            
            Output += "\n"

    CurrentLogView.set(Output)
    Root.update_idletasks()
    return

def SaveTrackerLog():
    CycleDate = datetime.strptime(CurrentCycle["StartTime"],"%m/%d/%y - %I:%M%p")
    Year = CycleDate.strftime("%Y")
    Month = CycleDate.strftime("%b")
    YearPath = os.path.join(TrackerPath,f"{Year}.json"
                            )
    if os.path.isfile(YearPath):
        with open(YearPath, "r") as f:
            try:
                Data = json.load(f)
            except:
                Data = {}
    else:
        Data = {}
    if Month not in Data:
        Data[Month] = {}

    if not CurrentCycle["TimeSpent"]:
        if not CurrentCycle["TimeSpent"]:

            CurrentCycle["TimeSpent"] = {
            "nullsuite": {
                "Name": "NullSuite",
                "FocusedTime": 1,
                "ActiveTime": 1,
                "Classification": None
            }
        }
    
    CycleName = CurrentCycle["StartTime"]
    Data[Month][CycleName] = CurrentCycle
    CurrentCycle["LastUpdated"] = time.time()
    with open(YearPath, "w") as f:
        json.dump(Data,f,indent=4)
    return

def GetDaySuffix(Day):
    if 11 <= Day <= 13:
        return "th"

    return {
        1: "st",
        2: "nd",
        3: "rd"
    }.get(Day % 10, "th")

def InjectTracker():
    Text = InjectionEntry.get().strip()
    if not Text:
        return
    InjectionID = f"injection_{time.time()}"
    Timestamp = datetime.now().strftime("%I:%M%p")
    CurrentCycle["TimeSpent"][InjectionID] = {
        "Name": f"[{Timestamp}] {Text}",
        "FocusedTime": 0,
        "ActiveTime": 0,
        "Classification": "Injection"
    }
    InjectionEntry.delete(0,"end")

    if OnCurrentCycle:
        ClickCycleButton(
            CurrentViewedYear,
            CurrentViewedMonth,
            CurrentViewedCycle
        )
    SaveTrackerLog()
    return

def GetClipboard():
    try:
        Targets = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
            capture_output=True,
            text=True
        )

        if Targets.returncode != 0:
            return None

        Targets = Targets.stdout.splitlines()

        # Images
        if any(Target.startswith("image/") for Target in Targets):

            MimeType = next(
                (Target for Target in Targets if Target.startswith("image/")),
                None
            )

            Image = subprocess.run(
                [
                    "xclip",
                    "-selection",
                    "clipboard",
                    "-t",
                    MimeType,
                    "-o"
                ],
                capture_output=True
            )

            return {
                "Type": "Image",
                "Hash": hashlib.sha256(Image.stdout).hexdigest(),
                "Targets": Targets,
                "MimeType": MimeType
            }

        # Text
        elif (
            "text/plain" in Targets or
            "UTF8_STRING" in Targets or
            "TEXT" in Targets
        ):

            Text = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True,
                text=True
            )

            return {
                "Type": "Text",
                "Text": Text.stdout,
                "Hash": hashlib.sha256(
                    Text.stdout.encode("utf-8")
                ).hexdigest(),
                "Targets": Targets
            }

        return {
            "Type": "Unsupported",
            "Hash": hashlib.sha256(
                "\n".join(Targets).encode("utf-8")
            ).hexdigest(),
            "Targets": Targets
        }

    except Exception as e:
        Log(f"NullFocus: Clipboard had an error?  {e}", "Error")
        return None

def AddClipBoardEntry(ClipBoardContents):
    global ClipBoardHistory

    if CurrentFocus is None:
        return

    DisplayName = CurrentFocus.replace("-", " ").title()

    MonthFolder = os.path.join(
        ClipboardPath,
        datetime.now().strftime("%Y - %b")
    )

    os.makedirs(MonthFolder, exist_ok=True)

    if ClipBoardContents["Type"] == "Text":

        Row = {
            "Text": ClipBoardContents["Text"],
            "TimeOfCopy": datetime.now().strftime("%m/%d/%y - %I:%M%p"),
            "Type": "Text",
            "Collapsed": False,
            "Path": None,
            "Focus": DisplayName,
            "Hash": ClipBoardContents["Hash"],
            "": False
        }

    elif ClipBoardContents["Type"] == "Image":

        ImagePath = os.path.join(
            MonthFolder,
            datetime.now().strftime("%Y-%m-%d---%H-%M-%S.png")
        )

        try:
            with open(ImagePath, "wb") as f:
                subprocess.run(
                    [
                        "xclip",
                        "-selection",
                        "clipboard",
                        "-t",
                        "image/png",
                        "-o"
                    ],
                    stdout=f,
                    check=True
                )
        except Exception as e:
            Log(f"NullFocus: Clipboard couldn't save image - {e}")
            return

        Row = {
            "Text": "",
            "TimeOfCopy": datetime.now().strftime("%m/%d/%y - %I:%M%p"),
            "Type": "Image",
            "Collapsed": False,
            "Path": ImagePath,
            "Focus": DisplayName,
            "Hash": ClipBoardContents["Hash"],
            "DeleteConfirmation": False
        }

    else:
        return

    ClipBoardHistory.insert(0, Row)

    BuildClipBoardRow(Row)



    SaveClipBoard()

def BuildClipBoardRow(Row):
    global ClipBoardRows, ClipBoardHistory, DeletionCheckBoxes

    CBRow = nulltk.Frame(
        ClipBoardList.Inner,
        bd=2,
        relief="solid"
    )

    if ClipBoardRows:
        CBRow.pack(fill="x",expand=True,anchor="n",pady=5,before=ClipBoardRows[0])
        ClipBoardRows.insert(0, CBRow)
    else:
        CBRow.pack(fill="x",expand=True,anchor="n",pady=5)
        ClipBoardRows.append(CBRow)

    CBRow.columnconfigure(1, weight=1)
    CBRow.columnconfigure(2, weight=1)
    CBRow.columnconfigure(3, weight=1)

    def CollapseRow():

        if Row["Collapsed"]:

            if Row["Type"] == "Text":
                TextHolder.grid_remove()

            elif Row["Type"] == "Image":
                ImageHolder.grid_remove()

            RowCollapse.config(text="▶")
            Row["Collapsed"] = False

        else:

            if Row["Type"] == "Text":
                TextHolder.grid(
                    row=1,
                    column=0,
                    sticky="ewns",
                    columnspan=99
                )

            elif Row["Type"] == "Image":
                ImageHolder.grid(
                    row=1,
                    column=0,
                    sticky="ewns",
                    columnspan=99
                )

            RowCollapse.config(text="▼")
            Row["Collapsed"] = True

    RowCollapse = nulltk.Button(CBRow,text="▶",width=2,command=CollapseRow)
    RowCollapse.grid(row=0,column=0,sticky="ew",padx=2)
    SourceLabel = nulltk.Label(CBRow,text=f"{Row['Focus']} at {Row['TimeOfCopy']} — {Row['Type'].upper()}",width = 50)
    SourceLabel.grid(row=0,column=2,sticky="ew")
    DeleteVar = tk.BooleanVar(value=False)
    DeletionBox = nulltk.Checkbutton(CBRow,variable=DeleteVar, text="Delete")
    DeletionBox.grid(row=0,column=1,sticky="w")

    CBRow.DeleteVar = DeleteVar
    CBRow.RowData = Row

    def ReCopy():
        global DontCopyToClipBoardData
        global LastClipBoard

        DontCopyToClipBoardData = True
        LastClipBoard = Row["Hash"]

        if Row["Type"] == "Text":

            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=Row["Text"].encode("utf-8"),
                check=True
            )

        elif Row["Type"] == "Image":

            subprocess.run(
                [
                    "xclip",
                    "-selection",
                    "clipboard",
                    "-t",
                    "image/png",
                    "-i",
                    Row["Path"]
                ],
                check=True
            )

    CopyButton = nulltk.Button(
        CBRow,
        text="Re-Copy",
        command=ReCopy,
        width = 50
    )

    CopyButton.grid(
        row=0,
        column=3,
        sticky="ew"
    )

    if Row["Type"] == "Text":

        TextHolder = nulltk.Frame(CBRow)

        TextHolder.grid(
            row=1,
            column=0,
            sticky="ewns",
            columnspan=99
        )

        Lines = Row["Text"].count("\n") + 1

        BigAssTextField = nulltk.Text(
            TextHolder,
            wrap="word",
            height=max(3, Lines)
        )

        BigAssTextField.insert(
            "1.0",
            Row["Text"]
        )

        BigAssTextField.config(
            state="disabled"
        )

        BigAssTextField.pack(
            fill="both",
            expand=True
        )

        TextHolder.grid_remove()

    elif Row["Type"] == "Image":

        ImageHolder = nulltk.Frame(CBRow)

        ImageHolder.grid(
            row=1,
            column=0,
            sticky="ewns",
            columnspan=99
        )

        try:

            Thumb = Image.open(
                Row["Path"]
            )

            Thumb.thumbnail(
                (800, 800)
            )

            Thumbnail = ImageTk.PhotoImage(
                Thumb
            )

            ImageLabel = nulltk.Label(
                ImageHolder,
                image=Thumbnail
            )

            ImageLabel.image = Thumbnail

            ImageLabel.pack(
                pady=5
            )

        except Exception as e:

            nulltk.Label(
                ImageHolder,
                text=f"Failed Loading Image\n{e}"
            ).pack()

        def OpenImage():

            subprocess.Popen(
                [
                    "xdg-open",
                    Row["Path"]
                ]
            )

        OpenButton = nulltk.Button(
            ImageHolder,
            text="Open Full Image",
            command=OpenImage
        )

        OpenButton.pack(
            pady=5
        )

        ImageHolder.grid_remove()

    ClipBoardList.BindMouseWheel(
        CBRow
    )

def SaveClipBoard():
    MonthFolder = os.path.join(
        ClipboardPath,
        datetime.now().strftime("%Y - %b")
    )

    os.makedirs(
        MonthFolder,
        exist_ok=True
    )

    ClipSave = os.path.join(
        MonthFolder,
        "000-ClipBoard.json"
    )

    with ClipLock:
        try:
            with open(ClipSave, "w") as f:
                json.dump(
                    ClipBoardHistory,
                    f,
                    indent=2
                )
        except Exception as e:
            Log(f"NullFocus: Clipboard couldn't save - {e}")

def DeleteClipboardItems():
    global ClipBoardRows, ClipBoardHistory
    for CBRow in ClipBoardRows[:]:
        if CBRow.DeleteVar.get():
            Row = CBRow.RowData

            if Row["Path"]:
                try:
                    if os.path.isfile(Row["Path"]):
                        os.remove(Row["Path"])
                except Exception as e:
                    Log(f"NullFocus: Clipboard couldn't delete - {e}")

            ClipBoardRows.remove(CBRow)
            ClipBoardHistory.remove(Row)

            CBRow.destroy()
    return

def SelectAllClipBoard():
    for CBRow in ClipBoardRows[:]:
        CBRow.DeleteVar.set(True)
    return

def SelectNoneClipBoard():
    for CBRow in ClipBoardRows[:]:
        CBRow.DeleteVar.set(False)
    return

def AddOperatorWindow():
    SearchForWindow(None,None,None,None,"Operator")
    return

def CreateOperatorRow(Window):
    global NullFocusOperatorRows

    CurrentPage = tk.BooleanVar(value=True)
    KeyOrAction = tk.BooleanVar(value=False)
    WindowSpecific = tk.BooleanVar(value=False)
    OnlyThisWindow = tk.StringVar(value=None)
    FilePath = tk.StringVar(value="")
    Command = tk.StringVar(value="")
    FileOrCommand = tk.BooleanVar(value=False)

    def GetCurrentPage():
        if CurrentPage.get():
            return "Focused"
        else:
            return "Unfocused"
    
    

    def ChangedPage():
        which = GetCurrentPage()
        if Window[which]["OnlyThisWindow"] != None:
            NormalizedClass = Window[which]["OnlyThisWindow"].split(".")[0].lower()
            OnlyThisWindow.set(NormalizedClass)
        else:
            OnlyThisWindow.set(None)
        KeyOrAction.set(Window[which]["KeyOrAction"])
        WindowSpecific.set(Window[which]["WindowSpecific"])
        
        FilePath.set(Window[which]["FilePath"])     
        Command.set(Window[which]["Command"])
        FileOrCommand.set(Window[which]["FileOrCommand"])

        OperatorUIUpdater()
    
    def RemoveOperator(Window, Button, Timeout=4):
        global NullFocusOperators
        EndTime = time.time() + (Timeout)

        def Tick(Window):
            if Window['DeleteConfirmation'] == False:
                return
            else:
                Remaining = int(EndTime - time.time())
                if Remaining <= 0:
                    if not Button.winfo_exists():
                        return
                    Button.config(text="Delete")
                    Window['DeleteConfirmation'] = False
                    return
                if not Button.winfo_exists():
                    return
                else:
                    Button.config(text=f"R U Sure? {Remaining}")
                    Root.after(1000, Tick, Window)

        if Window['DeleteConfirmation'] == False:
            Window['DeleteConfirmation'] = True
            Tick(Window)
            return

        NullFocusOperators.remove(Window)
        MainFrame.destroy()
        SaveConfig("NullFocus")

    MainFrame = nulltk.LabelFrame(OperatorList.Inner, text=Window['DisplayName'], bd=2)
    MainFrame.pack(fill="x", expand=True)
    MainFrame.columnconfigure(4,weight=1)

    OperatorFocused = nulltk.Checkbutton(MainFrame, text="Focused|UnFocused", variable=CurrentPage, command=lambda:ChangedPage())
    OperatorFocused.grid(row=0, column=0, sticky="ew")

    def OperatorUIUpdater():
        Window[GetCurrentPage()]['KeyOrAction'] = KeyOrAction.get()
        Window[GetCurrentPage()]['WindowSpecific']= WindowSpecific.get()
        Window[GetCurrentPage()]['OnlyThisWindow']= OnlyThisWindow.get()
        Window[GetCurrentPage()]['FileOrCustom']= FileOrCommand.get()
        Window[GetCurrentPage()]['FilePath']= FilePath.get()
        Window[GetCurrentPage()]['Command']= Command.get()

        OperatorKeyOutputButton.config(text="+".join(FormatKeyName(K)for K in Window[GetCurrentPage()]["Keys"]) or "Set Key")

        OperatorKeyOutputButton.grid_remove()
        OperatorWindowSpecificSwitcher.grid_remove()
        OperatorWindowSpecifiWindowShow.grid_remove()
        OperatorWindowSpecificChooseWindowButton.grid_remove()
        OperatorFileSwitcher.grid_remove()
        OperatorChooseFile.grid_remove()
        OperatorActionEntryShow.grid_remove()
        OperatorCustomRunButton.grid_remove()
        OperatorCustomEntryShow.grid_remove()


        if KeyOrAction.get():
            OperatorFileSwitcher.grid(row=0, column=2, sticky="ew", padx=2)
            if FileOrCommand.get():
                OperatorCustomRunButton.grid(row=0, column=3, sticky="ew", padx=2)
                OperatorCustomEntryShow.grid(row=0, column=4, sticky="ew", padx=2)
            else:
                OperatorChooseFile.grid(row=0, column=3, sticky="ew", padx=2)
                OperatorActionEntryShow.grid(row=0, column=4, sticky="ew", padx=2)

        else:
            OperatorKeyOutputButton.grid(row=0, column=2, sticky="ew", padx=2)
            OperatorWindowSpecificSwitcher.grid(row=0, column=3, sticky="ew", padx=2)
            if WindowSpecific.get():
                OperatorWindowSpecifiWindowShow.grid(row=0, column=4, sticky="ew", padx=2)
                OperatorWindowSpecificChooseWindowButton.grid(row=0, column=5, sticky="ew", padx=2)
        
        SaveConfig("NullFocus")
        return

    OperatorKeyActionSwitcher = nulltk.Checkbutton(MainFrame, text="Keys|Action", variable=KeyOrAction, command=lambda:OperatorUIUpdater())
    OperatorKeyActionSwitcher.grid(row=0, column=1, sticky="ew", padx=2)

    #--- keys
    OperatorKeyOutputButton = nulltk.Button(MainFrame,text=("+".join(FormatKeyName(K)for K in Window[GetCurrentPage()]["Keys"]) or "Set Key"),command=lambda: DetectKey(OperatorKeyOutputButton,Window[GetCurrentPage()],'Keys',"NullFocus"),width=25)

    OperatorWindowSpecificSwitcher = nulltk.Checkbutton(MainFrame, text="All|Window", variable=WindowSpecific, command=lambda:OperatorUIUpdater())
    OperatorWindowSpecifiWindowShow = nulltk.Entry(MainFrame, textvariable=OnlyThisWindow, state="readonly")
    OperatorWindowSpecificChooseWindowButton = nulltk.Button(MainFrame, command=lambda: SearchForWindow(Window[GetCurrentPage()], OnlyThisWindow, "OnlyThisWindow", "WindowDisplayName", "NullFocusOperator"), text="Choose Window", width=14)

    #-------- Action
    #--- file
    OperatorFileSwitcher = nulltk.Checkbutton(MainFrame, text="File|Custom", variable=FileOrCommand, command=lambda:OperatorUIUpdater())

    OperatorChooseFile = nulltk.Button(MainFrame, command=lambda: SearchForAnyFile(Window[GetCurrentPage()],FilePath,"FilePath"), text="Browse", width=8)

    OperatorActionEntryShow = nulltk.Entry(MainFrame, textvariable=FilePath, state="readonly")
    #--- command
    OperatorCustomRunButton= nulltk.Button(MainFrame, command=lambda: MidiCustomRun(Window[GetCurrentPage()]['Command']), text="Run", width=8)
    OperatorCustomEntryShow = nulltk.Entry(MainFrame, textvariable=Command,)
    
    #--- remove
    OperatorRemoveButton = nulltk.Button(MainFrame, command=lambda: RemoveOperator(Window,OperatorRemoveButton), text="Remove", width=16)
    OperatorRemoveButton.grid(row=0, column=20)

    OperatorList.BindMouseWheel(MainFrame)

    ChangedPage()
    NullFocusOperatorRows.append(MainFrame)
    return

def ExecuteWindowChange(Window, Type):

    if Window[Type]['KeyOrAction']:
        if Window[Type]['FileOrCommand']:
            MidiCustomRun(Window[Type]['Command'])
        else:
            MidiFileOpen(Window[Type]['FilePath'])
    else:
        if Window[Type]['WindowSpecific']:
            PressKeyCombo(Window[Type]["Keys"],Window[Type]["WindowSpecific"], Window[Type]['OnlyThisWindow'])
        else:
            PressKeyCombo(Window[Type]["Keys"])
        
    return

def SpotifyTracker():
    global CurrentSpotifySong, SpotifyID

    if SpotifyID is None:
        AttemptToGetSpotifyID()

        if SpotifyID is None:
            return



    try:
        WindowTitle = subprocess.check_output(
            ["xdotool", "getwindowname", SpotifyID]
        ).decode().strip()

    except Exception:
        SpotifyID = None
        return
    
    if " - " in WindowTitle:
        Artist, Song = WindowTitle.split(" - ", 1)
        NewSong = f"Song Name:\n{Song}\n\nArtist:\n{Artist}"
    else:
        if "Spotify" in WindowTitle:
            return
        else:
            NewSong = WindowTitle

    if NewSong != CurrentSpotifySong:
        CurrentSpotifySong = NewSong

        with open(SpotifySongPath, "w", encoding="utf-8") as f:
            f.write(CurrentSpotifySong)
    
def AttemptToGetSpotifyID():
    global SpotifyID

    try:
        IDs = subprocess.check_output(
            ["xdotool", "search", "--class", "spotify"]
        ).decode().splitlines()
    except:
        return None

    for WindowID in IDs:
        try:
            Title = subprocess.check_output(
                ["xdotool", "getwindowname", WindowID]
            ).decode().strip()

            if " - " in Title:
                SpotifyID = WindowID

        except:
            continue

    return None

NullFocusNotebook = nulltk.Notebook(NullFocus)
NullFocusManagePage = nulltk.Frame(NullFocusNotebook)
NullFocusLogsPage = nulltk.Frame(NullFocusNotebook)
NullFocusClockPage = nulltk.Frame(NullFocusNotebook)
NullFocusClipBoard = nulltk.Frame(NullFocusNotebook)
NullFocusOperator = nulltk.Frame(NullFocusNotebook)
NullFocusNotebook.pack(fill="both", expand=True)
NullFocusManagePage.rowconfigure(0, weight=1)
NullFocusManagePage.columnconfigure(0, weight=1)
NullFocusLogsPage.rowconfigure(0, weight=1)
NullFocusLogsPage.columnconfigure(0, weight=1)
NullFocusNotebook.add(NullFocusLogsPage, text="Logs")
NullFocusNotebook.add(NullFocusManagePage, text="Manage Tracking")
NullFocusNotebook.add(NullFocusClockPage, text="Circadian Clock")
NullFocusNotebook.add(NullFocusClipBoard, text="ClipBoard")
NullFocusNotebook.add(NullFocusOperator, text="Operator")
    #region ManagePage
NullFocusManagePageMain = nulltk.Frame(NullFocusManagePage)
NullFocusManagePageMain.pack(fill="both", expand=True)
NullFocusManagePageMain.columnconfigure(0, weight=1)
NullFocusManagePageMain.rowconfigure(0, weight=0)
NullFocusManagePageMain.rowconfigure(1, weight=0)
NullFocusManagePageMain.rowconfigure(2, weight=0)
NullFocusManagePageMain.rowconfigure(3, weight=1)
NullFocusManagePageSlidersNTexts = nulltk.Frame(NullFocusManagePageMain)
NullFocusManagePageSlidersNTexts.grid(row=0, column=0, sticky="ew", pady=5)
NullFocusManagePageSlidersNTexts.columnconfigure(0, weight=1)
NullFocusManagePageSlidersNTexts.columnconfigure(1, weight=1)
NullFocusManagePageSlidersNTexts.columnconfigure(2, weight=1)
NullFocusManagePageSlidersNTexts.rowconfigure(0, weight=0)
NullFocusManagePageSlidersNTexts.rowconfigure(1, weight=0)
NullFocusManagePageSlidersNTexts.rowconfigure(2, weight=0)
TrackerWriteInterval = tk.IntVar(value = 1)
TrackerMinimumWindowTime = tk.IntVar(value = 1)
TrackerNewDay = tk.IntVar(value = 3)
IgnoredAppListVar = tk.StringVar(value = "")
WriteIntervalText = nulltk.Label(NullFocusManagePageSlidersNTexts, text= f"Save To Disk Every: {TrackerWriteInterval.get()} Minutes")
WriteIntervalText.grid(row=0, column=0, sticky="ew", pady=0)
RequiredFocusText = nulltk.Label(NullFocusManagePageSlidersNTexts, text= f"Window Focus Time Req: {TrackerMinimumWindowTime.get()} Seconds")
RequiredFocusText.grid(row=0, column=1, sticky="ew", pady=0)
NewDayText = nulltk.Label(NullFocusManagePageSlidersNTexts, text= f"New Cycle After {TrackerNewDay.get()} Hours")
NewDayText.grid(row=0, column=2, sticky="ew", pady=0)
WriteIntervalSlider = nulltk.Scale(NullFocusManagePageSlidersNTexts,from_=1,to=60,orient="horizontal",variable=TrackerWriteInterval,showvalue=False, command=lambda e: UpdateTrackerQuality())
WriteIntervalSlider.grid(row=1, column=0, sticky="ew", padx=5)
RequiredFocusSlider = nulltk.Scale(NullFocusManagePageSlidersNTexts,from_=1,to=60,orient="horizontal",variable=TrackerMinimumWindowTime,showvalue=False, command=lambda e: UpdateTrackerQuality())
RequiredFocusSlider.grid(row=1, column=1, sticky="ew", padx=5)
NewDaySlider = nulltk.Scale(NullFocusManagePageSlidersNTexts,from_=1,to=23,orient="horizontal",variable=TrackerNewDay,showvalue=False, command=lambda e: UpdateTrackerQuality())
NewDaySlider.grid(row=1, column=2, sticky="ew", padx=5)
AddNewTrackerClass = nulltk.Button(NullFocusManagePageMain,text="New Category", command=lambda: AddNewTracker(None,False))
AddNewTrackerClass.grid(row=1, column=0, sticky="ew", pady=5, padx=5)
TrackerDiv = nulltk.Frame(NullFocusManagePageMain, height=3, bg="gray")
TrackerDiv.grid(row=2, column=0, sticky="ew", pady=5)
TrackerBottomLists = nulltk.Frame(NullFocusManagePageMain)
TrackerBottomLists.grid(row=3, column=0, sticky="ensw", pady=(0,5))
TrackerBottomLists.columnconfigure(0,weight=1)
TrackerBottomLists.columnconfigure(1,weight=6)
TrackerBottomLists.rowconfigure(0,weight=1)
IgnoredAppsFrame = nulltk.Frame(TrackerBottomLists)
IgnoredAppsFrame.grid(row=0, column=0, sticky="nsew")
IgnoredAppsFrame.columnconfigure(0,weight=1)
IgnoredAppsFrame.rowconfigure(0,weight=0)
IgnoredAppsFrame.rowconfigure(1,weight=1)
IgnoredAppsFrame.rowconfigure(2,weight=0)
AddIgnoredAppButton = nulltk.Button(IgnoredAppsFrame ,text="Add App", command=lambda: AddIgnoredTracker(), width = 30)
AddIgnoredAppButton.grid(row=0, column=0, sticky="ew", pady=5, padx=5)
IgnoredAppsList = ScrollableFrame(IgnoredAppsFrame)
IgnoredAppsList.grid(row=1, column=0, sticky="ewns",padx=5)
IgnoredAppsContainer = IgnoredAppsList.Inner
IgnoredAppsListText = nulltk.Label(IgnoredAppsContainer, textvariable = IgnoredAppListVar, anchor="center", justify="center")
IgnoredAppsListText.pack(fill="x", expand=True)
RemoveIgnoredAppButton = nulltk.Button(IgnoredAppsFrame ,text="Remove App", command=lambda: DeleteIgnoredTracker(), width = 30)
RemoveIgnoredAppButton.grid(row=2, column=0, sticky="ew", pady=5, padx=5)
TrackerClassificationList = ScrollableFrame(TrackerBottomLists)
TrackerClassificationList.grid(row=0, column=1, sticky="ensw", padx=5, pady=5)
ClassiciationListContainer = TrackerClassificationList.Inner
IgnoredAppsList.BindMouseWheel(NullFocusManagePageMain)
TrackerClassificationList.BindMouseWheel(NullFocusManagePageMain)
RequiredFocusSlider.bind("<Button-4>", lambda e: (TrackerMinimumWindowTime.set(min(60, TrackerMinimumWindowTime.get()+5)), UpdateTrackerQuality()))
RequiredFocusSlider.bind("<Button-5>", lambda e: (TrackerMinimumWindowTime.set(max(1, TrackerMinimumWindowTime.get()-5)), UpdateTrackerQuality()))
WriteIntervalSlider.bind("<Button-4>", lambda e: (TrackerWriteInterval.set(min(60, TrackerWriteInterval.get()+5)), UpdateTrackerQuality()))
WriteIntervalSlider.bind("<Button-5>", lambda e: (TrackerWriteInterval.set(max(1, TrackerWriteInterval.get()-5)), UpdateTrackerQuality()))
NewDaySlider.bind("<Button-4>", lambda e: (TrackerNewDay.set(min(23, TrackerNewDay.get()+1)), UpdateTrackerQuality()))
NewDaySlider.bind("<Button-5>", lambda e: (TrackerNewDay.set(max(1, TrackerNewDay.get()-1)), UpdateTrackerQuality()))
    #endregion
    #region Logs Page
NullFocusLogsPageInner = nulltk.Frame(NullFocusLogsPage)
NullFocusLogsPageInner.grid(row=0, column=0, sticky="nsew")
NullFocusLogsPageInner.rowconfigure(0,weight=0)
NullFocusLogsPageInner.rowconfigure(1,weight=0)
NullFocusLogsPageInner.rowconfigure(2,weight=1)
NullFocusLogsPageInner.columnconfigure(0,weight=1)
NullFocusLogsPageInner.columnconfigure(1,weight=1)
NullFocusLogsPageInner.columnconfigure(2,weight=1)
NullFocusLogsPageInner.columnconfigure(3,weight=7)
InjectorButton = nulltk.Button(NullFocusLogsPageInner, text="Inject", command= lambda: InjectTracker())
InjectorButton.grid(row=0, column=0, sticky="ew")
InjectorText = nulltk.Label(NullFocusLogsPageInner, text="What You Are Injecting:")
InjectorText.grid(row=0, column=1, sticky="ew", columnspan=2)
InjectionEntry = nulltk.Entry(NullFocusLogsPageInner,)
InjectionEntry.grid(row=0,column=3,padx=3,pady=3,sticky="ew")
ToolTip(InjectorText, "E.g. When you took your medication, or did something important. It will show what you type, with the timestamp.")
YearText = nulltk.Label(NullFocusLogsPageInner, text= f"Years", width=6)
YearText.grid(row=1, column=0, sticky="ew")
MonthText = nulltk.Label(NullFocusLogsPageInner, text= f"Months", width=7)
MonthText.grid(row=1, column=1, sticky="ew")
CycleText = nulltk.Label(NullFocusLogsPageInner, text= f"Cycles", width=8)
CycleText.grid(row=1, column=2, sticky="ew")
BreakDownText = nulltk.Label(NullFocusLogsPageInner, text= f"Breakdown")
BreakDownText.grid(row=1, column=3, sticky="ew")
CurrentLogView = tk.StringVar(value = "")
YearChoicesBox = nulltk.Frame(NullFocusLogsPageInner)
YearChoicesBox.grid(row=2,column=0, sticky="nsew",padx=5, pady=5)
YearChoicesBox.rowconfigure(0,weight=1)
YearChoicesBox.columnconfigure(0,weight=1)
YearChoices = ScrollableFrame(YearChoicesBox)
YearChoices.pack(fill="both", expand=True, anchor="n")
YearChoicesButtons = YearChoices.Inner
YearChoicesButtons.pack(fill="x", expand=True, anchor="n", padx=3)
MonthChoicesBox = nulltk.Frame(NullFocusLogsPageInner)
MonthChoicesBox.grid(row=2,column=1, sticky="nsew",padx=5, pady=5)
MonthChoicesBox.rowconfigure(0,weight=1)
MonthChoicesBox.columnconfigure(0,weight=1)
MonthChoices = ScrollableFrame(MonthChoicesBox)
MonthChoices.pack(fill="both", expand=True, anchor="n")
MonthChoicesButtons = MonthChoices.Inner
MonthChoicesButtons.pack(fill="x", expand=True, anchor="n", padx=3)
CycleChoicesBox = nulltk.Frame(NullFocusLogsPageInner)
CycleChoicesBox.grid(row=2,column=2, sticky="nsew",padx=5, pady=5)
CycleChoicesBox.rowconfigure(0,weight=1)
CycleChoicesBox.columnconfigure(0,weight=1)
CycleChoices = ScrollableFrame(CycleChoicesBox)
CycleChoices.pack(fill="both", expand=True, anchor="n")
CycleChoicesButtons = CycleChoices.Inner
CycleChoicesButtons.pack(fill="x", expand=True, anchor="n", padx=3)
LogDataBox = nulltk.Frame(NullFocusLogsPageInner)
LogDataBox.grid(row=2,column=3, sticky="nsew",padx=5, pady=5)
LogDataBox.rowconfigure(0,weight=1)
LogDataBox.columnconfigure(0,weight=1)
LogData = ScrollableFrame(LogDataBox)
LogData.pack(fill="both", expand=True, anchor="n")
LogDataInner = LogData.Inner
LogDataLabel = nulltk.Label(LogDataInner, textvariable=CurrentLogView)
LogDataLabel.pack(fill="both", expand=True, anchor="nw")
YearChoices.BindMouseWheel(NullFocusLogsPageInner)
MonthChoices.BindMouseWheel(NullFocusLogsPageInner)
CycleChoices.BindMouseWheel(NullFocusLogsPageInner)
LogData.BindMouseWheel(NullFocusLogsPageInner)
    #endregion
    #region Circadian Clock Page
NullFocusClockPage.columnconfigure(0,weight=1)
HereLine = nulltk.Label(NullFocusClockPage, text = "↓", font=("Arial, 18"))
HereLine.grid(row=0, column=0, sticky="nswe", pady=(10,0))
ClockLabel = nulltk.Label(NullFocusClockPage, image=ClockImage)
ClockLabel.image = ClockImage
ClockLabel.grid(row=1,column=0, sticky="nswe",pady=5)
    #endregion
    #region ClipBoardPage
NullFocusClipBoardPage = nulltk.Frame(NullFocusClipBoard)
NullFocusClipBoardPage.pack(fill="both",expand="true")
NullFocusClipBoardPage.pack(fill="both",expand="true")
NullFocusClipBoardPage.columnconfigure(0, weight=1)
NullFocusClipBoardPage.rowconfigure(1, weight=1)
ClipBoardTopRow = nulltk.Frame(NullFocusClipBoardPage)
ClipBoardTopRow.grid(column=0,row=0,sticky="ew",pady=(5,0), padx=5)
ClipBoardTopRow.columnconfigure(0,weight=1)
ClipBoardTopRow.columnconfigure(1,weight=1)
ClipBoardTopRow.columnconfigure(2,weight=1)
ClipboardDeletionButton= nulltk.Button(ClipBoardTopRow, text="Delete Checked", command=lambda: DeleteClipboardItems())
ClipboardDeletionButton.grid(row=0,column=0,sticky="ew")
ClipboardSelectAll= nulltk.Button(ClipBoardTopRow, text="Select All", command=lambda: SelectAllClipBoard())
ClipboardSelectAll.grid(row=0,column=1,sticky="ew")
ClipboardSelectNone= nulltk.Button(ClipBoardTopRow, text="Select None", command=lambda: SelectNoneClipBoard())
ClipboardSelectNone.grid(row=0,column=2,sticky="ew")
ClipBoardList = ScrollableFrame(NullFocusClipBoardPage)
ClipBoardList.grid(column=0,row=1,sticky="nesw",columnspan=99, pady=5, padx=5)
ClipBoardList.rowconfigure(0,weight=1)
ClipBoardList.columnconfigure(0,weight=1)
    #endregion
    #region  OperatorPage
NullFocusOperator.columnconfigure(0,weight=1)
NullFocusOperator.rowconfigure(2,weight=1)
NullFocusAddOperatorButton = nulltk.Button(NullFocusOperator, text = "Add Operator", command=lambda: AddOperatorWindow())
NullFocusAddOperatorButton.grid(row=0,column=0, sticky="ew", padx=5)
nulltk.Frame(NullFocusOperator,height=2,bg="gray").grid(row=1,column=0,sticky="ew",pady=6, padx=5)
OperatorList = ScrollableFrame(NullFocusOperator)
OperatorList.rowconfigure(0,weight=1)
OperatorList.columnconfigure(0,weight=1)
OperatorList.grid(row=2,column=0, sticky="ewns", pady=5, padx=5)
    #endregion

def NullFocusLoop():
    global LastWriteToDisk, CurrentCycle, FocusStartTime

    while True:
        if NullFocusActive.get():
            try:
                now = time.time()
                if (now - LastWriteToDisk>= (WriteToDiskSeconds * 60)):
                    SaveTrackerLog()
                    LastWriteToDisk = now
                else:
                    SpotifyTracker()
            except Exception as e:
                Log(f"NullFocus: Regular Loop error- {e}", "Error")
        time.sleep(1)

def NullFocusFocusLoop():
    for WindowID in WatchFocus():
        FocusedClass = GetWindowClass(WindowID)
        ChangedWindowFocus(FocusedClass)

def NullFocusClockLoop():
    global ResetClock, LastClockUpdate, ClockOriginal, ClockLabel, ClockImage, ClockRotation, ClockUpdatedViaCycle
     
    while True:
        if NullFocusActive.get():
            try:
                if ResetClock == True:
                    ResetClock = False
                    LastClockUpdate = time.time()
                    if ClockUpdatedViaCycle == False:
                        ClockRotation = 0
                        Rotated = ClockOriginal.rotate(ClockRotation,resample=Image.Resampling.BICUBIC,expand=False)
                        Rotated = Rotated.resize((750, 750),Image.Resampling.LANCZOS)
                        #Width, Height = (100,100)
                        #Rotated = Rotated.crop((0,0,Width,int(Height *0.49)))
                        ClockImage = ImageTk.PhotoImage(Rotated)
                        Root.after(0,lambda: ClockLabel.config(image=ClockImage))
                        ClockLabel.image = ClockImage
                    else:
                        ClockUpdatedViaCycle = False

                        while WaitForNullFocusLoad == False:
                            time.sleep(1)
                            continue

                        time.sleep(1)

                        CycleStart = datetime.strptime(CurrentCycle["StartTime"],"%m/%d/%y - %I:%M%p")
                        ElapsedSeconds = (datetime.now() - CycleStart).total_seconds()
                        ElapsedHalfHours = int(ElapsedSeconds // 1800)
                        ClockRotation = ElapsedHalfHours * 7.5

                        Rotated = ClockOriginal.rotate(ClockRotation,resample=Image.Resampling.BICUBIC,expand=False)
                        Rotated = Rotated.resize((750, 750),Image.Resampling.LANCZOS)
                        #Width, Height = (100,100)
                        #Rotated = Rotated.crop((0,0,Width,int(Height *0.49)))
                        ClockImage = ImageTk.PhotoImage(Rotated)
                        Root.after(0,lambda: ClockLabel.config(image=ClockImage))
                        ClockLabel.image = ClockImage
                        
                else:
                    if LastClockUpdate != None:
                        if time.time() - LastClockUpdate >= 1800:
                            LastClockUpdate = time.time()
                            ClockRotation += 7.5
                            Rotated = ClockOriginal.rotate(ClockRotation,resample=Image.Resampling.BICUBIC,expand=False)
                            Rotated = Rotated.resize((750, 750),Image.Resampling.LANCZOS)
                            #Width, Height = (100,100)
                            #Rotated = Rotated.crop((0,0,Width,int(Height *0.49)))
                            ClockImage = ImageTk.PhotoImage(Rotated)
                            Root.after(0,lambda: ClockLabel.config(image=ClockImage))
                            ClockLabel.image = ClockImage
                time.sleep(30)
                continue
            except Exception as e:
                Log(f"NullFocus: Somehow the Circadian Clock Loop Broke? - {e}")
        time.sleep(3)


    return

def NullFocusClipBoardLoop():
    global DontCopyToClipBoardData, LastClipBoard

    while True:
        
        if NullFocusActive.get():
            Current = GetClipboard()

            if DontCopyToClipBoardData:
                DontCopyToClipBoardData = False
                LastClipBoard = Current['Hash']
                continue

            if Current:
                if Current['Hash'] != LastClipBoard:


                    LastClipBoard = Current['Hash']
                    Root.after(0,lambda c=Current: AddClipBoardEntry(c))
        time.sleep(1.5)

def NullFocusRunOperators():
    for Operator in NullFocusOperators:

        if Operator['WindowClass'] == CurrentFocus:
            ExecuteWindowChange(Operator, "Focused")

        if Operator['WindowClass'] == OldFocus:
            ExecuteWindowChange(Operator, "Unfocused")

def StartUpNullFocus():
    global AppClassification,WriteToDiskSeconds,MinimumWindowTime,NewDayThreshold,LoadCompleted,ActualProgramLoadedCount
    global SystemLoading, YearButtons, CurrentCycle,ClassificationRows, OnCurrentCycle
    global CurrentViewedMonth, CurrentViewedYear, CurrentViewedCycle, WaitForNullFocusLoad
    global NullFocusOperatorRows, NullFocusOperators, ClipBoardHistory
    
    if NullFocusActive.get() == True:
        SystemLoading = True
        tracker = None

        if not os.path.isdir(ClipboardPath):
            os.makedirs(ClipboardPath, exist_ok=True)

        if not os.path.isfile(ConfigPath):
            Butts.set("Save File not found???")
            Root.update_idletasks()
            return False

        try:
            with open(ConfigPath, "r") as f:
                data = json.load(f)
                tracker = data.get("NullFocus", {})

        except Exception as e:
            Butts.set(f"ERROR LOADING Null Focus SAVE\n\n{e}")
            Root.update_idletasks()
            return False

        AppClassification = tracker.get("AppClassification", {})
        WriteToDiskSeconds = tracker.get("WriteToDiskSeconds",60)
        MinimumWindowTime = tracker.get("MinimumWindowTime",1)
        NewDayThreshold = tracker.get("NewDayThreshold",1)

        UpdateTrackerQuality()

        def StartTrackerListeners():
            global MouseListener
            global KeyboardListener
            MouseListener = mouse.Listener(on_click=OnMouseClick, on_scroll=OnMouseScroll)
            KeyboardListener = keyboard.Listener(on_press=OnKeyPress)
            MouseListener.start()
            KeyboardListener.start()
        
        StartTrackerListeners()

        # -----  Log and Manage Tabs

        YearFiles = [File for File in os.listdir(TrackerPath)if File.endswith(".json")]
        if len(YearFiles) == 0:
            Year = datetime.now().strftime("%Y")

            YearPath = os.path.join(TrackerPath,f"{Year}.json")

            with open(YearPath, "w") as f:
                json.dump({}, f, indent=4)

            YearFiles = [f"{Year}.json"]

            YearMonthPath = os.path.join(ClipboardPath,datetime.now().strftime("%Y - %b"))

            os.makedirs(YearMonthPath, exist_ok=True)

            SaveTrackerLog()
            
        ExistingYears = [Button.cget("text")for Button in YearButtons]

        FileYears = [os.path.splitext(File)[0]for File in YearFiles]

        if ExistingYears != FileYears:
            for button in YearButtons:
                button.destroy()

            YearButtons.clear()

            for Year in sorted(FileYears):
                Button = nulltk.Button(YearChoicesButtons,text=Year,command=lambda Y=Year: ClickYearButton(Y), width=15)
                Button.pack(fill="x")
                YearButtons.append(Button)

        LatestYear = max(os.path.splitext(File)[0]for File in YearFiles)
        LatestYearPath = os.path.join(TrackerPath,f"{LatestYear}.json")
        with open(LatestYearPath, "r") as f:
            Data = json.load(f)
        if Data:
            LatestMonth = max(Data.keys(),key=lambda m: datetime.strptime(m, "%b"))
        
        if Data[LatestMonth]:
            LatestCycleName = max(Data[LatestMonth].keys(),key=lambda x: datetime.strptime(x,"%m/%d/%y - %I:%M%p"))
            LatestCycle = Data[LatestMonth][LatestCycleName]
            LastCycleTime = LatestCycle.get("LastUpdated", 0)

            if (time.time() - LastCycleTime < (NewDayThreshold * 3600)):
                CurrentCycle = LatestCycle
            else:
                SleepTime = time.time() - LastCycleTime
                CurrentCycle = {
                    "StartTime": datetime.now().strftime("%m/%d/%y - %I:%M%p"),
                    "LastUpdated": time.time(),
                    "TimeSpent": {
                        "Sleep": {
                            "Name": "Sleep",
                            "FocusedTime": int(SleepTime),
                            "ActiveTime": 0,
                            "Classification": "Sleep"
                            }
                        }
                    }
                SaveTrackerLog()
        
        for i in ClassificationRows:
            i.destroy()

        ClassificationRows.clear()

        for Classifications, app in AppClassification.items():
            if Classifications == "Ignored" or Classifications == "Sleep":
                continue
            AddNewTracker(Classifications,True)

        # --- Operators Stuff

        for rows in NullFocusOperatorRows:
            rows.destroy()

        NullFocusOperatorRows.clear()

        NullFocusOperators.clear()


        for operators in tracker.get("Operators", []):
            NullFocusOperators.append(operators)
            CreateOperatorRow(operators)


        #---- ClipBoard stuff


        ClipBoardHistory.clear()

        for rows in ClipBoardRows:
            rows.destroy()

        ClipBoardRows.clear()

        MonthFolder = os.path.join(ClipboardPath,datetime.now().strftime("%Y - %b"))

        ClipSave = os.path.join(MonthFolder,"000-ClipBoard.json")
        os.makedirs(MonthFolder, exist_ok=True)

        if not os.path.isfile(ClipSave):
            with open(ClipSave, "w") as f:
                json.dump([], f, indent=2)

        try:
            with open(ClipSave, "r") as f:
                clippy = json.load(f)


        except Exception as e:
            Butts.set(f"ERROR LOADING ClipBoard Save\n\n{e}")
            Root.update_idletasks()
            return False
        
        ClipBoardHistory = clippy

        for Row in clippy:
            Row['Collapsed'] = False
            BuildClipBoardRow(Row)

        Notebook.add(NullFocus, text="NullFocus")
        ClickYearButton(LatestYear)
        ClickMonthButton(LatestYear, LatestMonth)
        ClickCycleButton(LatestYear,LatestMonth,CurrentCycle["StartTime"])
        OnCurrentCycle = True
        CurrentViewedCycle = CurrentCycle["StartTime"]
        CurrentViewedMonth = LatestMonth
        CurrentViewedYear = LatestYear

        WaitForNullFocusLoad = True
        ActualProgramLoadedCount+=1

    else:
        def StopTrackerListeners():
            global MouseListener
            global KeyboardListener

            if MouseListener:
                MouseListener.stop()
                MouseListener = None

            if KeyboardListener:
                KeyboardListener.stop()
                KeyboardListener = None

        StopTrackerListeners()
        Notebook.forget(NullFocus)

    SystemLoading = False
    LoadCompleted += 1
    return

#endregion

#region NullMoji
CustomEmojis = {}
CustomEmojiRows = []
RecentEmojis = []
BaseEmoji = {}
SearchAfterID = None
PreviousWindowID = None
CalledWithShortcut = False
CopiedEmoji = None
NullMojiSearchButtons = []
NullMojiRecentButtons = []
NullMojiAllEmojiButtons = []
RootState = ""
NullMojiPopupWindow = None

def QueueEmojiSearch(*_):
    global SearchAfterID

    if SearchAfterID:
        Root.after_cancel(SearchAfterID)

    SearchAfterID = Root.after(
        250,
        SearchForEmoji
    )

def SearchForEmoji():
    global NullMojiSearchButtons
    Search = NullMojiSearchBarVar.get().strip().lower()
    for Button in NullMojiSearchButtons:
        Button.destroy()
    NullMojiSearchButtons.clear()
    if len(Search) < 1:
        NullMojiAllSearchColumnList.grid_forget()
        NullMojiAllRecentColumnList.grid(row=2,column=0,sticky="nsew", columnspan=2)
        return
    else:
        NullMojiAllRecentColumnList.grid_forget()
        NullMojiAllSearchColumnList.grid(row=2,column=0,sticky="nsew", columnspan=2)

    CustomMatching = [
    EmojiData
    for EmojiData in CustomEmojis.values()
    if Search in EmojiData["Alias"].lower()]
    BaseMatching = [
        EmojiData
        for EmojiData in BaseEmoji
        if Search in EmojiData["Alias"].lower()
    ]
    Matching = CustomMatching + BaseMatching
    Matching = Matching[:100]
    ColumnCount = 3
    for i, EmojiData in enumerate(Matching):
        Button = nulltk.Button(NullMojiAllSearchColumnListInner,text=EmojiData["Emoji"],font=("Noto Color Emoji",15),command=lambda E=EmojiData: CopyEmoji(E),width = 4)
        Button.grid(row=i // ColumnCount,column=i % ColumnCount,padx=2,pady=2)
        Button.Emoji = EmojiData
        NullMojiSearchButtons.append(Button)
    Root.update_idletasks()
    NullMojiAllSearchColumnList.BindMouseWheel(NullMojiMainPage)

def AddCustomEmoji():
    global CustomEmojis
    if NullMojiCustomEmojiBarNameVar.get() == "":
        return
    
    if NullMojiCustomEmojiBarEmojiVar.get() == "":
        return

    CustomEmojis[NullMojiCustomEmojiBarNameVar.get()] = {
        "Emoji": NullMojiCustomEmojiBarEmojiVar.get(),
        "Alias": NullMojiCustomEmojiBarNameVar.get(),
        "DeleteConfirmation": False
    }

    SaveConfig("NullMoji")

    NullMojiCustomEmojiBarNameVar.set("")
    NullMojiCustomEmojiBarEmojiVar.set("")
    RebuildCustomEmojiUI()
    return

def CreateCustomEmojiBar(Key, DictEntry):
    global CustomEmojiRows

    

    EmojiFrame = nulltk.Frame(NullMojiAllCustomsColumnListInner, padx=5, pady=5)
    EmojiFrame.pack(expand=True,fill="x")
    EmojiFrame.rowconfigure(0,weight=1)
    EmojiFrame.columnconfigure(0,weight=1)
    CustomEmojiRows.append(EmojiFrame)

    InnerEmojiFrame = nulltk.Frame(EmojiFrame,)
    InnerEmojiFrame.grid(row=0,column=0, sticky="ew")
    InnerEmojiFrame.rowconfigure(0,weight=1)
    InnerEmojiFrame.columnconfigure(0,weight=1)
    InnerEmojiFrame.columnconfigure(1,weight=0)
    InnerEmojiFrame.columnconfigure(2,weight=0)

    EmojiFrameEmojiLabel = nulltk.Label(InnerEmojiFrame, text=DictEntry['Emoji'])
    EmojiFrameEmojiLabel.grid(row=0,column=0, sticky="ew")

    CustomEmojiCopyEmoji = nulltk.Button(InnerEmojiFrame, text="Copy", command=lambda: CopyEmoji(DictEntry))
    CustomEmojiCopyEmoji.grid(row=0,column=1,padx=3,pady=3,sticky="ew")

    DeleteCustomEmoji = nulltk.Button(InnerEmojiFrame, text="Del Custom", command=lambda: RemoveCustomEmoji(Key, DictEntry, DeleteCustomEmoji))
    DeleteCustomEmoji.grid(row=0,column=2,padx=3,pady=3,sticky="ew")
    return

def RemoveCustomEmoji(Key, HoldDict, Button, Timeout=4):
    EndTime = time.time() + Timeout
    def Tick():
        Remaining = int(EndTime - time.time())
        if Remaining <= 0:
            if not Button.winfo_exists():
                return
            Button.config(text="Del Custom")
            HoldDict['DeleteConfirmation'] = False
            return

        if not Button.winfo_exists():
            return
        Button.config(text=f"R U Sure? {Remaining}")
        Root.after(1000, Tick)
        return
    
    if HoldDict['DeleteConfirmation'] == False:
        HoldDict['DeleteConfirmation'] = True
        Remaining = int(EndTime - time.time())
        Button.config(text=f"R U Sure? {Remaining}")
        Tick()
        return
    
    CustomEmojis.pop(Key, None)
    RebuildCustomEmojiUI()
    
    return

def NullMojiFocus():

    global PreviousWindowID, CalledWithShortcut, NullMojiSearchButtons, NullMojiPopupWindow

    NullMojiPopup = nulltk.Toplevel(Root)
    NullMojiPopupWindow = NullMojiPopup
    NullMojiPopup.title("NullMoji")
    NullMojiPopup.configure(bg="#1e1e1e")
    PopupWidth = 500
    PopupHeight = 300
    ScreenWidth = Root.winfo_screenwidth()
    ScreenHeight = Root.winfo_screenheight()
    X = int((ScreenWidth / 2) - (PopupWidth / 2))
    Y = int((ScreenHeight / 2) - (PopupHeight / 2))
    NullMojiPopup.geometry(f"{PopupWidth}x{PopupHeight}+{X}+{Y}")
    SearchVar = tk.StringVar()
    SearchBar = nulltk.Entry(NullMojiPopup,textvariable=SearchVar,font=("Arial",18))
    SearchBar.pack(fill="x",padx=10,pady=10)
    ResultsFrame = nulltk.Frame(NullMojiPopup)
    ResultsFrame.pack(fill="both",expand=True)
    NullMojiPopup.lift()
    NullMojiPopup.attributes("-topmost", True)
    NullMojiPopup.after(10,lambda:NullMojiPopup.attributes("-topmost", False))
    NullMojiPopup.focus_force()
    SearchBar.focus_force()
    NullMojiSearchButtons = []
    def PopupSearch():
        Search = SearchVar.get().strip().lower()
        for Button in NullMojiSearchButtons:
            Button.destroy()
        NullMojiSearchButtons.clear()
        if len(Search) < 1:
            return
        CustomMatching = [
            EmojiData
            for EmojiData in CustomEmojis.values()
            if Search in EmojiData["Alias"].lower()
        ]
        BaseMatching = [
            EmojiData
            for EmojiData in BaseEmoji
            if Search in EmojiData["Alias"].lower()
        ]
        Matching = (
            CustomMatching +
            BaseMatching
        )[:100]
        ColumnCount = 3
        for i, EmojiData in enumerate(Matching):

            Button = nulltk.Button(
                ResultsFrame,
                text=EmojiData["Emoji"],
                font=("Noto Color Emoji",15),
                command=lambda E=EmojiData:
                    CopyEmoji(E),
                width=4
            )

            Button.grid(
                row=i // ColumnCount,
                column=i % ColumnCount,
                padx=2,
                pady=2
            )

            Button.Emoji = EmojiData
            NullMojiSearchButtons.append(Button)
        Root.update_idletasks()
    SearchVar.trace_add("write",lambda *_: PopupSearch())
    SearchBar.bind("<Escape>",lambda e: NullMojiPopup.destroy())
    SearchBar.bind("<Return>",SelectFirstEmoji)

    return

def SelectFirstEmoji(event=None):
    if not NullMojiSearchButtons:
        return
    FirstButton = NullMojiSearchButtons[0]
    Emoji = FirstButton.Emoji
    CopyEmoji(Emoji)

def RebuildCustomEmojiUI():
    global CustomEmojiRows
    for Row in CustomEmojiRows:
        Row.destroy()
    CustomEmojiRows.clear()
    for Key, DictEntry in CustomEmojis.items():
        CreateCustomEmojiBar(Key, DictEntry)

    NullMojiAllCustomsColumnList.BindMouseWheel(NullMojiMainPage)
    return

def GetActiveWindowID():
    try:
        Result = subprocess.run(
            ["xdotool","getwindowfocus"],
            capture_output=True,
            text=True
        )
        return Result.stdout.strip()
    except:
        return None
    
def CopyEmoji(Emoji):
    global CopiedEmoji, NullMojiSearchButtons, DontCopyToClipBoardData
    CopiedEmoji = Emoji['Emoji']
    DontCopyToClipBoardData = True
    subprocess.run(['xclip', '-selection', 'clipboard'], input=CopiedEmoji.encode('utf-8'), check=True)

    if PreviousWindowID is not None and CalledWithShortcut is not False:
        FocusBackOnOldWindow()

    
    NullMojiSearchBarVar.set("")
    UpdateRecent(Emoji)
    for Button in NullMojiSearchButtons:
        Button.destroy()
    NullMojiSearchButtons.clear()
    NullMojiAllSearchColumnList.grid_forget()
    NullMojiAllRecentColumnList.grid(row=2,column=0,sticky="nsew")
    return

def UpdateRecent(Emoji):
    global RecentEmojis, NullMojiRecentButtons
    if Emoji in RecentEmojis:
        RecentEmojis.remove(Emoji)
    RecentEmojis.insert(0, Emoji)
    BuildRecentEmojis()
    SaveConfig("NullMoji")

def BuildRecentEmojis():
    global RecentEmojis, NullMojiRecentButtons

    for Button in NullMojiRecentButtons:
        Button.destroy()
    NullMojiRecentButtons.clear()
    ColumnCount = 4
    for i, RecentEmoji in enumerate(RecentEmojis):
        Button = nulltk.Button(NullMojiAllRecentColumnListInner,text=RecentEmoji["Emoji"],font=("Noto Color Emoji",15),command=lambda E=RecentEmoji: CopyEmoji(E), width=3)
        Button.grid(row=i // ColumnCount,column=i % ColumnCount,padx=2,pady=2,)
        Button.bind("<Button-3>",lambda event, E=RecentEmoji, B=Button:RemoveRecentEmoji(E, B))
        NullMojiRecentButtons.append(Button)

    NullMojiAllRecentColumnList.BindMouseWheel(NullMojiMainPage)
    return
    
def RemoveRecentEmoji(Emoji,button):
    global RecentEmojis
    if Emoji in RecentEmojis:
        RecentEmojis.remove(Emoji)
        button.destroy()
    SaveConfig("NullMoji")
    BuildRecentEmojis()

def FocusBackOnOldWindow():
    global PreviousWindowID, CalledWithShortcut, NullMojiPopupWindow
    try:
        subprocess.run(['xdotool', 'windowactivate', PreviousWindowID], check=True)
        time.sleep(0.1)
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+v'], check=True)
        
        PreviousWindowID = None
        CalledWithShortcut = False
        NullMojiPopupWindow.destroy()
        NullMojiPopupWindow = None
    except Exception as e:
        Log(f"NullMoji: Couldn't refocus on last window - {e}")
    return

NullMojiMainPage = nulltk.Frame(NullMoji)
NullMojiMainPage.pack(fill="both", expand=True) 
NullMojiMainPage.columnconfigure(0, weight=1)
NullMojiMainPage.columnconfigure(1, weight=1)
NullMojiMainPage.columnconfigure(2, weight=1)
NullMojiMainPage.rowconfigure(0, weight=1)
NullMojiAllEmojisColumn = nulltk.Frame(NullMojiMainPage)
NullMojiAllEmojisColumn.grid(row=0,column=0, sticky="nsew")
NullMojiAllEmojisColumn.columnconfigure(0, weight=1)
NullMojiAllEmojisColumn.rowconfigure(0, weight=0)
NullMojiAllEmojisColumn.rowconfigure(1, weight=1)
NullMojiAllEmojisText = nulltk.Label(NullMojiAllEmojisColumn,text="All Emojis")
NullMojiAllEmojisText.grid(row=0, column=0, sticky="ew",)
NullMojiAllEmojisColumnList = ScrollableFrame(NullMojiAllEmojisColumn)
NullMojiAllEmojisColumnList.grid(row=1, column=0, sticky="ewns",columnspan=2)
NullMojiAllEmojisInner = NullMojiAllEmojisColumnList.Inner
NullMojiSearchBarVar = tk.StringVar(value = "")
NullMojiAllSearchColumn= nulltk.Frame(NullMojiMainPage)
NullMojiAllSearchColumn.grid(row=0,column=1, sticky="nsew")
NullMojiAllSearchColumn.columnconfigure(0, weight=1)
NullMojiAllSearchColumn.columnconfigure(1, weight=0)
NullMojiAllSearchColumn.rowconfigure(0, weight=0)
NullMojiAllSearchColumn.rowconfigure(1, weight=0)
NullMojiAllSearchColumn.rowconfigure(2, weight=1)
NullMojiSearchEmojisText = nulltk.Label(NullMojiAllSearchColumn,text="Recent/Search Emojis")
NullMojiSearchEmojisText.grid(row=0, column=0, sticky="ew",)
NullMojiSearchHelp = nulltk.Label(NullMojiAllSearchColumn,text="(?)",width=4)
NullMojiSearchHelp.grid(row=0, column=1, sticky="w",padx=(3,0))
ToolTip(NullMojiSearchHelp, "When not typing, Your recent selected emojis are shown.\n Right click to remove them.\n Left click to copy to clipboard")
NullMojiSearchBar = nulltk.Entry(NullMojiAllSearchColumn,textvariable=NullMojiSearchBarVar)
NullMojiSearchBar.grid(row=1,column=0,padx=3,pady=3,sticky="ew", columnspan=2)
NullMojiSearchBarVar.trace_add("write", lambda *_: QueueEmojiSearch())
NullMojiSearchBar.bind("<Return>", SelectFirstEmoji)
NullMojiAllSearchColumnList = ScrollableFrame(NullMojiAllSearchColumn)
NullMojiAllSearchColumnList.grid(row=2,column=0, sticky="nsew", columnspan=2)
NullMojiAllSearchColumnListInner = NullMojiAllSearchColumnList.Inner
NullMojiAllSearchColumnList.grid_forget()
NullMojiAllRecentColumnList = ScrollableFrame(NullMojiAllSearchColumn)
NullMojiAllRecentColumnList.grid(row=2,column=0, sticky="nsew", columnspan=2)
NullMojiAllRecentColumnListInner = NullMojiAllRecentColumnList.Inner
NullMojiCustomEmojiBarEmojiVar = tk.StringVar(value = "")
NullMojiCustomEmojiBarNameVar = tk.StringVar(value = "")
NullMojiAllCustomsColumn= nulltk.Frame(NullMojiMainPage)
NullMojiAllCustomsColumn.grid(row=0,column=2, sticky="nsew")
NullMojiAllCustomsColumn.columnconfigure(0, weight=1)
NullMojiAllCustomsColumn.columnconfigure(1, weight=0)
NullMojiAllCustomsColumn.columnconfigure(2, weight=0)
NullMojiAllCustomsColumn.rowconfigure(0, weight=0)
NullMojiAllCustomsColumn.rowconfigure(1, weight=0)
NullMojiAllCustomsColumn.rowconfigure(2, weight=0)
NullMojiAllCustomsColumn.rowconfigure(3, weight=1)
NullMojiCustomEmojisText = nulltk.Label(NullMojiAllCustomsColumn,text="Recent/Search Emojis")
NullMojiCustomEmojisText.grid(row=0, column=0, sticky="ew",)
NullMojiCustomHelp = nulltk.Label(NullMojiAllCustomsColumn,text="(?)",width=4)
NullMojiCustomHelp.grid(row=0, column=2, sticky="w",padx=(3,0))
ToolTip(NullMojiCustomHelp, "You can create Custom Emojis by filling in the name, and Emoji section. \nIt does not have to be emoji's. It can be plain text. e.g. \":)\"")
NullMojiAllCustomsColumnList = ScrollableFrame(NullMojiAllCustomsColumn)
NullMojiAllCustomsColumnList.grid(row=3,column=0, sticky="nsew", columnspan=3)
NullMojiAllCustomsColumnListInner = NullMojiAllCustomsColumnList.Inner
NullMojiCustomEmojiBarName = nulltk.Entry(NullMojiAllCustomsColumn,textvariable=NullMojiCustomEmojiBarNameVar, width = 1)
NullMojiCustomEmojiBarName.grid(row=1,column=0,padx=3,pady=3,sticky="ew")
NullMojiCustomEmojiNameText = nulltk.Label(NullMojiAllCustomsColumn,text="<- Name")
NullMojiCustomEmojiNameText.grid(row=1,column=1,padx=3,pady=3,sticky="ew")
NullMojiCustomEmojiBarEmoji = nulltk.Entry(NullMojiAllCustomsColumn,textvariable=NullMojiCustomEmojiBarEmojiVar, width = 1)
NullMojiCustomEmojiBarEmoji.grid(row=2,column=0,padx=3,pady=3,sticky="ew")
NullMojiCustomEmojiEmojiText = nulltk.Label(NullMojiAllCustomsColumn,text="<- Emoji")
NullMojiCustomEmojiEmojiText.grid(row=2,column=1,padx=3,pady=3,sticky="ew")
NullMojiCustomEmojiAddButton = nulltk.Button(NullMojiAllCustomsColumn, text="Add Custom", command=lambda: AddCustomEmoji())
NullMojiCustomEmojiAddButton.grid(row=1,column=2,padx=3,pady=3,sticky="ew", rowspan=2)

def StartUpNullMoji():
    global LoadCompleted, CustomEmojis, RecentEmojis,ActualProgramLoadedCount
   
    if NullMojiActive.get() == True:
        RebuildCustomEmojiUI()
        BuildRecentEmojis()
        Notebook.add(NullMoji, text="NullMoji")
        ActualProgramLoadedCount +=1
    else:
        Notebook.forget(NullMoji)

    LoadCompleted += 1
    return


#endregion

#region NullWire
OutputWires = {}
InputWires = {}

OutputRows = {}
InputRows = {}

LastOutputs = set()
LastInputs = set()
LastSources = set()

CurrentOutputs = []
CurrentInputs = []
CurrentSources = []
SourceWindowClass = {}

def ResolveID(WhatWeIdentifying, CallType):
    FoundSources = []

    if CallType == "AudioSource":
        FoundSources = FindAudioSourceByName(WhatWeIdentifying)

    elif CallType == "Output":
        FoundSources = FindOutputByName(WhatWeIdentifying)

    elif CallType == "Input":
        FoundSources = FindInputByName(WhatWeIdentifying)

    if FoundSources is None:
        return None
    else:
        return FoundSources

def FindOutputByName(Name):
    FoundOutputs = []

    try:
        out = subprocess.check_output(
            ["pactl", "list", "sinks"]
        ).decode()
    except:
        return FoundOutputs

    CurrentID = None

    for line in out.splitlines():
        line = line.strip()

        if line.startswith("Name:"):
            CurrentID = line.split(":", 1)[1].strip()

        elif line.startswith("Description:"):
            Description = line.split(":", 1)[1].strip()

            if Description == Name and CurrentID is not None:
                FoundOutputs.append(CurrentID)

    return FoundOutputs

def FindInputByName(Name):
    FoundInputs = []

    try:
        out = subprocess.check_output(
            ["pactl", "list", "sources"]
        ).decode()
    except:
        return FoundInputs

    CurrentID = None

    for line in out.splitlines():
        line = line.strip()

        if line.startswith("Name:"):
            CurrentID = line.split(":", 1)[1].strip()

        elif line.startswith("Description:"):
            Description = line.split(":", 1)[1].strip()

            if Description == Name and CurrentID is not None:
                FoundInputs.append(CurrentID)

    return FoundInputs

def FindAudioSourceByName(Name):
    FoundSources = []

    try:
        out = subprocess.check_output(
            ["pactl", "list", "sink-inputs"]
        ).decode()
    except:
        return FoundSources

    CurrentID = None

    for line in out.splitlines():
        line = line.strip()

        if line.startswith("Sink Input #"):
            CurrentID = line.replace("Sink Input #", "").strip()

        elif "application.name" in line:
            AppName = line.split("=", 1)[1].strip().strip('"')

            if AppName == Name and CurrentID is not None:
                FoundSources.append(CurrentID)

    return FoundSources

def PactlAttach(Source,Wire, AttachmentType, IDIndex):
    if AttachmentType == "SourceToSink":
        subprocess.call([
        NWPath,
        "ConnectSourceToSink",
        Source['Name'],
        Wire['InternalName'],
        str(Source['Mono'])
        ])
        print("made it past")
        
        return
    elif AttachmentType == "SinkToOutput":
        subprocess.call([
        NWPath,
        "ConnectSinkToAux",
        Wire['InternalName'],
        Source['IDs'][IDIndex],
        str(Source['Mono'])
        ])
        return
    elif AttachmentType == "SinkToInput":
        subprocess.call([
        NWPath,
        "ConnectMicToSink",
        Source['IDs'][IDIndex],
        Wire['InternalName'],
        ])
        return

    
    return

def PactlRemove(Source,Wire, DetachmentType, IDIndex):

    if DetachmentType == "SourceFromSink":

        subprocess.call([
        NWPath,
        "RemoveSourceFromSink",
        Source['Name']
        ])
        
        return
    elif DetachmentType == "SinkFromOutput":
        subprocess.call([
        NWPath,
        "RemoveSinkFromAux",
        Wire['InternalName'],
        Source['IDs'][IDIndex]
        ])
        return
    elif DetachmentType == "SinkFromInput":

        subprocess.call([
        NWPath,
        "RemoveMicFromSink",
        Source['IDs'][IDIndex],
        Wire['InternalName']
        ])
        return

    return

def PactlSetVolume(Source, VolumeType):

    Call = None
    

    if VolumeType == "Sink":
        Call = "SetSinkVolume"
        Name = Source['InternalName']

    elif VolumeType == "Aux":
        Call = "SetAuxVolume"
        Name = Source['IDs'][0]
        print(Name)

    elif VolumeType == "Mic":
        Call = "SetMicVolume"
        Name = Source['IDs'][0]

    elif VolumeType == "Source":
        Call = "SetSourceVolume"
        Name = Source['Name']

    if Call is None:
        Log(f"NullWire: Idk wtf you're tryna do. error setting volume", "Error")
        return

    subprocess.call([
        NWPath,
        Call,
        Name,
        str(Source['Volume']),
        str(Source['Muted'])
        ])

    return

def NullWireCreatePopupWindow(ThisType, Wire):

    ExcludeThis = Wire['Name']

    Result = {"Value": None}

    Popup = tk.Toplevel(Root)
    Popup.title(f"Select {ThisType}")
    Popup.geometry("600x800")
    Popup.grab_set()

    ListFrame = ScrollableFrame(Popup)
    ListFrame.pack(fill="both", expand=True)

    Inner = ListFrame.Inner

    if ThisType == "Output":
        GetAllOutputDevices()
        Items = CurrentOutputs

    elif ThisType == "Input":
        GetAllInputDevices()
        Items = CurrentInputs

    elif ThisType == "Source":
        GetAllAudioSources()

        Items = CurrentSources

    def SelectItem(Name, IsSteam):
        Result["Value"] = Name
        if IsSteam:
            if Wire['SteamAsk'] == False:
                Answer = NullMessageBox(Root,
                    "Audo Add Steam Games To This Wire?",
                    "Upon clicking yes... Anytime you start a game on Steam. It will auto connect to this Wire. \n Do you want this to happen?",
                    ("Yes Please", "No Thanks")
                    ).Show()
                
                if Answer == "Yes Please":
                    Wire['SteamAppAuto'] = True

                Wire['SteamAsk'] = True
        Popup.destroy()

    for Item in Items:
        if Item == ExcludeThis or Item == f"{ExcludeThis}_NullWire":
            continue

        if ThisType == "Output" and any(Device["Name"] == Item for Device in Wire["AttachedOutputs"]):
            continue

        if ThisType == "Input" and any(Device["Name"] == Item for Device in Wire["AttachedInputs"]):
            continue

        if ThisType == "Source" and any(Source["Name"] == Item for Source in Wire["AudioSourcesIn"]):
            continue

        if ThisType == "Source":
            WindowClass = SourceWindowClass.get(Item) or ""
            issteamapp = "steam_app" in WindowClass.lower()
        else:
            issteamapp = False

        Button = nulltk.Button(
            Inner,
            text=Item,
            command=lambda value=Item, steam=issteamapp: SelectItem(value,steam)
        )
        Button.pack(fill="x", padx=5, pady=2)

    Popup.wait_window()

    return Result["Value"]

def GetAllOutputDevices():
    global CurrentOutputs
    try:
        out = subprocess.check_output(["pactl", "list", "sinks"]).decode()
    except:
        return

    CurrentOutputs = []

    for line in out.splitlines():
        line = line.strip()
        if "Description:" in line:
            name = line.split(":", 1)[1].strip()
            if name not in CurrentOutputs:
                CurrentOutputs.append(name)

    return

def GetAllInputDevices():
    global CurrentInputs

    try:
        out = subprocess.check_output(["pactl", "list", "sources"]).decode()
    except:
        return

    CurrentInputs = []

    for line in out.splitlines():
        line = line.strip()

        if "Description:" in line:
            name = line.split(":", 1)[1].strip()

            if name not in CurrentInputs:
                CurrentInputs.append(name)

    return

def GetAllAudioSources():
    global CurrentSources, SourceWindowClass

    try:
        out = subprocess.check_output(
            ["pactl", "list", "sink-inputs"]
        ).decode()
    except:
        return []

    CurrentSources = []
    SourceWindowClass = {}

    CurrentName = None
    CurrentPID = None

    try:
        WindowList = subprocess.check_output(
            ["wmctrl", "-lp"]
        ).decode().splitlines()
    except:
        WindowList = []

    for line in out.splitlines():
        line = line.strip()

        if "application.name" in line:
            CurrentName = line.split("=", 1)[1].strip().strip('"')

        elif "application.process.id" in line:
            CurrentPID = line.split("=", 1)[1].strip().strip('"')

            if CurrentName is None:
                continue

            if CurrentName not in CurrentSources:
                CurrentSources.append(CurrentName)

            WMClass = None

            for Window in WindowList:
                Parts = Window.split(None, 4)

                if len(Parts) < 3:
                    continue

                WindowPID = Parts[2]

                if WindowPID == CurrentPID:
                    WindowID = Parts[0]

                    try:
                        ClassInfo = subprocess.check_output(
                            ["xprop", "-id", WindowID, "WM_CLASS"],
                            stderr=subprocess.DEVNULL
                        ).decode()

                        WMClass = ClassInfo.strip().split('"')[-2].lower()
                        break

                    except:
                        pass

            SourceWindowClass[CurrentName] = WMClass

    return

def NormalizeDeviceVolumesInSinks(DeviceName, NewVolume,NewMute,NewMono, Outputs):
    global OutputRows, InputRows
    Rows = OutputRows if Outputs else InputRows
    for MainFrame, RowData in Rows.items():
        if DeviceName in RowData["DeviceRows"]:
            RowData["DeviceRows"][DeviceName]["Volume"].set(NewVolume)
            RowData["DeviceRows"][DeviceName]["Mute"].set(NewMute)
            RowData["DeviceRows"][DeviceName]["Mono"].set(NewMono)

    return

def NormalizeSourceVolumesInSinks(SourceName, NewVolume,NewMute,NewMono):
    global OutputRows
    Rows = OutputRows
    for MainFrame, RowData in Rows.items():
        if SourceName in RowData["SourceRows"]:
            RowData["SourceRows"][SourceName]["Volume"].set(NewVolume)
            RowData["SourceRows"][SourceName]["Mute"].set(NewMute)
            RowData["SourceRows"][SourceName]["Mono"].set(NewMono)

    return


def AddOutputWire():
    global OutputWires

    if NullWireOutputName.get() == "" or NullWireOutputName.get() in OutputWires:
        return
    
    WireName = NullWireOutputName.get().strip()
    InternalName = WireName.replace(" ", "_") + "_NullWire"

    ThisOutputWire = OutputWires[NullWireOutputName.get()] = {
        "Name": WireName,
        "InternalName": InternalName,
        "Muted": False,
        "Volume": 100,
        "Delete": False,
        "LimiterToggle": False,
        "Limiter": 50,
        "SteamAppAuto": False,
        "SteamAsk": False,
        "AttachedOutputs": [],
        "AudioSourcesIn": []
    }

    NullWireOutputName.set("")

    CreateOutputWire(ThisOutputWire)

    return

def CreateOutputWire(OutputWire):
    global OutputRows, OutputWires

    subprocess.call([
        NWPath,
        "CreateSink",
        OutputWire['InternalName'],
        ])



    MainFrame = nulltk.LabelFrame(NullWireOutputListInner, text= OutputWire['Name'])
    MainFrame.pack(fill="x", expand=True, padx=10, pady=10)
    MainFrame.columnconfigure(1,weight=1)

    WireIsCollapsed = tk.BooleanVar(value=True)

    def CollapseWire(Button):
        if WireIsCollapsed.get() == True:
            WireIsCollapsed.set(False)
            Button.config(text="▼")
            WireAddativesFrame.grid(row=1,column=1,sticky="nsew")
        else:
            WireIsCollapsed.set(True)
            Button.config(text="▶")
            WireAddativesFrame.grid_forget()

        return

    CollapseButton = nulltk.Button(MainFrame, text = "▶", command=lambda: CollapseWire(CollapseButton))
    CollapseButton.grid(row=0,column=0, pady=10, padx=(10, 5), sticky="ew")

    # ---- Top Frame

    WireTopFrame = nulltk.Frame(MainFrame)
    WireTopFrame.grid(row=0,column=1,pady=(10,5), padx=(5,10), sticky="nsew", columnspan=99)
    

    def SetMute():
        OutputWire['Muted'] = Muted.get()
        PactlSetVolume(OutputWire,"Sink")
        return

    Muted = tk.BooleanVar(value=OutputWire['Muted'])
    WireMute = nulltk.Checkbutton(WireTopFrame, variable=Muted, command=SetMute, text="Mute")
    WireMute.grid(row=0,column=0, sticky="we", padx=(0,10))

    def SwitchLimited():
        OutputWire['LimiterToggle'] = Limited.get()
        LimitedToggle.grid(row=0,column=1, sticky="e")

        if Limited.get() == True:
            WireTopFrame.columnconfigure(2,weight=1)
            WireTopFrame.columnconfigure(3,weight=0)
            WireTopFrame.columnconfigure(5,weight=1)
            
            LimitedScale.grid(row=0,column=2, sticky="ew")
            LimitedAmountShow.grid(row=0,column=3, sticky="w", padx=(0,10))

            VolumeLabel.grid(row=0,column=4, sticky="e", padx=(10,0))
            VolumeScale.grid(row=0,column=5, sticky="ew")
            VolumeAmountShow.grid(row=0,column=6, sticky="w", padx=(0,10))
        else:
            LimitedScale.grid_forget()
            LimitedAmountShow.grid_forget()
            WireTopFrame.columnconfigure(2,weight=0)
            WireTopFrame.columnconfigure(3,weight=1)
            WireTopFrame.columnconfigure(5,weight=0)

            VolumeLabel.grid(row=0,column=2, sticky="e", padx=(10,0))
            VolumeScale.grid(row=0,column=3, sticky="ew", columnspan=1)
            VolumeAmountShow.grid(row=0,column=6, sticky="w", padx=(0,10))

    def SetLimiter():   
        OutputWire['Limiter'] = LimitedAmount.get()
        return
        
    Limited = tk.BooleanVar(value=OutputWire['LimiterToggle'])
    LimitedToggle = nulltk.Checkbutton(WireTopFrame, variable=Limited, command=SwitchLimited, text="Limiter")

    LimitedAmount = tk.IntVar(value=OutputWire['Limiter'])
    LimitedScale = nulltk.Scale(WireTopFrame,from_=0,to=100,orient="horizontal",showvalue=0,variable=LimitedAmount)
    LimitedAmountShow = nulltk.Label(WireTopFrame, textvariable=LimitedAmount, width=4)
    

    def SetVolume(event=None):
        OutputWire['Volume'] = Volume.get()
        PactlSetVolume(OutputWire,"Sink")
        return

    Volume = tk.IntVar(value=OutputWire['Volume'])
    VolumeLabel = nulltk.Label(WireTopFrame, text="Volume")
    VolumeLabel.grid(row=0,column=4, sticky="e", padx=(10,0))
    VolumeScale = nulltk.Scale(WireTopFrame,from_=0,to=200,orient="horizontal",showvalue=0,variable=Volume)
    VolumeScale.grid(row=0,column=5, sticky="ew")
    VolumeAmountShow = nulltk.Label(WireTopFrame, textvariable=Volume, width=4)
    VolumeAmountShow.grid(row=0,column=6, sticky="w", padx=(0,10))

    SwitchLimited()

    def DeleteWire(Button, Timeout=4):
        EndTime = time.time() + Timeout

        def tick():
            Remaining = int(EndTime - time.time())
            if Remaining <= 0:
                if not Button.winfo_exists():
                    return

                Button.config(text="Delete")
                OutputWire['Delete'] = False
                return

            if not Button.winfo_exists():
                return
            Button.config(text=f"R U Sure? {Remaining}")
            Root.after(1000, tick)
            return
        
        if OutputWire['Delete'] == False:
            OutputWire['Delete'] = True
            tick()
            return

        subprocess.call([
        NWPath,
        "DeleteSink",
        OutputWire['InternalName'],
        ])

        del OutputWires[OutputWire['Name']]
        del OutputRows[MainFrame]

        MainFrame.destroy()
        return
    
    DeleteButton = nulltk.Button(WireTopFrame, text="Delete", command=lambda: DeleteWire(DeleteButton))
    DeleteButton.grid(row=0,column=7,sticky="ew")

    WireAddativesFrame = nulltk.Frame(MainFrame)
    WireAddativesFrame.grid(row=1,column=1,sticky="nsew",padx=10, pady=10, columnspan=99)
    WireAddativesFrame.columnconfigure(0,weight=1)
    WireAddativesFrame.grid_forget()
    
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------- the bullshit part

    

    WireOutputList = nulltk.LabelFrame(WireAddativesFrame, text="Play Audio On These Devices")
    WireOutputList.grid(row=0,column=0, sticky="nsew", pady=10, columnspan=99, padx=10,)
    WireOutputList.columnconfigure(2,weight=1)

    def CollapseWireOutputList(Button):
        if WireOutputListIsCollapsed.get() == True:
            WireOutputListIsCollapsed.set(False)
            Button.config(text="▼")
            WireOutputListFrame.grid(row=0, column=2,sticky="nsew",padx=(0,5), pady=9)
        else:
            WireOutputListIsCollapsed.set(True)
            Button.config(text="▶")
            WireOutputListFrame.grid_forget()

        return
    
    WireOutputListIsCollapsed = tk.BooleanVar(value=False)
    WireOutputListCollapseButton = nulltk.Button(WireOutputList, text = "▶", command=lambda: CollapseWireOutputList(WireOutputListCollapseButton))
    WireOutputListCollapseButton.grid(row=0,column=0, pady=10, padx=(10, 5), sticky="new")

    def AddDeviceToWire():
        DeviceFound = NullWireCreatePopupWindow("Output",OutputWire)

        if DeviceFound == None:
            return

        Device = {
            "Name": DeviceFound,
            "Connected": True,
            "IDs": [],
            "Muted": False,
            "Mono": False,
            "Volume": 100,
            "Delete": False
            }
        OutputWire['AttachedOutputs'].append(Device)

        CreateDeviceOnWire(Device)
        return

    def CreateDeviceOnWire(DeviceSent):
        if WireOutputListIsCollapsed.get():
            CollapseWireOutputList(WireOutputListCollapseButton)

        DeviceFrame = nulltk.LabelFrame(WireOutputListListInner, text= DeviceSent['Name'], bd=4)
        DeviceFrame.pack(fill="both", expand=True, padx=10, pady=10)
        DeviceFrame.rowconfigure(0,weight=1)
        DeviceFrame.columnconfigure(4,weight=1)

        def ConnectDevice():
            DeviceSent['Connected'] = DeviceConnected.get()

            AllIDs = ResolveID(DeviceSent['Name'], "Output")

            if not AllIDs:
                Log(f"No Ids Found for {DeviceSent['Name']}", "Error")
                return
            
            else:
                DeviceSent['IDs'] = AllIDs
                for i in range(len(AllIDs)):
                    if DeviceConnected.get() == True:
                        PactlAttach(DeviceSent,OutputWire,"SinkToOutput", i)
                    else:
                        PactlRemove(DeviceSent,OutputWire,"SinkFromOutput", i)

            return

        DeviceConnected = tk.BooleanVar(value=DeviceSent['Connected'])
        DeviceConnectedToggle = nulltk.Checkbutton(DeviceFrame, variable=DeviceConnected, command=ConnectDevice, text="Connected |")
        DeviceConnectedToggle.grid(row=0,column=0, sticky="we", padx=(10,10), pady=5)


        def SetDeviceMono():
            DeviceSent['Mono'] = DeviceMono.get()
            PactlSetVolume(DeviceSent,"Aux")
            NormalizeDeviceVolumesInSinks(DeviceSent['Name'],DeviceSent['Volume'], DeviceSent['Muted'],DeviceSent['Mono'], True )
            return
        
        DeviceMono = tk.BooleanVar(value=DeviceSent['Mono'])
        DeviceMonoCheck = nulltk.Checkbutton(DeviceFrame, variable=DeviceMono, command=SetDeviceMono, text="Mono")
        DeviceMonoCheck.grid(row=0,column=1, sticky="we", padx=(10,0), pady=5)


        def SetDeviceMute():
            DeviceSent['Muted'] = DeviceMuted.get()
            PactlSetVolume(DeviceSent,"Aux")
            NormalizeDeviceVolumesInSinks(DeviceSent['Name'],DeviceSent['Volume'], DeviceSent['Muted'],DeviceSent['Mono'], True )

            return

        DeviceMuted = tk.BooleanVar(value=DeviceSent['Muted'])
        DeviceMute = nulltk.Checkbutton(DeviceFrame, variable=DeviceMuted, command=SetDeviceMute, text="Mute")
        DeviceMute.grid(row=0,column=2, sticky="we", padx=10, pady=5)

        def SetDeviceVolume(Event=None):
            DeviceSent['Volume'] = DeviceVolume.get()
            PactlSetVolume(DeviceSent,"Aux")
            NormalizeDeviceVolumesInSinks(DeviceSent['Name'],DeviceSent['Volume'], DeviceSent['Muted'],DeviceSent['Mono'], True )
            return


        DeviceVolume = tk.IntVar(value=DeviceSent['Volume'])
        DeviceVolumeLabel = nulltk.Label(DeviceFrame, text="Volume:")
        DeviceVolumeLabel.grid(row=0,column=3, sticky="w", pady=5)
        DeviceVolumeScale = nulltk.Scale(DeviceFrame,from_=0,to=100,orient="horizontal",showvalue=0,variable=DeviceVolume)
        DeviceVolumeScale.grid(row=0,column=4, sticky="ew", pady=5)
        DeviceVolumeAmountShow = nulltk.Label(DeviceFrame, textvariable=DeviceVolume)
        DeviceVolumeAmountShow.grid(row=0,column=5, sticky="w", padx=(0,10), pady=5)

        DeviceVolumeScale.bind("<ButtonRelease-1>", SetDeviceVolume)
        DeviceVolumeScale.bind("<Button-4>",lambda e: (DeviceVolumeScale.set(min(100, DeviceVolumeScale.get() + 5)),SetDeviceVolume()))
        DeviceVolumeScale.bind("<Button-5>",lambda e: (DeviceVolumeScale.set(max(0, DeviceVolumeScale.get() - 5)),SetDeviceVolume()))

        def DeleteDevice(Button, Timeout=4):
            EndTime = time.time() + Timeout

            def tick():
                Remaining = int(EndTime - time.time())
                if Remaining <= 0:
                    if not Button.winfo_exists():
                        return

                    Button.config(text="Remove")
                    DeviceSent['Delete'] = False
                    return

                if not Button.winfo_exists():
                    return
                Button.config(text=f"R U Sure? {Remaining}")
                Root.after(1000, tick)
                return

            if DeviceSent['Delete'] == False:
                DeviceSent['Delete'] = True
                tick()
                return


            PactlRemove(DeviceSent, OutputWire,"SinkFromOutput",0)
            OutputWire['AttachedOutputs'].remove(DeviceSent)
            del OutputRows[MainFrame]['DeviceRows'][DeviceSent['Name']]
            DeviceFrame.destroy()
            return
    
        DeviceDeleteButton = nulltk.Button(DeviceFrame, text="Remove", command=lambda: DeleteDevice(DeviceDeleteButton))
        DeviceDeleteButton.grid(row=0,column=6,sticky="ew", padx=10, pady=5)

        ConnectDevice()
        OutputRows[MainFrame]['DeviceRows'][DeviceSent['Name']] = {
            "Frame": DeviceFrame,
            "Volume": DeviceVolume,
            "Mute": DeviceMuted,
            "Mono": DeviceMono
        }
        return

    WireOutputListAddDevice = nulltk.Button(WireOutputList, text = "+", command=lambda: AddDeviceToWire())
    WireOutputListAddDevice.grid(row=0,column=1, pady=10, padx=(10, 5), sticky="new")

    WireOutputListFrame = nulltk.LabelFrame(WireOutputList)
    WireOutputListFrame.grid(row=0, column=2,sticky="nsew",padx=(0,5), pady=8)
    WireOutputListFrame.config(height=200)
    WireOutputListFrame.columnconfigure(0,weight=1)

    CollapseWireOutputList(WireOutputListCollapseButton)


    WireOutputListList = ScrollableFrame(WireOutputListFrame)
    WireOutputListList.grid(row=0, column=0,sticky="nsew")
    WireOutputListList.columnconfigure(0,weight=1)


    WireOutputListListInner = WireOutputListList.Inner

    #########----------------------------------------------------------------------------------------------------------------------------------------------------- sources list

    SourcesOutputList = nulltk.LabelFrame(WireAddativesFrame, text="Capture These Programs")
    SourcesOutputList.grid(row=1,column=0, sticky="nsew", pady=10, columnspan=99, padx=10)
    SourcesOutputList.columnconfigure(2,weight=1)

    def CollapseWireSourceList(Button):
        if WireSourceListIsCollapsed.get() == True:
            WireSourceListIsCollapsed.set(False)
            Button.config(text="▼")
            WireSourcesListFrame.grid(row=0, column=2,sticky="nsew",padx=(0,5), pady=9)
        else:
            WireSourceListIsCollapsed.set(True)
            Button.config(text="▶")
            WireSourcesListFrame.grid_forget()

        return

    def AddSourceToWire():
        DeviceFound = NullWireCreatePopupWindow("Source",OutputWire)

        if DeviceFound == None:
            return

        Device = {
            "Name": DeviceFound,
            "Connected": True,
            "ID": None,
            "Mono": False,
            "Muted": False,
            "Volume": 100,
            "Delete": False
            }
        
        OutputWire['AudioSourcesIn'].append(Device)

        CreateSourceOnWire(Device)
        return

    def CreateSourceOnWire(SourceSent):
        if WireSourceListIsCollapsed.get():
            CollapseWireSourceList(WireSourceListCollapseButton)

        SourceFrame = nulltk.LabelFrame(WireSourceListListInner, text=SourceSent['Name'], bd=4)
        SourceFrame.pack(fill="both", expand=True, padx=10, pady=10)
        SourceFrame.rowconfigure(0,weight=1)
        SourceFrame.columnconfigure(4,weight=1)

        def ConnectSource():
            SourceSent['Connected'] = SourceConnected.get()

            if SourceConnected.get() == True:
                PactlAttach(SourceSent,OutputWire,"SourceToSink", 0)
            else:
                PactlRemove(SourceSent,OutputWire,"SourceFromSink", 0)

            return

        SourceConnected = tk.BooleanVar(value=SourceSent['Connected'])
        SourceConnectedToggle = nulltk.Checkbutton(SourceFrame, variable=SourceConnected, command=ConnectSource, text="Connected |")
        SourceConnectedToggle.grid(row=0,column=0, sticky="we", padx=(10,10), pady=5)

        def SetSourceMono():
            SourceSent['Mono'] = SourceMono.get()
            if SourceConnected.get() == True:
                PactlAttach(SourceSent,OutputWire,"SourceToSink", 0)
            else:
                PactlRemove(SourceSent,OutputWire,"SourceFromSink", 0)

            NormalizeSourceVolumesInSinks(SourceSent['Name'],SourceSent['Volume'], SourceSent['Muted'],SourceSent['Mono'])
            return
        
        SourceMono = tk.BooleanVar(value=SourceSent['Mono'])
        SourceMonoCheck = nulltk.Checkbutton(SourceFrame, variable=SourceMono, command=SetSourceMono, text="Mono")
        SourceMonoCheck.grid(row=0,column=1, sticky="we", padx=(10,0), pady=5)

        def SetSourceMute():
            SourceSent['Muted'] = SourceMuted.get()
            PactlSetVolume(SourceSent,"Source")
            NormalizeSourceVolumesInSinks(SourceSent['Name'],SourceSent['Volume'], SourceSent['Muted'],SourceSent['Mono'])

            return

        SourceMuted = tk.BooleanVar(value=SourceSent['Muted'])
        SourceMute = nulltk.Checkbutton(SourceFrame, variable=SourceMuted, command=SetSourceMute, text="Mute")
        SourceMute.grid(row=0,column=2, sticky="we",padx=10, pady=5)

        def SetSourceVolume(Event=None):
            SourceSent['Volume'] = SourceVolume.get()
            PactlSetVolume(SourceSent,"Source")
            NormalizeSourceVolumesInSinks(SourceSent['Name'],SourceSent['Volume'], SourceSent['Muted'],SourceSent['Mono'])
            return


        SourceVolume = tk.IntVar(value=SourceSent['Volume'])
        SourceVolumeLabel = nulltk.Label(SourceFrame, text="Volume:")
        SourceVolumeLabel.grid(row=0,column=3, sticky="w", pady=10)
        SourceVolumeScale = nulltk.Scale(SourceFrame,from_=0,to=100,orient="horizontal",showvalue=0,variable=SourceVolume)
        SourceVolumeScale.grid(row=0,column=4, sticky="we", pady=5)
        SourceVolumeAmountShow = nulltk.Label(SourceFrame, textvariable=SourceVolume)
        SourceVolumeAmountShow.grid(row=0,column=5, sticky="w")

        SourceVolumeScale.bind("<ButtonRelease-1>", SetSourceVolume)
        SourceVolumeScale.bind("<Button-4>",lambda e: (SourceVolumeScale.set(min(100, SourceVolumeScale.get() + 5)),SetSourceVolume()))
        SourceVolumeScale.bind("<Button-5>",lambda e: (SourceVolumeScale.set(max(0, SourceVolumeScale.get() - 5)),SetSourceVolume()))

        def DeleteSource(Button, Timeout=4):
            EndTime = time.time() + Timeout

            def tick():
                Remaining = int(EndTime - time.time())
                if Remaining <= 0:
                    if not Button.winfo_exists():
                        return

                    Button.config(text="Remove")
                    SourceSent['Delete'] = False
                    return

                if not Button.winfo_exists():
                    return
                Button.config(text=f"R U Sure? {Remaining}")
                Root.after(1000, tick)
                return

            if SourceSent['Delete'] == False:
                SourceSent['Delete'] = True
                tick()
                return


            PactlRemove(SourceSent,OutputWire,"SourceFromSink",0)
            OutputWire['AudioSourcesIn'].remove(SourceSent)
            del OutputRows[MainFrame]['SourceRows'][SourceSent['Name']]
            SourceFrame.destroy()
            return
    
        SourceDeleteButton = nulltk.Button(SourceFrame, text="Remove", command=lambda: DeleteSource(SourceDeleteButton))
        SourceDeleteButton.grid(row=0,column=6,sticky="ew",padx=10)

        ConnectSource
        OutputRows[MainFrame]['SourceRows'][SourceSent['Name']] = {
            "Frame": SourceFrame,
            "Volume": SourceVolume,
            "Mute": SourceMuted,
            "Mono": SourceMono
        }
        return

    WireSourceListIsCollapsed = tk.BooleanVar(value=False)
    WireSourceListCollapseButton = nulltk.Button(SourcesOutputList, text = "▶", command=lambda: CollapseWireSourceList(WireSourceListCollapseButton))
    WireSourceListCollapseButton.grid(row=0,column=0, pady=10, padx=(10, 5), sticky="new")

    WireSourceListAddDevice = nulltk.Button(SourcesOutputList, text = "+", command=lambda: AddSourceToWire())
    WireSourceListAddDevice.grid(row=0,column=1, pady=10, padx=(10, 5), sticky="new")

    WireSourcesListFrame = nulltk.LabelFrame(SourcesOutputList)
    WireSourcesListFrame.grid(row=0, column=2,sticky="nsew",padx=(0,5), pady=9)
    WireSourcesListFrame.config(height=200)
    WireSourcesListFrame.columnconfigure(0,weight=1)

    CollapseWireSourceList(WireSourceListCollapseButton)

    WireSourceListList = ScrollableFrame(WireSourcesListFrame)
    WireSourceListList.grid(row=0, column=0,sticky="nsew")
    WireSourceListList.columnconfigure(0,weight=1)
    

    WireSourceListListInner = WireSourceListList.Inner

    #--- append

    OutputRows[MainFrame] = {
        "DeviceRows": {},
        "SourceRows": {}

    }

    #------ binding

    NullWireOutputList.BindMouseWheel(MainFrame)

    VolumeScale.bind("<ButtonRelease-1>", SetVolume)
    VolumeScale.bind("<Button-4>",lambda e: (VolumeScale.set(min(200, VolumeScale.get() + 5)),SetVolume()))
    VolumeScale.bind("<Button-5>",lambda e: (VolumeScale.set(max(0, VolumeScale.get() - 5)),SetVolume()))

    LimitedScale.bind("<ButtonRelease-1>", SetLimiter)
    LimitedScale.bind("<Button-4>",lambda e: (LimitedScale.set(min(100, LimitedScale.get() + 5)),SetLimiter()))
    LimitedScale.bind("<Button-5>",lambda e: (LimitedScale.set(max(0, LimitedScale.get() - 5)),SetLimiter()))

    #------ LoadingBullshit

    for item in OutputWire['AttachedOutputs']:
        CreateDeviceOnWire(item)
    for item in OutputWire['AudioSourcesIn']:
        CreateSourceOnWire(item)

    return    


def AddInputWire():

    return


NullWireNotebook = nulltk.Notebook(NullWire)
#REMOVEWHENDONE
#Notebook.forget(NullWire)

NullWireNotebook.pack(fill="both", expand=True)
NullWireOutputWires = nulltk.Frame(NullWireNotebook)
NullWireInputWires = nulltk.Frame(NullWireNotebook)
NullWireNotebook.add(NullWireOutputWires, text="Output Wires")
NullWireNotebook.add(NullWireInputWires, text="Input Wires")
    #region OutputWires
NullWireOutputPage = nulltk.Frame(NullWireOutputWires)
NullWireOutputPage.pack(fill="both", expand=True)
NullWireOutputPage.rowconfigure(1, weight=1)
NullWireOutputPage.columnconfigure(0, weight=1)

NullWireOutputTop = nulltk.Frame(NullWireOutputPage)
NullWireOutputTop.grid(row=0,column=0,sticky="ew", padx=10,pady=5)
NullWireOutputTop.rowconfigure(1, weight=1)
NullWireOutputTop.columnconfigure(1, weight=1)

NullWireOutputName = tk.StringVar(value="")

NullWireOutputEntry = nulltk.Entry(NullWireOutputTop, textvariable=NullWireOutputName)
NullWireOutputEntry.grid(row=0,column=1,sticky="ew")
NullWireOutputEntry.bind("<Return>",lambda event: AddOutputWire())

NullWireAddOutputWireButton = nulltk.Button(NullWireOutputTop, text="Add Output Wire", command=lambda: AddOutputWire(), width = 16)
NullWireAddOutputWireButton.grid(row=0,column=0,sticky="ew")


NullWireOutputList = ScrollableFrame(NullWireOutputPage)
NullWireOutputList.grid(row=1,column=0,sticky="nsew", columnspan=99)
NullWireOutputList.columnconfigure(0,weight=1)

NullWireOutputListInner = NullWireOutputList.Inner

    #endregion

    #region InputWires
NullWireInputPage = nulltk.Frame(NullWireInputWires)
NullWireInputPage.pack(fill="both", expand=True)
NullWireInputPage.rowconfigure(1, weight=1)
NullWireInputPage.columnconfigure(0, weight=1)

NullWireInputTop = nulltk.Frame(NullWireInputPage)
NullWireInputTop.grid(row=0,column=0,sticky="ew", padx=10,pady=5)
NullWireInputTop.rowconfigure(1, weight=1)
NullWireInputTop.columnconfigure(0, weight=1)

NullWireInputEntry = nulltk.Entry(NullWireInputTop)
NullWireInputEntry.grid(row=0,column=0,sticky="ew")
NullWireInputEntry.bind("<Return>",lambda event: AddInputWire())

NullWireAddInputWireButton = nulltk.Button(NullWireInputTop, text="Add Input Wire", command=lambda: AddInputWire(), width = 16)
NullWireAddInputWireButton.grid(row=0,column=1,sticky="ew")

NullWireInputList = ScrollableFrame(NullWireInputPage)
NullWireInputList.grid(row=1,column=0,sticky="nsew", columnspan=99)

NullWireInputListInner = NullWireInputList.Inner
NullWireInputListInner.grid(row=0,column=0,sticky="nsew", columnspan=99)

    #endregion


def NullWireLoop():
    global LastOutputs, LastInputs, LastSources
    
    tick = 0
    while True:
        if NullWireActive.get() == True:
            if tick == 0:
                GetAllAudioSources()
                if CurrentSources != LastSources:
                    LastSources = CurrentSources
                    
                    for source in CurrentSources:
                        pass
                pass

            elif tick == 1:
                pass
            elif tick == 2:
                pass
            tick = (tick + 1) % 3
        time.sleep(1)


def StartUpNullWire():
    global Sinks, Devices, LoadCompleted, ActualProgramLoadedCount
    

    if NullWireActive.get() == True:
        LoadCompleted += 1
        return

        if not os.path.isfile(ConfigPath):
            Butts.set("Save File not found???")
            Root.update_idletasks()
            return False
        try:
            with open(ConfigPath, "r") as f:
                data = json.load(f)
                wire = data.get("NullWire", {})

            
            Notebook.add(NullWire, text="NullWire")
        except Exception as e:
            Butts.set(f"ERROR LOADING NULL WIRE SAVE\n\n{e}")
            Root.update_idletasks()
            return False
        
        ActualProgramLoadedCount+=1
    else:
        Notebook.forget(NullWire)
    
    LoadCompleted += 1
    return

#endregion

#region Start

Root.protocol("WM_DELETE_WINDOW", HideToTray)
Root.after(100, Startup)
Root.mainloop()

#endregion






