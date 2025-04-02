
def file_is_safe(file_object, safe_size):
    pos = file_object.tell()
    file_object.seek(0,2)
    size = file_object.tell()
    file_object.seek(pos)
    if size <= safe_size:
        return True
    else:
        return False