"""One application owner per data directory, across processes and platforms."""
import os
import stat
from pathlib import Path


def _windows_shared_stat(path):
    """Read authoritative attributes without excluding SQLite's open handles."""
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    create=kernel.CreateFileW
    create.argtypes=(wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE)
    create.restype=wintypes.HANDLE
    close=kernel.CloseHandle;close.argtypes=(wintypes.HANDLE,);close.restype=wintypes.BOOL
    class Information(ctypes.Structure):
        _fields_=[('attributes',wintypes.DWORD),('creation',wintypes.FILETIME),('access',wintypes.FILETIME),('write',wintypes.FILETIME),('volume',wintypes.DWORD),('size_high',wintypes.DWORD),('size_low',wintypes.DWORD),('links',wintypes.DWORD),('index_high',wintypes.DWORD),('index_low',wintypes.DWORD)]
    query=kernel.GetFileInformationByHandle
    query.argtypes=(wintypes.HANDLE,ctypes.POINTER(Information));query.restype=wintypes.BOOL
    # Attribute access only, share read/write/delete, and never follow reparse points.
    handle=create(str(path),0x80,0x7,None,3,0x02200000,None)
    if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    try:
        info=Information()
        if not query(handle,ctypes.byref(info)):raise ctypes.WinError(ctypes.get_last_error())
        if info.attributes&0x400 or info.links!=1:raise ValueError('Managed data file must be a regular, unlinked file: '+path.name)
        fd=msvcrt.open_osfhandle(handle,os.O_RDONLY);handle=None
        try:return os.fstat(fd)
        finally:os.close(fd)
    finally:
        if handle is not None:close(handle)


def managed_file(path):
    """An internal file may be absent, but must never redirect to another file.

    Owner-selected directory aliases are allowed; managed file leaves are not.
    lstat also detects dangling links, which exists() alone would miss.
    """
    path=Path(path)
    try:info=path.lstat()
    except FileNotFoundError:return None
    if os.name=='nt' and stat.S_ISREG(info.st_mode) and info.st_nlink==0:
        try:info=_windows_shared_stat(path)
        except FileNotFoundError:return None
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:
        raise ValueError('Managed data file must be a regular, unlinked file: '+path.name)
    return info


def managed_database(path):
    for leaf in (Path(path),*[Path(str(path)+suffix) for suffix in ('-wal','-shm','-journal')]):
        managed_file(leaf)


class DataLock:
    def __init__(self,root):self.root=Path(root);self.stream=None
    def __enter__(self):
        self.root.mkdir(parents=True,exist_ok=True)
        path=self.root/'app.lock';managed_file(path)
        fd=os.open(path,os.O_RDWR|os.O_CREAT|getattr(os,'O_NOFOLLOW',0),0o600)
        try:
            info=os.fstat(fd);current=managed_file(path)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or current is None
                    or (info.st_dev,info.st_ino)!=(current.st_dev,current.st_ino)):
                raise ValueError('Managed lock changed while opening')
            self.stream=os.fdopen(fd,'r+b');fd=None
        finally:
            if fd is not None:os.close(fd)
        try:
            self.stream.seek(0)
            if self.stream.read(1)==b'':self.stream.write(b'0');self.stream.flush()
            self.stream.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.stream.close();self.stream=None
            raise RuntimeError('ENGINEER OS is already using this data directory. Open the existing app or close its console first.') from None
        return self
    def __exit__(self,*args):
        if self.stream is not None:self.stream.close();self.stream=None
