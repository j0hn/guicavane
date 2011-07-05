Guicavane: a graphical user interface for cuevana.
==================================================

Guicavane tries to bring to the desktop the functionality provided by
the website www.cuevana.tv. That is the posibility to watch series
and movies streaming from a free online storage server such as
megaupload.

Guicavane uses GTK toolkit for the frontend with Glade as ui design.
For the backend uses a library made by Roger Duran, pycavane.

To download the source and start enjoying Guicavana run:

Linux Users
-----------

::

    $ git clone git@github.com:j0hn/guicavane.git
    $ git submodule init
    $ git submodule update
    $ # ???
    $ # profit
    $ python main.py


Windows Users
-------------

You can download the windows installer from the Download button
on the github page and install it as usual.
Make sure you have VLC installed and verify the path on guicavane
preferences so it points to vlc.exe. It's important that the path
to vlc.exe is quoted, so the preferences looks like this (or similar):

::

    "C:\Program files\Video LAN\VLC\vlc.exe" %s
