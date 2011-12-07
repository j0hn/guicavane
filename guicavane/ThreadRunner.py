#!/usr/bin/env python
# coding: utf-8

"""
ThreadRunner.

This module provides the class GtkThreadRunner that is used
to run a function on a thread and return the result when it's done
"""

import Queue
import gobject
import threading
import traceback
from guicavane.Utils.Log import console
from StringIO import StringIO

log = console("ThreadRunner")


class GtkThreadRunner(threading.Thread):
    """
    Run `func` in a thread with `args` and `kwargs` as arguments, when
    finished call callback with the result obtained or an exception caught.
    """

    def __init__(self, callback, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.callback = callback
        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.result = Queue.Queue()

        self.start()
        gobject.timeout_add(300, self.check)

    def run(self):
        """
        Main function of the thread, run func with args and kwargs
        and get the result, call callback with the result

        if an exception is thrown call callback with the exception
        """

        try:
            result = (False, self.func(*self.args, **self.kwargs))
        except Exception, ex:
            result = (True, ex)

            if self.func.im_class == type:
                methodname = "%s.%s" % (self.func.__self__.__name__, \
                                        self.func.im_func.func_name)
            else:
                methodname = "%s.%s" % (self.func.im_class.__name__, \
                                        self.func.im_func.func_name)

            error_str = StringIO()
            error_str.write("running: %s, args: %s, kwargs: %s\nDetails:\n" % \
                (methodname, self.args, self.kwargs))

            traceback.print_exc(file=error_str)
            error_str.seek(0)
            log.error(error_str.read())

        self.result.put(result)

    def check(self):
        """ Check if func finished. """

        try:
            result = self.result.get(False, 0.1)
        except Queue.Empty:
            return True

        self.callback(result)

        return False
