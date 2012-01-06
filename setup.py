#!/usr/bin/env python
# coding: utf-8

import os
import sys
from distutils.core import setup
from distutils.command.install import install

VERSION_NUMBER = "1.6.3"


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
    hosts_dir = "guicavane/Hosts"
    hosts = os.listdir(hosts_dir)
    hosts = ["guicavane.Hosts." + x for x in hosts if os.path.isdir(
        os.path.join(hosts_dir, x))]

    translations_dir = "guicavane/Translations"
    translations = []
    for trans in os.listdir(translations_dir):
        trans_path = os.path.join(translations_dir, trans)
        if os.path.isdir(trans_path):
            translations.append("Translations/" + trans + "/LC_MESSAGES/*")

    setup(
        name = "guicavane",
        version = VERSION_NUMBER,
        license = "GPL-3",
        author = "Gonzalo García Berrotarán",
        author_email = "j0hn.com.ar@gmail.com",
        description = "Graphical user interface for www.cuevana.tv",
        url = "http://www.github.com/j0hn/guicavane/",
        packages = ["guicavane", "guicavane.Downloaders", "guicavane.Utils",
                    "guicavane.Accounts", "guicavane.Hosts"] + hosts,
        package_data = {"guicavane": ["Glade/*.glade", "Images/*.png",
            "Images/Downloaders/*.png"] + translations},
        scripts = ["bin/guicavane"],
        cmdclass = {"install": CustomInstall}
    )

def setup_windows():
    import py2exe

    outdata_win = {
        "script": "bin\\guicavane",
        "dest_base": "guicavane",
        "icon_resources": [(1, "guicavane\\Images\\logo.ico")]
    }

    outdata_con = outdata_win.copy()
    outdata_con['dest_base'] = "guicavane_debug"

    opts = {
        'py2exe': {
            'packages': 'encodings, gtk, guicavane, guicavane.Downloaders',
            'includes': 'cairo, pangocairo, pango, atk, gobject, os, urllib,' \
                        'urllib2, cookielib, guicavane, gettext, gtk.glade, ' \
                        'gio, unicodedata, webbrowser, ' \
                        'guicavane.Downloaders, guicavane.Accounts, ' \
                        'guicavane.Utils',
            'excludes': ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                         "pywin.dialogs", "pywin.dialogs.list", "Tkconstants",
                         "Tkinter", "tcl", "doctest", "macpath", "pdb",
                         "ftplib", "win32wnet", "getopt",],
            'dll_excludes': ["w9xpopen.exe"],
            'dist_dir': './windows/build',
        }
    }


    files = []
    files.append(("Glade",
        ["guicavane\\Glade\\" + x for x in os.listdir("guicavane\\Glade")]))
    files.append(("Images",
        ["guicavane\\Images\\" + x for x in os.listdir("guicavane\\Images") if \
            not os.path.isdir("guicavane\\Images\\" + x)]))
    files.append(("Images\\Downloaders\\",
        ["guicavane\\Images\\Downloaders\\" + x for x in os.listdir("guicavane\\Images\\Downloaders\\")]))
    files.append(("Images\\Sites\\",
        ["guicavane\\Images\\Sites\\" + x for x in os.listdir("guicavane\\Images\\Sites\\")]))

    for translation in os.listdir("guicavane\\Translations\\"):
        if not os.path.isdir("guicavane\\Translations\\" + translation):
            continue

        files.append(("Translations\\" + translation + "\\LC_MESSAGES",
            ["guicavane\\Translations\\" + translation + "\\LC_MESSAGES\\" + \
            x for x in os.listdir("guicavane\\Translations\\" + translation + "\\LC_MESSAGES")]))


    hosts_dir = "guicavane\\Hosts"
    hosts = os.listdir(hosts_dir)
    hosts = [os.path.join(hosts_dir, x) for x in hosts if os.path.isdir(
        os.path.join(hosts_dir, x))]

    for host in hosts:
        cleanhost = host.replace("guicavane\\", "")
        files.append((cleanhost, [os.path.join(host, x) for x in os.listdir(host)]))

    setup(
        name = "Guicavane",
        license = "GPL-3",
        author = "Gonzalo García Berrotarán",
        author_email = "j0hn.com.ar@gmail.com",
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
