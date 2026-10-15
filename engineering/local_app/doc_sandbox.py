"""Linux DOC conversion child: limits and network denial before exec."""
import ctypes
import ctypes.util
import errno
import os
import resource
import socket
import stat
import sys


def apply(passive_local_ipc=False):
    if sys.platform!='linux':raise RuntimeError('DOC sandbox is Linux only')
    if type(passive_local_ipc) is not bool:raise RuntimeError('Invalid sandbox profile')
    if passive_local_ipc:
        # LibreOffice 24 requires local OSL pipe IPC. This profile is used only
        # after the formula scaffold whitelist, never for uploaded DOC packages.
        # Remove pre-existing sockets before allowing connect: only AF_UNIX
        # sockets can subsequently be created. Fail closed without procfs.
        for name in os.listdir('/proc/self/fd'):
            descriptor=int(name)
            try:
                if stat.S_ISSOCK(os.fstat(descriptor).st_mode):os.close(descriptor)
            except OSError:
                # The directory iterator itself may already have closed its fd.
                try:os.fstat(descriptor)
                except OSError:continue
                raise
    library=ctypes.util.find_library('seccomp')
    if not library:raise RuntimeError('Network sandbox unavailable')
    lib=ctypes.CDLL(library)
    lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
    lib.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint];lib.seccomp_rule_add.restype=ctypes.c_int
    class ArgCompare(ctypes.Structure):
        _fields_=[('arg',ctypes.c_uint),('op',ctypes.c_uint),
                  ('datum_a',ctypes.c_uint64),('datum_b',ctypes.c_uint64)]
    lib.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(ArgCompare)]
    lib.seccomp_rule_add_array.restype=ctypes.c_int
    lib.seccomp_load.argtypes=[ctypes.c_void_p];lib.seccomp_load.restype=ctypes.c_int
    lib.seccomp_release.argtypes=[ctypes.c_void_p]
    context=lib.seccomp_init(0x7fff0000)
    if not context:raise RuntimeError('Sandbox creation failed')
    try:
        denied=['sendto','sendmsg','sendmmsg','socketcall','io_uring_setup']
        if not passive_local_ipc:denied+=['socket','connect']
        else:
            call=lib.seccomp_syscall_resolve_name(b'socket')
            # SCMP_CMP_NE: reject every address family except local Unix IPC.
            comparison=ArgCompare(0,1,socket.AF_UNIX,0)
            if call<0 or lib.seccomp_rule_add_array(context,0x00050000|errno.EPERM,call,1,ctypes.byref(comparison))!=0:
                raise RuntimeError('Local IPC sandbox rule failed')
        for name in denied:
            call=lib.seccomp_syscall_resolve_name(name.encode())
            if call>=0 and lib.seccomp_rule_add(context,0x00050000|errno.EPERM,call,0)!=0:raise RuntimeError('Network rule failed')
        if lib.seccomp_load(context)!=0:raise RuntimeError('Network denial failed')
    finally:lib.seccomp_release(context)
    resource.setrlimit(resource.RLIMIT_CPU,(90,90))
    resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024**2,100*1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE,(512,512))


if __name__=='__main__':
    args=sys.argv[1:]
    passive_local_ipc=bool(args and args[0]=='--passive-local-ipc')
    if passive_local_ipc:args=args[1:]
    apply(passive_local_ipc=passive_local_ipc)
    if not args or not os.path.isabs(args[0]):raise SystemExit(2)
    os.execv(args[0],args)
