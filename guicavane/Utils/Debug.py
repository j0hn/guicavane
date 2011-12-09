from guicavane.Utils.Log import console
from tempfile import NamedTemporaryFile

log = console()

def tmp_dump(data, what="Data"):
    """
    Create a dump file of data in the temp directory, with a random name
    """
    with NamedTemporaryFile(delete=False) as fd:
        name = fd.name
        fd.write(data)
    log.debug("Dumped '%s' in '%s'" % (what, name))
