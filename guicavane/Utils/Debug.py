from tempfile import NamedTemporaryFile


def tmp_dump(data):
    """
    Create a dump file of data in the temp directory, with a random name
    """
    with NamedTemporaryFile(delete=False) as fd:
        name = fd.name
        fd.write(data)
    return name
