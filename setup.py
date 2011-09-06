#!/usr/bin/env python
# coding: utf-8

import os
import sys
from distutils.core import setup
from distutils.command.install import install

VERSION_NUMBER = "1.5.0"


class CustomInstall(install):
    def run(self):
        install.run(self)

        for script in self.distribution.scripts:
            script_path = os.path.join(self.install_scripts,
                os.path.basename(script))

            with open(script_path, "rb") as fh:
                content = fh.read()

            content = content.replace("@ INSTALLED_BASE_DIR @",
                self._custom_data_dir)

            with open(script_path, "wb") as fh:
                fh.write(content)

    def finalize_options(self):
        install.finalize_options(self)

        data_dir = os.path.join(self.prefix, "share", self.distribution.get_name())

        if self.root is None:
            build_dir = data_dir
        else:
            build_dir = os.path.join(self.root, data_dir[1:])

        self.install_lib = build_dir
        self._custom_data_dir = data_dir

def setup_linux():
    setup(
        name = "guicavane",
        version = VERSION_NUMBER,
        livense = "GPL-3",
        author = "Gonzalo García Berrotarán",
        author_email = "j0hn.com.ar@gmail.com",
        description = "Graphical user interface for www.cuevana.tv",
        url = "http://www.github.com/j0hn/guicavane/",
        packages = ["guicavane", "guicavane.Downloaders",
                    "guicavane.Accounts", "pycavane"],
        package_data = {"guicavane": ["glade/*.glade", "images/*.png",
            "images/hosts/*.png"]},
        scripts = ["bin/guicavane"],
        cmdclass = {"install": CustomInstall}
    )

def setup_windows():
    import py2exe

    outdata_win = {
        "script": "main.py",
        "dest_base": "guicavane",
        "icon_resources": [(1, "images/logo.ico")]
    }

    outdata_con = outdata_win.copy()
    outdata_con['dest_base'] = "guicavane_debug"

    opts = {
        'py2exe': {
            'packages': 'encodings, gtk, guicavane, guicavane.Downloaders',
            'includes': 'cairo, pangocairo, pango, atk, gobject, os, urllib,' \
                        'urllib2, cookielib, pycavane, guicavane, ' \
                        'guicavane.Downloaders, guicavane.Accounts, gio, ' \
                        'unicodedata, webbrowser',
            'excludes': ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                         "pywin.dialogs", "pywin.dialogs.list", "Tkconstants",
                         "Tkinter", "tcl", "doctest", "macpath", "pdb",
                         "ftplib", "win32wnet", "getopt",],
            'dll_excludes': ["w9xpopen.exe"],
            'dist_dir': './windows/build',
        }
    }

    files = []
    files.append(("glade", ["glade\\" + x for x in os.listdir("glade")]))
    files.append(("images", ["images\\" + x for x in os.listdir("images") if not os.path.isdir("images\\" + x)]))
    files.append(("images\\hosts\\", ["images\\hosts\\" + x for x in os.listdir("images\\hosts\\")]))

    setup(
        name = "Guicavane",
        description = "Graphical user interface for www.cuevana.tv",
        version = VERSION_NUMBER,
        windows = [outdata_win],
        console = [outdata_con],
        options = opts,
        data_files = files
    )


if __name__ == "__main__":
    path = os.path.dirname(sys.argv[0])
    if path:
        os.chdir(path)

    if os.name == "nt":
        setup_windows()
    else:
        setup_linux()
