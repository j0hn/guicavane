from distutils.core import setup
import os
import py2exe

outdata_win = {
    "script": "guicavane.py",
    "icon_resources": [(1, "images/logo.ico")]
}

outdata_con = outdata_win.copy()
outdata_con['dest_base'] = "guicavane_debug"

opts = {
    'py2exe': {
        'packages': 'encodings, gtk',
        'includes': 'cairo, pangocairo, pango, atk, gobject, os, urllib, urllib2, cookielib, pycavane, config, gio',
        'excludes': ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
            "pywin.dialogs", "pywin.dialogs.list", "Tkconstants","Tkinter","tcl",
            "doctest", "macpath", "pdb", "ftplib", "win32wnet", "getopt",],
        'dll_excludes': ["w9xpopen.exe"],
        'dist_dir': './windows/build',
        }
    }

files = []
files.append((".", ["gui.glade"]))
files.append(("images", ["images/" + x for x in os.listdir("images")]))
    
setup(
    name="Guicavane",
    description="Graphical user interface for www.cuevana.tv",
    version="0.9",
    windows=[outdata_win],
    console=[outdata_con],
    options=opts,
    data_files=files)
