"""One application owner per data directory, across processes and platforms."""
import os
from pathlib import Path


class DataLock:
    def __init__(self,root):self.root=Path(root);self.stream=None
    def __enter__(self):
        self.root.mkdir(parents=True,exist_ok=True)
        self.stream=(self.root/'app.lock').open('a+b');self.stream.seek(0)
        if self.stream.read(1)==b'':self.stream.write(b'0');self.stream.flush()
        self.stream.seek(0)
        try:
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
